from pathlib import Path

from webapp.jobs import JobRegistry


def sweep(registry: JobRegistry, ttl: float, now: float) -> int:
    """Delete artifacts and drop jobs older than `ttl` seconds. Returns count removed."""
    removed = 0
    for job in registry.all():
        if now - job.created_at < ttl:
            continue
        if job.zip_path:
            Path(job.zip_path).unlink(missing_ok=True)
        registry.remove(job.id)
        removed += 1
    return removed
