# yvision-parser: Public Release + Account Export Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the exporter work for any yvision.kz account (username / profile URL / numeric id) and prepare the repo for a public GitHub release, without publishing the author's personal export.

**Architecture:** Add a `resolver.py` that turns user input into a numeric `user_id` via `GET /api/v2/users/{username}`, then drive the existing (unchanged) `fetch_all_posts` + save pipeline from a new `argparse` CLI in `main.py`. Write posts under `<output>/<username>/<year>/`. Add README/LICENSE/.gitignore and untrack the personal `posts/` export.

**Tech Stack:** Python 3.11+, httpx, beautifulsoup4, markdownify, pytest (dev).

**Reference:** Design doc `docs/plans/2026-06-26-github-publish-account-export-design.md`.

---

## Conventions

- Run everything from the repo root `/Users/drugoi/projects/yvision-parser`.
- Create a venv once before starting: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt pytest`.
- Tests never hit the network — the HTTP client is monkeypatched/mocked.
- Per author preference, commit messages do **not** credit Claude/AI.

---

## Task 1: Clean up `requirements.txt`

**Files:**
- Modify: `requirements.txt`

**Step 1: Replace contents**

`requirements.txt` should be exactly:

```
httpx>=0.27.0
markdownify>=0.11.0
beautifulsoup4>=4.12.0
```

Rationale: `playwright` is never imported anywhere in the code; the `httpx[socks2]` extra is invalid (the real extra is `socks`, and no SOCKS proxy is used).

**Step 2: Verify the app still imports**

Run: `python -c "import main, fetcher, converter, downloader, models"`
Expected: no output, exit 0. (If httpx was only installed via the old extra, `pip install -r requirements.txt` first.)

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: drop unused playwright dep and invalid httpx extra"
```

---

## Task 2: Create `resolver.py` — parse account input (pure parsing, no network)

This task is split into the pure parser (Task 2) and the network resolve (Task 3) so the parsing logic is tested without mocks.

**Files:**
- Create: `resolver.py`
- Test: `tests/test_resolver.py`

**Step 1: Write the failing test**

Create `tests/test_resolver.py`:

```python
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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_resolver.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'resolver'`.

**Step 3: Write minimal implementation**

Create `resolver.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_resolver.py -v`
Expected: PASS (all 7 tests).

**Step 5: Commit**

```bash
git add resolver.py tests/test_resolver.py
git commit -m "feat: parse username, profile URL, or numeric id into account input"
```

---

## Task 3: Add network resolution to `resolver.py` — `resolve_account`

**Files:**
- Modify: `resolver.py`
- Test: `tests/test_resolver.py`

**Step 1: Write the failing test**

Append to `tests/test_resolver.py`:

```python
import httpx

import resolver as resolver_mod


def _mock_client(handler):
    transport = httpx.MockTransport(handler)
    return httpx.Client(transport=transport)


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
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_resolver.py -v`
Expected: FAIL — `AttributeError: module 'resolver' has no attribute 'resolve_account'` (and `_make_client` / `AccountNotFound` missing).

**Step 3: Write minimal implementation**

Add to `resolver.py` (keep `parse_account_input` and `_username_from_url`):

```python
import httpx

_API_BASE = "https://brain.yvision.kz/api/v2"


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
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_resolver.py -v`
Expected: PASS (all tests, including Task 2's).

**Step 5: Commit**

```bash
git add resolver.py tests/test_resolver.py
git commit -m "feat: resolve account input to numeric user_id via yvision API"
```

---

## Task 4: Wire CLI into `main.py` (argparse + per-username output)

**Files:**
- Modify: `main.py:51-77` (the `main()` function and `__main__` guard)
- Test: `tests/test_main_cli.py`

**Step 1: Write the failing test**

Create `tests/test_main_cli.py`:

```python
import main as main_mod


def test_parse_args_account_and_default_output():
    args = main_mod.parse_args(["drugoi"])
    assert args.account == "drugoi"
    assert args.output == "posts"


def test_parse_args_custom_output():
    args = main_mod.parse_args(["8249", "--output", "/tmp/export"])
    assert args.account == "8249"
    assert args.output == "/tmp/export"


def test_account_is_required(capsys):
    import pytest
    with pytest.raises(SystemExit):
        main_mod.parse_args([])
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_main_cli.py -v`
Expected: FAIL — `AttributeError: module 'main' has no attribute 'parse_args'`.

**Step 3: Write minimal implementation**

In `main.py`, add `import argparse` at the top. Replace the `main()` function and
`__main__` block (currently `main.py:51-77`) with:

```python
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="yvision-parser",
        description="Export a yvision.kz blog account's posts to Markdown.",
    )
    parser.add_argument(
        "account",
        help="yvision username, profile URL (https://<name>.yvision.kz), or numeric user id",
    )
    parser.add_argument(
        "--output",
        default="posts",
        help="base output directory (posts are written under <output>/<username>/). Default: posts",
    )
    return parser.parse_args(argv)


def main():
    args = parse_args()

    user_id, username = resolve_account(args.account)
    output_dir = Path(args.output) / username
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching all posts for {username} (id {user_id})...")
    posts = fetch_all_posts(user_id)
    if not posts:
        print("No posts found.")
        return
    print(f"\nTotal posts: {len(posts)}")
    print(
        f"Date range: {posts[-1].date.strftime('%Y-%m-%d')} — {posts[0].date.strftime('%Y-%m-%d')}\n"
    )

    existing = set()
    for post in posts:
        filepath = f"{post.year}/{post.date_slug}-{post.safe_slug}.md"
        filepath = re.sub(r"[^\w.\-]", "_", filepath)
        if filepath in existing:
            print(f"  Skipping duplicate: {filepath}")
            continue
        existing.add(filepath)
        save_post(post, output_dir)

    print(f"\nDone! {len(existing)} posts saved to {output_dir}/")


if __name__ == "__main__":
    main()
```

Also add to the imports at the top of `main.py`:

```python
from resolver import resolve_account
```

(The empty-posts guard replaces the old code, which would crash on `posts[-1]` for an
account with zero posts.)

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_main_cli.py -v`
Expected: PASS (3 tests).

**Step 5: Sanity-check the whole suite + help text**

Run: `pytest -v && python main.py --help`
Expected: all tests pass; help shows the `account` positional and `--output` option.

**Step 6: Commit**

```bash
git add main.py tests/test_main_cli.py
git commit -m "feat: accept account argument and write under per-username output dir"
```

---

## Task 5: Untrack the personal export

**Files:**
- Git index only (no file contents change; `posts/` stays on disk)

**Step 1: Untrack `posts/`**

Note: `posts/` may already be untracked (the repo has uncommitted state). This command
is safe either way — `--ignore-unmatch` prevents an error if nothing is tracked.

```bash
git rm -r --cached --ignore-unmatch posts
```

**Step 2: Verify files still exist on disk**

Run: `ls posts/ | head`
Expected: the year folders (2009…2014) and `images/` are still present locally.

**Step 3: Commit (only if something was staged)**

```bash
git commit -m "chore: stop tracking personal export under posts/" || echo "nothing to untrack"
```

---

## Task 6: Add `.gitignore`

**Files:**
- Create: `.gitignore`

**Step 1: Create `.gitignore`**

```
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/

# macOS
.DS_Store

# Exported blog data (personal)
posts/
```

**Step 2: Verify ignores take effect**

Run: `git status --porcelain | grep -E 'posts/|__pycache__|\.DS_Store' || echo "clean"`
Expected: `clean` (none of these show as untracked/modified).

**Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore for python, macOS, and personal exports"
```

---

## Task 7: Add `LICENSE` (MIT)

**Files:**
- Create: `LICENSE`

**Step 1: Create `LICENSE`** with the standard MIT text:

```
MIT License

Copyright (c) 2026 Nikita Bayev

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**Step 2: Commit**

```bash
git add LICENSE
git commit -m "chore: add MIT license"
```

---

## Task 8: Write `README.md`

**Files:**
- Create: `README.md`

**Step 1: Create `README.md`**

````markdown
# yvision-parser

Export a [yvision.kz](https://yvision.kz) blog account's posts to Markdown files,
with images downloaded locally and YAML frontmatter, organized by year.

## Features

- Export by **username**, **profile URL**, or **numeric user id**
- Converts post HTML to clean Markdown (`markdownify` + `BeautifulSoup`)
- Downloads inline images and rewrites links to local copies
- YAML frontmatter (title, date, original URL, tags, view/comment/like counts)
- Output organized as `posts/<username>/<year>/<date>-<slug>.md`

## Install

Requires Python 3.11+.

```bash
git clone https://github.com/<you>/yvision-parser.git
cd yvision-parser
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
# by username
python main.py drugoi

# by profile URL
python main.py https://drugoi.yvision.kz

# by numeric user id
python main.py 8249

# custom output directory
python main.py drugoi --output ./export
```

Posts are written to `posts/<username>/`. Re-running skips images that are already
downloaded.

## Output example

```
posts/drugoi/
  2013/
    2013-01-01-pochemu-kazahstan.md
  images/
    2013/
      tumblr_xxxx.jpg
```

```markdown
---
title: "Post title"
date: 2013-01-01
original_url: https://yvision.kz/p/311830
tags: ["tag1", "tag2"]
views: 1328
comments: 0
likes: 5
---

Post body in Markdown…
```

## Development

```bash
pip install pytest
pytest
```

## Notes

- Exports **public** posts only, via yvision's public API. No login.
- Please use this to back up **your own** content and respect yvision.kz's Terms of
  Service. The author is not affiliated with yvision.kz.

## License

[MIT](LICENSE) © 2026 Nikita Bayev
````

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with install, usage, and output examples"
```

---

## Task 9: Final verification

**Step 1: Full test suite**

Run: `pytest -v`
Expected: all tests pass.

**Step 2: Confirm no personal data is tracked**

Run: `git ls-files | grep -E '^posts/' || echo "posts/ not tracked — good"`
Expected: `posts/ not tracked — good`.

**Step 3: Confirm published file set is clean**

Run: `git ls-files`
Expected (order may vary): `.gitignore`, `LICENSE`, `README.md`, `converter.py`,
`docs/plans/...`, `downloader.py`, `fetcher.py`, `main.py`, `models.py`,
`requirements.txt`, `resolver.py`, `tests/test_main_cli.py`, `tests/test_resolver.py`.
No `posts/`, no `__pycache__`, no `.DS_Store`.

**Step 4: Live smoke test (optional, hits the network)**

Run: `python main.py drugoi --output /tmp/yv-smoke && ls /tmp/yv-smoke/drugoi`
Expected: posts download into `/tmp/yv-smoke/drugoi/<year>/`.

---

## Done

The repo is ready to push to a public GitHub remote:

```bash
git remote add origin git@github.com:<you>/yvision-parser.git
git push -u origin main
```
