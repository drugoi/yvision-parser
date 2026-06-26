# Design: Prepare yvision-parser for GitHub & let users export their own accounts

**Date:** 2026-06-26
**Status:** Approved

## Problem

`yvision-parser` is a small Python CLI that exports a yvision.kz blog account's posts
to Markdown (with locally-downloaded images, organized by year). Today it is hardcoded
to a single account (`user_id = 8249`, the author's own account `drugoi`) and lacks the
scaffolding (README, LICENSE, .gitignore) needed to publish publicly. The author's
personal 17 MB export currently lives in `posts/` and must not be published.

Goal: make the tool work for **any** user's own account, and prepare the repo for a
public GitHub release.

## Decisions (locked)

- **Account input:** accept a username, profile URL, or numeric id — auto-resolve to `user_id`.
- **Scope:** public posts only, via the existing unauthenticated API. No login.
- **License:** MIT, © 2026 Nikita Bayev.
- **Packaging:** clone + run script (`pip install -r requirements.txt`, then `python main.py <account>`).
- **Personal export:** untrack `posts/` (keep on disk, gitignore it). Nothing personal ships.
- **Output layout:** `posts/<username>/<year>/...` so multiple exports don't collide.

## API facts (verified live)

- `GET https://brain.yvision.kz/api/v2/users/{username}` → full user object including
  numeric `id`. This is the username→id resolver. (A numeric value in this slot 404s —
  the slot is a username, not an id.)
- `GET https://brain.yvision.kz/api/v2/users/{id}/posts?count=N&publication_date=<cursor>`
  → paginated posts. Requires the **numeric** id (username here errors). This is the
  existing `fetcher` endpoint — unchanged.
- Profile URLs are subdomain-based: `https://{username}.yvision.kz`.
- **Privacy note:** the `users/{username}` response also contains `email`, `phone`, `dob`.
  The resolver reads **only** `id`, `username`, `fullname` and never logs/stores the rest.

## Components

### `resolver.py` (new)
```python
def resolve_account(account: str) -> tuple[int, str]:
    """Return (user_id, username) for a username, profile URL, or numeric id."""
```
Logic:
1. Numeric string → treat as `user_id`; fetch `users/{... }`? Numeric id can't be
   resolved by the by-username endpoint, so for a numeric input we trust it and derive
   the username later from the first page of posts (the post `user` object carries
   `username`). Display falls back to the id if unavailable.
2. URL (`http`/contains `.yvision.kz`) → parse hostname, take the subdomain label as the
   username, then resolve.
3. Otherwise → treat the whole string as a username.
4. Resolve via `GET /api/v2/users/{username}`; 200 → read `id`. 404 → raise a clear
   `User '<x>' not found on yvision.kz`.

### `main.py` (changed)
- Replace hardcoded `user_id`/`output_dir` with `argparse`:
  ```
  python main.py <account> [--output DIR]
  ```
  - `<account>` (required): username | profile URL | numeric id.
  - `--output` (default `posts`): base dir; posts are written under `<output>/<username>/`.
- Call `resolve_account()`, then the existing `fetch_all_posts(user_id)` and save loop,
  unchanged.

### `fetcher.py`, `converter.py`, `downloader.py`, `models.py`
- Unchanged (the numeric posts endpoint and conversion already work).

## Repo scaffolding

- **`README.md`** — description, install, usage examples (username / URL / id), output
  format, MIT badge, and a short "export your own data; respect yvision's ToS" note.
- **`LICENSE`** — MIT, © 2026 Nikita Bayev.
- **`.gitignore`** — `__pycache__/`, `*.pyc`, `.venv/`, `.DS_Store`, `posts/`.
- **`requirements.txt`** — drop `playwright` (never imported) and the invalid `[socks2]`
  extra; keep `httpx`, `markdownify`, `beautifulsoup4`.
- **`git rm --cached -r posts`** — untrack the personal export (files stay on disk).

## Error handling

- Unknown username/URL → clear "user not found" message, non-zero exit.
- Network/timeout errors → surfaced with the failing URL (per-image download already
  tolerates failures and continues).

## Testing

- `tests/test_resolver.py` (pytest) covering input parsing — username, profile URL
  (with/without scheme, trailing slash), numeric id — with the HTTP call **mocked**
  (no live API hits). README documents `pip install pytest && pytest`.

## Out of scope (YAGNI)

- Authentication / private & draft posts.
- PyPI packaging / console entry point.
- Concurrency / rate-limit tuning beyond the existing fixed delay.
