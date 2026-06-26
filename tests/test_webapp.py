import io
import zipfile

import pytest
from fastapi.testclient import TestClient

import webapp.app as appmod
from resolver import AccountNotFound


@pytest.fixture
def client(monkeypatch, tmp_path):
    def fake_resolve(account):
        if account == "nope":
            raise AccountNotFound("User 'nope' not found on yvision.kz")
        return (8249, "drugoi")

    def fake_export(account, dest_dir, *, include_images=True, on_progress=None):
        from exporter import ExportResult
        target = dest_dir / "drugoi" / "2014"
        target.mkdir(parents=True, exist_ok=True)
        (target / "post.md").write_text("# hi", encoding="utf-8")
        if on_progress:
            on_progress(1, 1, "saving")
        return ExportResult(username="drugoi", total=1, saved=1)

    monkeypatch.setattr(appmod, "resolve_account", fake_resolve)
    monkeypatch.setattr(appmod, "export_account", fake_export)
    monkeypatch.setattr(appmod, "EXPORT_DIR", tmp_path)
    monkeypatch.setattr(appmod, "run_in_background", lambda fn: fn())  # run synchronously
    return TestClient(appmod.app)


def test_export_unknown_user_returns_404(client):
    r = client.post("/api/export", json={"account": "nope", "include_images": False})
    assert r.status_code == 404
    assert "не найден" in r.json()["detail"]


def test_export_happy_path_then_download(client):
    r = client.post("/api/export", json={"account": "drugoi", "include_images": False})
    assert r.status_code == 202
    job_id = r.json()["job_id"]

    s = client.get(f"/api/export/{job_id}")
    assert s.status_code == 200
    assert s.json()["state"] == "done"
    assert s.json()["username"] == "drugoi"

    d = client.get(f"/api/export/{job_id}/download")
    assert d.status_code == 200
    assert d.headers["content-type"] == "application/zip"
    zf = zipfile.ZipFile(io.BytesIO(d.content))
    assert any(name.endswith("post.md") for name in zf.namelist())


def test_status_unknown_job_404(client):
    assert client.get("/api/export/nope").status_code == 404
