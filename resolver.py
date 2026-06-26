from urllib.parse import urlparse

import httpx

_BASE_DOMAIN = "yvision.kz"
_API_BASE = "https://brain.yvision.kz/api/v2"


def parse_account_input(account: str) -> tuple[str, str]:
    """Classify raw user input.

    Returns (kind, value) where kind is:
      - "id":       value is a numeric user id string
      - "username": value is a yvision username
    Raises ValueError if the input cannot be interpreted as an account.
    """
    text = account.strip().lstrip("@").strip()
    if not text:
        raise ValueError("Empty account input")

    if text.isdigit():
        return "id", text

    looks_like_url = "://" in text or text.endswith(_BASE_DOMAIN) or "/" in text
    if looks_like_url:
        return "username", _username_from_url(text)

    return "username", text


def _username_from_url(text: str) -> str:
    candidate = text if "://" in text else f"https://{text}"
    host = urlparse(candidate).hostname or ""
    if not host.endswith(_BASE_DOMAIN):
        raise ValueError(f"Not a yvision.kz address: {text!r}")
    subdomain = host[: -len(_BASE_DOMAIN)].rstrip(".")
    if not subdomain or subdomain == "www":
        raise ValueError(
            f"No username found in {text!r} — expected https://<username>.{_BASE_DOMAIN}"
        )
    return subdomain


class AccountNotFound(Exception):
    pass


def _make_client() -> httpx.Client:
    return httpx.Client(base_url=_API_BASE, timeout=30, follow_redirects=True)


def resolve_account(account: str) -> tuple[int, str]:
    """Resolve raw input to (user_id, username). Raises AccountNotFound if unknown.

    Only `id` and `username` are read from the API response — other personal
    fields (email/phone/dob) are deliberately ignored.
    """
    kind, value = parse_account_input(account)
    with _make_client() as client:
        if kind == "id":
            return _resolve_by_id(client, int(value))
        return _resolve_by_username(client, value)


def _resolve_by_username(client: httpx.Client, username: str) -> tuple[int, str]:
    resp = client.get(f"/users/{username}")
    if resp.status_code == 404:
        raise AccountNotFound(f"User {username!r} not found on yvision.kz")
    resp.raise_for_status()
    data = resp.json()
    return int(data["id"]), str(data.get("username") or username)


def _resolve_by_id(client: httpx.Client, user_id: int) -> tuple[int, str]:
    resp = client.get(f"/users/{user_id}/posts", params={"count": 1})
    resp.raise_for_status()
    items = resp.json().get("items") or []
    if not items:
        raise AccountNotFound(f"No posts found for user id {user_id} on yvision.kz")
    username = items[0].get("user", {}).get("username") or str(user_id)
    return user_id, str(username)
