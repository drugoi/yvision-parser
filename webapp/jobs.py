import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    id: str
    username: str
    state: str = "queued"          # queued | running | done | error
    done: int = 0
    total: int = 0
    phase: str = ""
    error: str | None = None
    zip_path: str | None = None
    created_at: float = 0.0

    def start(self) -> None:
        self.state = "running"

    def update(self, done: int, total: int, phase: str) -> None:
        self.done, self.total, self.phase = done, total, phase

    def finish(self, zip_path: str) -> None:
        self.zip_path = zip_path
        self.state = "done"

    def fail(self, message: str) -> None:
        self.error = message
        self.state = "error"


@dataclass
class JobRegistry:
    _jobs: dict[str, Job] = field(default_factory=dict)

    def create(self, username: str, now: float = 0.0) -> Job:
        job = Job(id=uuid.uuid4().hex, username=username, created_at=now)
        self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        return self._jobs.get(job_id)

    def all(self) -> list[Job]:
        return list(self._jobs.values())

    def remove(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)
