import httpx
import pytest

import resolver as resolver_mod
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


def _mock_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport, base_url=resolver_mod.API_BASE)


def test_resolve_username_returns_id(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/users/drugoi"
        return httpx.Response(200, json={"id": 8249, "username": "drugoi", "fullname": "N"})

    monkeypatch.setattr(resolver_mod, "_make_client", lambda: _mock_client(handler))
    user_id, username = resolver_mod.resolve_account("https://drugoi.yvision.kz")
    assert user_id == 8249
    assert username == "drugoi"


def test_resolve_unknown_username_raises(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"code": 404, "message": "user_not_found"})

    monkeypatch.setattr(resolver_mod, "_make_client", lambda: _mock_client(handler))
    with pytest.raises(resolver_mod.AccountNotFound):
        resolver_mod.resolve_account("nope_not_real")


def test_resolve_numeric_id_uses_posts_endpoint(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v2/users/8249/posts"
        return httpx.Response(200, json={"items": [{"user": {"id": 8249, "username": "drugoi"}}]})

    monkeypatch.setattr(resolver_mod, "_make_client", lambda: _mock_client(handler))
    user_id, username = resolver_mod.resolve_account("8249")
    assert user_id == 8249
    assert username == "drugoi"
