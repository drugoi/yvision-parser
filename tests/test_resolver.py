import pytest

from resolver import parse_account_input


def test_plain_username():
    kind, value = parse_account_input("drugoi")
    assert kind == "username"
    assert value == "drugoi"


def test_numeric_id():
    kind, value = parse_account_input("8249")
    assert kind == "id"
    assert value == "8249"


def test_full_profile_url():
    kind, value = parse_account_input("https://drugoi.yvision.kz")
    assert kind == "username"
    assert value == "drugoi"


def test_profile_url_trailing_slash_and_path():
    kind, value = parse_account_input("https://drugoi.yvision.kz/posts/")
    assert kind == "username"
    assert value == "drugoi"


def test_profile_url_without_scheme():
    kind, value = parse_account_input("drugoi.yvision.kz")
    assert kind == "username"
    assert value == "drugoi"


def test_username_with_whitespace_and_at():
    kind, value = parse_account_input("  @drugoi  ")
    assert kind == "username"
    assert value == "drugoi"


def test_bare_domain_is_rejected():
    with pytest.raises(ValueError):
        parse_account_input("https://yvision.kz")
