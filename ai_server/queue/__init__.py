"""ai_server.queue -- task queue subsystem (NOT the stdlib `queue` module).

Submodules:
    task          Task dataclass + TaskStatus enum + transition guard
    persistence   SQLite SoT for tasks (init / CRUD / heartbeat)
    inproc_queue  multiprocessing.Queue wrapper + SHUTDOWN_EVENT
    recovery      rebuild queue from SQLite on process restart
    watchdog      HeartbeatWatchdog for stale RUNNING detection

Importing this package side-effect-fully registers its submodules under
`ai_server.queue.*` so callers can write `from ai_server.queue.task import Task`.

NOTE on stdlib collision: the package is named `queue`, which collides
with the stdlib `queue` module when C:\FitScan (or the parent dir) is
on sys.path before Python's stdlib path. We mitigate by exposing a
`is_our_queue` sentinel and by re-exporting `task`/`persistence` eagerly
so attribute access is always explicit (`ai_server.queue.task.Task`).
"""
from __future__ import annotations

from . import inproc_queue, persistence, recovery, task, watchdog  # noqa: F401

__all__ = ["task", "persistence", "inproc_queue", "recovery", "watchdog"]
