# QueueCTL — System Architecture Overview

### Backend Developer Internship Project  
**Author:** Abhinav Karri | Electronics & Communication Engineering (ECE) × CS — Amrita University  
**Project:** CLI-Based Background Job Queue System  

---

## 1. Introduction

The `QueueCTL` system is a **CLI-based background job queue manager** that executes shell commands as asynchronous jobs.  
It supports multiple worker threads, exponential retry backoff, persistence using SQLite, and real-time monitoring via a Flask-based dashboard.

This document explains the **software architecture**, **module responsibilities**, and **data flow** between core components.

---

## 2. High-Level Architecture

                    ┌────────────────────────┐
                    │       User CLI         │
                    │ (queuectl command)     │
                    └───────────┬────────────┘
                                │
                ┌───────────────┼────────────────┐
                │                                │
      ┌─────────▼──────────┐          ┌──────────▼──────────┐
      │   CLI Commands     │          │   Web Dashboard     │
      │ (Typer Interface)  │          │   (Flask App)       │
      └─────────┬──────────┘          └──────────┬──────────┘
                │                                │
     ┌──────────▼──────────┐         ┌───────────▼───────────┐
     │  Worker Manager     │         │   Database (SQLite)   │
     │ (Thread-based pool) │         │  Persistent Job Store │
     └──────────┬──────────┘         └───────────┬───────────┘
                │                                │
                └────────────────────────────────┘
                      

---

## 3. Core Components

### 3.1 CLI Layer (`cli/`)
Implements all user-facing commands using **Typer**, a modern CLI framework for Python.

| Module | Responsibility |
|---------|----------------|
| `enqueue.py` | Adds new jobs to the queue with optional scheduling, retries, and priorities |
| `worker.py` | Starts/stops background worker threads |
| `list_jobs.py` | Displays jobs filtered by status |
| `dlq.py` | Manages the Dead Letter Queue — retry or purge failed jobs |
| `config_cli.py` | Provides configuration management commands |
| `status_cli.py` | Displays overall system and worker status |

---

### 3.2 Core Logic Layer (`core/`)

| Module | Responsibility |
|---------|----------------|
| **`worker_engine.py`** | Contains the `WorkerManager` class, responsible for worker lifecycle, concurrency control, and retry logic |
| **`storage.py`** | Manages persistent job data using SQLite |
| **`config.py`** | Loads and maintains user configuration (`config.json`) for runtime parameters |

---

### 3.3 Web Layer (`web/dashboard.py`)
A lightweight **Flask** web interface providing:
- Job summaries (pending, processing, completed, failed, dead)
- Last 20 recent jobs
- Auto-refresh every 5 seconds
- Quick overview of system health

---

## 4. Data Flow

### 4.1 Job Lifecycle

1. **Enqueue**
   - User runs `queuectl enqueue '{"command": "echo hello"}'`
   - The job is validated, assigned an ID, and stored in SQLite with status = `pending`.

2. **Worker Start**
   - `queuectl worker-start --count 3` spawns worker threads.
   - Each worker polls the database for `pending` jobs.

3. **Processing**
   - The worker locks and updates job status to `processing`.
   - Executes the command using Python’s `subprocess.run()`.

4. **Completion or Failure**
   - On success → job marked `completed`.
   - On failure → job retried using exponential backoff.

5. **Dead Letter Queue (DLQ)**
   - After exceeding `max_retries`, the job status changes to `dead`.
   - These jobs can be retried manually via `queuectl dlq-retry <id>`.

---

## 5. Data Model

### SQLite Schema

| Field | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Unique Job ID (UUID) |
| `command` | TEXT | Command to execute |
| `status` | TEXT | Job status (`pending`, `processing`, `completed`, `failed`, `dead`) |
| `priority` | INTEGER | Higher number = higher priority |
| `attempts` | INTEGER | Number of retries attempted |
| `max_retries` | INTEGER | Maximum allowed retries |
| `run_at` | TEXT | Scheduled execution time |
| `created_at` | TEXT | Job creation timestamp |
| `updated_at` | TEXT | Last update timestamp |

---

## 6. Worker Execution Model

### Threaded Worker Engine

- Workers run as independent **threads** within a single process.
- Each worker:
  1. Fetches one pending job at a time (atomic lock).
  2. Executes the command using `subprocess.run()`.
  3. Writes job logs to `logs/<job_id>.log`.
  4. Updates job state in the database.
  5. Handles failures with exponential retry:
     ```
     delay = backoff_base ^ attempts
     ```
  6. Moves job to DLQ after max retries.

---

## 7. Concurrency and Safety

- Uses **threading** for concurrency.
- SQLite handles concurrency with **transactional isolation**.
- Workers check for a `stop_signal.json` file for graceful shutdown.
- Status of workers is tracked via `worker_threads.json`.

---

## 8. Configuration Layer

All runtime configurations are persisted in `config.json`.

Example:
```json
{
  "max_retries": 3,
  "backoff_base": 2,
  "worker_count": 1,
  "job_timeout": 30
}
```

| Parameter      | Purpose                              |
| -------------- | ------------------------------------ |
| `max_retries`  | Number of times to retry failed jobs |
| `backoff_base` | Exponential delay base               |
| `worker_count` | Default number of worker threads     |
| `job_timeout`  | Max runtime before timeout           |


## 9. Web Dashboard

Developed using Flask and auto-refreshes every 5 seconds.
Displays:
- Job counts by status
- 20 most recent jobs
- Priority, attempts, created/updated times
- Uses Bootstrap-like CSS for visual clarity.


## 10. Error Handling and Logging

Each job has a dedicated log file in logs/ directory.

System messages use standardized prefixes:
- [INFO] for normal operation
- [OK] for success
- [WARN] for warnings
- [FAIL] for critical errors

Typer’s styled output enhances readability.

## 11. Persistence and Recovery

Job data is stored in store.db (SQLite).

On system restart:

- Jobs marked as processing are reset to pending.
- Unfinished jobs are picked up automatically by the next worker start.
- Ensures no data loss or duplication across restarts.

## Summary

- QueueCTL follows a modular design, separating CLI, core, and web layers.
- Workers are managed through threads, enabling parallel job execution.
- SQLite provides reliable persistence and recovery.
- The dashboard enables quick insights into system performance.
- The solution adheres to production-grade standards in robustness and maintainability.