from agent.test_generation.llm.extract import extract_code
from agent.test_generation.llm.validation import check_syntax

FENCED = "Buyrun:\n```python\nimport pytest\n\ndef test_x(seeded_db, api_client):\n    assert True\n```\nson."


def test_extract_from_fenced_block():
    code = extract_code(FENCED)
    assert code.startswith("import pytest")
    assert "def test_x" in code
    assert "```" not in code


def test_extract_unfenced_returns_text():
    assert extract_code("def test_y():\n    pass").startswith("def test_y")


def test_extract_empty():
    assert extract_code("") == ""


def test_syntax_valid_with_expected_func():
    ok, err = check_syntax("def test_x():\n    assert 1 == 1\n", expected_func="test_x")
    assert ok and err is None


def test_syntax_invalid():
    ok, err = check_syntax("def test_x(:\n    pass")
    assert not ok and "SyntaxError" in err


def test_syntax_missing_expected_func():
    ok, err = check_syntax("def other():\n    pass", expected_func="test_x")
    assert not ok and "test_x" in err


def test_syntax_empty():
    ok, err = check_syntax("   ")
    assert not ok
