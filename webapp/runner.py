import logging
import shutil
import tempfile
from pathlib import Path
from typing import Callable

from webapp.jobs import Job

ExportFn = Callable[..., object]

logger = logging.getLogger(__name__)


def run_export(
    job: Job,
    account: str,
    include_images: bool,
    export_dir: Path,
    export_fn: ExportFn,
) -> None:
    """Build the export ZIP for `job`. Updates job state; never raises."""
    job.start()
    work = Path(tempfile.mkdtemp(prefix="yv-", dir=export_dir))
    try:
        export_fn(
            account, work, include_images=include_images,
            on_progress=lambda d, t, p: job.update(d, t, p),
        )
        zip_base = export_dir / job.id
        shutil.make_archive(str(zip_base), "zip", root_dir=work)
        job.finish(zip_path=f"{zip_base}.zip")
    except Exception as exc:  # surface any failure to the UI
        logger.exception("export failed for job %s (account=%s)", job.id, account)
        job.fail(str(exc))
    finally:
        shutil.rmtree(work, ignore_errors=True)
