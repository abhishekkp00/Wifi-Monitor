# Wi-Fi Monitor — Live Network Dashboard

A clean, premium, real-time Wi-Fi and network quality monitoring application. Built with Python, Flask, and Server-Sent Events (SSE), this tool runs local and internet speed tests, analyzes Wi-Fi environments, and logs everything to a local SQLite database with a professional, dark monochromatic web interface.

---

## Key Features

- **Live Dashboard:** Real-time updates via SSE for RTT, packet loss, download speed, and jitter.
- **Wi-Fi Scanner & Recommendation Engine:** 
  - Scans nearby networks, evaluates signal strength, bands (2.4/5GHz), security, and link rates.
  - Automatically calculates a network score (0–100) and displays a graded list (A+ to F).
  - Highlights a **"Best Pick"** network with direct optimization tips.
- **Direct Connect:** Initiate connections to nearby networks from the dashboard using an integrated password modal (powered by system `nmcli`).
- **Active Diagnostics:** Periodically pings target hosts in the background to build network quality history.
- **Historical Analysis:** Persistent SQLite logging for detailed past performance charts.

---

## Tech Stack

- **Backend:** Python 3, Flask, SQLite3
- **Frontend:** Vanilla HTML5, CSS3 (zinc monochromatic dark theme), JavaScript, Chart.js
- **System Integrations:** `nmcli`, `ping`, `speedtest-cli`, `ip`

---

## Getting Started

### Prerequisites
- Linux (with `NetworkManager` / `nmcli` for Wi-Fi scanning and connections)
- Python 3.8+

### Setup & Installation

1. **Clone & Enter Repo**
   ```bash
   git clone https://github.com/abhishekkp00/wifi-monitor.git
   cd wifi-monitor
   ```

2. **Virtual Environment & Dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start the Dashboard**
   ```bash
   python -m dashboard.app
   ```
   Open `http://localhost:5001` in your browser.

---

## CLI Usage

You can run individual tasks or generate text reports directly from your terminal:

```bash
# Get CLI options
python -m wifi_monitor.main --help

# Run a ping diagnostic
python -m wifi_monitor.main ping --host 8.8.8.8 --count 10

# Print local network information
python -m wifi_monitor.main wifi-info

# Show terminal quality report
python -m wifi_monitor.main report
```

---

## Running Tests

Run the test suite with `pytest`:

```bash
python -m pytest tests/ -v
```
