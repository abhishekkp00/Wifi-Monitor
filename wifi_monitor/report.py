"""
Report module for displaying summaries of test results.
"""

from wifi_monitor.storage import get_results


def print_summary(last_n: int = 10, test_type: str = "all"):
    """
    Print a summary of recent test results.
    
    Args:
        last_n: Number of recent results to display
        test_type: Filter by test type ('ping', 'throughput', or 'all')
    """
    results = get_results(limit=last_n, test_type=test_type)

    if not results:
        print(f"\nNo test results found for test_type='{test_type}'.\n")
        return

    print(f"\n{'═' * 80}")
    print(f"Test Results Summary (showing last {len(results)} results)")
    print(f"{'═' * 80}\n")

    for i, result in enumerate(results, 1):
        timestamp = result.get("timestamp", "N/A")
        test_type_val = result.get("test_type", "unknown").upper()
        status = result.get("status", "UNKNOWN")

        print(f"[{i}] {timestamp} | {test_type_val} | Status: {status}")

        if test_type_val == "PING" or result.get("test_type") == "ping":
            print(f"      Host: {result.get('host', 'N/A')}")
            print(f"      Packets: {result.get('packets_sent', 'N/A')} sent")
            print(f"      Loss: {result.get('packet_loss_pct', 'N/A')}%")
            print(f"      RTT avg: {result.get('rtt_avg_ms', 'N/A')} ms")

        elif test_type_val == "THROUGHPUT" or result.get("test_type") == "throughput":
            print(f"      Server: {result.get('server', 'N/A')}")
            print(f"      Protocol: {result.get('protocol', 'N/A').upper()}")
            print(f"      Throughput: {result.get('throughput_mbps', 'N/A')} Mbps")
            if result.get("jitter_ms") is not None:
                print(f"      Jitter: {result.get('jitter_ms')} ms")
            if result.get("packet_loss_pct") is not None:
                print(f"      Loss: {result.get('packet_loss_pct')}%")

        if status != "SUCCESS":
            print(f"      Error: {result.get('error', 'Unknown error')}")

        print()

    print(f"{'═' * 80}\n")
