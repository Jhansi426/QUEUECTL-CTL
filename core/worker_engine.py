from pathlib import Path
import threading
import json
import os
import subprocess
import time
import signal
import platform
from datetime import datetime, timezone, timedelta
from core.storage import Database
from core.config import ConfigManager


class WorkerManager:
    """
    Thread-based worker manager for QueueCTL.
    Handles:
    - job execution
    - retries with exponential backoff
    - per-job logging
    - timeout enforcement
    - graceful shutdown
    """

    workers = []
    stop_flag = False
    STATUS_FILE = "worker_threads.json"
    STOP_SIGNAL_FILE = "stop_signal.json"

    def __init__(self, worker_count: int = 1, backoff_base: int = 2):
        self.db = Database()
        self.worker_count = worker_count
        self.backoff_base = backoff_base
        self.config_mgr = ConfigManager()

    # ----------------------------------------------------------------------
    # Worker Lifecycle
    # ----------------------------------------------------------------------
    def start_workers(self):
        """Start multiple worker threads and reset any stuck jobs."""
        WorkerManager.stop_flag = False
        self._remove_stale_stop_file()

        # Revert processing jobs
        try:
            self.db.reset_processing_jobs()
        except Exception as e:
            self._console("warning", f"Could not reset processing jobs: {e}")

        WorkerManager.workers.clear()
        for i in range(self.worker_count):
            thread = threading.Thread(
                target=self.worker_loop,
                name=f"Worker-{i+1}",
                daemon=True
            )
            WorkerManager.workers.append(thread)
            thread.start()

        self._console("info", f"Started {self.worker_count} worker(s).")
        self._update_status_file()
        self.setup_signal_handlers()

    @staticmethod
    def stop_all():
        """Signal all workers to stop gracefully."""
        WorkerManager.stop_flag = True
        try:
            with open(WorkerManager.STOP_SIGNAL_FILE, "w", encoding="utf-8") as f:
                json.dump({"stop": True, "timestamp": datetime.now(timezone.utc).isoformat()}, f, indent=2)
        except Exception:
            pass
        print("Stop signal written. Workers will shut down gracefully.")

    # ----------------------------------------------------------------------
    # Worker Loop
    # ----------------------------------------------------------------------
    def worker_loop(self):
        """Main worker loop that continuously fetches and executes jobs."""
        db = Database()
        config = ConfigManager()
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        while not WorkerManager.stop_flag:
            self._update_status_file()
            job = db.fetch_next_pending_job()

            if not job:
                time.sleep(1)
                continue

            job_id = job["id"]
            cmd = job["command"]
            attempts = job["attempts"]
            max_retries = job["max_retries"]
            try:
                job_timeout = int(config.get_value("job_timeout") or 30)
            except Exception:
                job_timeout = 30


            db.update_job_status(job_id, "processing")
            log_path = log_dir / f"{job_id}.log"
            self._write_log_header(log_path, job_id, cmd, job_timeout)

            start_time = time.time()
            result = None

            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    text=True,
                    timeout=job_timeout
                )
                self._write_job_output(log_path, result, start_time)

                if result.stdout:
                    border = "─" * 65
                    typer.secho("\n" + border, fg=typer.colors.BRIGHT_BLACK)
                    typer.secho(f"[ Job Output | ID: {job_id} ]", fg=typer.colors.CYAN, bold=True)
                    typer.secho(border, fg=typer.colors.BRIGHT_BLACK)
                    typer.secho(result.stdout.strip(), fg=typer.colors.GREEN, bold=True)
                    typer.secho(border + "\n", fg=typer.colors.BRIGHT_BLACK)
                
                if result.returncode == 0:
                    db.update_job_status(job_id, "completed")
                    self._console("success", f"Job {job_id} completed successfully.")
                else:
                    raise subprocess.SubprocessError(f"Non-zero exit code: {result.returncode}")

            except subprocess.TimeoutExpired:
                self._console("warning", f"{job_id} timed out after {job_timeout}s.")
                self._append_to_log(log_path, f"TIMEOUT: exceeded {job_timeout}s limit.")
                self._handle_failure(db, job_id, attempts, max_retries)

            except Exception as e:
                self._console("error", f"{job_id} failed: {e}")
                self._append_to_log(log_path, f"ERROR: {e}")
                self._handle_failure(db, job_id, attempts, max_retries)

            if WorkerManager.stop_flag:
                self._console("info", f"{threading.current_thread().name} received stop signal.")
                break

            time.sleep(0.2)

        self._console("info", f"{threading.current_thread().name} stopped gracefully.")
        self._update_status_file()

    # ----------------------------------------------------------------------
    # Retry / Failure Handling
    # ----------------------------------------------------------------------
    def _handle_failure(self, db: Database, job_id: str, attempts: int, max_retries: int):
        """Handle job retry or mark as dead after exceeding max retries."""
        try:
            db.increment_attempts(job_id)
            job = db.get_job(job_id)
            current_attempts = job["attempts"] if job else (attempts + 1)

            if current_attempts >= max_retries:
                db.update_job_status(job_id, "dead")
                self._console("error", f"{job_id} moved to DLQ (max retries exceeded).")
            else:
                delay = self.backoff_base ** current_attempts
                next_run = datetime.now(timezone.utc) + timedelta(seconds=delay)
                with db.con:
                    db.con.execute(
                        "UPDATE jobs SET status='pending', run_at=?, updated_at=? WHERE id=?",
                        (
                            next_run.strftime("%Y-%m-%d %H:%M:%S"),
                            datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                            job_id,
                        ),
                    )
                self._console("info", f"{job_id} will retry in {delay}s (attempt {current_attempts}/{max_retries}).")

        except Exception as e:
            db.update_job_status(job_id, "dead")
            self._console("error", f"Error handling failure for {job_id}: {e}. Marked as dead.")

    # ----------------------------------------------------------------------
    # Logging Helpers
    # ----------------------------------------------------------------------
    def _write_log_header(self, log_path: Path, job_id: str, cmd: str, timeout: int):
        """Write the header section for a job log."""
        header = (
            f"[{datetime.now(timezone.utc).isoformat()}] START JOB {job_id}\n"
            f"COMMAND: {cmd}\nTIMEOUT: {timeout}s\n\n"
        )
        self._append_to_log(log_path, header)

    def _write_job_output(self, log_path: Path, result, start_time: float):
        """Write process output and metadata to the log file."""
        duration = round(time.time() - start_time, 3)
        content = [
            "=== STDOUT ===",
            result.stdout or "(no output)",
            "\n=== STDERR ===",
            result.stderr or "(no errors)",
            f"\nEXIT CODE: {result.returncode}",
            f"DURATION: {duration}s",
            f"[{datetime.now(timezone.utc).isoformat()}] END JOB\n"
        ]
        self._append_to_log(log_path, "\n".join(content))

    def _append_to_log(self, log_path: Path, text: str):
        """Append text to a job's log file."""
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(text.strip() + "\n")
        except Exception:
            pass

    # ----------------------------------------------------------------------
    # Utility / Status
    # ----------------------------------------------------------------------
    @staticmethod
    def _remove_stale_stop_file():
        """Remove old stop file if it exists."""
        try:
            if os.path.exists(WorkerManager.STOP_SIGNAL_FILE):
                os.remove(WorkerManager.STOP_SIGNAL_FILE)
        except Exception:
            pass

    @staticmethod
    def _update_status_file():
        """Write JSON file tracking active worker threads."""
        try:
            active = [t.name for t in threading.enumerate() if t.name.startswith("Worker-")]
            data = {
                "active_workers": len(active),
                "threads": active,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            with open(WorkerManager.STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    @staticmethod
    def setup_signal_handlers():
        """Handle interrupt and termination signals."""
        def handle_signal(signum, frame):
            print("\nReceived termination signal. Stopping workers gracefully...")
            WorkerManager.stop_all()

        try:
            signal.signal(signal.SIGINT, handle_signal)
            if platform.system() != "Windows":
                signal.signal(signal.SIGTERM, handle_signal)
        except Exception:
            pass

    # ----------------------------------------------------------------------
    # Console Output Formatting
    # ----------------------------------------------------------------------
    @staticmethod
    def _console(level: str, message: str):
        """Print structured messages with level-based prefixes."""
        ts = datetime.now().strftime("%H:%M:%S")
        prefixes = {
            "info": "[INFO]",
            "success": "[ OK ]",
            "warning": "[WARN]",
            "error": "[FAIL]"
        }
        print(f"{ts} {prefixes.get(level, '[LOG]')} {message}")
