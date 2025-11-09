import typer
import os
import json
from core.storage import Database


app = typer.Typer(help="Show system and worker status for QueueCTL")


@app.command()
def status():
    """Display overall job and worker status."""
    db = Database()
    summary = db.get_job_summary()

    print("\nQueue Status Overview")
    print("-" * 50)

    states = ["pending", "processing", "completed", "failed", "dead"]
    for state in states:
        count = summary.get(state, 0)
        print(f"{state.capitalize():<12}: {count}")

    print("\nWorker Thread Status")
    print("-" * 50)

    status_file = "worker_threads.json"
    stop_file = "stop_signal.json"

    # ----------------------------------------------------------------------
    # Worker Info
    # ----------------------------------------------------------------------
    try:
        if os.path.exists(status_file):
            with open(status_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            active = data.get("active_workers", 0)
            threads = data.get("threads", [])
            timestamp = data.get("timestamp", "N/A")

            print(f"Active Workers : {active}")
            print(f"Worker Names   : {', '.join(threads) if threads else '(none)'}")
            print(f"Last Updated   : {timestamp}")
        else:
            print("Active Workers : 0 (no active threads)")
    except Exception as e:
        print(f"Warning: Could not read worker status ({e})")

    # ----------------------------------------------------------------------
    # Stop Signal Info
    # ----------------------------------------------------------------------
    try:
        if os.path.exists(stop_file):
            with open(stop_file, "r", encoding="utf-8") as f:
                stop_data = json.load(f)
            ts = stop_data.get("timestamp", "Unknown")
            print(f"\nStop Signal Detected : {ts}")
    except Exception as e:
        print(f"Warning: Could not read stop signal ({e})")

    print("-" * 50)
