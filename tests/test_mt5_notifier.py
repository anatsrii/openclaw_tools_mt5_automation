#!/usr/bin/env python3
"""
Test script for MT5 Notifier Tool

Test all notification operations.
"""

import sys
import json
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.notify import (
    MT5Notifier,
    Severity,
    send,
    send_trade_alert,
    send_daily_report,
    send_error,
    send_bot_status,
    test_connection,
    get_enabled_channels
)


def print_result(title: str, result: dict):
    """Pretty print result."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

    for key, val in result.items():
        if isinstance(val, (dict, list)) and val:
            print(f"  {key}:")
            if isinstance(val, dict):
                for k, v in val.items():
                    print(f"    {k}: {v}")
            else:
                for item in val:
                    print(f"    - {item}")
        elif val and not isinstance(val, (dict, list)):
            print(f"  {key}: {val}")


def test_basic_send():
    """Test basic message sending."""
    print("\n[TEST 1] Basic Send")

    # Test different severity levels
    severities = ["debug", "info", "warning", "critical"]

    for severity in severities:
        result = send(
            f"Test message - {severity}",
            severity=severity,
            async_send=False
        )
        print(f"  {severity}: {result['status']}")

    return result


def test_trade_alert():
    """Test trade notifications."""
    print("\n[TEST 2] Trade Alerts")

    # Buy alert
    result1 = send_trade_alert(
        action="BUY",
        symbol="EURUSD",
        volume=0.1,
        entry_price=1.0850,
        comment="Daily breakout",
        async_send=False
    )
    print(f"  Buy: {result1['status']}")

    # Sell alert with profit
    result2 = send_trade_alert(
        action="CLOSE",
        symbol="EURUSD",
        profit=+150.50,
        async_send=False
    )
    print(f"  Close (Profit): {result2['status']}")

    # Sell with loss
    result3 = send_trade_alert(
        action="CLOSE",
        symbol="GBPUSD",
        profit=-80.25,
        async_send=False
    )
    print(f"  Close (Loss): {result3['status']}")

    return result3


def test_daily_report():
    """Test daily report."""
    print("\n[TEST 3] Daily Report")

    result = send_daily_report(
        total_profit=150.50,
        trade_count=5,
        wins=3,
        losses=2,
        max_drawdown=2.5,
        async_send=False
    )

    print(f"  Status: {result['status']}")
    print_result("Daily Report Result", result)

    return result


def test_error_notification():
    """Test error notifications."""
    print("\n[TEST 4] Error Notifications")

    result = send_error(
        source="compile",
        error_message="Function 'MyFunction' not defined",
        ea_name="TestEA",
        async_send=False
    )

    print(f"  Error: {result['status']}")
    print_result("Error Result", result)

    return result


def test_bot_status():
    """Test bot status notifications."""
    print("\n[TEST 5] Bot Status")

    statuses = ["started", "stopped", "crashed"]

    for status in statuses:
        result = send_bot_status(
            status=status,
            ea_name="MyRobot",
            details=f"Test {status} notification",
            async_send=False
        )
        print(f"  {status}: {result['status']}")

    return result


def test_severity_filter():
    """Test severity filtering."""
    print("\n[TEST 6] Severity Filtering")

    # Create notifier with warning minimum
    notifier = MT5Notifier()
    notifier.set_min_severity("warning")

    result = send(
        "This is debug (should be skipped)",
        severity="debug",
        async_send=False
    )
    print(f"  Debug (min=warning): {result['status']}")

    result = send(
        "This is warning (should be sent)",
        severity="warning",
        async_send=False
    )
    print(f"  Warning (min=warning): {result['status']}")

    return result


def test_specific_channel():
    """Test sending to specific channel."""
    print("\n[TEST 7] Specific Channel")

    channels = get_enabled_channels()
    print(f"  Enabled channels: {channels}")

    if channels:
        result = send(
            "Testing specific channel",
            channel=channels[0],
            async_send=False
        )
        print(f"  Send to {channels[0]}: {result['status']}")
    else:
        print("  No channels enabled in config")

    return result


def test_async_sending():
    """Test async message queuing."""
    print("\n[TEST 8] Async Queuing")

    # Send multiple messages asynchronously
    results = []
    for i in range(3):
        result = send(
            f"Async message {i+1}",
            async_send=True
        )
        results.append(result)
        print(f"  Message {i+1}: {result['status']}")

    # Results should be "queued"
    statuses = [r['status'] for r in results]
    print(f"  All queued: {'✓' if all(s == 'queued' for s in statuses) else '✗'}")

    return results[0]


def test_connection():
    """Test channel connections."""
    print("\n[TEST 9] Connection Test")

    result = test_connection()
    print_result("Connection Test", result)

    for channel, success in result.get("results", {}).items():
        status = "✓" if success else "✗"
        print(f"  {status} {channel}")

    return result


def test_with_class():
    """Test using class directly."""
    print("\n[TEST 10] Class-based Usage")

    notifier = MT5Notifier()

    # Get enabled channels
    channels = notifier.get_enabled_channels()
    print(f"  Enabled channels: {channels}")

    # Send
    result = notifier.send(
        "Direct class usage test",
        severity="info",
        async_send=False
    )
    print(f"  Send result: {result['status']}")

    # Check severity enum
    print(f"\n  Severity enum:")
    print(f"    DEBUG < INFO: {Severity.DEBUG < Severity.INFO}")
    print(f"    INFO < WARNING: {Severity.INFO < Severity.WARNING}")
    print(f"    WARNING < CRITICAL: {Severity.WARNING < Severity.CRITICAL}")

    return result


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MT5 Notifier - Test Suite")
    print("=" * 70)

    tests = [
        ("Basic Send", test_basic_send),
        ("Trade Alerts", test_trade_alert),
        ("Daily Report", test_daily_report),
        ("Error Notification", test_error_notification),
        ("Bot Status", test_bot_status),
        ("Severity Filter", test_severity_filter),
        ("Specific Channel", test_specific_channel),
        ("Async Queuing", test_async_sending),
        ("Connection Test", test_connection),
        ("Class Usage", test_with_class),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            passed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name} failed: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
