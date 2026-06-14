# Wi-Fi Monitor — Live Network Dashboard

A premium, real-time Wi-Fi and network quality monitoring application. Built with Python, Flask, and Server-Sent Events (SSE), this tool runs local and internet speed tests, stores the results in a local SQLite database, and visualizes everything on a stunning, dynamic dashboard.

![Dashboard Preview](dashboard_preview.png) *(Note: Add a screenshot of the dashboard here!)*

***

## What It Does

Most speed tests are a one-off. This monitor actively runs in the background and builds a historical profile of your connection quality.

- **Real-time Dashboard:** Built with HTML, CSS (no bloated UI frameworks), and Chart.js, powered by Flask SSE. Updates live without page reloads.
- **Background Ping Tests:** Automatically pings a reliable host (e.g., 8.8.8.8) every 5 minutes to measure Latency (RTT) and Packet Loss.
- **Live Speed Tests:** Run a `speedtest-cli` internet speed test directly from the UI and watch the download/upload numbers spin up in real-time.
- **Wi-Fi Metadata:** Captures your current SSID, Gateway, Interface, and IP Address using Linux network tools (`nmcli` and `ip`).
- **Quality Score:** Calculates a unified 0-100 Quality Score (Excellent, Good, Fair, Poor) based on latency, loss, and throughput.
- **Persistent Storage:** Everything is logged to a local SQLite database, powering historical charts and recent test run tables.

***

## Tech Stack

| Component | Technology |
|---|---|
| **Backend** | Python 3, Flask |
| **Database** | SQLite3 |
| **Real-time Data** | Server-Sent Events (SSE) |
| **Frontend UI** | Vanilla HTML/CSS, JavaScript, Chart.js |
| **Networking Tools** | `ping`, `speedtest-cli`, `iperf3`, `nmcli`, `ip` |

***

## Getting Started

### Prerequisites

This tool relies on standard Linux networking commands. You'll need:
- Linux (Ubuntu/Debian recommended)
- Python 3.8+
- `ping` and `ip` (usually pre-installed)
- `nmcli` (NetworkManager)
- `iperf3` (optional, for local LAN throughput testing)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/abhishekkp00/wifi-monitor.git
   cd wifi-monitor
   ```

2. **Set up a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(This installs Flask, pytest, and speedtest-cli)*

***

## Usage

### 1. Launch the Dashboard
The easiest way to use the monitor is through the web dashboard.

```bash
# Start the Flask app
python -m dashboard.app
```
Then open `http://127.0.0.1:5000` in your web browser.

**What happens when you launch it:**
- The Flask server starts.
- A background daemon thread starts pinging `8.8.8.8` every 5 minutes automatically.
- The UI connects via SSE and updates instantly.

### 2. Run Tests from the CLI
You can also run tests manually from the terminal. Results will still be saved to the database and show up in the dashboard.

```bash
# See all commands
python -m wifi_monitor.main --help

# Run a single ping test (10 packets to 8.8.8.8)
python -m wifi_monitor.main ping --host 8.8.8.8 --count 10

# View current Wi-Fi info
python -m wifi_monitor.main wifi-info

# Show a terminal summary report of stored results
python -m wifi_monitor.main report
```

***

## Project Structure

```text
wifi-monitor/
├── dashboard/               # Flask Web Application
│   ├── app.py               # Flask server, SSE streams, API endpoints
│   └── templates/
│       └── index.html       # The premium UI frontend
├── wifi_monitor/            # Core Python Package
│   ├── main.py              # CLI entry point
│   ├── cli.py               # argparse definitions
│   ├── commands.py          # CLI command handlers
│   ├── config.py            # JSON config loader
│   ├── logger.py            # Standardized logging
│   ├── ping_test.py         # Subprocess logic for ping
│   ├── throughput_test.py   # Subprocess logic for speedtest-cli and iperf3
│   ├── storage.py           # SQLite database interactions
│   ├── report.py            # Summary calculations
│   ├── wifi_info.py         # Network interface & SSID detection
│   └── utils.py             # Shared formatting helpers
├── config/
│   └── default.json         # Settings (intervals, targets, UI limits)
├── data/
│   └── results.db           # SQLite DB (created automatically)
├── tests/                   # Pytest suite (54 passing tests)
├── requirements.txt         # pip dependencies
└── README.md                # You are here
```

***

## How the Live Speed Test Works

When you click **"Speed Test"** in the UI:
1. The frontend opens a sleek modal and connects to `/api/run/speedtest/stream`.
2. Flask spawns `speedtest-cli` in a subprocess.
3. Flask reads the subprocess stdout line-by-line in real-time.
4. Flask parses the lines, formats them into JSON events, and yields them over the SSE stream.
5. The frontend JavaScript interprets these events, updating the live progress bar, logging console output, and animating the big Download/Upload counters.
6. Upon completion, the result is saved to SQLite, and the main dashboard charts update automatically.

***

## Troubleshooting

- **Speed test fails with `TOOL_NOT_FOUND`:** Ensure you installed dependencies in the active virtual environment (`pip install -r requirements.txt`). The app specifically looks for `speedtest-cli` in the same `bin` directory as the running Python executable.
- **Wi-Fi SSID shows "Not available":** The app tries to use `nmcli dev wifi` and `nmcli connection show --active`. If your system doesn't use NetworkManager, this feature won't work, but the rest of the dashboard will continue to function normally.
- **Pings randomly show FAILED or 100% loss:** This is completely normal! It means the app caught a temporary network drop or latency spike. That's exactly what this tool is built to detect.

***

## Development & Testing

Run the full test suite (54 unit and integration tests) using `pytest`:

```bash
python -m pytest tests/ -v
```
