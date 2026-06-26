import threading
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from exporter import export_account
from resolver import AccountNotFound, resolve_account
from webapp.jobs import JobRegistry
from webapp.runner import run_export

EXPORT_DIR = Path("/data/exports")
MAX_CONCURRENT = 2

app = FastAPI(title="myvision exporter")
registry = JobRegistry()
_semaphore = threading.Semaphore(MAX_CONCURRENT)

_STATIC = Path(__file__).parent / "static"


class ExportRequest(BaseModel):
    account: str
    include_images: bool = True


def run_in_background(fn: Callable[[], None]) -> None:
    threading.Thread(target=fn, daemon=True).start()


@app.post("/api/export", status_code=202)
def start_export(req: ExportRequest):
    try:
        _user_id, username = resolve_account(req.account)
    except AccountNotFound:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    except ValueError:
        raise HTTPException(status_code=400, detail="Некорректный логин или ссылка")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    job = registry.create(username=username)

    def task() -> None:
        with _semaphore:
            run_export(job, req.account, req.include_images, EXPORT_DIR, export_account)

    run_in_background(task)
    return {"job_id": job.id}


@app.get("/api/export/{job_id}")
def job_status(job_id: str):
    job = registry.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return {
        "state": job.state,
        "done": job.done,
        "total": job.total,
        "phase": job.phase,
        "username": job.username,
        "error": job.error,
    }


@app.get("/api/export/{job_id}/download")
def download(job_id: str):
    job = registry.get(job_id)
    if job is None or job.state != "done" or not job.zip_path:
        raise HTTPException(status_code=404, detail="Файл не готов")
    filename = f"{job.username}-yvision-export.zip"
    return FileResponse(job.zip_path, media_type="application/zip", filename=filename)


@app.get("/", response_class=HTMLResponse)
def index():
    return (_STATIC / "index.html").read_text(encoding="utf-8")


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
