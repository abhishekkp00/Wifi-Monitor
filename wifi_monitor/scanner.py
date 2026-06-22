"""
wifi_monitor/scanner.py
-----------------------
Scan nearby Wi-Fi networks and calculate channel congestion & recommendations.
Uses nmcli under the hood.
"""
from __future__ import annotations
import re
import subprocess
from wifi_monitor.logger import logger

def scan_nearby_wifi() -> list[dict]:
    """
    Run nmcli to list nearby Wi-Fi access points and parse the results.
    Returns a list of dictionaries with details.
    """
    try:
        proc = subprocess.run(
            ["nmcli", "-t", "-f", "active,ssid,bssid,chan,rate,signal,security", "dev", "wifi"],
            capture_output=True, text=True, timeout=8
        )
        if proc.returncode != 0:
            logger.warning("nmcli dev wifi list returned non-zero code: %d", proc.returncode)
            return []
        
        networks = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # nmcli -t uses ':' as separator, but BSSID contains escaped colons '\:'
            # Replace '\:' with a placeholder to prevent wrong splitting
            line_replaced = line.replace("\\:", "TEMP_COLON")
            parts = line_replaced.split(":")
            if len(parts) < 7:
                continue
            
            active = (parts[0].strip().lower() == "yes")
            ssid = parts[1].strip()
            bssid = parts[2].replace("TEMP_COLON", ":").strip()
            channel_str = parts[3].strip()
            rate = parts[4].strip()
            signal_str = parts[5].strip()
            security = parts[6].strip()
            
            try:
                channel = int(channel_str)
            except ValueError:
                channel = 0
                
            try:
                signal = int(signal_str)
            except ValueError:
                signal = 0
                
            # Classify band (2.4 GHz vs 5 GHz)
            band = "2.4 GHz" if 1 <= channel <= 14 else "5 GHz" if channel >= 32 else "Unknown"
            
            networks.append({
                "active": active,
                "ssid": ssid if ssid else "(Hidden Network)",
                "bssid": bssid,
                "channel": channel,
                "band": band,
                "rate": rate,
                "signal": signal,
                "security": security if security else "Open"
            })
            
        # Sort by signal strength descending
        networks.sort(key=lambda x: x["signal"], reverse=True)
        return networks
        
    except Exception as e:
        logger.error("Error scanning nearby Wi-Fi: %s", e)
        return []

def analyze_channels(networks: list[dict]) -> dict:
    """
    Analyze scanned networks to check channel usage and suggest best channels.
    """
    congestion_24 = {}
    congestion_5 = {}
    
    # Initialize standard channels
    for ch in [1, 6, 11]:
        congestion_24[ch] = 0
    for ch in [36, 40, 44, 48, 149, 153, 157, 161]:
        congestion_5[ch] = 0
        
    for net in networks:
        ch = net["channel"]
        band = net["band"]
        if band == "2.4 GHz":
            congestion_24[ch] = congestion_24.get(ch, 0) + 1
        elif band == "5 GHz":
            congestion_5[ch] = congestion_5.get(ch, 0) + 1
            
    # Find current active connection channel details
    active_net = next((net for net in networks if net["active"]), None)
    active_channel = active_net["channel"] if active_net else None
    active_band = active_net["band"] if active_net else None
    active_ssid = active_net["ssid"] if active_net else None
    
    # Simple recommendation algorithm
    # 2.4 GHz recommendations: look at standard non-overlapping 1, 6, 11
    rec_24 = min([1, 6, 11], key=lambda ch: congestion_24.get(ch, 0))
    # 5 GHz recommendations: look at standard indoor channels
    rec_5 = min([36, 40, 44, 48, 149, 153, 157, 161], key=lambda ch: congestion_5.get(ch, 0))
    
    explanation = []
    if active_net:
        cur_ch = active_net["channel"]
        if active_band == "2.4 GHz":
            others = congestion_24.get(cur_ch, 1) - 1
            if others > 0:
                explanation.append(
                    f"Your current network <strong style='color:var(--teal)'>{active_ssid}</strong> is on 2.4 GHz Channel <strong style='color:var(--yellow)'>{cur_ch}</strong>, which has {others} other interfering network(s) on it."
                )
            else:
                explanation.append(
                    f"Your current network <strong style='color:var(--teal)'>{active_ssid}</strong> is on 2.4 GHz Channel <strong style='color:var(--green)'>{cur_ch}</strong> with no other networks on the same channel."
                )
                
            if rec_24 != cur_ch and congestion_24.get(rec_24, 0) < congestion_24.get(cur_ch, 0):
                explanation.append(
                    f"We recommend switching your router to Channel <strong style='color:var(--green)'>{rec_24}</strong> which has less congestion ({congestion_24[rec_24]} network(s) detected)."
                )
        else: # 5 GHz
            others = congestion_5.get(cur_ch, 1) - 1
            if others > 0:
                explanation.append(
                    f"Your current network <strong style='color:var(--teal)'>{active_ssid}</strong> is on 5 GHz Channel <strong style='color:var(--yellow)'>{cur_ch}</strong>, which has {others} other interfering network(s) on it."
                )
            else:
                explanation.append(
                    f"Your current network <strong style='color:var(--teal)'>{active_ssid}</strong> is on 5 GHz Channel <strong style='color:var(--green)'>{cur_ch}</strong> with no other networks on the same channel."
                )
                
            if rec_5 != cur_ch and congestion_5.get(rec_5, 0) < congestion_5.get(cur_ch, 0):
                explanation.append(
                    f"We recommend switching your router to Channel <strong style='color:var(--green)'>{rec_5}</strong> which has less congestion ({congestion_5[rec_5]} network(s) detected)."
                )
    else:
        explanation.append("No active Wi-Fi connection detected on your system. Showing general channel recommendations.")
        explanation.append(f"For 2.4 GHz, Channel <strong style='color:var(--green)'>{rec_24}</strong> is the least congested ({congestion_24.get(rec_24, 0)} networks).")
        explanation.append(f"For 5 GHz, Channel <strong style='color:var(--green)'>{rec_5}</strong> is the least congested ({congestion_5.get(rec_5, 0)} networks).")
        
    return {
        "congestion_24": congestion_24,
        "congestion_5": congestion_5,
        "active_channel": active_channel,
        "active_band": active_band,
        "recommended_24": rec_24,
        "recommended_5": rec_5,
        "recommendation_summary": " ".join(explanation)
    }
