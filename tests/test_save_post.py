from pathlib import Path

import exporter as exporter_mod
from models import Post


def _post(html: str) -> Post:
    return Post(
        id=1,
        slug="1-hello",
        title="Hello",
        content_html=html,
        publication_date="2014-02-02 10:00:00+00",
    )


def test_save_post_without_images_keeps_external_urls(tmp_path, monkeypatch):
    called = {"download": False}
    monkeypatch.setattr(exporter_mod, "download_images",
                        lambda *a, **k: called.__setitem__("download", True))
    html = '<p>x</p><img src="https://im.example.com/a.png" alt="a">'
    exporter_mod.save_post(_post(html), tmp_path, include_images=False)
    md = next(tmp_path.rglob("*.md")).read_text()
    assert "https://im.example.com/a.png" in md
    assert "images/2014/" not in md
    assert called["download"] is False


def test_save_post_with_images_downloads_and_rewrites(tmp_path, monkeypatch):
    called = {"download": False}
    monkeypatch.setattr(exporter_mod, "download_images",
                        lambda *a, **k: called.__setitem__("download", True))
    html = '<p>x</p><img src="https://im.example.com/a.png" alt="a">'
    exporter_mod.save_post(_post(html), tmp_path, include_images=True)
    md = next(tmp_path.rglob("*.md")).read_text()
    assert "images/2014/" in md
    assert called["download"] is True
