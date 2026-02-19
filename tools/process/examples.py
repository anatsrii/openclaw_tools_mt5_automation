#!/usr/bin/env python3
"""
MT5 Process Control - Quick Examples

Practical examples of using the mt5_process_control module.
"""

from tools.process import (
    start_mt5,
    stop_mt5,
    restart_mt5,
    get_mt5_status,
    watch_mt5,
    stop_watch,
    MT5ProcessControl
)
import time


# ==============================================================================
# EXAMPLE 1: Simple Start and Stop
# ==============================================================================
def example_simple_start_stop():
    """Example: Start and stop MT5."""
    print("\n=== Example 1: Simple Start and Stop ===")

    # Start MT5
    result = start_mt5(minimized=True)
    print(f"Start result: {result['status']}")
    if result['status'] == 'success':
        print(f"  PID: {result['pid']}")
        print(f"  Startup time: {result['startup_time']:.1f} seconds")

    # Wait a bit
    time.sleep(5)

    # Stop MT5
    result = stop_mt5(force=False)
    print(f"Stop result: {result['status']}")
    if result['was_running']:
        print("  MT5 was running")


# ==============================================================================
# EXAMPLE 2: Check Status
# ==============================================================================
def example_check_status():
    """Example: Check MT5 status."""
    print("\n=== Example 2: Check Status ===")

    status = get_mt5_status()
    print(f"Status: {status['status']}")
    print(f"  Running: {status['is_running']}")
    print(f"  Responsive: {status['is_responsive']}")
    if status['pid']:
        print(f"  PID: {status['pid']}")
        print(f"  Uptime: {status['uptime_minutes']:.1f} minutes")


# ==============================================================================
# EXAMPLE 3: Restart
# ==============================================================================
def example_restart():
    """Example: Restart MT5."""
    print("\n=== Example 3: Restart ===")

    result = restart_mt5(wait_seconds=3)
    print(f"Restart result: {result['status']}")
    if result['status'] == 'success':
        print(f"  New PID: {result['new_pid']}")
        print(f"  Total time: {result['total_time']:.1f} seconds")


# ==============================================================================
# EXAMPLE 4: Using Class with Callback
# ==============================================================================
def example_class_with_callback():
    """Example: Use MT5ProcessControl class with callback."""
    print("\n=== Example 4: Class with Callback ===")

    def on_mt5_event(event_type, data):
        """Handle MT5 events."""
        print(f"  [EVENT] {event_type}: {data}")

    controller = MT5ProcessControl()

    # Start
    result = controller.start_mt5()
    print(f"Start: {result['status']}")

    # Monitor
    watch_result = controller.watch_mt5(
        interval=5,
        auto_restart=True,
        callback=on_mt5_event
    )
    print(f"Watch started: {watch_result['status']}")

    # Watch for 15 seconds
    print("  Monitoring for 15 seconds...")
    time.sleep(15)

    # Stop watch and MT5
    controller.stop_watch()
    controller.stop_mt5()
    print("Done")


# ==============================================================================
# EXAMPLE 5: Monitoring with Restart on Crash
# ==============================================================================
def example_monitoring_with_auto_restart():
    """Example: Monitor MT5 with auto-restart."""
    print("\n=== Example 5: Monitoring with Auto-Restart ===")

    def notify(event_type, data):
        """Notification handler."""
        if event_type == "crash_detected":
            print(f"  ⚠️  MT5 crashed! (was PID {data['last_pid']})")
        elif event_type == "auto_restart":
            print(f"  🔄 Auto-restart #{data['restart_count']}")
        elif event_type == "unresponsive":
            print(f"  ❌ MT5 not responding (PID {data['pid']})")

    # Start MT5
    start_result = start_mt5()
    if start_result['status'] == 'success':
        print(f"MT5 started (PID {start_result['pid']})")

        # Start monitoring
        watch_result = watch_mt5(
            interval=10,          # Check every 10 seconds
            auto_restart=True,    # Auto-restart on crash
            callback=notify
        )

        if watch_result['status'] == 'success':
            print("Monitoring started...")
            print("Monitoring for 30 seconds (Ctrl+C to stop)...")

            try:
                time.sleep(30)
            except KeyboardInterrupt:
                pass
            finally:
                stop_watch()
                stop_mt5()
                print("Monitoring stopped")


# ==============================================================================
# EXAMPLE 6: Error Handling
# ==============================================================================
def example_error_handling():
    """Example: Proper error handling."""
    print("\n=== Example 6: Error Handling ===")

    # Try to start
    result = start_mt5()

    if result['status'] == 'success':
        print(f"✓ MT5 started successfully")
        print(f"  PID: {result['pid']}")
        print(f"  Startup: {result['startup_time']:.1f}s")
    else:
        print(f"✗ Failed to start MT5")
        print(f"  Error: {result['error']}")
        print(f"  Message: {result['message']}")

    # Check status with error handling
    status = get_mt5_status()
    if status['error']:
        print(f"Error checking status: {status['error']}")
    else:
        if status['is_running']:
            print(f"✓ MT5 running (PID {status['pid']})")
        else:
            print("✗ MT5 not running")


# ==============================================================================
# EXAMPLE 7: Multiple Operations
# ==============================================================================
def example_workflow():
    """Example: Complete workflow."""
    print("\n=== Example 7: Complete Workflow ===")

    controller = MT5ProcessControl()

    # Step 1: Check current status
    print("Step 1: Checking current status...")
    status = controller.get_mt5_status()
    print(f"  MT5 running: {status['is_running']}")

    # Step 2: Start if not running
    if not status['is_running']:
        print("Step 2: Starting MT5...")
        result = controller.start_mt5(minimized=True)
        if result['status'] == 'success':
            print(f"  Started with PID {result['pid']}")
        else:
            print(f"  Failed: {result['error']}")
            return

    # Step 3: Check responsiveness
    print("Step 3: Checking responsiveness...")
    status = controller.get_mt5_status()
    if status['is_responsive']:
        print("  ✓ MT5 is responsive")
    else:
        print("  ⚠️  MT5 is not responsive, restarting...")
        restart_result = controller.restart_mt5()
        print(f"  Restarted (new PID: {restart_result['new_pid']})")

    # Step 4: Cleanup
    print("Step 4: Closing MT5...")
    result = controller.stop_mt5()
    print(f"  Closed: {result['status']}")


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MT5 Process Control - Examples")
    print("=" * 60)

    examples = [
        ("Simple Start/Stop", example_simple_start_stop),
        ("Check Status", example_check_status),
        ("Restart", example_restart),
        ("Class with Callback", example_class_with_callback),
        ("Auto-Restart Monitoring", example_monitoring_with_auto_restart),
        ("Error Handling", example_error_handling),
        ("Complete Workflow", example_workflow),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    while True:
        try:
            choice = input("\nSelect example (1-7) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                break
            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                examples[idx][1]()
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number")
        except KeyboardInterrupt:
            print("\nStopped")
            break
