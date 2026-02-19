#!/usr/bin/env python3
"""Test MT5 Scheduler Tool"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.scheduler import (
    get_current_session,
    schedule_task,
    is_market_open,
    list_tasks,
    cancel_task,
    create_default_schedules
)


def test_current_session():
    """Test getting current session."""
    print("\n[TEST 1] Current Session")
    result = get_current_session()
    print(f"  Status: {result['status']}")
    print(f"  Sessions: {result['sessions']}")
    print(f"  Overlap: {result['is_overlap']}")
    print(f"  Local time: {result['local_time']}")
    return result


def test_market_open():
    """Test market open check."""
    print("\n[TEST 2] Market Open Check")
    result = is_market_open("XAUUSD")
    print(f"  Open: {result['is_open']}")
    print(f"  Session: {result['current_session']}")
    print(f"  Weekend: {result['is_weekend']}")
    return result


def test_schedule_cron():
    """Test cron scheduling."""
    print("\n[TEST 3] Cron Task")

    def test_func():
        print("Test cron task executed")

    result = schedule_task(
        test_func,
        "cron",
        task_id="test_cron",
        cron_expr="0 6 * * *"
    )
    print(f"  Status: {result['status']}")
    print(f"  Task ID: {result['task_id']}")
    return result


def test_schedule_interval():
    """Test interval scheduling."""
    print("\n[TEST 4] Interval Task")

    def check_status():
        print("Status check")

    result = schedule_task(
        check_status,
        "interval",
        task_id="status_check",
        minutes=5
    )
    print(f"  Status: {result['status']}")
    print(f"  Task ID: {result['task_id']}")
    return result


def test_list_tasks():
    """Test listing tasks."""
    print("\n[TEST 5] List Tasks")
    result = list_tasks()
    print(f"  Total: {result['count']}")
    for task in result['tasks'][:3]:
        print(f"    - {task['id']}: {task['name']}")
    return result


def test_cancel_task():
    """Test cancelling task."""
    print("\n[TEST 6] Cancel Task")
    result = cancel_task("test_cron")
    print(f"  Status: {result['status']}")
    print(f"  Message: {result['message']}")
    return result


def test_default_schedules():
    """Test creating default schedules."""
    print("\n[TEST 7] Default Schedules")
    result = create_default_schedules()
    print(f"  Status: {result['status']}")
    print(f"  Created: {len(result['schedules'])} schedules")
    return result


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MT5 Scheduler - Test Suite")
    print("=" * 70)

    tests = [
        ("Current Session", test_current_session),
        ("Market Open", test_market_open),
        ("Schedule Cron", test_schedule_cron),
        ("Schedule Interval", test_schedule_interval),
        ("List Tasks", test_list_tasks),
        ("Cancel Task", test_cancel_task),
        ("Default Schedules", test_default_schedules),
    ]

    passed = 0
    failed = 0

    for name, func in tests:
        try:
            func()
            passed += 1
        except Exception as e:
            print(f"[ERROR] {name}: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"Passed: {passed}, Failed: {failed}")
    print("=" * 70)


if __name__ == "__main__":
    main()
