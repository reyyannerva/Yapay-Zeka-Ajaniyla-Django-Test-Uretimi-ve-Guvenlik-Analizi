from agent.test_generation.llm.loaders import templatize
from agent.test_generation.llm.prompt import render
from agent.test_generation.llm.prompt import test_name as make_test_name


def test_templatize_detail_and_publish():
    assert templatize("/api/articles/1/") == ("/api/articles/{pk}/", 1)
    assert templatize("/api/articles/2/publish/") == ("/api/articles/{pk}/publish/", 2)
    assert templatize("/api/articles/") == ("/api/articles/", None)


def test_all_38_scenarios_join(cases):
    assert len(cases) == 38


def test_case_fields_are_correct(cases):
    c = cases["SC-UPD-001"]
    assert c.http_method == "PUT"
    assert c.url_name == "article-detail"
    assert c.pk == 1
    assert c.user_username == "alice"
    assert c.expected_secure_status == 200


def test_flaw_case_meta(cases):
    c = cases["SC-FLW-001"]
    assert c.is_known_flaw is True
    assert c.deviation_kind == "status"
    assert c.observed_flawed_status == 200
    assert c.expected_secure_status == 403  # altın güvenli beklenti


def test_prompt_contains_generation_input(cases):
    p = render(cases["SC-AUZ-001"])
    assert "article-detail" in p
    assert "403" in p            # beklenen güvenli durum
    assert "carol" in p
    assert "PUT" in p


def test_prompt_has_no_answer_key_leakage(cases):
    """SIZINTI KORUMASI: cevap anahtarı meta prompt'a konmaz."""
    p = render(cases["SC-FLW-001"]).lower()
    assert "is_known_flaw" not in p
    assert "known_flaw" not in p
    assert "observed_flawed_status" not in p
    assert "deviation" not in p
    assert "security_finding" not in p
    assert "split" not in p and "dev/test" not in p
    # Not: ham "200" sayısı writable_fields.max_length içinde meşru biçimde geçtiğinden,
    # gözlenen güvensiz kodun sızmadığını alan ADLARININ yokluğuyla doğruluyoruz (yukarıda).
    assert "observed" not in p and "gözlenen" not in p


def test_test_name_format():
    assert make_test_name("SC-AUT-002") == "test_sc_aut_002"
