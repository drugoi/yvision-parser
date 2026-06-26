import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from converter import (
    extract_image_urls,
    html_to_markdown,
    rewrite_image_urls,
)
from downloader import download_images
from fetcher import fetch_all_posts
from models import Post
from resolver import resolve_account


@dataclass
class ExportResult:
    username: str
    total: int
    saved: int


def render_frontmatter(post: Post) -> str:
    lines = [
        "---",
        f'title: "{post.title.replace('"', '\\"')}"',
        f"date: {post.date.strftime('%Y-%m-%d')}",
        f"original_url: {post.original_url}",
    ]
    if post.tags:
        tags = ", ".join(f'"{t}"' for t in post.tags)
        lines.append(f"tags: [{tags}]")
    lines.append(f"views: {post.views_count}")
    lines.append(f"comments: {post.comments_count}")
    lines.append(f"likes: {post.likes_count}")
    lines.append("---")
    return "\n".join(lines)


def save_post(post: Post, output_dir: Path, *, include_images: bool = True) -> None:
    year_dir = output_dir / str(post.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    if include_images:
        image_urls = extract_image_urls(post.content_html)
        if image_urls:
            download_images(image_urls, post.year, output_dir)
        html = rewrite_image_urls(post.content_html, post.year)
    else:
        html = post.content_html

    body = html_to_markdown(html)

    filename = f"{post.date_slug}-{post.safe_slug}.md"
    filename = re.sub(r"[^\w.\-]", "_", filename)

    filepath = year_dir / filename
    filepath.write_text(f"{render_frontmatter(post)}\n\n{body}\n", encoding="utf-8")


def _post_key(post: Post) -> str:
    key = f"{post.year}/{post.date_slug}-{post.safe_slug}.md"
    return re.sub(r"[^\w.\-]", "_", key)


def _unique_posts(posts: list[Post]) -> list[Post]:
    seen: set[str] = set()
    unique: list[Post] = []
    for post in posts:
        key = _post_key(post)
        if key in seen:
            continue
        seen.add(key)
        unique.append(post)
    return unique


def export_account(
    account: str,
    dest_dir: Path,
    *,
    include_images: bool = True,
    on_progress: Callable[[int, int, str], None] | None = None,
) -> ExportResult:
    user_id, username = resolve_account(account)
    output_dir = Path(dest_dir) / username
    output_dir.mkdir(parents=True, exist_ok=True)

    posts = fetch_all_posts(user_id)
    unique = _unique_posts(posts)
    total = len(unique)

    saved = 0
    for post in unique:
        save_post(post, output_dir, include_images=include_images)
        saved += 1
        if on_progress is not None:
            on_progress(saved, total, "saving")

    return ExportResult(username=username, total=total, saved=saved)
