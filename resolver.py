from urllib.parse import urlparse

_BASE_DOMAIN = "yvision.kz"


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
