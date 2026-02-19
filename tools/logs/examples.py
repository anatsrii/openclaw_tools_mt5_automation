#!/usr/bin/env python3
"""
MT5 Log Parser - Usage Examples

Practical examples of log parsing and monitoring.
"""

import time
from tools.logs import (
    MT5LogParser,
    get_latest_journal,
    get_compile_errors,
    get_trade_history,
    get_ea_prints,
    watch_journal,
    stop_watch,
    detect_anomalies
)


# ==============================================================================
# EXAMPLE 1: Read Latest Journal Entries
# ==============================================================================
def example_read_journal():
    """Example: Read and display latest journal entries."""
    print("\n=== Example 1: Read Latest Journal ===")

    result = get_latest_journal(lines=30)

    if result["status"] == "success":
        print(f"File: {result['file_path']}")
        print(f"Total lines: {result['total_lines']}")
        print(f"Showing last {len(result['entries'])} entries:\n")

        for entry in result["entries"]:
            # Color code by type
            icon = "❌" if entry["type"] == "error" else "⚠️ " if entry["type"] == "warning" else "ℹ️"
            print(f"{icon} {entry['timestamp']} [{entry['source']}] {entry['message']}")

    else:
        print(f"Error: {result['error']}")


# ==============================================================================
# EXAMPLE 2: Check Compile Errors
# ==============================================================================
def example_compile_errors():
    """Example: Check EA for compile errors."""
    print("\n=== Example 2: Compile Errors ===")

    result = get_compile_errors("MyEA")

    if result["status"] == "success":
        if result["error_count"] + result["warning_count"] == 0:
            print("✓ No compile errors found!")
        else:
            print(f"Errors: {result['error_count']}, Warnings: {result['warning_count']}\n")

            # Group by type
            errors = [e for e in result["errors"] if e["is_error"]]
            warnings = [e for e in result["errors"] if e["is_warning"]]

            if errors:
                print("ERRORS:")
                for err in errors:
                    print(f"  Line {err['line']}: {err['error_code']} - {err['message']}")

            if warnings:
                print("\nWARNINGS:")
                for warn in warnings:
                    print(f"  {warn['error_code']} - {warn['message']}")

    else:
        print(f"Error: {result['error']}")


# ==============================================================================
# EXAMPLE 3: Analyze Trade History
# ==============================================================================
def example_trade_history():
    """Example: Get and analyze trade history."""
    print("\n=== Example 3: Trade History (Last 48 Hours) ===")

    result = get_trade_history(hours=48)

    if result["status"] == "success":
        if not result["trades"]:
            print("No trades found in the last 48 hours")
            return

        print(f"Total trades: {result['trade_count']}\n")

        # Calculate statistics
        wins = [t for t in result["trades"] if t["profit"] and t["profit"] > 0]
        losses = [t for t in result["trades"] if t["profit"] and t["profit"] <= 0]

        print(f"Wins: {len(wins)}, Losses: {len(losses)}")

        if result["trades"]:
            total_profit = sum(t["profit"] for t in result["trades"] if t["profit"])
            print(f"Total P/L: {total_profit:+.2f}\n")

        # Show recent trades
        print("Recent trades:")
        for trade in result["trades"][-5:]:
            profit_str = f"+{trade['profit']:.2f}" if trade['profit'] > 0 else f"{trade['profit']:.2f}"
            print(f"  {trade['time']} {trade['action']:6} {trade['symbol']} {trade['volume']:5} "
                  f"@ {trade['price']:10} ({profit_str})")

    else:
        print(f"Error: {result['error']}")


# ==============================================================================
# EXAMPLE 4: Monitor Journal in Real-time
# ==============================================================================
def example_monitor_journal():
    """Example: Watch journal in real-time."""
    print("\n=== Example 4: Real-time Journal Monitoring ===")
    print("Monitoring for 30 seconds...\n")

    stats = {"info": 0, "warning": 0, "error": 0}

    def on_new_entry(entry):
        stats[entry["type"]] += 1
        icon = "❌" if entry["type"] == "error" else "⚠️ " if entry["type"] == "warning" else "✓"
        print(f"{icon} [{entry['type'].upper()}] {entry['message'][:70]}")

    # Start monitoring
    watch_journal(on_new_entry)

    # Watch for 30 seconds
    time.sleep(30)

    # Stop monitoring
    stop_watch()

    print(f"\nMonitoring stats:")
    print(f"  Info:    {stats['info']}")
    print(f"  Warning: {stats['warning']}")
    print(f"  Error:   {stats['error']}")


# ==============================================================================
# EXAMPLE 5: Monitor Errors Only
# ==============================================================================
def example_monitor_errors():
    """Example: Monitor only errors and warnings."""
    print("\n=== Example 5: Error Monitoring (20 seconds) ===")
    print("Watching for errors and warnings only...\n")

    errors_found = []

    def on_error_event(entry):
        errors_found.append(entry)
        print(f"🔴 {entry['message']}")

    # Start watching errors only
    watch_journal(
        on_error_event,
        filter_keywords=["error", "warning", "failed", "invalid"]
    )

    # Monitor for 20 seconds
    time.sleep(20)

    # Stop
    stop_watch()

    print(f"\nTotal error events: {len(errors_found)}")
    if errors_found:
        print("Last error:", errors_found[-1]["message"][:100])


# ==============================================================================
# EXAMPLE 6: Get EA Debug Output
# ==============================================================================
def example_ea_debug():
    """Example: Extract EA Print() debug output."""
    print("\n=== Example 6: EA Debug Output ===")

    result = get_ea_prints("MyEA", hours=2)

    if result["status"] == "success":
        if not result["prints"]:
            print("No Print output found for MyEA in the last 2 hours")
            return

        print(f"Found {result['count']} Print statements:\n")

        for entry in result["prints"][-10:]:
            print(f"{entry['timestamp']} | {entry['message']}")

    else:
        print(f"Error: {result['error']}")


# ==============================================================================
# EXAMPLE 7: Detect Issues
# ==============================================================================
def example_detect_issues():
    """Example: Detect connection and account issues."""
    print("\n=== Example 7: Anomaly Detection ===")

    result = detect_anomalies(hours=24)

    if result["status"] == "success":
        if not result["anomalies"]:
            print("✓ No anomalies detected in the last 24 hours!")
            return

        print(f"Found {len(result['anomalies'])} anomalies:\n")

        for anom in result["anomalies"]:
            severity_icon = "🔴" if anom["severity"] == "critical" else "🟡"
            print(f"{severity_icon} {anom['type'].upper()}")
            print(f"   Occurrences: {anom['count']}")
            print(f"   Message: {anom['message']}")
            print(f"   Time: {anom['timestamp']}\n")

    else:
        print(f"Error: {result['error']}")


# ==============================================================================
# EXAMPLE 8: Daily Report
# ==============================================================================
def example_daily_report():
    """Example: Generate daily trading report."""
    print("\n=== Example 8: Daily Trading Report ===\n")

    parser = MT5LogParser()

    # Get all relevant data
    journal = parser.get_latest_journal(lines=100)
    trades = parser.get_trade_history(hours=24)
    print_output = parser.get_ea_prints("MyEA", hours=24)
    anomalies = parser.detect_anomalies(hours=24)

    print("📊 DAILY REPORT")
    print("=" * 50)

    # Summary
    if trades["status"] == "success" and trades["trades"]:
        total_trades = len(trades["trades"])
        total_profit = sum(t["profit"] for t in trades["trades"] if t["profit"])
        print(f"\n📈 TRADING")
        print(f"  Trades:    {total_trades}")
        print(f"  Total P/L: {total_profit:+.2f}")

    # EA Activity
    if print_output["status"] == "success":
        print(f"\n🤖 EA ACTIVITY")
        print(f"  Print statements: {print_output['count']}")

    # Issues
    if anomalies["status"] == "success" and anomalies["anomalies"]:
        print(f"\n⚠️  ISSUES")
        print(f"  Anomalies detected: {len(anomalies['anomalies'])}")
        for anom in anomalies["anomalies"]:
            print(f"    - {anom['type']}: {anom['count']}x")

    else:
        print("\n✓ No issues detected")

    # Recent entries
    if journal["status"] == "success" and journal["entries"]:
        print(f"\n📋 RECENT EVENTS")
        for entry in journal["entries"][-3:]:
            print(f"  {entry['timestamp']} {entry['message'][:60]}")

    print("\n" + "=" * 50)


# ==============================================================================
# EXAMPLE 9: Performance Monitoring
# ==============================================================================
def example_performance_monitor():
    """Example: Monitor and log performance metrics."""
    print("\n=== Example 9: Performance Monitoring ===")
    print("Running for 60 seconds...\n")

    metrics = {
        "updates": 0,
        "errors": 0,
        "timestamp_first": None,
        "timestamp_last": None,
    }

    def track_entry(entry):
        metrics["updates"] += 1
        if entry["type"] == "error":
            metrics["errors"] += 1

        if not metrics["timestamp_first"]:
            metrics["timestamp_first"] = entry["timestamp"]
        metrics["timestamp_last"] = entry["timestamp"]

    # Monitor
    watch_journal(track_entry)
    time.sleep(60)
    stop_watch()

    print(f"\nPerformance Metrics:")
    print(f"  Total updates: {metrics['updates']}")
    print(f"  Errors: {metrics['errors']}")
    print(f"  Avg per second: {metrics['updates'] / 60:.1f}")
    if metrics["errors"] > 0:
        print(f"  Error rate: {metrics['errors'] / metrics['updates'] * 100:.1f}%")


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MT5 Log Parser - Examples")
    print("=" * 60)

    examples = [
        ("Read Latest Journal", example_read_journal),
        ("Check Compile Errors", example_compile_errors),
        ("Trade History", example_trade_history),
        ("Monitor Journal", example_monitor_journal),
        ("Monitor Errors", example_monitor_errors),
        ("EA Debug Output", example_ea_debug),
        ("Detect Anomalies", example_detect_issues),
        ("Daily Report", example_daily_report),
        ("Performance Monitor", example_performance_monitor),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    while True:
        try:
            choice = input("\nSelect example (1-9) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                break

            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                try:
                    examples[idx][1]()
                except KeyboardInterrupt:
                    print("\nCancelled")
                except Exception as e:
                    print(f"Error: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("Invalid selection")
        except ValueError:
            print("Please enter a number")
        except KeyboardInterrupt:
            print("\nStopped")
            break
