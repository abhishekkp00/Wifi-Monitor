"""
dashboard/app.py
----------------
Flask dashboard with:
  - SSE /api/stream  — pushes summary+chart updates every 10 s
  - POST /api/run/ping        — trigger ping test immediately
  - POST /api/run/speedtest   — trigger speed test immediately
  - GET  /api/status          — latest test status & quality score
"""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from datetime import datetime, timezone

from flask import Flask, Response, jsonify, render_template, request

from wifi_monitor.config   import get_cfg
from wifi_monitor.ping_test import run_ping
from wifi_monitor.report   import ping_summary, throughput_summary
from wifi_monitor.storage  import fetch_recent, fetch_chart_data, count_runs, save_result, init_db
from wifi_monitor.throughput_test import run_speedtest, _SPEEDTEST_BIN
from wifi_monitor.wifi_info import get_wifi_info

# ── shared state for live test status ─────────────────────────────────────────
_lock   = threading.Lock()
_status = {"running": None, "last_ping": None, "last_speed": None}


def _set_status(**kw):
    with _lock:
        _status.update(kw)


def _quality_score(ping: dict, tp: dict) -> dict:
    score = 100
    reasons = []
    loss = ping.get("avg_loss_pct")
    rtt  = ping.get("avg_rtt_ms")
    mbps = tp.get("avg_mbps")

    if loss is not None:
        if loss >= 10:  score -= 40; reasons.append("high packet loss")
        elif loss >= 5: score -= 20; reasons.append("elevated packet loss")
        elif loss >= 2: score -= 10; reasons.append("some packet loss")

    if rtt is not None:
        if rtt >= 200:  score -= 30; reasons.append("very high latency")
        elif rtt >= 100: score -= 15; reasons.append("high latency")
        elif rtt >= 50:  score -= 5;  reasons.append("moderate latency")

    if mbps is not None:
        if mbps < 5:   score -= 20; reasons.append("very slow connection")
        elif mbps < 10: score -= 10; reasons.append("slow connection")

    score = max(0, min(100, score))
    grade = "EXCELLENT" if score >= 90 else "GOOD" if score >= 70 else "FAIR" if score >= 50 else "POOR"
    return {"score": score, "grade": grade, "reasons": reasons}


def _format_label(ts: str) -> str:
    if not ts or "T" not in ts:
        return ts[-8:] if ts else ""
    time_part = ts.split("T")[1]
    return time_part.split(".")[0][:8] if "." in time_part else time_part.split("+")[0][:8]


def _enrich_with_wifi(r: dict) -> dict:
    try:
        wi = get_wifi_info()
        if wi.get("available"):
            r.update({
                "ssid": wi.get("ssid"),
                "interface": wi.get("interface"),
                "ip_address": wi.get("ip_address"),
                "signal_strength": wi.get("signal_strength"),
            })
    except Exception:
        pass
    return r


def _build_summary_payload():
    limit_tbl   = get_cfg("dashboard", "table_limit", 20)
    limit_chart = get_cfg("dashboard", "chart_limit", 50)

    ps  = ping_summary(limit=limit_tbl)
    ts  = throughput_summary(limit=limit_tbl)
    cnt = count_runs()
    wi  = get_wifi_info()
    qs  = _quality_score(ps, ts)

    pc = fetch_chart_data(limit=limit_chart, test_type="ping")
    tc = fetch_chart_data(limit=limit_chart, test_type="throughput")

    recent = fetch_recent(limit=limit_tbl)

    return {
        "summary": {
            "ping":       ps,
            "throughput": ts,
            "counts":     cnt,
            "wifi":       wi,
            "quality":    qs,
        },
        "chart_ping": {
            "labels":      [_format_label(str(r.get("timestamp", ""))) for r in pc],
            "rtt_avg":     [r.get("rtt_avg_ms")      for r in pc],
            "packet_loss": [r.get("packet_loss_pct") for r in pc],
            "signal_strength": [r.get("signal_strength") for r in pc],
        },
        "chart_throughput": {
            "labels":     [_format_label(str(r.get("timestamp", ""))) for r in tc],
            "throughput": [r.get("throughput_mbps") for r in tc],
            "jitter":     [r.get("jitter_ms")       for r in tc],
        },
        "recent": [dict(r) for r in recent],
        "ts": datetime.now(timezone.utc).isoformat(),
    }


# ── background test runner ────────────────────────────────────────────────────

def _run_ping_bg(host: str, count: int):
    _set_status(running="ping")
    try:
        r = run_ping(host=host, count=count)
        _enrich_with_wifi(r)
        save_result(r)
        _set_status(last_ping=r)
    finally:
        _set_status(running=None)


def _run_speedtest_bg():
    _set_status(running="speedtest")
    try:
        r = run_speedtest()
        _enrich_with_wifi(r)
        save_result(r)
        _set_status(last_speed=r)
    finally:
        _set_status(running=None)



# ── Flask app factory ─────────────────────────────────────────────────────────

def create_app(auto_run: bool = False) -> Flask:
    app = Flask(__name__, template_folder="templates")
    init_db()

    # -- auto background runner ------------------------------------------------
    if auto_run:
        interval = get_cfg("scheduler", "interval_seconds", 300)  # default 5 min
        ping_host = get_cfg("scheduler", "ping_host", "8.8.8.8")
        ping_count = get_cfg("ping", "default_count", 10)

        def _scheduler():
            time.sleep(3)  # let Flask start first
            while True:
                _run_ping_bg(ping_host, ping_count)
                time.sleep(interval)

        t = threading.Thread(target=_scheduler, name="auto-runner", daemon=True)
        t.start()

    # ── routes ─────────────────────────────────────────────────────────────────

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/api/summary")
    def api_summary():
        limit = get_cfg("dashboard", "table_limit", 20)
        ps  = ping_summary(limit=limit)
        ts  = throughput_summary(limit=limit)
        cnt = count_runs()
        wi  = get_wifi_info()
        qs  = _quality_score(ps, ts)
        return jsonify({"ping": ps, "throughput": ts, "counts": cnt, "wifi": wi, "quality": qs})

    @app.route("/api/chart/ping")
    def api_chart_ping():
        limit = get_cfg("dashboard", "chart_limit", 50)
        rows  = fetch_chart_data(limit=limit, test_type="ping")
        return jsonify({
            "labels":      [_format_label(str(r.get("timestamp", ""))) for r in rows],
            "rtt_avg":     [r.get("rtt_avg_ms")      for r in rows],
            "packet_loss": [r.get("packet_loss_pct") for r in rows],
        })

    @app.route("/api/chart/throughput")
    def api_chart_throughput():
        limit = get_cfg("dashboard", "chart_limit", 50)
        rows  = fetch_chart_data(limit=limit, test_type="throughput")
        return jsonify({
            "labels":     [_format_label(str(r.get("timestamp", ""))) for r in rows],
            "throughput": [r.get("throughput_mbps") for r in rows],
            "jitter":     [r.get("jitter_ms")       for r in rows],
        })

    @app.route("/api/recent")
    def api_recent():
        limit = get_cfg("dashboard", "table_limit", 20)
        return jsonify(fetch_recent(limit=limit))

    @app.route("/api/status")
    def api_status():
        with _lock:
            return jsonify(dict(_status))

    @app.route("/api/wifi/scan")
    def api_wifi_scan():
        from wifi_monitor.scanner import scan_nearby_wifi, analyze_channels
        networks = scan_nearby_wifi()
        analysis = analyze_channels(networks)
        return jsonify({
            "networks": networks,
            "analysis": analysis
        })

    @app.route("/api/wifi/connect", methods=["POST"])
    def api_wifi_connect():
        """Connect to a Wi-Fi network via nmcli."""
        body = request.get_json(silent=True) or {}
        ssid = body.get("ssid", "").strip()
        password = body.get("password", "").strip()

        if not ssid:
            return jsonify({"success": False, "error": "SSID is required"}), 400

        try:
            cmd = ["nmcli", "device", "wifi", "connect", ssid]
            if password:
                cmd += ["password", password]

            proc = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=20
            )

            if proc.returncode == 0:
                output = proc.stdout.strip()
                return jsonify({"success": True, "message": output or f"Connected to {ssid}"})
            else:
                err = proc.stderr.strip() or proc.stdout.strip()
                return jsonify({"success": False, "error": err or "Connection failed"}), 500

        except subprocess.TimeoutExpired:
            return jsonify({"success": False, "error": "Connection timed out after 20 seconds"}), 504
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500


    # ── on-demand test triggers ────────────────────────────────────────────────

    @app.route("/api/run/ping", methods=["POST"])
    def api_run_ping():
        with _lock:
            if _status["running"]:
                return jsonify({"error": f"Test already running: {_status['running']}"}), 409
        body  = request.get_json(silent=True) or {}
        host  = body.get("host",  get_cfg("ping", "default_host",  "8.8.8.8"))
        count = body.get("count", get_cfg("ping", "default_count", 10))
        threading.Thread(target=_run_ping_bg, args=(host, count), daemon=True).start()
        return jsonify({"status": "started", "host": host, "count": count})

    @app.route("/api/run/speedtest", methods=["POST"])
    def api_run_speedtest():
        with _lock:
            if _status["running"]:
                return jsonify({"error": f"Test already running: {_status['running']}"}), 409
        threading.Thread(target=_run_speedtest_bg, daemon=True).start()
        return jsonify({"status": "started"})

    # ── SSE real-time stream ───────────────────────────────────────────────────

    @app.route("/api/stream")
    def api_stream():
        def generate():
            while True:
                try:
                    payload = _build_summary_payload()
                    with _lock:
                        payload["running"] = _status["running"]
                    yield f"data: {json.dumps(payload, default=str)}\n\n"
                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"
                time.sleep(10)

        return Response(
            generate(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ── Live streaming speed test (SSE) ──────────────────────────────────────

    @app.route("/api/run/speedtest/stream")
    def api_speedtest_stream():
        with _lock:
            if _status["running"]:
                def _busy():
                    yield f"data: {json.dumps({'type':'error','message':f'Test already running: {_status["running"]}'})}\n\n"
                return Response(_busy(), mimetype="text/event-stream",
                                headers={"Cache-Control":"no-cache"})

        def generate():
            _set_status(running="speedtest")
            result = None
            try:
                proc = subprocess.Popen(
                    [_SPEEDTEST_BIN, "--no-pre-allocate"],
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True
                )
                dl_mbps = ul_mbps = server = ping_ms = None

                for raw in iter(proc.stdout.readline, ""):
                    line = raw.rstrip()
                    if not line:
                        continue
                    yield f"data: {json.dumps({'type':'log','text':line})}\n\n"

                    if "Hosted by" in line:
                        m = re.search(r"Hosted by (.+?)\s*\[", line)
                        if m: server = m.group(1).strip()
                        m2 = re.search(r"\]:\s*([\d.]+)\s*ms", line)
                        if m2: ping_ms = round(float(m2.group(1)), 2)
                        yield f"data: {json.dumps({'type':'server','server':server,'ping':ping_ms})}\n\n"

                    elif "Testing download" in line:
                        yield f"data: {json.dumps({'type':'stage','stage':'download'})}\n\n"

                    elif "Testing upload" in line:
                        yield f"data: {json.dumps({'type':'stage','stage':'upload'})}\n\n"

                    elif line.startswith("Download:"):
                        m = re.search(r"Download:\s*([\d.]+)", line)
                        if m: dl_mbps = round(float(m.group(1)), 2)
                        yield f"data: {json.dumps({'type':'download','mbps':dl_mbps})}\n\n"

                    elif line.startswith("Upload:"):
                        m = re.search(r"Upload:\s*([\d.]+)", line)
                        if m: ul_mbps = round(float(m.group(1)), 2)
                        yield f"data: {json.dumps({'type':'upload','mbps':ul_mbps})}\n\n"

                proc.wait()

                result = {
                    "test_type": "throughput", "protocol": "TCP",
                    "status": "SUCCESS" if dl_mbps else "FAILED",
                    "throughput_mbps": dl_mbps, "upload_mbps": ul_mbps,
                    "rtt_avg_ms": ping_ms, "server": server,
                    "notes": f"upload={ul_mbps} Mbps" if ul_mbps else None,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "host": None, "interface": None, "ssid": None,
                    "ip_address": None, "local_ip": None, "remote_ip": None,
                    "duration_seconds": None, "bandwidth_target": None,
                    "bandwidth": None, "packets_sent": None,
                    "packets_received": None, "packet_loss_pct": None,
                    "rtt_min_ms": None, "rtt_max_ms": None, "rtt_mdev_ms": None,
                    "jitter_ms": None, "iperf_version": None, "raw_output": None,
                    "error": None, "error_message": None,
                }
                if dl_mbps:
                    _enrich_with_wifi(result)
                    save_result(result)
                    _set_status(last_speed=result)

                yield f"data: {json.dumps({'type':'done','dl':dl_mbps,'ul':ul_mbps,'server':server,'ping':ping_ms})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type':'error','message':str(e)})}\n\n"
            finally:
                _set_status(running=None)

        return Response(generate(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return app


if __name__ == "__main__":
    app = create_app(auto_run=True)
    app.run(
        host=get_cfg("dashboard", "host",  "127.0.0.1"),
        port=get_cfg("dashboard", "port",  5001),
        debug=get_cfg("dashboard", "debug", False),
        use_reloader=False,   # reloader conflicts with background threads
        threaded=True,
    )