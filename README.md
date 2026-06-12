# Wi-Fi Throughput & Latency Monitor CLI

A Linux-based command-line tool to automate Wi-Fi network testing. It measures latency, packet loss, and throughput using standard Linux networking tools (`ping`, `iperf3`), stores results in SQLite, and generates summaries to help you compare network quality across different setups, locations, and time periods.

***

## Why This Project Exists

Most people check their Wi-Fi quality by eyeballing a speed test or doing a quick ping manually. That works once, but it tells you nothing about:

- How performance changes over time
- How different access points compare
- Whether your connection degrades at certain hours
- What the actual packet loss and jitter look like under load

This tool automates all of that. You run one command, results get logged, and you can query summaries whenever you want. It's a simplified version of what professional network test platforms like LANforge do - just without the enterprise price tag.

***

## Current Status

| Day | Module | Status |
|-----|--------|--------|
| Day 1 | Project structure + CLI skeleton (`argparse`) | ✅ Done |
| Day 2 | Ping test module + parser + unit tests | ✅ Done |
| Day 3 | Throughput test (`iperf3`) | 🔜 Upcoming |
| Day 4 | Shell scripting + scheduler | 🔜 Upcoming |
| Day 5 | SQLite storage layer | 🔜 Upcoming |
| Day 6 | Report + export commands | 🔜 Upcoming |
| Day 7 | Wi-Fi metadata (`nmcli`) | 🔜 Upcoming |
| Day 8 | Full test suite + error handling | 🔜 Upcoming |
| Day 9 | README polish + demo data | 🔜 Upcoming |

***

## What It Can Do Right Now

As of Day 2, the tool can:

- Run a ping test to any host and capture latency metrics
- Parse RTT (min, avg, max, mdev) and packet loss from ping output
- Display a clean, structured summary in the terminal
- Handle edge cases gracefully — unreachable hosts, ICMP-blocked routers, timeouts
- Run all subcommand `--help` pages
- Pass 4 unit tests for the ping parser (no network required)

***

## Project Structure

```
wifi-monitor/
├── wifi_monitor/
│   ├── __init__.py
│   ├── main.py           ← CLI entry point (argparse, subcommands)
│   ├── ping_test.py      ← Ping module: run + parse + format
│   ├── utils.py          ← Shared helpers (command checks, formatting)
│   ├── throughput_test.py  (Day 3)
│   ├── wifi_info.py        (Day 7)
│   ├── storage.py          (Day 5)
│   ├── report.py           (Day 6)
│   └── scheduler.py        (Day 4)
├── tests/
│   └── test_ping_parser.py  ← Unit tests for ping parser
├── data/
│   └── results.db           ← SQLite database (Day 5)
├── config/
│   └── default.json         ← Test profiles (Day 4)
├── scripts/
│   ├── run_suite.sh         ← Shell script to run full suite (Day 4)
│   └── sample_cron.txt      ← Cron schedule example (Day 4)
├── requirements.txt
├── .gitignore
└── README.md
```

***

## Setup

### Requirements

- Ubuntu / Debian Linux (or WSL on Windows)
- Python 3.8+
- `ping` (usually pre-installed)
- `iperf3` — install with: `sudo apt install iperf3`
- `nmcli` — comes with NetworkManager: `sudo apt install network-manager`

### Installation

```bash
# Clone the repo
git clone https://github.com/abhishekkp00/wifi-monitor.git
cd wifi-monitor

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

`requirements.txt` is minimal right now — no third-party packages are required for Day 1 and Day 2. The tool only uses Python standard library modules (`subprocess`, `argparse`, `re`, `sqlite3`, `datetime`).

***

## Usage

### See all available commands

```bash
python -m wifi_monitor.main --help
```

Output:

```
usage: wifi-monitor [-h] [--version] <command> ...

Wi-Fi Throughput & Latency Monitor CLI
--------------------------------------
Automates Wi-Fi network testing using ping, iperf3, nmcli.
Results are stored in SQLite and summarized on demand.

Available Commands:
  ping        Measure latency and packet loss to a target host.
  throughput  Measure network throughput using iperf3.
  wifi-info   Show current Wi-Fi connection details (SSID, interface, IP).
  run-suite   Run all tests (ping + throughput + wifi-info) in one go.
  report      Show summary of stored test results.
  export      Export stored results to CSV or JSON.
```

### Run a ping test

```bash
# Default: 10 packets to 8.8.8.8
python -m wifi_monitor.main ping

# Custom host and count
python -m wifi_monitor.main ping --host 1.1.1.1 --count 5

# Your local gateway
python -m wifi_monitor.main ping --host 192.168.1.1 --count 3
```

**Sample output (successful):**

```
Running ping test → host: 8.8.8.8  count: 5

================================================
  Ping Test — 8.8.8.8
  Time      : 2026-06-12T10:57:19
================================================
  Sent      : 5
  Received  : 5
  Loss      : 0.0%
  RTT min   : 12.3 ms
  RTT avg   : 15.1 ms
  RTT max   : 22.4 ms
  RTT mdev  : 3.2 ms
================================================
```

**Sample output (ICMP blocked — e.g. home router):**

```
Running ping test → host: 192.168.1.1  count: 3

================================================
  Ping Test — 192.168.1.1
  Time      : 2026-06-12T10:57:19
================================================
  Sent      : 3
  Received  : 0
  Loss      : 100.0%
  RTT       : (not available — all packets lost)
================================================
```

> Note: Many home routers block ICMP ping requests by default. 100% packet loss to `192.168.1.1` is expected and correct — the tool handles this gracefully.

### Check version

```bash
python -m wifi_monitor.main --version
# wifi-monitor 1.0.0
```

### Subcommand help

Each command has its own `--help`:

```bash
python -m wifi_monitor.main ping --help
python -m wifi_monitor.main throughput --help
python -m wifi_monitor.main report --help
```

***

## Running the Tests

The unit tests validate the ping parser using realistic sample output. They do **not** require a network connection.

```bash
# Without pytest (plain Python)
python tests/test_ping_parser.py

# With pytest (if installed)
python -m pytest tests/ -v
```

Expected output:

```
Running ping parser unit tests...

  [PASS] test_successful_ping
  [PASS] test_partial_loss
  [PASS] test_full_loss
  [PASS] test_empty_output

All tests passed! ✅
```

### What the tests cover

| Test | Description |
|------|-------------|
| `test_successful_ping` | Parses 0% loss with correct RTT values |
| `test_partial_loss` | Parses 60% loss scenario |
| `test_full_loss` | Handles 100% loss — RTT fields stay `None` |
| `test_empty_output` | Empty string input — no crash, all fields `None` |

***

## How It Works (Technical Overview)

### Ping module (`ping_test.py`)

The tool runs the system `ping` command using Python's `subprocess.run()`:

```python
subprocess.run(["ping", "-c", str(count), host], capture_output=True, text=True, timeout=...)
```

Using a list instead of a shell string is intentional — it avoids shell injection and makes argument handling predictable.

The raw stdout is then parsed with two regex patterns:

**Packet statistics line:**
```
5 packets transmitted, 5 received, 0% packet loss, time 4004ms
```

**RTT summary line:**
```
rtt min/avg/max/mdev = 11.800/12.880/14.200/0.821 ms
```

The parsed fields are returned as a Python dict. The raw output is also preserved in the dict — this matters for debugging and for the storage layer (Day 5), where having the original output lets you re-parse without re-running the test.

### Error handling

The module handles these cases cleanly:

- `ping` command not installed → user-friendly message with install hint
- Host unreachable or all packets lost → loss = 100%, RTT = None
- Subprocess timeout → error message in result dict
- No RTT line in output (all packets lost) → skipped silently

### CLI structure (`main.py`)

The CLI uses Python's `argparse` with subparsers. Each subcommand (`ping`, `throughput`, `report`, etc.) has its own argument set and its own handler function. The handler is registered using `set_defaults(func=...)`, so the entry point just calls `args.func(args)` — no long `if/elif` chains.

***

## Metrics Explained

| Metric | What it means |
|--------|---------------|
| RTT avg | Average round-trip time. Lower is better. High values mean sluggish responses. |
| RTT mdev | Standard deviation of RTT. High mdev = inconsistent/jittery connection. |
| Packet loss % | Percentage of packets that never came back. Even 1–2% is noticeable for real-time apps. |
| RTT max | Worst-case latency observed. Useful for spotting rare but severe spikes. |

***

## Upcoming Features

These are planned for the next few days of development:

- **Day 3** — `iperf3` throughput measurement (TCP and UDP bandwidth in Mbps)
- **Day 4** — Shell script to run a full test suite; cron-based scheduling
- **Day 5** — SQLite storage: every test result saved with timestamp and metadata
- **Day 6** — `report` command: summaries, averages, comparisons across runs
- **Day 7** — Wi-Fi metadata: current SSID, interface, IP via `nmcli`
- **Day 8** — `run-suite` to combine all tests; export to CSV/JSON

***

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3 (standard library only so far) |
| CLI | `argparse` |
| Process execution | `subprocess` |
| Network testing | `ping`, `iperf3` (Day 3), `tcpdump` (Day 8) |
| Wi-Fi info | `nmcli` (Day 7) |
| Storage | SQLite via `sqlite3` (Day 5) |
| Testing | Plain `unittest` assertions / `pytest` compatible |
| OS | Linux (Ubuntu/Debian) or WSL |

***

## Known Limitations (as of Day 2)

- Results are not stored yet — storage layer comes in Day 5.
- Throughput testing requires a running `iperf3` server — covered in Day 3.
- Wi-Fi metadata (SSID, signal strength) not yet collected — covered in Day 7.
- `tcpdump` packet capture for debugging is planned for Day 8.

***
