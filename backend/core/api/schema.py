"""OpenAPI 3 şema tanımları (drf-spectacular) — H4-05 / Issue #37.

Bu modül API görünümlerinin **davranışını değiştirmez**; yalnızca şema üretimine bilgi ekler.
H4-02 (#34) ve H4-04 (#36) görünümleri bu dosyada ``OpenApiViewExtension`` ile, görünüm dosyalarına
dokunulmadan belgelenir. Örnek yanıtlar, API'ye gerçek istekler gönderilerek alınmış çıktılardır;
``core/tests/test_openapi.py`` örneklerin gerçek yanıtlarla ve şemanın gerçek davranışla uyumunu doğrular.

Şema üretimi sırasında drf-spectacular görünümleri anonim bir istekle örnekler. Sahiplik süzgeci
(``OwnedQuerysetMixin``) anonim kullanıcıyla sorgu kuramayacağından, yalnızca şemaya özel alt sınıflarda
``swagger_fake_view`` iken boş queryset döndürülür; çalışan API'de bu yol hiçbir zaman kullanılmaz.
"""
from __future__ import annotations

from functools import lru_cache

from drf_spectacular.extensions import OpenApiViewExtension
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_serializer,
    extend_schema_view,
)
from rest_framework import serializers

from ..projects.serializers import ProjectCreateSerializer, ProjectSerializer, ProjectUpdateSerializer

# ============================================================================ ortak hata gövdeleri

ARCHIVE_ERROR_CODES = [
    "UNSUPPORTED_TYPE", "EMPTY_FILE", "NOT_A_ZIP", "CORRUPT_ARCHIVE", "UNSUPPORTED_COMPRESSION", "ENCRYPTED",
    "EMPTY_ARCHIVE", "FILE_TOO_LARGE", "TOO_MANY_ENTRIES", "PATH_TRAVERSAL", "BACKSLASH_PATH", "ABSOLUTE_PATH",
    "DRIVE_PATH", "UNC_PATH", "INVALID_NAME", "RESERVED_NAME", "SYMLINK", "SPECIAL_FILE", "DUPLICATE_PATH",
    "CASE_COLLISION", "PATH_CONFLICT", "PATH_TOO_LONG", "TOO_DEEP", "MEMBER_TOO_LARGE", "UNCOMPRESSED_TOO_LARGE",
    "COMPRESSION_RATIO", "NO_DJANGO_SETTINGS", "NO_DJANGO_ENTRYPOINT", "UNSAFE_ARCHIVE",
]
ARCHIVE_ENTRY_REASONS = ARCHIVE_ERROR_CODES + ["CORRUPT_MEMBER"]


class DetailErrorSerializer(serializers.Serializer):
    """DRF'nin standart hata gövdesi: ``{"detail": "..."}`` (SimpleJWT hatalarında ek olarak ``code``)."""

    detail = serializers.CharField()
    code = serializers.CharField(required=False, help_text="Yalnızca SimpleJWT token hatalarında (ör. token_not_valid).")


class TokenErrorMessageSerializer(serializers.Serializer):
    token_class = serializers.CharField()
    token_type = serializers.CharField()
    message = serializers.CharField()


class TokenErrorSerializer(serializers.Serializer):
    """Geçersiz veya süresi dolmuş access token ile korumalı uç nokta çağrıldığında SimpleJWT yanıtı."""

    detail = serializers.CharField()
    code = serializers.CharField()
    messages = TokenErrorMessageSerializer(many=True, required=False)


class ArchiveEntryErrorSerializer(serializers.Serializer):
    path = serializers.CharField(help_text="Arşivdeki girdi adı (en fazla 300 karakter); sunucu yolu değildir.")
    reason = serializers.ChoiceField(choices=ARCHIVE_ENTRY_REASONS)


class ArchiveErrorItemSerializer(serializers.Serializer):
    code = serializers.ChoiceField(choices=ARCHIVE_ERROR_CODES)
    detail = serializers.CharField()
    entries = ArchiveEntryErrorSerializer(many=True, required=False)


class ArchiveErrorSerializer(serializers.Serializer):
    """Arşiv doğrulama hatası (400). Alan hataları (ör. ``name``) aynı nesnede yer alabilir."""

    archive = ArchiveErrorItemSerializer(many=True)


class MessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


VALIDATION_DESCRIPTION = ("Doğrulama hatası. Gövde, alan adı → hata iletileri listesi biçimindedir "
                          "(DRF standardı); nesne düzeyi hatalar `non_field_errors` altındadır.")


class ValidationErrorSerializer(serializers.Serializer):
    """Gösterim amaçlı: gerçek gövdede anahtarlar istekteki alan adlarıdır (ör. ``name``, ``specification``)."""

    field_name = serializers.ListField(child=serializers.CharField(), required=False,
                                       help_text="Alan adı → hata iletileri (örnekler gerçek yanıtlardır).")
    non_field_errors = serializers.ListField(child=serializers.CharField(), required=False)


def validation_error(*examples: OpenApiExample) -> OpenApiResponse:
    return OpenApiResponse(response=ValidationErrorSerializer, description=VALIDATION_DESCRIPTION,
                           examples=list(examples))


def ex(name: str, value, summary: str | None = None, status: int | None = None, request: bool = False):
    return OpenApiExample(name, value=value, summary=summary or name, request_only=request,
                          response_only=not request, status_codes=[str(status)] if status else None)


# Gerçek yanıtlardan alınmış örnekler (tarih/kimlik değerleri örnektir).
EX_NO_CREDENTIALS = ex("Token yok", {"detail": "Giriş bilgileri verilmedi."}, status=401)
EX_INVALID_TOKEN = ex("Geçersiz veya süresi dolmuş token", {
    "detail": "Verilen token hiçbir token tipi için geçerli değil", "code": "token_not_valid",
    "messages": [{"token_class": "AccessToken", "token_type": "access", "message": "Token is invalid"}]}, status=401)
UNAUTHORIZED = OpenApiResponse(TokenErrorSerializer, description="Kimlik doğrulama yok, token geçersiz veya süresi dolmuş.",
                               examples=[EX_NO_CREDENTIALS, EX_INVALID_TOKEN])
NOT_FOUND_PROJECT = OpenApiResponse(DetailErrorSerializer, description=(
    "Kayıt yok **veya başka kullanıcıya ait** (sahiplik süzgeci; varlığı ifşa edilmez)."),
    examples=[ex("Bulunamadı", {"detail": "No Project matches the given query."}, status=404)])


def not_found(model: str) -> OpenApiResponse:
    return OpenApiResponse(DetailErrorSerializer, description=(
        "Kayıt yok **veya başka kullanıcıya ait** (sahiplik süzgeci; varlığı ifşa edilmez)."),
        examples=[ex("Bulunamadı", {"detail": f"No {model} matches the given query."}, status=404)])


# ============================================================================ kimlik doğrulama (H4-02)

@extend_schema_serializer(component_name="Login")
class LoginRequestSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Access token (varsayılan ömür 15 dk, JWT_ACCESS_MINUTES).")
    refresh = serializers.CharField(help_text="Refresh token (varsayılan ömür 7 gün, JWT_REFRESH_DAYS).")


@extend_schema_serializer(component_name="TokenRefresh")
class RefreshRequestSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField()


LOCKOUT_DESCRIPTION = (
    "Hesap kilidi (django-axes, kullanıcı adı bazında): **3 başarısız denemeden sonra hesap 15 dakika "
    "kilitlenir**. Kilidi tetikleyen üçüncü başarısız deneme ve kilit süresince yapılan tüm denemeler "
    "(doğru parolayla bile) **429** döner; yanıtta `Retry-After` başlığı **yoktur**. Kilit süresi dolunca "
    "giriş yeniden yapılabilir; başarılı giriş sayacı sıfırlar. Hatalı kullanıcı adı ile hatalı parola aynı "
    "401 yanıtını üretir (hesap varlığı ifşa edilmez). Ayrıca anonim giriş isteklerine istek sınırı "
    "uygulanır (`LOGIN_THROTTLE_RATE`, varsayılan 10/dk); bu sınır aşıldığında da 429 döner ve bu durumda "
    "`Retry-After` başlığı bulunur."
)
EX_LOCKED = ex("Hesap kilitli", {"detail": "Çok fazla başarısız giriş denemesi. Hesap geçici olarak kilitlendi; "
                                           "lütfen bir süre sonra tekrar deneyin."}, status=429)

login_schema = extend_schema(
    tags=["Kimlik Doğrulama"], auth=[], operation_id="auth_login",
    summary="Giriş yap (access/refresh token al)",
    description="Kullanıcı adı ve parolayla SimpleJWT access/refresh token çifti döndürür.\n\n" + LOCKOUT_DESCRIPTION,
    request=LoginRequestSerializer,
    examples=[ex("Giriş isteği", {"username": "ornek_kullanici", "password": "<parola>"}, request=True)],
    responses={
        200: OpenApiResponse(TokenPairSerializer, description="Giriş başarılı.", examples=[
            ex("Token çifti", {"access": "<access-token>", "refresh": "<refresh-token>"}, status=200)]),
        400: validation_error(ex("Eksik alan", {"username": ["Bu alan zorunlu."], "password": ["Bu alan zorunlu."]},
                                 status=400)),
        401: OpenApiResponse(DetailErrorSerializer, description="Hatalı kullanıcı adı veya parola (ayrım yapılmaz).",
                             examples=[ex("Hatalı bilgiler", {"detail": "Verilen kimlik bilgileriyle aktif bir hesap "
                                                                        "bulunamadı"}, status=401)]),
        429: OpenApiResponse(DetailErrorSerializer, description="Hesap kilitli veya giriş istek sınırı aşıldı.",
                             examples=[EX_LOCKED]),
    },
)

refresh_schema = extend_schema(
    tags=["Kimlik Doğrulama"], auth=[], operation_id="auth_refresh",
    summary="Access token yenile",
    description=("Geçerli refresh token ile yeni access token alınır. `ROTATE_REFRESH_TOKENS` açık olduğu için "
                 "yanıtta **yeni bir refresh token** da döner; eski refresh token kara listeye alınır ve yeniden "
                 "kullanılamaz (401)."),
    request=RefreshRequestSerializer,
    responses={
        200: OpenApiResponse(TokenPairSerializer, examples=[
            ex("Yeni token çifti", {"access": "<access-token>", "refresh": "<yeni-refresh-token>"}, status=200)]),
        400: validation_error(ex("Eksik alan", {"refresh": ["Bu alan zorunlu."]}, status=400)),
        401: OpenApiResponse(DetailErrorSerializer, description="Refresh token geçersiz, süresi dolmuş veya kara listede.",
                             examples=[ex("Geçersiz refresh", {"detail": "Token is invalid", "code": "token_not_valid"},
                                          status=401)]),
    },
)

logout_schema = extend_schema(
    tags=["Kimlik Doğrulama"], operation_id="auth_logout",
    summary="Çıkış yap (refresh token'ı kara listeye al)",
    description="Gönderilen refresh token kara listeye alınır; bu token ile artık yenileme yapılamaz. Access token "
                "süresi dolana kadar geçerli kalır (SimpleJWT davranışı).",
    request=RefreshRequestSerializer,
    responses={
        205: OpenApiResponse(description="Çıkış başarılı (gövde yok)."),
        400: OpenApiResponse(DetailErrorSerializer, examples=[
            ex("Eksik refresh", {"detail": "refresh alanı zorunludur."}, status=400),
            ex("Geçersiz refresh", {"detail": "Geçersiz veya süresi dolmuş token."}, status=400)]),
        401: UNAUTHORIZED,
    },
)

me_schema = extend_schema(
    tags=["Kimlik Doğrulama"], operation_id="auth_me",
    summary="Oturumdaki kullanıcı",
    description="Kimliği doğrulanmış kullanıcının temel bilgileri. Parola veya token bilgisi döndürülmez.",
    responses={200: OpenApiResponse(MeSerializer, examples=[
        ex("Kullanıcı", {"id": 1, "username": "ornek_kullanici", "email": "ornek@example.test"}, status=200)]),
        401: UNAUTHORIZED},
)


@extend_schema_serializer(component_name="PasswordReset")
class PasswordResetRequestDocSerializer(serializers.Serializer):
    email = serializers.EmailField()


@extend_schema_serializer(component_name="PasswordResetConfirm")
class PasswordResetConfirmDocSerializer(serializers.Serializer):
    uid = serializers.CharField(help_text="E-postadaki bağlantıdan gelen base64 kullanıcı kimliği.")
    token = serializers.CharField(help_text="E-postadaki bağlantıdan gelen Django parola sıfırlama token'ı.")
    new_password = serializers.CharField(write_only=True, help_text="Django parola doğrulayıcılarından geçmelidir.")


reset_request_schema = extend_schema(
    tags=["Parola İşlemleri"], auth=[], operation_id="auth_password_reset_request",
    summary="Şifre sıfırlama bağlantısı iste",
    description=("Adres kayıtlı ve hesap aktifse e-postaya `FRONTEND_PASSWORD_RESET_URL?uid=...&token=...` "
                 "bağlantısı gönderilir. **Yanıt, adresin kayıtlı olup olmamasından bağımsız olarak aynıdır** "
                 "(hesap varlığı ifşa edilmez); e-posta gönderim hataları da yanıtı değiştirmez. İstek sınırı: "
                 "`LOGIN_THROTTLE_RATE`."),
    request=PasswordResetRequestDocSerializer,
    examples=[ex("Talep", {"email": "kullanici@example.test"}, request=True)],
    responses={
        200: OpenApiResponse(MessageSerializer, examples=[
            ex("Genel yanıt", {"detail": "E-posta kayıtlıysa şifre sıfırlama bağlantısı gönderildi."}, status=200)]),
        400: validation_error(ex("Geçersiz e-posta", {"email": ["Geçerli bir e-posta adresi girin."]}, status=400)),
        429: OpenApiResponse(DetailErrorSerializer, description="İstek sınırı aşıldı."),
    },
)

reset_confirm_schema = extend_schema(
    tags=["Parola İşlemleri"], auth=[], operation_id="auth_password_reset_confirm",
    summary="Yeni parola belirle",
    description=("E-postadaki `uid` ve `token` ile yeni parola belirlenir. Token Django'nun "
                 "`PasswordResetTokenGenerator` token'ıdır; `PASSWORD_RESET_TIMEOUT` (varsayılan 3600 sn) sonunda "
                 "geçersizleşir. **Tek kullanımlıktır**: parola değişince aynı bağlantı yeniden kullanılamaz. "
                 "Geçersiz, süresi dolmuş ve kullanılmış bağlantılar aynı genel hatayı üretir."),
    request=PasswordResetConfirmDocSerializer,
    examples=[ex("Yeni parola", {"uid": "<uid>", "token": "<token>", "new_password": "<yeni-parola>"}, request=True)],
    responses={
        200: OpenApiResponse(MessageSerializer, examples=[ex("Başarılı", {"detail": "Parola güncellendi."}, status=200)]),
        400: validation_error(
            ex("Geçersiz/süresi dolmuş/kullanılmış bağlantı", {"token": ["Bağlantı geçersiz veya süresi dolmuş."]},
               status=400),
            ex("Eksik alanlar", {"uid": ["Bu alan zorunlu."], "token": ["Bu alan zorunlu."],
                                 "new_password": ["Bu alan zorunlu."]}, status=400)),
        429: OpenApiResponse(DetailErrorSerializer, description="İstek sınırı aşıldı."),
    },
)


class LoginViewExtension(OpenApiViewExtension):
    target_class = "core.auth.views.LoginView"

    def view_replacement(self):
        return extend_schema_view(post=login_schema)(self.target)


class TokenRefreshViewExtension(OpenApiViewExtension):
    target_class = "rest_framework_simplejwt.views.TokenRefreshView"

    def view_replacement(self):
        return extend_schema_view(post=refresh_schema)(self.target)


class LogoutViewExtension(OpenApiViewExtension):
    target_class = "core.auth.views.LogoutView"

    def view_replacement(self):
        return extend_schema_view(post=logout_schema)(self.target)


class MeViewExtension(OpenApiViewExtension):
    target_class = "core.auth.views.MeView"

    def view_replacement(self):
        return extend_schema_view(get=me_schema)(self.target)


class PasswordResetRequestViewExtension(OpenApiViewExtension):
    target_class = "core.auth.views.PasswordResetRequestView"

    def view_replacement(self):
        return extend_schema_view(post=reset_request_schema)(self.target)


class PasswordResetConfirmViewExtension(OpenApiViewExtension):
    target_class = "core.auth.views.PasswordResetConfirmView"

    def view_replacement(self):
        return extend_schema_view(post=reset_confirm_schema)(self.target)


# ============================================================================ projeler (H4-03)

def _upload_limits_text() -> str:
    from django.conf import settings

    lim = settings.PROJECT_UPLOAD_LIMITS
    mib = 1024 * 1024
    return (f"Sınırlar (ortam değişkenleriyle değiştirilebilir; bkz. backend/docs/h4_03_project_api.md §4): "
            f"arşiv ≤ {lim['max_upload_bytes'] // mib} MiB, açılmış toplam ≤ "
            f"{lim['max_total_uncompressed_bytes'] // mib} MiB, tek dosya ≤ {lim['max_member_bytes'] // mib} MiB, "
            f"≤ {lim['max_entries']} girdi, derinlik ≤ {lim['max_depth']}, yol ≤ {lim['max_path_length']} karakter, "
            f"sıkıştırma oranı ≤ {lim['max_compression_ratio']}.")


PROJECT_ID = OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH, description="Proje kimliği.")
EX_PROJECT = {
    "id": 1, "name": "Mağaza API", "description": "", "source_type": "ARCHIVE", "validation_status": "VALID",
    "archive": {"original_name": "magaza.zip", "size_bytes": 1429,
                "sha256": "6cd7e458160cd1c6bf515fbd899f4bca46fc6213c9825c70c6774f9c2a4ea7bc",
                "uploaded_at": "2026-11-18T15:12:51.053405+03:00"},
    "validation_report": {"warnings": [], "checked_at": "2026-11-18T12:12:51+00:00", "django_apps": ["shop"],
                          "drf_detected": True, "schema_version": 1, "manage_py_found": True,
                          "manage_py_paths": ["manage.py"], "rejected_entries": [],
                          "settings_modules": ["config/settings.py"], "installed_apps_count": 4,
                          "declared_settings_modules": ["config.settings"]},
    "analysis_run_count": 0, "created_at": "2026-11-18T15:12:51.053405+03:00",
    "updated_at": "2026-11-18T15:12:51.053420+03:00",
}


def project_create_schema():
    return extend_schema(
        tags=["Proje Yükleme"], operation_id="projects_create",
        summary="ZIP arşivi yükleyerek proje oluştur",
        description=(
            "`multipart/form-data` ile `name` (zorunlu), `description` (isteğe bağlı) ve `archive` (zorunlu, "
            "**.zip**) gönderilir. Sahip sunucuda oturumdaki kullanıcı olarak atanır. Yüklenen kod çalıştırılmaz, "
            "içe aktarılmaz ve diske açılmaz. Arşiv şu durumlarda 400 ile reddedilir: boş dosya, desteklenmeyen tür "
            "veya içerik, bozuk/kesik/şifreli arşiv, Zip Slip (`..`), mutlak/sürücü/UNC yolu, sembolik bağlantı, "
            "özel dosya, yinelenen/çakışan yollar, boyut/girdi/derinlik/oran sınırları (ZIP bombası), Django yapısı "
            "bulunamaması. **400 ile 413 farkı:** boyut sınırını aşan yükleme gövde okunurken durdurulur ve 413 "
            "döner; içeriği doğrulanıp reddedilen arşiv 400 döner.\n\n" + _upload_limits_text()),
        request={"multipart/form-data": ProjectCreateSerializer},
        responses={
            201: OpenApiResponse(ProjectSerializer, description="Proje oluşturuldu.",
                                 examples=[ex("Oluşturulan proje", EX_PROJECT, status=201)]),
            400: OpenApiResponse(ArchiveErrorSerializer, description=(
                "Geçersiz arşiv (`archive[].code`) veya alan hatası (ör. `name`, korumalı alan gönderme)."),
                examples=[
                    ex("Zip Slip", {"archive": [{"code": "PATH_TRAVERSAL", "detail": "Arşiv güvenli olmayan veya "
                                                 "geçersiz girdiler içeriyor.", "entries": [
                                                     {"path": "../evil.py", "reason": "PATH_TRAVERSAL"}]}]}, status=400),
                    ex("Django projesi değil", {"archive": [{"code": "NO_DJANGO_SETTINGS", "detail": (
                        "Arşivde Django ayar modülü bulunamadı: INSTALLED_APPS içeren bir settings.py veya "
                        "settings/ paketi gereklidir.")}]}, status=400),
                    ex("Eksik alanlar", {"name": ["Bu alan zorunlu."], "archive": ["Hiçbir dosya verilmedi."]},
                       status=400),
                    ex("Korumalı alan", {"owner": ["Bu alan istemci tarafından gönderilemez veya değiştirilemez."]},
                       status=400)]),
            401: UNAUTHORIZED,
            413: OpenApiResponse(DetailErrorSerializer, description="Arşiv boyut sınırını aşıyor.", examples=[
                ex("Çok büyük", {"detail": "Yüklenen dosya en fazla 52428800 bayt olabilir."}, status=413)]),
            415: OpenApiResponse(DetailErrorSerializer, description="multipart/form-data dışı içerik türü.", examples=[
                ex("Yanlış içerik türü", {"detail": "Proje oluşturma multipart/form-data ile yapılmalıdır."},
                   status=415)]),
            429: OpenApiResponse(DetailErrorSerializer, description="Kullanıcı başına yükleme sınırı aşıldı "
                                                                     "(`PROJECT_UPLOAD_THROTTLE_RATE`)."),
        },
    )


def _project_update(partial: bool):
    return extend_schema(
        tags=["Proje Yönetimi"], operation_id="projects_partial_update" if partial else "projects_update",
        summary="Proje adını/açıklamasını güncelle" + (" (kısmi)" if partial else ""),
        description=("Yalnızca `name` ve `description` değiştirilebilir. Diğer alanlar (`owner`, `validation_status`, "
                     "`source_archive`, `archive_sha256` vb.) **400 ile reddedilir**. Arşiv bu uç noktayla "
                     "değiştirilemez." + ("" if partial else " PUT'ta `name` zorunludur.")),
        parameters=[PROJECT_ID],
        request=ProjectUpdateSerializer,
        responses={200: ProjectSerializer,
                   400: validation_error(
                       ex("Korumalı alan", {"owner": ["Bu alan istemci tarafından gönderilemez veya değiştirilemez."]},
                          status=400),
                       ex("Aynı ad", {"name": ["Bu adla kayıtlı bir projeniz zaten var."]}, status=400)),
                   401: UNAUTHORIZED, 404: NOT_FOUND_PROJECT},
    )


project_schemas = dict(
    create=project_create_schema(),
    list=extend_schema(
        tags=["Proje Yönetimi"], operation_id="projects_list", summary="Projelerimi listele",
        description="Yalnızca oturumdaki kullanıcının projeleri, yeniden eskiye, sayfalı (`page`, `page_size` ≤ 100).",
        responses={200: ProjectSerializer(many=True), 401: UNAUTHORIZED}),
    retrieve=extend_schema(
        tags=["Proje Yönetimi"], operation_id="projects_retrieve", summary="Proje detayı",
        description="Depolama yolu, sunucu dosya adı veya mutlak yol döndürülmez.", parameters=[PROJECT_ID],
        responses={200: ProjectSerializer, 401: UNAUTHORIZED, 404: NOT_FOUND_PROJECT}),
    update=_project_update(False),
    partial_update=_project_update(True),
    destroy=extend_schema(
        tags=["Proje Yönetimi"], operation_id="projects_destroy", summary="Projeyi sil",
        description=("Proje ve CASCADE ile bağlı kayıtlar (referans gereksinimler, analiz çalıştırmaları ve "
                     "sonuçları) kalıcı olarak silinir; arşiv dosyası işlem tamamlandıktan sonra depodan silinir. "
                     "Aktif (QUEUED…SCANNING) analizi olan proje silinemez."),
        parameters=[PROJECT_ID],
        responses={204: OpenApiResponse(description="Silindi (gövde yok)."), 401: UNAUTHORIZED,
                   404: NOT_FOUND_PROJECT,
                   409: OpenApiResponse(DetailErrorSerializer, description="Projede aktif durumda (QUEUED, ANALYZING, GENERATING, VALIDATING, EXECUTING, SCANNING) analiz var.",
                                        examples=[ex("Aktif analiz", {
                       "detail": "Projenin devam eden bir analizi var; analiz bitmeden proje silinemez."},
                       status=409)])}),
)


class ProjectViewSetExtension(OpenApiViewExtension):
    target_class = "core.projects.views.ProjectViewSet"

    def view_replacement(self):
        return extend_schema_view(**project_schemas)(self.target)


# ============================================================================ analiz çalıştırmaları (H4-04)

class ExecutionProgressSerializer(serializers.Serializer):
    """``core.progress.ExecutionProgress.as_dict()`` — sayaçlar test yürütme kayıtlarından türetilir."""

    total = serializers.IntegerField(help_text="En az bir yürütme kaydı olan test sayısı.")
    completed = serializers.IntegerField(help_text="Son denemesi PASS/FAIL/ERROR/TIMEOUT/STOPPED/NOT_RUN olan testler.")
    running = serializers.IntegerField()
    pending = serializers.IntegerField()
    by_status = serializers.DictField(child=serializers.IntegerField(), help_text="Son deneme durumuna göre sayılar.")
    completed_duration_ms_total = serializers.IntegerField()
    completed_with_duration = serializers.IntegerField()
    run_started_at = serializers.DateTimeField(allow_null=True)
    percent = serializers.FloatField(allow_null=True, help_text="Henüz yürütme kaydı yoksa null (0 değil).")


@lru_cache(maxsize=None)
def _analysis_detail_doc():
    from .serializers import AnalysisRunDetailSerializer

    @extend_schema_serializer(component_name="AnalysisRunDetail")
    class AnalysisRunDetailDocSerializer(AnalysisRunDetailSerializer):
        progress = ExecutionProgressSerializer(read_only=True)
        requirements_snapshot = serializers.ListField(child=serializers.DictField(), read_only=True, help_text=(
            "Analiz oluşturulduğunda projenin aktif referans gereksinimlerinin anlık görüntüsü."))

    return AnalysisRunDetailDocSerializer


STATUS_DESCRIPTION = (
    "Durum değerleri: birincil iş akışı `QUEUED` → `ANALYZING` → `GENERATING` → `EXECUTING` → `COMPLETED` / "
    "`FAILED`; model ayrıca `VALIDATING`, `SCANNING` ve `CANCELLED` durumlarını destekler (veri sözlüğü 8). "
    "Bu sürümde analiz oluşturmak **arka plan görevi başlatmaz**: kayıt `QUEUED` durumunda oluşturulur, "
    "`celery_task_id`, `started_at` ve `finished_at` null kalır (Celery entegrasyonu sonraki iş kalemidir)."
)
RUN_ID = OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH, description="Analiz çalıştırması kimliği.")
EX_RUN = {"id": 1, "project": 1, "status": "QUEUED", "method": "DIRECT_LLM", "llm_provider": "GROQ",
          "llm_model": "openai/gpt-oss-120b", "fallback_enabled": True, "celery_task_id": None,
          "coverage_percent": None, "error_code": "", "error_message": "",
          "created_at": "2026-11-18T15:13:34.314827+03:00", "started_at": None, "finished_at": None,
          "updated_at": "2026-11-18T15:13:34.314850+03:00", "requirements_snapshot": [], "generated_test_count": 0,
          "progress": {"total": 0, "completed": 0, "running": 0, "pending": 0, "by_status": {},
                       "completed_duration_ms_total": 0, "completed_with_duration": 0, "run_started_at": None,
                       "percent": None}}


@lru_cache(maxsize=None)
def analysis_schemas():
    from .serializers import AnalysisRunCreateSerializer, AnalysisRunListSerializer

    detail = _analysis_detail_doc()
    return dict(
        create=extend_schema(
            tags=["Analiz İşlemleri"], operation_id="analysis_runs_create", summary="Analiz çalıştırması oluştur",
            description=("Sahip olunan bir proje için analiz kaydı oluşturur. `RULE_BASED` yönteminde "
                         "`llm_provider`/`llm_model` verilmez; `DIRECT_LLM` ve `HYBRID` yöntemlerinde ikisi de "
                         "zorunludur. Projede aktif analiz varsa 400 döner. Projenin aktif referans gereksinimleri "
                         "`requirements_snapshot` olarak saklanır.\n\n" + STATUS_DESCRIPTION),
            request=AnalysisRunCreateSerializer,
            examples=[ex("Kural tabanlı", {"project": 1, "method": "RULE_BASED"}, request=True),
                      ex("LLM", {"project": 1, "method": "DIRECT_LLM", "llm_provider": "GROQ",
                                 "llm_model": "openai/gpt-oss-120b"}, request=True)],
            responses={
                201: OpenApiResponse(detail, examples=[ex("Oluşturulan analiz", EX_RUN, status=201)]),
                400: validation_error(
                    ex("LLM alanları eksik", {"llm_model": ["LLM yöntemlerinde llm_provider ve llm_model zorunludur."]},
                       status=400),
                    ex("RULE_BASED ile LLM alanı", {"llm_provider": ["RULE_BASED yönteminde LLM sağlayıcı/model "
                                                                     "verilmez."]}, status=400),
                    ex("Başkasının veya olmayan proje", {"project": ["Geçersiz pk \"99999\" - obje bulunamadı."]},
                       status=400),
                    ex("Projede aktif analiz var", {"non_field_errors": [
                        "project  alanları benzersiz bir set yapmak gerekir."]}, status=400)),
                401: UNAUTHORIZED}),
        list=extend_schema(
            tags=["Analiz İşlemleri"], operation_id="analysis_runs_list", summary="Analizlerimi listele",
            description="Yalnızca kullanıcının projelerine ait analizler (sayfasız dizi).\n\n" + STATUS_DESCRIPTION,
            responses={200: AnalysisRunListSerializer(many=True), 401: UNAUTHORIZED}),
        retrieve=extend_schema(
            tags=["Analiz İşlemleri"], operation_id="analysis_runs_retrieve", summary="Analiz detayı ve ilerleme",
            description="Durum, görev kimliği, zaman damgaları ve test yürütme kayıtlarından türetilen ilerleme.",
            parameters=[RUN_ID],
            responses={200: detail, 401: UNAUTHORIZED, 404: not_found("AnalysisRun")}),
    )


def _fake_view_guard(target):
    """Şema üretiminde (anonim örnek istek) sahiplik süzgecinin sorgu kurmasını engelleyen alt sınıf."""

    class SchemaView(target):
        def get_queryset(self):
            if getattr(self, "swagger_fake_view", False):
                return self.queryset.model.objects.none()
            return super().get_queryset()

        def get_serializer_context(self):
            context = super().get_serializer_context()
            if getattr(self, "swagger_fake_view", False):
                context.pop("request", None)  # _OwnedProjectMixin anonim kullanıcıyla sorgu kurmasın
            return context

    SchemaView.__name__ = target.__name__
    SchemaView.__qualname__ = target.__qualname__
    SchemaView.__module__ = target.__module__
    return SchemaView


class AnalysisRunViewSetExtension(OpenApiViewExtension):
    target_class = "core.api.views.AnalysisRunViewSet"

    def view_replacement(self):
        return extend_schema_view(**analysis_schemas())(_fake_view_guard(self.target))


# ============================================================================ referans gereksinimler (H4-04)

REQ_ID = OpenApiParameter("id", OpenApiTypes.INT, OpenApiParameter.PATH, description="Referans gereksinim kimliği.")
EX_SPEC = {"schema_version": 1, "endpoint": "/api/orders/<int:pk>/", "method": "DELETE",
           "expected_status_by_role": {"anonymous": 401, "staff": 204}}
EX_REQ_REQUEST = {"project": 1, "requirement_code": "ACC-ORDERS-DELETE", "category": "ACCESS_RULE",
                  "title": "Sipariş silme", "expected_result": "anonim 401, staff 204", "specification": EX_SPEC}
EX_REQ = {"id": 1, "project": 1, "requirement_code": "ACC-ORDERS-DELETE", "category": "ACCESS_RULE",
          "source": "FORM", "title": "Sipariş silme", "description": "", "expected_result": "anonim 401, staff 204",
          "specification": EX_SPEC, "is_active": True, "revision": 1, "http_method": "DELETE",
          "created_at": "2026-11-18T15:12:51.137000+03:00", "updated_at": "2026-11-18T15:12:51.137000+03:00"}
REQ_DESCRIPTION = (
    "`category` değerine göre `specification` yapısı değişir: `ROLE` → {schema_version, role}; `ACCESS_RULE` → "
    "{schema_version, endpoint, **method**, expected_status_by_role}; `DEPLOY_EXPECTATION` → {schema_version, "
    "setting, expected_value, check_id?}. `ACCESS_RULE` için `method` yalnızca **GET, POST, PUT, PATCH, DELETE** "
    "olabilir (serializer + model doğrulaması + veritabanı CHECK kısıtı). `expected_result` ROLE dışındaki "
    "kategorilerde zorunludur. `requirement_code` proje içinde tekildir."
)
REQ_400 = validation_error(
    ex("Desteklenmeyen HTTP metodu", {"specification": {"method": ["\"HEAD\" geçerli bir seçim değil."]}}, status=400),
    ex("Eksik specification alanları", {"specification": {"endpoint": ["Bu alan zorunlu."],
                                                          "expected_status_by_role": ["Bu alan zorunlu."]}},
       status=400),
    ex("Eksik zorunlu alanlar", {"requirement_code": ["Bu alan zorunlu."], "category": ["Bu alan zorunlu."],
                                 "title": ["Bu alan zorunlu."]}, status=400),
    ex("expected_result eksik", {"expected_result": ["ROLE dışındaki kategorilerde zorunludur."]}, status=400))


@lru_cache(maxsize=None)
def requirement_schemas():
    from .serializers import ReferenceRequirementAPISerializer as Req

    common = dict(tags=["Referans Gereksinimler"])
    write_examples = [
        ex("ACCESS_RULE", EX_REQ_REQUEST, request=True),
        ex("ROLE", {"project": 1, "requirement_code": "ROLE-STAFF", "category": "ROLE", "title": "staff",
                    "specification": {"schema_version": 1, "role": "staff"}}, request=True),
        ex("DEPLOY_EXPECTATION", {"project": 1, "requirement_code": "DEP-DEBUG", "category": "DEPLOY_EXPECTATION",
                                  "title": "DEBUG kapalı", "expected_result": "DEBUG False", "specification": {
                                      "schema_version": 1, "setting": "DEBUG", "expected_value": False,
                                      "check_id": "security.W018"}}, request=True),
        ex("Geçersiz metot (400)", {**EX_REQ_REQUEST, "requirement_code": "ACC-X",
                                    "specification": {**EX_SPEC, "method": "HEAD"}}, request=True),
    ]
    return dict(
        list=extend_schema(**common, operation_id="reference_requirements_list", summary="Referans gereksinimlerimi listele",
                           description="Yalnızca kullanıcının projelerine ait kayıtlar (sayfasız dizi).",
                           responses={200: Req(many=True), 401: UNAUTHORIZED}),
        create=extend_schema(**common, operation_id="reference_requirements_create", summary="Referans gereksinim oluştur",
                             description=REQ_DESCRIPTION, examples=write_examples,
                             responses={201: OpenApiResponse(Req, examples=[ex("Oluşturulan gereksinim", EX_REQ,
                                                                                status=201)]),
                                        400: REQ_400, 401: UNAUTHORIZED}),
        retrieve=extend_schema(**common, operation_id="reference_requirements_retrieve", summary="Referans gereksinim detayı",
                               parameters=[REQ_ID], responses={200: Req, 401: UNAUTHORIZED,
                                                               404: not_found("ReferenceRequirement")}),
        update=extend_schema(**common, operation_id="reference_requirements_update", summary="Referans gereksinimi güncelle",
                             description=REQ_DESCRIPTION + " Her güncellemede `revision` bir artar.",
                             parameters=[REQ_ID], examples=write_examples[:1],
                             responses={200: Req, 400: REQ_400, 401: UNAUTHORIZED, 404: not_found("ReferenceRequirement")}),
        partial_update=extend_schema(**common, operation_id="reference_requirements_partial_update",
                                     summary="Referans gereksinimi kısmen güncelle",
                                     description="Her güncellemede `revision` bir artar.", parameters=[REQ_ID],
                                     responses={200: Req, 400: REQ_400, 401: UNAUTHORIZED,
                                                404: not_found("ReferenceRequirement")}),
        destroy=extend_schema(**common, operation_id="reference_requirements_destroy", summary="Referans gereksinimi sil",
                              parameters=[REQ_ID], responses={204: OpenApiResponse(description="Silindi."),
                                                              401: UNAUTHORIZED, 404: not_found("ReferenceRequirement")}),
    )


class ReferenceRequirementViewSetExtension(OpenApiViewExtension):
    target_class = "core.api.views.ReferenceRequirementViewSet"

    def view_replacement(self):
        return extend_schema_view(**requirement_schemas())(_fake_view_guard(self.target))
