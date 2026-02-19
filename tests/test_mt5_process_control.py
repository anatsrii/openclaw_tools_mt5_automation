#!/usr/bin/env python3
"""
Test script for MT5 Process Control Tool

This script demonstrates all functions of the mt5_process_control module.
"""

import sys
import time
import json
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.process import (
    MT5ProcessControl,
    start_mt5,
    stop_mt5,
    restart_mt5,
    get_mt5_status,
    watch_mt5,
    stop_watch
)


def print_result(title: str, result: dict):
    """Pretty print result dict."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")
    print(json.dumps(result, indent=2, default=str))


def test_check_status():
    """Test getting MT5 status."""
    print("\n[TEST 1] Check MT5 Status")
    result = get_mt5_status()
    print_result("MT5 Status Check", result)
    return result


def test_start_mt5():
    """Test starting MT5."""
    print("\n[TEST 2] Start MT5")
    result = start_mt5(minimized=True)
    print_result("MT5 Startup", result)
    time.sleep(2)
    return result


def test_get_status_after_start():
    """Test status after starting."""
    print("\n[TEST 3] Check Status After Start")
    result = get_mt5_status()
    print_result("MT5 Status After Startup", result)
    return result


def test_restart_mt5():
    """Test restarting MT5."""
    print("\n[TEST 4] Restart MT5")
    result = restart_mt5(wait_seconds=3)
    print_result("MT5 Restart", result)
    time.sleep(2)
    return result


def test_watch_mt5():
    """Test watching MT5 with callback."""
    print("\n[TEST 5] Start Watching MT5")

    def on_event(event_type: str, data: dict):
        """Callback for watch events."""
        print(f"  [WATCH EVENT] {event_type}: {data}")

    result = watch_mt5(interval=5, auto_restart=True, callback=on_event)
    print_result("Watch Started", result)

    # Watch for 20 seconds
    print("  Watching for 20 seconds...")
    time.sleep(20)

    stop_result = stop_watch()
    print_result("Watch Stopped", stop_result)
    return result


def test_stop_mt5():
    """Test stopping MT5."""
    print("\n[TEST 6] Stop MT5")
    result = stop_mt5(force=False)
    print_result("MT5 Stop", result)
    time.sleep(1)
    return result


def test_with_class():
    """Test using MT5ProcessControl class directly."""
    print("\n[TEST 7] Using MT5ProcessControl Class")

    controller = MT5ProcessControl()

    # Get status
    status = controller.get_mt5_status()
    print_result("Status Via Class", status)

    if not status["is_running"]:
        # Start
        start_result = controller.start_mt5()
        print_result("Start Via Class", start_result)
        time.sleep(2)

        # Check status
        status = controller.get_mt5_status()
        print_result("Status Check Via Class", status)

        # Stop
        stop_result = controller.stop_mt5()
        print_result("Stop Via Class", stop_result)


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("  MT5 Process Control - Test Suite")
    print("=" * 60)

    tests = [
        ("Check Initial Status", test_check_status),
        ("Start MT5", test_start_mt5),
        ("Status After Start", test_get_status_after_start),
        ("Restart MT5", test_restart_mt5),
        ("Watch MT5", test_watch_mt5),
        ("Stop MT5", test_stop_mt5),
        ("Class-based Usage", test_with_class),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[ERROR] {test_name} failed: {str(e)}")
            failed += 1

    # Summary
    print("\n" + "=" * 60)
    print("  Test Summary")
    print("=" * 60)
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Total:  {passed + failed}")
    print("=" * 60)


if __name__ == "__main__":
    main()
