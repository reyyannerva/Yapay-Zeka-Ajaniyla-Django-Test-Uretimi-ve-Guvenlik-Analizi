"""Veri kalitesi kontrolleri — H3-02 / Issue #28.

Her kontrol saf bir fonksiyondur: girdi olarak ham senaryo listesini (ve gerekiyorsa şema,
fixture, rota bilgisini) alır, bulgu sözlükleri listesi döndürür. Kaynak veri DEĞİŞTİRİLMEZ.

Katmanlar birbirinden ayrı raporlanır (``kontrol_katmani`` sütunu):
    * JSON Schema               — yapısal doğrulama (kanonik scenarios.schema.json ile)
    * Semantik                  — şemanın ifade edemediği anlamsal tutarlılık
    * Referans bütünlüğü        — fixture/endpoint referanslarının statik doğrulaması
    * Django URL çözümlemesi    — view'ın metodu destekleyip desteklemediği (istek atılmaz)
    * JSON/CSV tutarlılığı      — türetilmiş CSV'nin kanonik JSON ile birebir uyumu
    * Durum kodu incelemesi     — proje-özgü SEZGİSEL kurallar; çıktısı "inceleme" niteliğindedir,
                                  kesin hata olarak yorumlanmamalıdır.

Kayıt kimliği yoksa veya geçersizse uydurma kimlik üretilmez; ``scenarios[<sıra>]`` konumu
kullanılır.
"""
from __future__ import annotations

import ast
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from .data import HTTP_METHODS, Route, resolve_route

FINDING_COLUMNS = [
    "bulgu_no", "konum", "senaryo_id", "alan", "sorun_turu", "onem_derecesi",
    "kontrol_katmani", "aciklama", "kanit", "onerilen_duzeltme",
]
SEVERITY_ORDER = ["Kritik", "Yüksek", "Orta", "Düşük", "Bilgi"]

LAYER_SCHEMA = "JSON Schema"
LAYER_SEMANTIC = "Semantik"
LAYER_REFERENCE = "Referans bütünlüğü (statik)"
LAYER_DJANGO = "Django URL çözümlemesi"
LAYER_CSV = "JSON/CSV tutarlılığı"
LAYER_STATUS = "Durum kodu incelemesi (sezgisel)"

REQUIREMENT_REF_RX = re.compile(r"^İST-\d{2}$")  # proje konvansiyonu (README/İster belgeleri)


def _locator(idx: int, scenario: Any) -> tuple[str, str | None]:
    sid = scenario.get("id") if isinstance(scenario, dict) else None
    if isinstance(sid, str) and sid.strip():
        return f"scenarios[{idx}]", sid
    return f"scenarios[{idx}]", None


def finding(idx: int | None, scenario: Any, field: str, issue: str, severity: str, layer: str,
            explanation: str, evidence: str, fix: str, locator: str | None = None) -> dict:
    if idx is None:
        loc, sid = (locator or "veri kümesi"), None
    else:
        loc, sid = _locator(idx, scenario)
    return {
        "konum": loc, "senaryo_id": sid, "alan": field, "sorun_turu": issue,
        "onem_derecesi": severity, "kontrol_katmani": layer, "aciklama": explanation,
        "kanit": evidence, "onerilen_duzeltme": fix,
    }


def _is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


# --------------------------------------------------------------------------------------
# 1) JSON Schema
# --------------------------------------------------------------------------------------
def check_json_schema(data: Any, schema: dict) -> list[dict]:
    """Kanonik JSON Schema (Draft 2020-12) ile yapısal doğrulama."""
    from jsonschema import Draft202012Validator

    out = []
    scenarios = data.get("scenarios", []) if isinstance(data, dict) else []
    for err in sorted(Draft202012Validator(schema).iter_errors(data), key=lambda e: [str(p) for p in e.path]):
        path = list(err.path)
        if len(path) >= 2 and path[0] == "scenarios" and isinstance(path[1], int):
            idx = path[1]
            sc = scenarios[idx] if idx < len(scenarios) else {}
            field = "/".join(str(p) for p in path[2:]) or "<kayıt>"
            if err.validator == "required":
                m = re.search(r"'([^']+)' is a required property", err.message)
                field = (field + "/" if field != "<kayıt>" else "") + (m.group(1) if m else "?")
            out.append(finding(idx, sc, field, "JSON_SEMA_IHLALI", "Yüksek", LAYER_SCHEMA,
                               f"Şema kuralı '{err.validator}' ihlal edildi.", err.message,
                               "Kaydı scenarios.schema.json ile uyumlu hale getirin."))
        else:
            loc = "/".join(str(p) for p in path) or "<kök>"
            out.append(finding(None, None, loc, "JSON_SEMA_IHLALI", "Yüksek", LAYER_SCHEMA,
                               f"Şema kuralı '{err.validator}' ihlal edildi.", err.message,
                               "Veri kümesi kökünü şemayla uyumlu hale getirin.", locator=loc))
    return out


# --------------------------------------------------------------------------------------
# 2) Semantik / alan düzeyi kontroller (şemadaki tanımlar okunarak)
# --------------------------------------------------------------------------------------
def schema_vocabulary(schema: dict) -> dict[str, Any]:
    """Şemadan zorunlu alanları, enum değerlerini ve null'a izin verilen alanları okur."""
    sc = schema["$defs"]["scenario"]
    props = sc["properties"]

    def _nullable(p: dict) -> bool:
        t = p.get("type")
        return t == "null" or (isinstance(t, list) and "null" in t)

    return {
        "required": list(sc.get("required", [])),
        "enums": {k: list(v["enum"]) for k, v in props.items() if "enum" in v},
        "nullable": {k for k, v in props.items() if _nullable(v)},
        "id_pattern": props.get("id", {}).get("pattern"),
        "fixture_required": list(props.get("fixture_ref", {}).get("required", [])),
    }


def check_record_fields(scenarios: list[Any], schema: dict) -> list[dict]:
    """Eksik zorunlu alan, null, boş metin, geçersiz enum/tip ve bilerek-hata açıklaması."""
    vocab = schema_vocabulary(schema)
    enums = vocab["enums"]
    id_rx = re.compile(vocab["id_pattern"]) if vocab["id_pattern"] else None
    out: list[dict] = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            out.append(finding(i, s, "<kayıt>", "GECERSIZ_KAYIT_TIPI", "Kritik", LAYER_SEMANTIC,
                               "Senaryo kaydı bir JSON nesnesi değil.", f"tip={type(s).__name__}",
                               "Kaydı nesne olarak yeniden yazın."))
            continue
        for f in vocab["required"]:
            if f not in s:
                out.append(finding(i, s, f, "EKSIK_ZORUNLU_ALAN", "Yüksek", LAYER_SEMANTIC,
                                   f"Zorunlu '{f}' alanı yok.", "alan kayıtta bulunmuyor",
                                   f"'{f}' alanını şemadaki tanıma uygun değerle ekleyin."))
            elif s[f] is None and f not in vocab["nullable"]:
                out.append(finding(i, s, f, "NULL_ZORUNLU_ALAN", "Yüksek", LAYER_SEMANTIC,
                                   f"Zorunlu '{f}' alanı null.", f"{f}=null",
                                   f"'{f}' için geçerli bir değer girin."))
        for f, v in s.items():
            if isinstance(v, str) and not v.strip():
                out.append(finding(i, s, f, "BOS_METIN", "Orta", LAYER_SEMANTIC,
                                   f"'{f}' alanı boş veya yalnızca boşluk.", repr(v),
                                   f"'{f}' alanını anlamlı bir değerle doldurun."))
        sid = s.get("id")
        if isinstance(sid, str) and sid.strip() and id_rx and not id_rx.match(sid):
            out.append(finding(i, s, "id", "GECERSIZ_KIMLIK_BICIMI", "Orta", LAYER_SEMANTIC,
                               "Senaryo kimliği şemadaki biçime uymuyor.",
                               f"id={sid!r}, beklenen desen {vocab['id_pattern']}",
                               "Kimliği SC-XXX-000 biçimine getirin."))
        issue_by_field = {
            "http_method": "GECERSIZ_HTTP_METODU", "category": "GECERSIZ_KATEGORI",
            "user_role": "GECERSIZ_ROL", "label": "GECERSIZ_ETIKET",
            "expected_http_status": "GECERSIZ_DURUM_KODU",
        }
        for f, allowed in enums.items():
            if f not in s or s[f] is None:
                continue
            v = s[f]
            issue = issue_by_field.get(f, "GECERSIZ_DEGER")
            if f == "expected_http_status" and not _is_int(v):
                out.append(finding(i, s, f, issue, "Yüksek", LAYER_SEMANTIC,
                                   "Durum kodu tamsayı değil (biçim hatası).",
                                   f"değer={v!r} ({type(v).__name__})",
                                   "Durum kodunu tamsayı olarak yazın (ör. 403)."))
            elif v not in allowed:
                hint = ""
                if isinstance(v, str) and v.upper() in allowed:
                    hint = f" Büyük/küçük harf farkı: '{v.upper()}' olmalı."
                out.append(finding(i, s, f, issue, "Yüksek", LAYER_SEMANTIC,
                                   f"'{f}' izin verilen değerler dışında.{hint}",
                                   f"değer={v!r}; izinli={allowed}",
                                   f"'{f}' değerini şemadaki listeden seçin."))
        if "is_intentional_flaw" in s and not isinstance(s["is_intentional_flaw"], bool):
            out.append(finding(i, s, "is_intentional_flaw", "GECERSIZ_TIP", "Yüksek", LAYER_SEMANTIC,
                               "is_intentional_flaw mantıksal (true/false) değil.",
                               f"değer={s['is_intentional_flaw']!r}", "true/false kullanın."))
        flaw = s.get("is_intentional_flaw") is True
        expl = s.get("flaw_explanation")
        if flaw and not (isinstance(expl, str) and expl.strip()):
            out.append(finding(i, s, "flaw_explanation", "EKSIK_HATA_ACIKLAMASI", "Yüksek", LAYER_SEMANTIC,
                               "Bilerek-hatalı senaryoda zafiyet açıklaması yok.", f"flaw_explanation={expl!r}",
                               "Zafiyet türünü ve güvenli uçta beklenen davranışı açıklayın."))
        if s.get("is_intentional_flaw") is False and isinstance(expl, str) and expl.strip():
            out.append(finding(i, s, "flaw_explanation", "TUTARSIZ_ETIKET", "Düşük", LAYER_SEMANTIC,
                               "Hatalı olmayan senaryoda flaw_explanation dolu.", expl,
                               "Açıklamayı kaldırın veya is_intentional_flaw değerini gözden geçirin."))
        fx = s.get("fixture_ref")
        if isinstance(fx, dict):
            for k in vocab["fixture_required"]:
                if k not in fx:
                    out.append(finding(i, s, f"fixture_ref/{k}", "EKSIK_ZORUNLU_ALAN", "Yüksek", LAYER_SEMANTIC,
                                       f"fixture_ref.{k} anahtarı yok.", json.dumps(fx, ensure_ascii=False),
                                       f"fixture_ref.{k} ekleyin (gerekirse null)."))
        refs = s.get("requirement_refs")
        if isinstance(refs, list):
            bad = [r for r in refs if not (isinstance(r, str) and REQUIREMENT_REF_RX.match(r))]
            if bad:
                out.append(finding(i, s, "requirement_refs", "GECERSIZ_ISTER_REFERANSI", "Düşük", LAYER_SEMANTIC,
                                   "İster referansı proje konvansiyonuna (İST-00) uymuyor.", f"{bad}",
                                   "Referansları 'İST-xx' biçiminde yazın."))
    return out


def check_duplicate_ids(scenarios: list[Any]) -> list[dict]:
    """Yinelenen senaryo kimlikleri (her yinelenen kayıt ayrı bulgu)."""
    positions: dict[str, list[int]] = defaultdict(list)
    for i, s in enumerate(scenarios):
        sid = s.get("id") if isinstance(s, dict) else None
        if isinstance(sid, str):
            positions[sid].append(i)
    out = []
    for sid, idxs in sorted(positions.items()):
        if len(idxs) > 1:
            for i in idxs:
                out.append(finding(i, scenarios[i], "id", "YINELENEN_KIMLIK", "Kritik", LAYER_SEMANTIC,
                                   f"'{sid}' kimliği {len(idxs)} kayıtta kullanılmış.",
                                   f"konumlar={[f'scenarios[{j}]' for j in idxs]}",
                                   "Kimliklerden birini benzersiz yeni bir kimlikle değiştirin."))
    return out


def _request_key(s: dict) -> tuple:
    fx = s.get("fixture_ref") if isinstance(s.get("fixture_ref"), dict) else {}
    return (s.get("http_method"), s.get("endpoint"), fx.get("user"),
            json.dumps(s.get("request_input"), sort_keys=True, ensure_ascii=False))


def check_duplicate_content(scenarios: list[Any]) -> list[dict]:
    """Farklı kimlikle aynı isteği (metot+endpoint+kimlik+girdi) tanımlayan kayıtlar."""
    groups: dict[tuple, list[int]] = defaultdict(list)
    for i, s in enumerate(scenarios):
        if isinstance(s, dict):
            groups[_request_key(s)].append(i)
    out = []
    for key, idxs in groups.items():
        if len(idxs) > 1:
            ids = [scenarios[j].get("id") for j in idxs]
            for i in idxs:
                out.append(finding(i, scenarios[i], "http_method+endpoint+fixture_ref.user+request_input",
                                   "OLASI_YINELENEN_KAYIT", "Düşük", LAYER_SEMANTIC,
                                   "Aynı istek birden fazla senaryoda tanımlanmış.",
                                   f"anahtar={key}; kimlikler={ids}",
                                   "Kayıtları birleştirin veya ayırt edici koşulu belgeleyin."))
    return out


def check_label_consistency(scenarios: list[Any]) -> list[dict]:
    """Pozitif/negatif etiketinin durum kodu ve bilerek-hata işaretiyle tutarlılığı."""
    out = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            continue
        label, status, flaw = s.get("label"), s.get("expected_http_status"), s.get("is_intentional_flaw")
        if not _is_int(status) or label not in ("positive", "negative"):
            continue
        if flaw is True:
            if label != "negative":
                out.append(finding(i, s, "label", "TUTARSIZ_ETIKET", "Orta", LAYER_SEMANTIC,
                                   "Bilerek-hatalı senaryo 'positive' etiketli; veri kümesinde hatalı "
                                   "davranışlar 'negative' olarak etiketlenir.",
                                   f"label={label}, is_intentional_flaw=true",
                                   "Etiketi gözden geçirin (güvensiz davranış = negative)."))
            continue
        if label == "positive" and status >= 400:
            out.append(finding(i, s, "label", "TUTARSIZ_ETIKET", "Yüksek", LAYER_SEMANTIC,
                               "Pozitif senaryo ret durum kodu bekliyor.", f"label=positive, status={status}",
                               "Etiketi 'negative' yapın veya beklenen durum kodunu düzeltin."))
        if label == "negative" and status < 400:
            out.append(finding(i, s, "label", "TUTARSIZ_ETIKET", "Yüksek", LAYER_SEMANTIC,
                               "Bilerek-hatalı olmayan negatif senaryo başarılı (2xx) durum bekliyor.",
                               f"label=negative, status={status}, is_intentional_flaw={flaw}",
                               "Etiketi, durum kodunu veya is_intentional_flaw değerini düzeltin."))
    return out


# --------------------------------------------------------------------------------------
# 3) Fixture ve endpoint referans bütünlüğü (statik)
# --------------------------------------------------------------------------------------
def check_fixture_references(scenarios: list[Any], users: list[dict], articles: list[dict],
                             routes: list[Route]) -> list[dict]:
    """fixture_ref.user / fixture_ref.article / endpoint referanslarını doğrular.

    Rol semantiği kullanıcı adından değil fixture verisinden (is_staff, owner) doğrulanır.
    """
    users_by_name = {u["fields"]["username"]: u for u in users}
    articles_by_pk = {a["pk"]: a for a in articles}
    out: list[dict] = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            continue
        fx = s.get("fixture_ref") if isinstance(s.get("fixture_ref"), dict) else None
        role, status = s.get("user_role"), s.get("expected_http_status")
        if fx is None:
            continue  # eksik/bozuk fixture_ref alan kontrollerinde raporlanır
        user, article = fx.get("user"), fx.get("article")
        urow = users_by_name.get(user) if user is not None else None
        if user is not None and urow is None:
            out.append(finding(i, s, "fixture_ref/user", "KIRIK_FIXTURE_REFERANSI", "Yüksek", LAYER_REFERENCE,
                               "Referans verilen kullanıcı users.json içinde yok.",
                               f"user={user!r}; mevcut={sorted(users_by_name)}",
                               "Var olan bir fixture kullanıcısını referans gösterin."))
        if (user is None) != (role == "anonymous") and role is not None:
            out.append(finding(i, s, "user_role", "ROL_TUTARSIZLIGI", "Yüksek", LAYER_REFERENCE,
                               "Anonim rol ile fixture kullanıcısı tutarsız.",
                               f"user_role={role}, fixture_ref.user={user!r}",
                               "Anonim senaryolarda user=null, diğerlerinde bir fixture kullanıcısı kullanın."))
        if urow is not None:
            staff = bool(urow["fields"].get("is_staff"))
            if role == "admin" and not staff:
                out.append(finding(i, s, "user_role", "ROL_TUTARSIZLIGI", "Yüksek", LAYER_REFERENCE,
                                   "admin rolündeki kullanıcı fixture'da is_staff değil.",
                                   f"user={user}, is_staff=false", "Yönetici fixture kullanıcısı kullanın."))
            if role in ("user", "owner") and staff:
                out.append(finding(i, s, "user_role", "ROL_TUTARSIZLIGI", "Orta", LAYER_REFERENCE,
                                   "Yönetici (is_staff) kullanıcı admin dışı rolle etiketlenmiş.",
                                   f"user={user}, user_role={role}", "Rolü 'admin' yapın veya kullanıcıyı değiştirin."))
        arow = articles_by_pk.get(article) if article is not None else None
        if article is not None and arow is None and status != 404:
            out.append(finding(i, s, "fixture_ref/article", "KIRIK_FIXTURE_REFERANSI", "Yüksek", LAYER_REFERENCE,
                               "Referans verilen makale articles.json içinde yok ve 404 beklenmiyor.",
                               f"article={article}; mevcut={sorted(articles_by_pk)}; status={status}",
                               "Var olan bir makale kullanın veya mevcut olmayan kaynak için 404 bekleyin."))
        if urow is not None and not urow["fields"].get("is_staff"):
            if role == "owner":
                if arow is not None and arow["fields"].get("owner") != urow["pk"]:
                    out.append(finding(i, s, "user_role", "ROL_TUTARSIZLIGI", "Yüksek", LAYER_REFERENCE,
                                       "owner rolü, referans makalenin sahibi olmayan kullanıcıyla eşleşmiş.",
                                       f"user={user} (pk={urow['pk']}), article={article} owner={arow['fields'].get('owner')}",
                                       "Makalenin gerçek sahibini kullanın veya rolü 'user' yapın."))
                elif arow is None:
                    why = "koleksiyon ucu (nesne yok)" if article is None else f"makale {article} fixture'da yok"
                    out.append(finding(i, s, "user_role", "ROL_DOGRULANAMIYOR", "Bilgi", LAYER_REFERENCE,
                                       "owner rolü fixture verisinden doğrulanamıyor; istek hedefinde sahibi "
                                       "belirlenebilecek bir nesne yok.",
                                       f"{why}; user={user}",
                                       "Rolün anlamını belgeleyin (ör. 'başka kayıtların sahibi olan kullanıcı') "
                                       "veya bu senaryolarda 'user' rolünü kullanın."))
            if role == "user" and arow is not None and arow["fields"].get("owner") == urow["pk"]:
                out.append(finding(i, s, "user_role", "ROL_TUTARSIZLIGI", "Orta", LAYER_REFERENCE,
                                   "user rolü, referans makalenin sahibiyle eşleşmiş.",
                                   f"user={user}, article={article}", "Rolü 'owner' yapın."))
        route, pk = resolve_route(s.get("endpoint"), routes)
        if isinstance(s.get("endpoint"), str) and route is None:
            out.append(finding(i, s, "endpoint", "COZUMLENEMEYEN_ENDPOINT", "Yüksek", LAYER_REFERENCE,
                               "Endpoint, urls.py'den çıkarılan hiçbir rota desenine uymuyor.",
                               f"endpoint={s.get('endpoint')!r}; desenler={[r.pattern for r in routes]}",
                               "Endpoint'i mevcut bir rotaya göre düzeltin."))
            continue
        if route is None:
            continue
        if pk is not None and str(article) != pk:
            out.append(finding(i, s, "fixture_ref/article", "TUTARSIZ_FIXTURE_REFERANSI", "Yüksek", LAYER_REFERENCE,
                               "Endpoint'teki nesne kimliği fixture_ref.article ile uyuşmuyor.",
                               f"endpoint pk={pk}, fixture_ref.article={article}",
                               "fixture_ref.article değerini endpoint ile eşitleyin."))
        if pk is None and article is not None:
            out.append(finding(i, s, "fixture_ref/article", "TUTARSIZ_FIXTURE_REFERANSI", "Orta", LAYER_REFERENCE,
                               "Koleksiyon ucunda makale referansı verilmiş.",
                               f"endpoint={s.get('endpoint')}, article={article}",
                               "Koleksiyon uçlarında article=null kullanın."))
        flaw = s.get("is_intentional_flaw")
        if flaw is True and not route.insecure:
            out.append(finding(i, s, "is_intentional_flaw", "TUTARSIZ_ETIKET", "Orta", LAYER_REFERENCE,
                               "Bilerek-hatalı senaryo güvenli (views.py) bir uca işaret ediyor.",
                               f"endpoint={s.get('endpoint')} → {route.view_name} ({route.view_module}.py)",
                               "Senaryoyu insecure.py ucuna yönlendirin veya işareti kaldırın."))
        if flaw is False and route.insecure:
            out.append(finding(i, s, "is_intentional_flaw", "TUTARSIZ_ETIKET", "Orta", LAYER_REFERENCE,
                               "Bilerek güvensiz uca giden senaryo bilerek-hatalı olarak işaretlenmemiş.",
                               f"endpoint={s.get('endpoint')} → {route.view_name} (insecure.py)",
                               "is_intentional_flaw=true ve flaw_explanation ekleyin ya da amacı belgeleyin."))
    return out


def check_method_support(scenarios: list[Any], method_support: dict | None) -> list[dict]:
    """Django URL çözümlemesine göre metot desteği ile 405 beklentisinin tutarlılığı."""
    if not method_support:
        return []
    out = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            continue
        sup = method_support.get(s.get("endpoint"))
        method, status = s.get("http_method"), s.get("expected_http_status")
        if not sup or method not in HTTP_METHODS:
            continue
        allowed = method in sup["allowed_methods"]
        if not allowed and status != 405:
            out.append(finding(i, s, "expected_http_status", "DURUM_KODU_TUTARSIZLIGI", "Yüksek", LAYER_DJANGO,
                               "View bu metodu desteklemiyor; DRF bu durumda 405 döndürür.",
                               f"{sup['view']} izinli={sup['allowed_methods']}; beklenen={status}",
                               "Beklenen durumu 405 yapın veya endpoint/metodu düzeltin."))
        if allowed and status == 405:
            out.append(finding(i, s, "expected_http_status", "DURUM_KODU_TUTARSIZLIGI", "Yüksek", LAYER_DJANGO,
                               "405 bekleniyor ancak view bu metodu destekliyor.",
                               f"{sup['view']} izinli={sup['allowed_methods']}",
                               "Beklenen durum kodunu gözden geçirin."))
    return out


# --------------------------------------------------------------------------------------
# 4) Durum kodu makullük incelemesi (sezgisel; kesin hata DEĞİL)
# --------------------------------------------------------------------------------------
def check_status_plausibility(scenarios: list[Any]) -> list[dict]:
    """Yalnızca inceleme gerektiren durumları işaretler.

    Evrensel HTTP varsayımı yapılmaz (ör. "her başarılı DELETE 204 olmalı" kuralı yoktur).
    Kurallar bu hedef uygulamanın yapılandırmasına dayanır: BasicAuthentication etkin olduğundan
    kimlik doğrulanmamış isteğe DRF 401 döndürür; ``is_staff`` yönetici nesne izinlerini geçer.
    Bu kurallara aykırı kayıtlar "inceleme" olarak raporlanır.
    """
    out = []
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict):
            continue
        status, role, method = s.get("expected_http_status"), s.get("user_role"), s.get("http_method")
        cat, flaw = s.get("category"), s.get("is_intentional_flaw")
        if not _is_int(status):
            continue
        notes = []
        if role == "anonymous" and status == 403:
            notes.append("anonim istek için 403 (BasicAuthentication etkinken DRF genellikle 401 döndürür)")
        if role != "anonymous" and status == 401:
            notes.append("kimliği doğrulanmış istek için 401")
        if role == "admin" and status == 403:
            notes.append("yönetici için 403 (izin sınıfı is_staff'a izin veriyor)")
        if status == 201 and method != "POST":
            notes.append(f"{method} için 201")
        if status == 204 and method != "DELETE":
            notes.append(f"{method} için 204")
        if cat == "INPUT_VALIDATION" and status not in (400, 401, 403, 404) and not flaw:
            notes.append(f"girdi doğrulama kategorisinde {status}")
        if cat == "AUTHENTICATION" and status not in (401, 403) and not flaw and s.get("label") == "negative":
            notes.append(f"negatif kimlik doğrulama senaryosunda {status}")
        for n in notes:
            out.append(finding(i, s, "expected_http_status", "DURUM_KODU_INCELEME", "Bilgi", LAYER_STATUS,
                               "Beklenen durum kodu proje-özgü sezgisel kurala uymuyor; inceleme gerekir.",
                               n, "H3-01 senaryo↔uygulama testi sonucu ve view kodu ile birlikte değerlendirin."))
    return out


# --------------------------------------------------------------------------------------
# 5) JSON ↔ CSV tutarlılığı
# --------------------------------------------------------------------------------------
def export_columns(export_script: Path) -> list[str]:
    """export_scenarios_csv.py içindeki COLS listesini AST ile (çalıştırmadan) okur."""
    tree = ast.parse(export_script.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "COLS" for t in node.targets):
            return list(ast.literal_eval(node.value))
    raise ValueError(f"{export_script} içinde COLS tanımı bulunamadı.")


def expected_csv_row(s: dict) -> dict[str, str]:
    """export_scenarios_csv.py'deki dönüşümün birebir karşılığı (metin olarak)."""
    fx = s.get("fixture_ref") or {}
    return {
        "id": str(s.get("id")),
        "category": str(s.get("category")),
        "http_method": str(s.get("http_method")),
        "endpoint": str(s.get("endpoint")),
        "user_role": str(s.get("user_role")),
        "expected_http_status": str(s.get("expected_http_status")),
        "label": str(s.get("label")),
        "is_intentional_flaw": str(s.get("is_intentional_flaw")),
        "fixture_user": fx.get("user") or "",
        "fixture_article": str(fx["article"]) if fx.get("article") is not None else "",
        "request_input": json.dumps(s["request_input"], ensure_ascii=False) if s.get("request_input") else "",
        "expected_behavior": str(s.get("expected_behavior", "")),
        "flaw_explanation": s.get("flaw_explanation", ""),
        "requirement_refs": ";".join(s.get("requirement_refs") or []),
    }


def check_csv_consistency(scenarios: list[Any], csv_df: pd.DataFrame, columns: list[str]) -> list[dict]:
    """Türetilmiş CSV'nin kanonik JSON'dan üretilecek CSV ile hücre hücre aynı olduğunu doğrular."""
    out: list[dict] = []
    if list(csv_df.columns) != list(columns):
        out.append(finding(None, None, "<başlık>", "CSV_SUTUN_UYUSMAZLIGI", "Yüksek", LAYER_CSV,
                           "CSV sütunları dışa aktarım betiğindeki COLS ile aynı değil.",
                           f"csv={list(csv_df.columns)}; beklenen={columns}",
                           "export_scenarios_csv.py ile CSV'yi yeniden üretin.", locator="scenarios.csv"))
    json_ids = [s.get("id") for s in scenarios if isinstance(s, dict)]
    csv_ids = list(csv_df["id"]) if "id" in csv_df.columns else []
    if len(csv_df) != len(json_ids):
        out.append(finding(None, None, "<satır sayısı>", "CSV_SATIR_UYUSMAZLIGI", "Yüksek", LAYER_CSV,
                           "CSV satır sayısı JSON senaryo sayısından farklı.",
                           f"csv={len(csv_df)}, json={len(json_ids)}",
                           "CSV'yi yeniden üretin.", locator="scenarios.csv"))
    for sid in sorted(set(json_ids) - set(csv_ids), key=str):
        i = json_ids.index(sid)
        out.append(finding(i, scenarios[i], "id", "CSV_EKSIK_KAYIT", "Yüksek", LAYER_CSV,
                           "JSON'daki kayıt CSV'de yok.", f"id={sid}", "CSV'yi yeniden üretin."))
    for sid in sorted(set(csv_ids) - set(json_ids), key=str):
        out.append(finding(None, None, "id", "CSV_FAZLA_KAYIT", "Yüksek", LAYER_CSV,
                           "CSV'de JSON'da olmayan bir kayıt var.", f"id={sid}",
                           "CSV'yi kanonik JSON'dan yeniden üretin.", locator=f"scenarios.csv id={sid}"))
    common = [sid for sid in json_ids if sid in set(csv_ids)]
    if common and [x for x in csv_ids if x in set(common)] != common:
        out.append(finding(None, None, "<sıra>", "CSV_SIRA_UYUSMAZLIGI", "Düşük", LAYER_CSV,
                           "CSV satır sırası JSON sırasından farklı.", "sıra karşılaştırması",
                           "CSV'yi yeniden üretin.", locator="scenarios.csv"))
    csv_by_id = {r["id"]: r for r in csv_df.to_dict("records")} if "id" in csv_df.columns else {}
    for i, s in enumerate(scenarios):
        if not isinstance(s, dict) or s.get("id") not in csv_by_id:
            continue
        exp, got = expected_csv_row(s), csv_by_id[s["id"]]
        for col in columns:
            if col in got and col in exp and str(got[col]) != exp[col]:
                out.append(finding(i, s, col, "CSV_DEGER_UYUSMAZLIGI", "Yüksek", LAYER_CSV,
                                   "CSV hücresi kanonik JSON'dan türetilen değerden farklı.",
                                   f"csv={got[col]!r}; json'dan beklenen={exp[col]!r}",
                                   "CSV'yi export_scenarios_csv.py ile yeniden üretin (JSON kanoniktir)."))
    return out


# --------------------------------------------------------------------------------------
# Birleştirme
# --------------------------------------------------------------------------------------
def findings_frame(findings: Iterable[dict]) -> pd.DataFrame:
    """Bulguları sabit sütunlu, deterministik sıralı tabloya dönüştürür (boşsa başlıklarla)."""
    rows = list(findings)
    df = pd.DataFrame(rows, columns=[c for c in FINDING_COLUMNS if c != "bulgu_no"])
    if df.empty:
        return pd.DataFrame(columns=FINDING_COLUMNS)
    df["_sev"] = df["onem_derecesi"].map({s: k for k, s in enumerate(SEVERITY_ORDER)})
    df["_idx"] = df["konum"].str.extract(r"scenarios\[(\d+)\]")[0].astype(float).fillna(1e9)
    df = (df.sort_values(["_sev", "_idx", "sorun_turu", "alan", "kanit"], kind="mergesort")
            .drop(columns=["_sev", "_idx"]).reset_index(drop=True))
    df.insert(0, "bulgu_no", [f"DQ-{k:03d}" for k in range(1, len(df) + 1)])
    return df


CHECK_REGISTRY = [
    ("JSON Schema doğrulaması (Draft 2020-12)", LAYER_SCHEMA,
     lambda ctx: check_json_schema(ctx.data, ctx.schema)),
    ("Eksik/null zorunlu alan, boş metin, geçersiz enum/tip, kimlik biçimi, hata açıklaması", LAYER_SEMANTIC,
     lambda ctx: check_record_fields(ctx.scenarios, ctx.schema)),
    ("Yinelenen senaryo kimliği", LAYER_SEMANTIC, lambda ctx: check_duplicate_ids(ctx.scenarios)),
    ("Aynı isteği tanımlayan yinelenen içerik", LAYER_SEMANTIC, lambda ctx: check_duplicate_content(ctx.scenarios)),
    ("Pozitif/negatif etiket – durum kodu – bilerek-hata tutarlılığı", LAYER_SEMANTIC,
     lambda ctx: check_label_consistency(ctx.scenarios)),
    ("Fixture kullanıcı/makale, rol semantiği, endpoint çözümleme, güvensiz uç işareti", LAYER_REFERENCE,
     lambda ctx: check_fixture_references(ctx.scenarios, ctx.users, ctx.articles, ctx.routes)),
    ("View metot desteği ile 405 beklentisi", LAYER_DJANGO,
     lambda ctx: check_method_support(ctx.scenarios, ctx.method_support)),
    ("Durum kodu makullüğü (proje-özgü sezgisel kurallar)", LAYER_STATUS,
     lambda ctx: check_status_plausibility(ctx.scenarios)),
    ("Türetilmiş CSV ↔ kanonik JSON hücre karşılaştırması", LAYER_CSV,
     lambda ctx: check_csv_consistency(ctx.scenarios, ctx.csv_df, export_columns(ctx.paths.export_script))),
]


def run_checks(ctx) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Tüm kontrolleri çalıştırır; (bulgular, çalıştırılan kontrol envanteri) döndürür."""
    findings: list[dict] = []
    inventory = []
    for name, layer, fn in CHECK_REGISTRY:
        res = fn(ctx)
        executed = not (layer == LAYER_DJANGO and not ctx.method_support)
        inventory.append({
            "kontrol": name, "kontrol_katmani": layer,
            "durum": "Çalıştırıldı" if executed else "Atlandı (Django URL çözümlemesi yok)",
            "incelenen_kayit": len(ctx.scenarios), "bulgu_sayisi": len(res),
        })
        findings += res
    return findings_frame(findings), pd.DataFrame(inventory)


def run_all_checks(ctx) -> pd.DataFrame:
    """Bağlamdaki gerçek veri kümesi üzerinde tüm kontrolleri çalıştırır."""
    return run_checks(ctx)[0]


def check_summary(findings: pd.DataFrame) -> pd.DataFrame:
    """Kontrol katmanı × önem derecesi özet tablosu."""
    if findings.empty:
        return pd.DataFrame(columns=["kontrol_katmani", "onem_derecesi", "bulgu_sayisi"])
    return (findings.groupby(["kontrol_katmani", "onem_derecesi"]).size()
            .rename("bulgu_sayisi").reset_index())


def counter_by(findings: pd.DataFrame, col: str) -> Counter:
    return Counter(findings[col]) if not findings.empty else Counter()
