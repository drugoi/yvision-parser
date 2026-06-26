from webapp.jobs import JobRegistry
from webapp.cleanup import sweep


def test_sweep_removes_expired(tmp_path):
    reg = JobRegistry()
    job = reg.create(username="u", now=0.0)
    z = tmp_path / f"{job.id}.zip"
    z.write_bytes(b"PK")
    job.finish(zip_path=str(z))

    removed = sweep(reg, ttl=10, now=1000.0)   # 1000 >> 0 + 10 → expired
    assert removed == 1
    assert not z.exists()
    assert reg.get(job.id) is None


def test_sweep_keeps_fresh(tmp_path):
    reg = JobRegistry()
    job = reg.create(username="u", now=995.0)
    z = tmp_path / f"{job.id}.zip"
    z.write_bytes(b"PK")
    job.finish(zip_path=str(z))

    assert sweep(reg, ttl=60, now=1000.0) == 0
    assert z.exists()
