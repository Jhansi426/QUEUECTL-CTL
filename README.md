# QueueCTL — CLI-Based Background Job Queue System

### Backend Developer Internship Assignment — Python Implementation  
**Author:** Jhansi Paluri

---

Demo video: https://drive.google.com/file/d/1NJSgv-QP6dPqObotwMeiODIwKltt8I9P/view?usp=sharing
 
## Overview

`QueueCTL` is a command-line-based background job queue system built in Python.  
It allows users to enqueue shell command jobs, execute them via worker threads, automatically retry failed jobs with exponential backoff, and persist job data using SQLite.  
Failed jobs that exceed retry limits are moved to a Dead Letter Queue (DLQ) for manual retry.

It includes a minimal Flask-based dashboard for real-time job monitoring and configuration control.

---

## Key Features

- Enqueue shell command jobs via CLI  
- Persistent SQLite storage  
- Multi-worker concurrency  
- Exponential retry with configurable backoff  
- Dead Letter Queue (DLQ) for failed jobs  
- Job scheduling using `run_at` timestamp  
- Job priority ordering  
- Job output logging  
- Graceful worker shutdown  
- Web dashboard with auto-refresh  
- Bash-based automated test suite  

---

## Tech Stack

| Component | Technology |
|------------|-------------|
| Language | Python 3.11+ |
| CLI Framework | Typer |
| Database | SQLite |
| Web Framework | Flask |
| Testing | Bash Shell Scripts |
| Packaging | setuptools |
| Persistence | File-based SQLite database (`store.db`) |

---

## Setup Instructions

### Step 1: Clone the Repository
```bash
git clone https://github.com/<your-username>/queuectl.git
cd queuectl
```

### Step 2: Create and Activate a Virtual Environment

```bash
python -m venv virenv
source virenv/Scripts/activate  
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Install QueueCTL Locally
```bash
pip install -e .
```

## CLI Usage
All functionality is available through the queuectl command.

### View All Commands
```bash 
queuectl --help
```

### View Command Help
```bash
queuectl enqueue --help
queuectl worker-start --help
queuectl dlq-list --help
queuectl config-show --help
```

## Command Reference

| Category       | Example Command                                 | Description                                                                |
| -------------- | ----------------------------------------------- | -------------------------------------------------------------------------- |
| Enqueue Job    | `queuectl enqueue '{"command":"echo Hello"}'`   | Add a new job                                                              |
| Start Workers  | `queuectl worker-start --count 2`               | Start multiple workers                                                     |
| Stop Workers   | `queuectl worker-stop`                          | Gracefully stop all workers                                                |
| Job List       | `queuectl list --status pending`                | List jobs by status                                                        |
| Status         | `queuectl status`                               | Display job state summary and worker threads                               |
| DLQ Management | `queuectl dlq-list` / `queuectl dlq-retry <id>` | View or retry jobs from the DLQ                                            |
| Configuration  | `queuectl config-set max_retries 5`             | Update configuration values                                                |
| Dashboard      | `queuectl dashboard`                            | Launch the web dashboard at your local host |


## Job Lifecycle States

| State      | Description                         |
| ---------- | ----------------------------------- |
| pending    | Waiting to be picked up by a worker |
| processing | Currently being executed            |
| completed  | Successfully executed               |
| failed     | Failed but still retryable          |
| dead       | Permanently failed (moved to DLQ)   |


## Configuration Management
Default configuration is stored in config.json:
```json
{
  "max_retries": 3,
  "backoff_base": 2,
  "worker_count": 1,
  "job_timeout": 30
}
```
### Configuration Commands
```bash
queuectl config-show
queuectl config-set max_retries 5
queuectl config-get job_timeout
queuectl config-reset
```

## Web Dashboard
Launch the dashboard:
```bash
queuectl dashboard
```

### Dashboard features
- Auto-refreshes every 5 seconds
- Displays job counts by state (pending, processing, completed, failed, dead)
- Shows 20 most recent jobs with details
- Displays job priority, attempts, and timestamps

## Testing
A full Bash-based test suite is included to validate all functionality.

### Run All Tests
```bash
chmod +x tests/*.sh
tests/test_all.sh
```

### Run Specific Tests
```bash
tests/test_01_enqueue.sh         # Enqueue validation
tests/test_03_retry_backoff.sh   # Retry & DLQ handling
tests/test_07_persistence.sh     # Persistence verification
tests/test_10_concurrency.sh     # Multi-worker concurrency
```

## Project File Structure


'''queuectl/
├── cli/
│   ├── enqueue.py
│   ├── worker.py
│   ├── list_jobs.py
│   ├── dlq.py
│   ├── config_cli.py
│   └── status_cli.py
│
├── core/
│   ├── storage.py
│   ├── worker_engine.py
│   └── config.py
│
├── web/
│   └── dashboard.py
│
├── tests/
│   ├── test_01_enqueue.sh
│   ├── test_02_worker.sh
│   ├── test_03_retry_backoff.sh
│   ├── test_04_dlq.sh
│   ├── test_06_scheduled.sh
│   ├── test_07_persistence.sh
│   ├── test_08_dashboard.sh
│   ├── test_09_priority.sh
│   ├── test_10_concurrency.sh
│   └── utils.sh
│
├── main.py
├── setup.py
├── requirements.txt
├── config.json
└── README.md'''







