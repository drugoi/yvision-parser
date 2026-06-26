from webapp.jobs import Job, JobRegistry


def test_create_and_fetch_job():
    reg = JobRegistry()
    job = reg.create(username="drugoi")
    assert job.state == "queued"
    assert reg.get(job.id) is job


def test_progress_updates_job():
    reg = JobRegistry()
    job = reg.create(username="drugoi")
    job.update(done=3, total=10, phase="saving")
    assert (job.done, job.total, job.phase) == (3, 10, "saving")
    job.finish(zip_path="/tmp/x.zip")
    assert job.state == "done"
    assert job.zip_path == "/tmp/x.zip"


def test_failed_job_records_error():
    reg = JobRegistry()
    job = reg.create(username="u")
    job.fail("boom")
    assert job.state == "error"
    assert job.error == "boom"


def test_unknown_job_is_none():
    assert JobRegistry().get("nope") is None
