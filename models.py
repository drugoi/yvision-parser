from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Post:
    id: int
    slug: str
    title: str
    content_html: str
    publication_date: str
    modification_date: str | None = None
    tags: list[str] = field(default_factory=list)
    views_count: int = 0
    comments_count: int = 0
    likes_count: int = 0
    cover: str | None = None
    original_url: str = ""

    @property
    def date(self) -> datetime:
        return datetime.fromisoformat(self.publication_date)

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def date_slug(self) -> str:
        return self.date.strftime("%Y-%m-%d")

    @property
    def safe_slug(self) -> str:
        slug = self.slug
        if slug.startswith(f"{self.id}-"):
            slug = slug[len(f"{self.id}-") :]
        return slug
