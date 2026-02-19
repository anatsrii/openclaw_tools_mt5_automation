#!/usr/bin/env python3
"""MT5 Scheduler - Usage Examples"""

from tools.scheduler import (
    get_current_session,
    schedule_task,
    is_market_open,
    create_default_schedules,
    wait_for_session
)


def example_check_session():
    """Example: Check current market session."""
    print("\n=== Example 1: Check Session ===")

    session = get_current_session()
    print(f"Active: {session['sessions']}")
    print(f"Overlap: {session['is_overlap']}")
    print(f"Next session: {session['next_session']}")


def example_schedule_daily():
    """Example: Schedule daily report."""
    print("\n=== Example 2: Daily Task ===")

    def send_daily_report():
        print("Sending daily report...")

    result = schedule_task(
        send_daily_report,
        "cron",
        task_id="daily_report",
        cron_expr="0 6 * * *"  # 06:00 every day
    )
    print(f"Scheduled: {result['task_id']}")


def example_schedule_interval():
    """Example: Schedule repeating check."""
    print("\n=== Example 3: Interval Task ===")

    def check_mt5_status():
        status = is_market_open("XAUUSD")
        print(f"Market open: {status['is_open']}")

    result = schedule_task(
        check_mt5_status,
        "interval",
        task_id="status_check",
        minutes=5  # Every 5 minutes
    )
    print(f"Scheduled: {result['task_id']}")


def example_market_hours():
    """Example: Check market hours."""
    print("\n=== Example 4: Market Hours ===")

    market = is_market_open("XAUUSD")
    print(f"Open: {market['is_open']}")
    print(f"Session: {market['current_session']}")

    if not market['is_open']:
        print(f"Opens in: {market['time_until_open']}")


def example_default_schedules():
    """Example: Create recommended schedules."""
    print("\n=== Example 5: Default Schedules ===")

    result = create_default_schedules()
    print(f"Created {len(result['schedules'])} schedules:")
    for sid, sinfo in result['schedules'].items():
        print(f"  - {sid}")


def example_session_based():
    """Example: Schedule on session events."""
    print("\n=== Example 6: Session-Based ===")

    def on_london_open():
        print("London session opening...")

    result = schedule_task(
        on_london_open,
        "session_open",
        task_id="london_open",
        session="London"
    )
    print(f"Scheduled: {result['task_id']}")


def example_trading_workflow():
    """Example: Complete trading workflow."""
    print("\n=== Example 7: Trading Workflow ===")

    def start_trading():
        print("Starting trading session...")

    def check_status():
        market = is_market_open()
        if market['is_open']:
            print(f"Trading active: {market['current_session']}")

    def send_report():
        print("Sending end-of-day report...")

    # Schedule all
    schedule_task(start_trading, "cron", cron_expr="0 0 * * 1-5")  # Mon-Fri 00:00
    schedule_task(check_status, "interval", minutes=30)
    schedule_task(send_report, "cron", cron_expr="0 23 * * *")

    print("✓ Trading workflow scheduled")


if __name__ == "__main__":
    print("\nMT5 Scheduler Examples")
    print("=" * 50)

    examples = [
        ("Check Session", example_check_session),
        ("Daily Task", example_schedule_daily),
        ("Interval Task", example_schedule_interval),
        ("Market Hours", example_market_hours),
        ("Default Schedules", example_default_schedules),
        ("Session-Based", example_session_based),
        ("Trading Workflow", example_trading_workflow),
    ]

    for i, (name, func) in enumerate(examples, 1):
        print(f"\n{i}. {name}")
        try:
            func()
        except Exception as e:
            print(f"   Error: {e}")
