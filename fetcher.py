import httpx
from models import Post

API_BASE = "https://brain.yvision.kz/api/v2"
BASE_URL = f"{API_BASE}/users/{{user_id}}/posts"


def fetch_posts(user_id: int, count: int = 10, cursor: str | None = None) -> dict:
    params: dict = {"count": count}
    if cursor:
        params["publication_date"] = cursor
    r = httpx.get(BASE_URL.format(user_id=user_id), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def parse_post(item: dict) -> Post:
    return Post(
        id=item["id"],
        slug=item["slug"],
        title=item["title"],
        content_html=item["content"],
        publication_date=item["publication_date"],
        modification_date=item.get("modification_date"),
        tags=[t.get("title", "") for t in item.get("tags") or [] if t.get("title")],
        views_count=item.get("views_count", 0),
        comments_count=item.get("comments_count", 0),
        likes_count=item.get("likes_count", 0),
        cover=item.get("cover"),
        original_url=f"https://yvision.kz/p/{item['id']}",
    )


def fetch_all_posts(user_id: int) -> list[Post]:
    posts: list[Post] = []
    cursor = None
    page = 0

    while True:
        page += 1
        data = fetch_posts(user_id, count=10, cursor=cursor)
        items = data.get("items", [])
        if not items:
            break

        for item in items:
            posts.append(parse_post(item))

        print(f"  Page {page}: fetched {len(items)} posts (total: {len(posts)})")

        if not data.get("has_next_page"):
            break
        cursor = data["publication_date"]

    return posts
