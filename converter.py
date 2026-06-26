import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md


def html_to_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    _unwrap_iframes(soup)
    _fix_images(soup)
    return md(str(soup), heading_style="atx", bullets="-", strip=["script", "style"])


def extract_image_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if not src.startswith("data:"):
            urls.append(src)
    return urls


def local_image_url(url: str, year: int) -> str:
    name = _image_filename(url)
    return f"images/{year}/{name}"


def rewrite_image_urls(html: str, year: int) -> str:
    def replacer(match):
        url = match.group(1)
        if url.startswith("data:"):
            return match.group(0)
        local = local_image_url(url, year)
        return f'src="{local}"'

    return re.sub(r'src="([^"]+)"', replacer, html)


def _fix_images(soup: BeautifulSoup) -> None:
    for img in soup.find_all("img"):
        src = img.get("src", "")
        if not src:
            continue
        img["src"] = _normalize_url(src)
        img.attrs = {k: v for k, v in img.attrs.items() if k in {"src", "alt"}}


def _unwrap_iframes(soup: BeautifulSoup) -> None:
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src") or iframe.get("data-src", "")
        if src:
            link = soup.new_tag("a", href=_normalize_url(src))
            link.string = src
            iframe.replace_with(link)
        else:
            iframe.decompose()


def _normalize_url(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return urljoin("https://yvision.kz", url)
    return url


def _image_filename(url: str) -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1]
    if not name or len(name) < 3:
        name = str(abs(hash(url)))[:12]
    name = re.sub(r"[^\w.\-]", "_", name)
    return name
