import argparse
import re
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


def save_post(post: Post, output_dir: Path) -> None:
    year_dir = output_dir / str(post.year)
    year_dir.mkdir(parents=True, exist_ok=True)

    image_urls = extract_image_urls(post.content_html)
    if image_urls:
        download_images(image_urls, post.year, output_dir)

    rewritten_html = rewrite_image_urls(post.content_html, post.year)
    body = html_to_markdown(rewritten_html)

    filename = f"{post.date_slug}-{post.safe_slug}.md"
    filename = re.sub(r"[^\w.\-]", "_", filename)

    filepath = year_dir / filename
    filepath.write_text(f"{render_frontmatter(post)}\n\n{body}\n", encoding="utf-8")
    print(f"  Saved: {filepath}")


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
