import time
from pathlib import Path

import httpx

from converter import _image_filename, _normalize_url


def download_images(
    urls: list[str],
    year: int,
    output_dir: Path,
    delay: float = 0.3,
) -> list[tuple[str, str]]:
    img_dir = output_dir / "images" / str(year)
    img_dir.mkdir(parents=True, exist_ok=True)

    downloaded = []
    client = httpx.Client(timeout=30, follow_redirects=True)

    for url in urls:
        url = _normalize_url(url)
        filename = _image_filename(url)
        dest = img_dir / filename

        if dest.exists():
            downloaded.append((url, str(dest)))
            continue

        try:
            r = client.get(url)
            r.raise_for_status()
            dest.write_bytes(r.content)
            downloaded.append((url, str(dest)))
        except Exception as e:
            print(f"    Failed to download {url}: {e}")
        time.sleep(delay)

    client.close()
    return downloaded
