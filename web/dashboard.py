from flask import Flask, render_template_string
from core.storage import Database
from datetime import datetime

app = Flask(__name__)
db = Database()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>QueueCTL Dashboard</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --bg: #f4f6f8;
            --text: #2c3e50;
            --card-bg: #ffffff;
            --shadow: rgba(0, 0, 0, 0.08);
            --pending: #f39c12;
            --processing: #3498db;
            --completed: #2ecc71;
            --failed: #e74c3c;
            --dead: #8e44ad;
        }

        body {
            font-family: 'Inter', 'Segoe UI', Arial, sans-serif;
            background: var(--bg);
            color: var(--text);
            margin: 0;
            padding: 25px;
        }

        h1 {
            font-size: 1.8rem;
            font-weight: 600;
            color: #1f2937;
            margin-bottom: 10px;
        }

        .top-bar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
        }

        .timestamp {
            font-size: 0.9rem;
            color: #555;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .stat {
            background: var(--card-bg);
            border-top: 4px solid transparent;
            padding: 15px 20px;
            border-radius: 12px;
            box-shadow: 0 2px 6px var(--shadow);
            text-align: center;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat:hover {
            transform: translateY(-3px);
            box-shadow: 0 3px 8px var(--shadow);
        }

        .stat-title {
            text-transform: uppercase;
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 5px;
            letter-spacing: 0.05rem;
        }

        .stat-value {
            font-size: 1.6rem;
            font-weight: 600;
        }

        .pending { border-top-color: var(--pending); }
        .processing { border-top-color: var(--processing); }
        .completed { border-top-color: var(--completed); }
        .failed { border-top-color: var(--failed); }
        .dead { border-top-color: var(--dead); }

        .table-wrapper {
            overflow-x: auto;
            border-radius: 12px;
            box-shadow: 0 2px 6px var(--shadow);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            background: var(--card-bg);
        }

        th, td {
            padding: 12px 14px;
            font-size: 0.9rem;
            border-bottom: 1px solid #eee;
            white-space: nowrap;
        }

        th {
            background: #007bff;
            color: white;
            position: sticky;
            top: 0;
            text-align: left;
            z-index: 1;
        }

        tr:nth-child(even) {
            background: #fafafa;
        }

        tr:hover {
            background: #f1f5f9;
        }

        .status-pill {
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 0.8rem;
            color: white;
        }

        .status-pending { background: var(--pending); }
        .status-processing { background: var(--processing); }
        .status-completed { background: var(--completed); }
        .status-failed { background: var(--failed); }
        .status-dead { background: var(--dead); }

        footer {
            text-align: center;
            margin-top: 25px;
            color: #666;
            font-size: 0.85rem;
        }

        .refresh-btn {
            background: #007bff;
            border: none;
            color: white;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: background 0.2s;
        }

        .refresh-btn:hover {
            background: #005fcc;
        }

        .legend {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            margin-bottom: 20px;
            font-size: 0.85rem;
        }

        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }

        .dot-pending { background: var(--pending); }
        .dot-processing { background: var(--processing); }
        .dot-completed { background: var(--completed); }
        .dot-failed { background: var(--failed); }
        .dot-dead { background: var(--dead); }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(5px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .fade-in {
            animation: fadeIn 0.4s ease;
        }
    </style>
</head>
<body>
    <div class="top-bar">
        <h1>QueueCTL Dashboard</h1>
        <div class="timestamp">
            Last Updated: {{ now }}
            <button class="refresh-btn" onclick="location.reload()">Refresh</button>
        </div>
    </div>

    <div class="stats fade-in">
        {% for state, count in summary.items() %}
        <div class="stat {{ state }}">
            <div class="stat-title">{{ state.capitalize() }}</div>
            <div class="stat-value">{{ count }}</div>
        </div>
        {% endfor %}
    </div>

    <div class="legend">
        <div class="legend-item"><span class="dot dot-pending"></span> Pending</div>
        <div class="legend-item"><span class="dot dot-processing"></span> Processing</div>
        <div class="legend-item"><span class="dot dot-completed"></span> Completed</div>
        <div class="legend-item"><span class="dot dot-failed"></span> Failed</div>
        <div class="legend-item"><span class="dot dot-dead"></span> Dead</div>
    </div>

    <div class="table-wrapper fade-in">
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Command</th>
                    <th>Status</th>
                    <th>Priority</th>
                    <th>Attempts</th>
                    <th>Created</th>
                    <th>Updated</th>
                </tr>
            </thead>
            <tbody>
                {% for job in jobs %}
                <tr>
                    <td>{{ job['id'] }}</td>
                    <td>{{ job['command'] }}</td>
                    <td><span class="status-pill status-{{ job['status'] }}">{{ job['status'].capitalize() }}</span></td>
                    <td>{{ job['priority'] }}</td>
                    <td>{{ job['attempts'] }}</td>
                    <td>{{ job['created_at'] }}</td>
                    <td>{{ job['updated_at'] }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <footer>
        QueueCTL © 2025 — Updated at {{ now }} (UTC)
    </footer>
</body>
</html>
"""

@app.route("/")
def dashboard():
    summary = db.get_job_summary()
    cur = db.con.cursor()
    cur.execute("""
        SELECT * FROM jobs
        ORDER BY datetime(created_at) DESC
        LIMIT 20;
    """)
    jobs = cur.fetchall()
    return render_template_string(HTML_TEMPLATE, summary=summary, jobs=jobs, now=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"))


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
