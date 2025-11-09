import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "store.db"


class Database:
    """
    SQLite-backed job store for QueueCTL.
    Provides atomic operations for enqueueing, updating, and fetching jobs.
    """

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.con = sqlite3.connect(self.db_path, check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self._create_tables()

    # ----------------------------------------------------------------------
    #  Table Initialization
    # ----------------------------------------------------------------------
    def _create_tables(self):
        """Create the 'jobs' table if it does not already exist."""
        with self.con:
            self.con.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    priority INTEGER DEFAULT 0,
                    run_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
            """)

    # ----------------------------------------------------------------------
    #  Job Creation
    # ----------------------------------------------------------------------
    def add_job(self, job_id, command, max_retries, priority=0, run_at=None):
        """
        Insert a new job into the database.
        All timestamps are stored in UTC ('YYYY-MM-DD HH:MM:SS' format).
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        run_at = self._validate_run_at(run_at) or now

        with self.con:
            self.con.execute("""
                INSERT INTO jobs (
                    id, command, status, attempts, max_retries,
                    priority, run_at, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (job_id, command, "pending", 0, max_retries, priority, run_at, now, now))

    # ----------------------------------------------------------------------
    #  Job Retrieval
    # ----------------------------------------------------------------------
    def pending_jobs(self):
        """Return the first pending job (oldest first)."""
        cur = self.con.cursor()
        cur.execute("""
            SELECT * FROM jobs
            WHERE status = 'pending'
            ORDER BY created_at ASC
            LIMIT 1;
        """)
        return cur.fetchone()

    def get_job(self, job_id):
        """Return a job by ID."""
        cur = self.con.cursor()
        cur.execute("SELECT * FROM jobs WHERE id = ?;", (job_id,))
        return cur.fetchone()

    def list_job_bystatus(self, status):
        """List jobs by their current status."""
        cur = self.con.cursor()
        if status.lower() == "all":
            cur.execute("SELECT * FROM jobs ORDER BY datetime(created_at) DESC;")
        else:
            cur.execute("SELECT * FROM jobs WHERE status = ? ORDER BY datetime(created_at) DESC;", (status,))
        return cur.fetchall()

    # ----------------------------------------------------------------------
    #  Job Updates
    # ----------------------------------------------------------------------
    def update_job_status(self, job_id, status):
        """Update a job's status."""
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        with self.con:
            self.con.execute("""
                UPDATE jobs
                SET status = ?, updated_at = ?
                WHERE id = ?;
            """, (status, now, job_id))

    def increment_attempts(self, job_id):
        """Increment retry count for a job."""
        with self.con:
            self.con.execute("UPDATE jobs SET attempts = attempts + 1 WHERE id = ?;", (job_id,))

    def reset_processing_jobs(self):
        """Revert 'processing' jobs to 'pending' (used after restart)."""
        with self.con:
            self.con.execute("""
                UPDATE jobs
                SET status = 'pending', updated_at = CURRENT_TIMESTAMP
                WHERE status = 'processing';
            """)

    # ----------------------------------------------------------------------
    #  Job Fetching (For Workers)
    # ----------------------------------------------------------------------
    def fetch_next_pending_job(self):
        """
        Select and lock the next job ready to run.
        Chooses highest priority first, then earliest 'run_at'.
        """
        with self.con:
            cursor = self.con.execute("""
                UPDATE jobs
                SET status = 'processing', updated_at = ?
                WHERE id = (
                    SELECT id
                    FROM jobs
                    WHERE status = 'pending'
                    AND datetime(run_at) <= datetime('now', 'utc')
                    ORDER BY priority DESC, datetime(run_at) ASC, created_at ASC
                    LIMIT 1
                )
                RETURNING *;
            """, (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),))
            return cursor.fetchone()

    # ----------------------------------------------------------------------
    #  Job Summary
    # ----------------------------------------------------------------------
    def get_job_summary(self):
        """Return a count of jobs grouped by their status."""
        cur = self.con.cursor()
        cur.execute("SELECT status, COUNT(*) AS count FROM jobs GROUP BY status;")
        rows = cur.fetchall()
        return {row["status"]: row["count"] for row in rows}

    # ----------------------------------------------------------------------
    #  Helper Methods
    # ----------------------------------------------------------------------
    @staticmethod
    def _validate_run_at(run_at):
        """Validate and normalize run_at to UTC timestamp."""
        if not run_at:
            return None
        try:
            dt = datetime.fromisoformat(run_at.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.astimezone()
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return None
