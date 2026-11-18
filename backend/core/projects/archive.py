"""Yüklenen proje arşivinin güvenlik doğrulaması — H4-03 / Issue #35.

Arşiv **hiçbir zaman diske açılmaz, içindeki kod içe aktarılmaz veya çalıştırılmaz**. Doğrulama yalnızca
ZIP merkez dizinini okur ve her dosya girdisini sınırlı parçalar hâlinde bellekte açıp sayar:

* Biçim: uzantı ``.zip`` **ve** içerik ZIP imzasıyla başlamalı; bozuk/kesik/şifreli arşiv reddedilir.
* Yol güvenliği (Zip Slip): ``..``, ters eğik çizgi, mutlak yol, sürücü harfi (``C:``), UNC (``//sunucu``),
  denetim karakterleri, Windows'a özel ayrılmış adlar ve geçersiz karakterler reddedilir.
* Girdi türü: sembolik bağlantılar ve özel dosyalar (FIFO, aygıt, soket) reddedilir.
* Çakışmalar: yinelenen yol, büyük/küçük harf duyarsız çakışma (Windows/macOS) ve dosya–dizin çakışması.
* Kaynak sınırları: girdi sayısı, dizin derinliği, yol uzunluğu, tek dosya ve toplam açılmış boyut,
  sıkıştırma oranı. Bildirilen boyutlara güvenilmez: içerik gerçekten açılarak sayılır, sınır aşıldığı
  anda okuma durur; CRC hatası bozuk arşiv sayılır.

Sonuç, ``projects.validation_report`` (veri sözlüğü 10.1) için bir sözlük ve Django yapı taraması için
okunabilir küçük metin dosyalarıdır.
"""
from __future__ import annotations

import hashlib
import re
import stat
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import BinaryIO

ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
_CHUNK = 64 * 1024
_DRIVE_RX = re.compile(r"^[A-Za-z]:")
_INVALID_CHARS_RX = re.compile(r'[<>:"|?*]')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)),
                     *(f"LPT{i}" for i in range(1, 10))}
#: Açılmayacak (ileride çıkarılmayacak) gizli/hassas dosyalar; arşiv reddedilmez, raporda belirtilir.
_SECRET_NAMES = {".env", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519", ".netrc", ".pgpass"}
_SECRET_SUFFIXES = (".pem", ".key", ".p12", ".pfx")


@dataclass(frozen=True)
class ArchiveLimits:
    max_upload_bytes: int = 50 * 1024 * 1024
    max_total_uncompressed_bytes: int = 200 * 1024 * 1024
    max_member_bytes: int = 20 * 1024 * 1024
    max_entries: int = 10_000
    max_depth: int = 32
    max_path_length: int = 240
    max_compression_ratio: int = 100
    ratio_check_min_bytes: int = 1024 * 1024
    #: Şu anda yalnızca ZIP desteklenir; başka biçim eklemek ayrı bir doğrulayıcı gerektirir.
    allowed_extensions: tuple[str, ...] = (".zip",)

    @classmethod
    def from_settings(cls) -> "ArchiveLimits":
        from django.conf import settings

        exts = tuple(e.lower() for e in getattr(settings, "PROJECT_UPLOAD_ALLOWED_EXTENSIONS", [".zip"])
                     if e.lower() == ".zip")
        return cls(**getattr(settings, "PROJECT_UPLOAD_LIMITS", {}), allowed_extensions=exts or (".zip",))


class ArchiveRejected(Exception):
    """Arşiv güvenli değil veya geçersiz. ``code`` makine-okunur nedendir; ``entries`` ilgili girdilerdir."""

    def __init__(self, code: str, detail: str, entries: list[dict] | None = None):
        super().__init__(detail)
        self.code = code
        self.detail = detail
        self.entries = entries or []

    def as_dict(self) -> dict:
        data = {"code": self.code, "detail": self.detail}
        if self.entries:
            data["entries"] = self.entries[:50]
        return data


@dataclass
class ArchiveInspection:
    sha256: str
    size_bytes: int
    file_count: int
    dir_count: int
    uncompressed_bytes: int
    files: list[str]
    #: Django yapı taraması için okunan küçük metin dosyaları (yol → içerik); dosyalar çalıştırılmaz.
    texts: dict[str, str] = field(default_factory=dict)
    excluded: list[dict] = field(default_factory=list)


def _entry_error(path: str, reason: str) -> dict:
    return {"path": path[:300], "reason": reason}


def normalize_member_path(raw: str) -> tuple[str | None, str | None]:
    """ZIP girdi adını güvenli göreli POSIX yoluna çevirir. Dönüş: (yol, ret_nedeni)."""
    if raw == "" or "\x00" in raw or any(ord(c) < 32 or ord(c) == 127 for c in raw):
        return None, "INVALID_NAME"
    if "\\" in raw:
        return None, "BACKSLASH_PATH"
    if raw.startswith("//"):
        return None, "UNC_PATH"
    if raw.startswith("/"):
        return None, "ABSOLUTE_PATH"
    if _DRIVE_RX.match(raw):
        return None, "DRIVE_PATH"
    parts = [p for p in raw.split("/") if p not in ("", ".")]
    if not parts:
        return None, "INVALID_NAME"
    for part in parts:
        if part == "..":
            return None, "PATH_TRAVERSAL"
        if _INVALID_CHARS_RX.search(part) or part.endswith((" ", ".")):
            return None, "INVALID_NAME"
        if part.split(".")[0].upper() in _WINDOWS_RESERVED:
            return None, "RESERVED_NAME"
    return "/".join(parts), None


def _entry_kind(info: zipfile.ZipInfo) -> str:
    """'file' | 'dir' | 'symlink' | 'special' — Unix mod bitleri varsa onlara göre."""
    mode = (info.external_attr >> 16) & 0xFFFF
    if mode:
        if stat.S_ISLNK(mode):
            return "symlink"
        if stat.S_ISCHR(mode) or stat.S_ISBLK(mode) or stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode):
            return "special"
        if stat.S_ISDIR(mode):
            return "dir"
    return "dir" if info.filename.endswith("/") else "file"


def _sha256_and_size(fileobj: BinaryIO, limit: int) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    fileobj.seek(0)
    while chunk := fileobj.read(_CHUNK):
        total += len(chunk)
        if total > limit:
            raise ArchiveRejected("FILE_TOO_LARGE", f"Arşiv en fazla {limit} bayt olabilir.")
        digest.update(chunk)
    fileobj.seek(0)
    return digest.hexdigest(), total


def _is_secret(path: str) -> bool:
    name = path.rsplit("/", 1)[-1].lower()
    return name in _SECRET_NAMES or name.startswith(".env.") or name.endswith(_SECRET_SUFFIXES)


def inspect_zip(fileobj: BinaryIO, filename: str, limits: ArchiveLimits,
                text_wanted=lambda path: False, text_limit: int = 256 * 1024) -> ArchiveInspection:
    """Arşivi doğrular; güvenli değilse ``ArchiveRejected`` yükseltir. Hiçbir dosya diske yazılmaz."""
    name = (filename or "").lower()
    if not name.endswith(limits.allowed_extensions):
        raise ArchiveRejected("UNSUPPORTED_TYPE",
                              f"Desteklenen arşiv türleri: {', '.join(limits.allowed_extensions)}.")
    sha256, size = _sha256_and_size(fileobj, limits.max_upload_bytes)
    if size == 0:
        raise ArchiveRejected("EMPTY_FILE", "Yüklenen dosya boş.")
    head = fileobj.read(4)
    fileobj.seek(0)
    if head not in ZIP_SIGNATURES:
        raise ArchiveRejected("NOT_A_ZIP", "Dosya içeriği geçerli bir ZIP arşivi değil.")
    try:
        zf = zipfile.ZipFile(fileobj)
    except (zipfile.BadZipFile, zipfile.LargeZipFile, OSError, ValueError, EOFError):
        raise ArchiveRejected("CORRUPT_ARCHIVE", "Arşiv bozuk veya eksik; açılamadı.") from None
    with zf:
        infos = zf.infolist()
        if not infos:
            raise ArchiveRejected("EMPTY_ARCHIVE", "Arşivde hiç dosya yok.")
        if len(infos) > limits.max_entries:
            raise ArchiveRejected("TOO_MANY_ENTRIES", f"Arşiv en fazla {limits.max_entries} girdi içerebilir.")

        bad: list[dict] = []
        seen: dict[str, str] = {}
        folded: dict[str, str] = {}
        files: list[tuple[str, zipfile.ZipInfo]] = []
        dirs: set[str] = set()
        declared_total = 0
        for info in infos:
            path, reason = normalize_member_path(info.filename)
            if reason:
                bad.append(_entry_error(info.filename, reason))
                continue
            if len(path) > limits.max_path_length:
                bad.append(_entry_error(path, "PATH_TOO_LONG"))
                continue
            if path.count("/") + 1 > limits.max_depth:
                bad.append(_entry_error(path, "TOO_DEEP"))
                continue
            kind = _entry_kind(info)
            if kind == "symlink":
                bad.append(_entry_error(path, "SYMLINK"))
                continue
            if kind == "special":
                bad.append(_entry_error(path, "SPECIAL_FILE"))
                continue
            if info.flag_bits & 0x1:
                bad.append(_entry_error(path, "ENCRYPTED"))
                continue
            if path in seen:
                # Aynı dizin girdisinin tekrar edilmesi zararsızdır; dosya tekrarı veya dosya/dizin karışımı değildir.
                if not (kind == "dir" and seen[path] == "dir"):
                    bad.append(_entry_error(path, "DUPLICATE_PATH"))
                continue
            key = path.casefold()
            if key in folded and folded[key] != path:
                bad.append(_entry_error(path, "CASE_COLLISION"))
                continue
            seen[path], folded[key] = kind, path
            if kind == "dir":
                dirs.add(path)
                continue
            if info.file_size > limits.max_member_bytes:
                bad.append(_entry_error(path, "MEMBER_TOO_LARGE"))
                continue
            if (info.file_size >= limits.ratio_check_min_bytes
                    and info.file_size > limits.max_compression_ratio * max(info.compress_size, 1)):
                bad.append(_entry_error(path, "COMPRESSION_RATIO"))
                continue
            declared_total += info.file_size
            files.append((path, info))
        if bad:
            raise ArchiveRejected(_primary_reason(bad), "Arşiv güvenli olmayan veya geçersiz girdiler içeriyor.", bad)

        # Dosya–dizin çakışması: bir yol hem dosya hem başka girdilerin üst dizini olamaz.
        file_paths = {p for p, _ in files}
        implicit_dirs = {"/".join(p.split("/")[:i]) for p in seen for i in range(1, p.count("/") + 1)}
        conflicts = sorted(file_paths & (implicit_dirs | dirs))
        if conflicts:
            raise ArchiveRejected("PATH_CONFLICT", "Aynı yol hem dosya hem dizin olarak kullanılmış.",
                                  [_entry_error(p, "PATH_CONFLICT") for p in conflicts])
        if declared_total > limits.max_total_uncompressed_bytes:
            raise ArchiveRejected("UNCOMPRESSED_TOO_LARGE",
                                  f"Açılmış toplam boyut en fazla {limits.max_total_uncompressed_bytes} bayt olabilir.")

        # Bildirilen boyutlara güvenmeden gerçek içeriği sınırlı okuyarak say.
        actual_total = 0
        texts: dict[str, str] = {}
        for path, info in files:
            member_total = 0
            keep = text_wanted(path) and info.file_size <= text_limit
            buf = bytearray()
            try:
                with zf.open(info) as fh:
                    while chunk := fh.read(_CHUNK):
                        member_total += len(chunk)
                        actual_total += len(chunk)
                        if member_total > limits.max_member_bytes:
                            raise ArchiveRejected("MEMBER_TOO_LARGE", "Bir arşiv girdisi boyut sınırını aşıyor.",
                                                  [_entry_error(path, "MEMBER_TOO_LARGE")])
                        if actual_total > limits.max_total_uncompressed_bytes:
                            raise ArchiveRejected("UNCOMPRESSED_TOO_LARGE",
                                                  "Açılmış toplam boyut sınırı aşıldı.")
                        if keep and len(buf) <= text_limit:
                            buf.extend(chunk[: text_limit + 1 - len(buf)])
            except ArchiveRejected:
                raise
            except NotImplementedError:
                raise ArchiveRejected("UNSUPPORTED_COMPRESSION", "Arşiv desteklenmeyen bir sıkıştırma yöntemi kullanıyor.",
                                      [_entry_error(path, "UNSUPPORTED_COMPRESSION")]) from None
            except (zipfile.BadZipFile, zlib.error, EOFError, OSError, ValueError, RuntimeError):
                raise ArchiveRejected("CORRUPT_ARCHIVE", "Arşiv içeriği bozuk (CRC veya sıkıştırma hatası).",
                                      [_entry_error(path, "CORRUPT_MEMBER")]) from None
            if keep and len(buf) <= text_limit:
                texts[path] = bytes(buf).decode("utf-8", errors="replace")
        if actual_total >= limits.ratio_check_min_bytes and actual_total > limits.max_compression_ratio * size:
            raise ArchiveRejected("COMPRESSION_RATIO", "Arşivin toplam sıkıştırma oranı sınırı aşıyor.")

    return ArchiveInspection(
        sha256=sha256, size_bytes=size, file_count=len(files), dir_count=len(dirs | implicit_dirs),
        uncompressed_bytes=actual_total, files=sorted(file_paths), texts=texts,
        excluded=[_entry_error(p, "SECRET_FILE_EXCLUDED") for p in sorted(file_paths) if _is_secret(p)],
    )


_REASON_PRIORITY = ("PATH_TRAVERSAL", "ABSOLUTE_PATH", "DRIVE_PATH", "UNC_PATH", "BACKSLASH_PATH", "SYMLINK",
                    "SPECIAL_FILE", "COMPRESSION_RATIO", "MEMBER_TOO_LARGE", "ENCRYPTED", "DUPLICATE_PATH",
                    "CASE_COLLISION", "RESERVED_NAME", "INVALID_NAME", "PATH_TOO_LONG", "TOO_DEEP")


def _primary_reason(bad: list[dict]) -> str:
    reasons = {b["reason"] for b in bad}
    return next((r for r in _REASON_PRIORITY if r in reasons), "UNSAFE_ARCHIVE")
