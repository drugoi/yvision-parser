import exporter as exporter_mod
from models import Post


def _posts():
    return [
        Post(id=1, slug="1-a", title="A", content_html="<p>a</p>",
             publication_date="2014-02-02 10:00:00+00"),
        Post(id=2, slug="2-b", title="B", content_html="<p>b</p>",
             publication_date="2013-05-05 10:00:00+00"),
    ]


def test_export_account_reports_progress_and_saves(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter_mod, "resolve_account", lambda acc: (8249, "drugoi"))
    monkeypatch.setattr(exporter_mod, "fetch_all_posts", lambda uid: _posts())
    seen = []
    result = exporter_mod.export_account(
        "drugoi", tmp_path, include_images=False,
        on_progress=lambda done, total, phase: seen.append((done, total)),
    )
    assert result.username == "drugoi"
    assert result.total == 2
    assert result.saved == 2
    assert seen == [(1, 2), (2, 2)]                       # progress fires once per saved post
    assert len(list(tmp_path.rglob("*.md"))) == 2          # files written under tmp_path/drugoi/...


def test_export_account_writes_under_username_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(exporter_mod, "resolve_account", lambda acc: (8249, "drugoi"))
    monkeypatch.setattr(exporter_mod, "fetch_all_posts", lambda uid: _posts())
    exporter_mod.export_account("drugoi", tmp_path, include_images=False)
    assert (tmp_path / "drugoi").is_dir()                  # engine creates <dest>/<username>/


def test_export_account_dedups_duplicate_slugs(tmp_path, monkeypatch):
    dup = Post(id=1, slug="1-a", title="A", content_html="<p>a</p>",
               publication_date="2014-02-02 10:00:00+00")
    monkeypatch.setattr(exporter_mod, "resolve_account", lambda acc: (1, "u"))
    monkeypatch.setattr(exporter_mod, "fetch_all_posts", lambda uid: [dup, dup])
    result = exporter_mod.export_account("u", tmp_path, include_images=False)
    assert result.total == 1
    assert result.saved == 1
