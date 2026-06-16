"""GPU worker process launcher.

The launcher is the parent process. It:
    1. Verifies the platform is Linux/WSL2 (T012).
    2. Initializes the tasks table (idempotent).
    3. Recovers any pending/stale tasks from the previous run (T006).
    4. Spawns N independent GPU worker processes — one per GPU — each pinning
       CUDA_VISIBLE_DEVICES to a single device so they have independent CUDA
       contexts (T010).
    5. Supervises the workers: if one dies, restart it (T009).
    6. Tracks a per-GPU 'breaker' — if a GPU crashes 5+ times in 10 minutes,
       mark it BROKEN and stop scheduling work to it (T008).
    7. Installs a watchdog in the parent to reap stale RUNNING tasks (T007).
    8. Starts the FastAPI API Gateway in a child process (api.py).

Why this design:
    - In-process multi-GPU is dangerous: CUDA context sharing can OOM/segfault
      across workers. Independent processes give us isolation.
    - The parent does no GPU work — it only supervises.
    - The API process is a sibling of workers; it only does enqueue/status.
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Deque

logger = logging.getLogger(__name__)


# ─── Constants ───────────────────────────────────────────────────────────────

RESTART_WINDOW_SEC = 600       # 10 minutes
MAX_RESTARTS_PER_WINDOW = 5    # >5 in 10 min → breaker opens
WATCHDOG_TIMEOUT_SEC = 600      # 10 min heartbeat timeout
WATCHDOG_SCAN_SEC = 30          # scan interval
DEFAULT_GPUS = [0, 1, 2, 3]     # override via env FITSCAN_GPUS=0,1
API_PORT = int(os.getenv("PORT", "8080"))


# ─── T012: Platform check ────────────────────────────────────────────────────

def _assert_platform() -> None:
    """AI server requires Linux or WSL2. Windows native is not supported.

    Rationale:
        - multiprocessing on Windows uses 'spawn', which forces children to
          reimport everything — fragile with CUDA + PyTorch.
        - AI server is expected to run on a dedicated Ubuntu 22.04 box or WSL2.
    """
    if sys.platform == "win32":
        raise RuntimeError(
            "AI server requires Linux/WSL2. "
            "On Windows, run inside WSL2 (wsl --install). "
            f"Current platform: {sys.platform}"
        )
    # We accept Linux and (darwin is excluded by design for GPU reasons).
    if sys.platform not in ("linux", "linux2"):
        raise RuntimeError(
            f"AI server supports Linux only. Current: {sys.platform}"
        )


# ─── T008: GPU breaker ───────────────────────────────────────────────────────

@dataclass
class GPUState:
    gpu_id: int
    role: str                     # 'fast' | 'multi' | 'idle'
    proc: subprocess.Popen | None = None
    restart_times: Deque[float] = field(default_factory=deque)
    healthy: bool = True
    last_death_reason: str = ""

    def record_restart(self) -> None:
        self.restart_times.append(time.time())
        self._trim()

    def _trim(self) -> None:
        cutoff = time.time() - RESTART_WINDOW_SEC
        while self.restart_times and self.restart_times[0] < cutoff:
            self.restart_times.popleft()

    def should_open_breaker(self) -> bool:
        self._trim()
        return len(self.restart_times) >= MAX_RESTARTS_PER_WINDOW

    def is_busy(self) -> bool:
        return self.proc is not None and self.proc.poll() is None


# ─── T009: Worker supervisor ─────────────────────────────────────────────────

class WorkerSupervisor:
    """Owns the worker subprocesses and the API subprocess.

    Polls every 2s. On worker death:
        - log the reason
        - record restart
        - if breaker should open, mark GPU unhealthy and STOP scheduling
        - otherwise spawn a new worker on the same GPU
    """

    def __init__(self, gpu_ids: list[int]):
        self.gpu_states: dict[int, GPUState] = {
            gid: GPUState(
                gpu_id=gid,
                role=self._role_for(gid, gpu_ids),
            )
            for gid in gpu_ids
        }
        self.api_proc: subprocess.Popen | None = None
        self._stop = False

    @staticmethod
    def _role_for(gid: int, all_ids: list[int]) -> str:
        """Default role assignment:
            - smallest id     → 'fast'   (single-image SMPL)
            - second smallest → 'multi'  (multi-image SMPLer-X)
            - others          → 'idle'   (overflow + eval)
        Override by setting env FITSCAN_ROLE_<gid>=fast|multi|idle.
        """
        env_role = os.getenv(f"FITSCAN_ROLE_{gid}")
        if env_role:
            return env_role
        if gid == all_ids[0]:
            return "fast"
        if len(all_ids) > 1 and gid == all_ids[1]:
            return "multi"
        return "idle"

    def start_api(self) -> None:
        """Spawn the FastAPI gateway in a child process."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent) + os.pathsep + env.get("PYTHONPATH", "")
        self.api_proc = subprocess.Popen(
            [sys.executable, "-m", "ai_server.api"],
            env=env,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
        logger.info(f"[supervisor] API gateway spawned pid={self.api_proc.pid}")

    def start_all_workers(self) -> None:
        for gid, state in self.gpu_states.items():
            if state.is_busy():
                continue
            self._spawn_worker(state)

    def _spawn_worker(self, state: GPUState) -> None:
        """Spawn a worker process pinned to a single GPU.

        CUDA_VISIBLE_DEVICES=<gid> ensures PyTorch / CUDA only sees this one
        device, which gives the worker an isolated CUDA context.
        """
        env = os.environ.copy()
        env["CUDA_VISIBLE_DEVICES"] = str(state.gpu_id)
        env["FITSCAN_GPU_ID"] = str(state.gpu_id)
        env["FITSCAN_ROLE"] = state.role
        env["PYTHONPATH"] = str(Path(__file__).resolve().parent.parent) + os.pathsep + env.get("PYTHONPATH", "")
        state.proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "ai_server.worker_process",
                "--gpu",
                str(state.gpu_id),
                "--role",
                state.role,
            ],
            env=env,
            stdout=sys.stdout,
            stderr=subprocess.STDOUT,
        )
        logger.info(
            f"[supervisor] spawned worker gpu={state.gpu_id} role={state.role} pid={state.proc.pid}"
        )

    def supervise(self) -> None:
        """Main loop: poll worker state, restart on death, run breaker logic."""
        while not self._stop:
            # 1) Watch API process
            if self.api_proc is not None and self.api_proc.poll() is not None:
                logger.error(
                    f"[supervisor] API gateway died rc={self.api_proc.returncode}, restarting"
                )
                self.start_api()

            # 2) Watch each worker
            for state in self.gpu_states.values():
                if state.proc is None:
                    # First-time spawn (if start_all_workers was skipped)
                    if state.healthy:
                        self._spawn_worker(state)
                    continue
                if state.proc.poll() is None:
                    continue  # still alive
                rc = state.proc.returncode
                state.last_death_reason = f"exit_code={rc}"
                logger.error(
                    f"[supervisor] worker gpu={state.gpu_id} role={state.role} "
                    f"died rc={rc}"
                )
                state.proc = None
                if not state.healthy:
                    continue
                state.record_restart()
                if state.should_open_breaker():
                    state.healthy = False
                    logger.critical(
                        f"[supervisor] BREAKER OPEN for gpu={state.gpu_id} "
                        f"({len(state.restart_times)} restarts in "
                        f"{RESTART_WINDOW_SEC}s). Will NOT restart."
                    )
                    continue
                # Brief backoff to avoid thrashing on persistent crash
                time.sleep(1)
                self._spawn_worker(state)
            time.sleep(2)

    def shutdown(self) -> None:
        logger.info("[supervisor] shutting down")
        self._stop = True
        from ai_server.queue.inproc_queue import request_shutdown
        request_shutdown()
        # Terminate API and workers gracefully
        for state in self.gpu_states.values():
            if state.proc is not None and state.proc.poll() is None:
                try:
                    state.proc.terminate()
                except Exception:
                    pass
        if self.api_proc is not None and self.api_proc.poll() is None:
            try:
                self.api_proc.terminate()
            except Exception:
                pass
        time.sleep(2)
        # Force-kill survivors
        for state in self.gpu_states.values():
            if state.proc is not None and state.proc.poll() is None:
                try:
                    state.proc.kill()
                except Exception:
                    pass
        if self.api_proc is not None and self.api_proc.poll() is None:
            try:
                self.api_proc.kill()
            except Exception:
                pass


# ─── main ────────────────────────────────────────────────────────────────────

def _parse_gpu_ids() -> list[int]:
    raw = os.getenv("FITSCAN_GPUS")
    if raw:
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError as e:
            raise ValueError(f"Invalid FITSCAN_GPUS: {raw!r}") from e
    return list(DEFAULT_GPUS)


def main() -> int:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    _assert_platform()

    from ai_server.queue.persistence import init_schema
    from ai_server.queue.recovery import recover_once
    from ai_server.queue.watchdog import HeartbeatWatchdog

    # 1. Schema
    init_schema()
    logger.info("[launcher] schema initialized")

    # 2. Recovery
    n = recover_once(timeout_sec=WATCHDOG_TIMEOUT_SEC)
    logger.info(f"[launcher] recovered {n} tasks")

    # 3. Watchdog (parent process)
    wd = HeartbeatWatchdog(
        timeout_sec=WATCHDOG_TIMEOUT_SEC,
        scan_interval_sec=WATCHDOG_SCAN_SEC,
    )
    wd.start()

    # 4. Supervisor
    gpu_ids = _parse_gpu_ids()
    sup = WorkerSupervisor(gpu_ids=gpu_ids)
    sup.start_api()
    sup.start_all_workers()

    # 5. Signal handling
    def _on_signal(signum, frame):
        logger.info(f"[launcher] received signal {signum}")
        sup.shutdown()
        wd.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, _on_signal)
    signal.signal(signal.SIGTERM, _on_signal)

    # 6. Main loop
    try:
        sup.supervise()
    except KeyboardInterrupt:
        _on_signal(signal.SIGINT, None)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
