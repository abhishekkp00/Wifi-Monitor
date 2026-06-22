"""Unit tests for scanner.py."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from wifi_monitor.scanner import analyze_channels

def test_analyze_channels_basic():
    """Test channel congestion analyzer with mock data."""
    networks = [
        {"active": True, "ssid": "MyWiFi", "bssid": "11:22:33:44:55:66", "channel": 6, "band": "2.4 GHz", "rate": "130 Mbit/s", "signal": 90, "security": "WPA2"},
        {"active": False, "ssid": "Neighbor1", "bssid": "22:33:44:55:66:77", "channel": 6, "band": "2.4 GHz", "rate": "130 Mbit/s", "signal": 60, "security": "WPA2"},
        {"active": False, "ssid": "Neighbor2", "bssid": "33:44:55:66:77:88", "channel": 1, "band": "2.4 GHz", "rate": "130 Mbit/s", "signal": 40, "security": "WPA2"},
    ]
    
    result = analyze_channels(networks)
    
    assert result["active_channel"] == 6
    assert result["active_band"] == "2.4 GHz"
    # Channel 11 has 0 APs, so it should be the recommended one
    assert result["recommended_24"] == 11
    assert "MyWiFi" in result["recommendation_summary"]
    assert "11" in result["recommendation_summary"]

def test_analyze_channels_no_active():
    """Test channel analyzer when there is no active network."""
    networks = [
        {"active": False, "ssid": "GuestWiFi", "bssid": "11:22:33:44:55:66", "channel": 36, "band": "5 GHz", "rate": "270 Mbit/s", "signal": 80, "security": "Open"},
    ]
    
    result = analyze_channels(networks)
    
    assert result["active_channel"] is None
    assert result["active_band"] is None
    # 36 has 1 network, others in 5 GHz list have 0 networks, so recommended_5 should be one of the 0 ones, e.g. 40
    assert result["recommended_5"] != 36
    assert "No active Wi-Fi connection detected" in result["recommendation_summary"]
