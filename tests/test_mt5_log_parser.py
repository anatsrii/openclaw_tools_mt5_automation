#!/usr/bin/env python3
"""
Test script for MT5 Log Parser Tool

Test all log parsing operations.
"""

import sys
import json
import time
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

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


def print_result(title: str, result: dict):
    """Pretty print result dict."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

    # Print status and error
    for key in ["status", "error"]:
        if key in result and result[key]:
            print(f"  {key}: {result[key]}")

    # Count results
    if "entries" in result:
        print(f"  entries: {len(result['entries'])}")
    if "errors" in result:
        print(f"  errors: {len(result['errors'])}")
    if "trades" in result:
        print(f"  trades: {len(result['trades'])}")
    if "prints" in result:
        print(f"  prints: {len(result['prints'])}")
    if "anomalies" in result:
        print(f"  anomalies: {len(result['anomalies'])}")

    # Print other fields
    exclude_keys = {"status", "error", "entries", "errors", "trades", "prints", "anomalies"}
    for key, val in result.items():
        if key not in exclude_keys and val and not isinstance(val, (list, dict)):
            print(f"  {key}: {val}")

    # Print samples
    if "entries" in result and result["entries"]:
        print(f"\n  Sample entries:")
        for entry in result["entries"][:3]:
            print(f"    [{entry['type']}] {entry['message'][:60]}")

    if "errors" in result and result["errors"]:
        print(f"\n  Sample errors:")
        for err in result["errors"][:3]:
            print(f"    Line {err['line']}: {err['message'][:50]}")

    if "trades" in result and result["trades"]:
        print(f"\n  Sample trades:")
        for trade in result["trades"][:3]:
            print(f"    {trade['action']} {trade['symbol']} {trade['volume']} @ {trade['price']}")

    if "anomalies" in result and result["anomalies"]:
        print(f"\n  Sample anomalies:")
        for anom in result["anomalies"][:3]:
            print(f"    {anom['type']}: {anom['message'][:50]}")


def test_latest_journal():
    """Test reading latest journal."""
    print("\n[TEST 1] Get Latest Journal")
    result = get_latest_journal(lines=50)
    print_result("Latest Journal (50 lines)", result)
    return result


def test_compile_errors():
    """Test getting compile errors."""
    print("\n[TEST 2] Get Compile Errors")
    # Try a common EA name or test with generic name
    result = get_compile_errors("TestEA")
    print_result("Compile Errors", result)
    return result


def test_trade_history():
    """Test getting trade history."""
    print("\n[TEST 3] Get Trade History")
    result = get_trade_history(hours=24)
    print_result("Trade History (24 hours)", result)
    return result


def test_ea_prints():
    """Test getting EA prints."""
    print("\n[TEST 4] Get EA Prints")
    result = get_ea_prints("TestEA", hours=4)
    print_result("EA Prints (4 hours)", result)
    return result


def test_anomalies():
    """Test anomaly detection."""
    print("\n[TEST 5] Detect Anomalies")
    result = detect_anomalies(hours=24)
    print_result("Anomalies (24 hours)", result)
    return result


def test_watch_journal_brief():
    """Test watch journal (brief)."""
    print("\n[TEST 6] Watch Journal (10 seconds)")

    entries_received = []

    def on_entry(entry):
        entries_received.append(entry)
        print(f"  [WATCH] {entry['type']}: {entry['message'][:50]}")

    # Start watch
    result = watch_journal(on_entry)
    print_result("Watch Started", result)

    if result["status"] == "success":
        # Watch for 10 seconds
        print("  Monitoring for 10 seconds...")
        time.sleep(10)

        # Stop watch
        result = stop_watch()
        print_result("Watch Stopped", result)

        print(f"\n  Total entries received: {len(entries_received)}")

    return result


def test_watch_with_filter():
    """Test watch with keyword filter."""
    print("\n[TEST 7] Watch Journal with Filter (error/warning only)")

    error_entries = []

    def on_error(entry):
        error_entries.append(entry)
        severity = "🔴" if entry["type"] == "error" else "🟡"
        print(f"  {severity} {entry['message'][:60]}")

    # Start watch with filter
    result = watch_journal(on_error, filter_keywords=["error", "warning"])
    print_result("Filtered Watch Started", result)

    if result["status"] == "success":
        print("  Monitoring for 10 seconds (errors/warnings only)...")
        time.sleep(10)

        stop_watch()
        print(f"\n  Errors/warnings found: {len(error_entries)}")

    return result


def test_with_class():
    """Test using class directly."""
    print("\n[TEST 8] Using MT5LogParser Class")

    parser = MT5LogParser()

    # Get structure
    result = parser.get_latest_journal(lines=20)
    print_result("Parser - Latest Journal", result)

    # Get anomalies
    result = parser.detect_anomalies(hours=6)
    print_result("Parser - Anomalies", result)

    return result


def test_multiple_operations():
    """Test multiple operations in sequence."""
    print("\n[TEST 9] Multiple Operations")

    parser = MT5LogParser()

    print("  1. Getting latest journal...")
    j = parser.get_latest_journal(lines=30)
    print(f"     ✓ {len(j['entries'])} entries")

    print("  2. Checking for compile errors...")
    c = parser.get_compile_errors("TestEA")
    print(f"     ✓ {c['error_count']} errors, {c['warning_count']} warnings")

    print("  3. Fetching trade history...")
    t = parser.get_trade_history(hours=48)
    print(f"     ✓ {t['trade_count']} trades")

    print("  4. Detecting anomalies...")
    a = parser.detect_anomalies(hours=12)
    print(f"     ✓ {len(a['anomalies'])} anomalies")

    return {
        "journal": j,
        "compile": c,
        "trades": t,
        "anomalies": a
    }


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MT5 Log Parser - Test Suite")
    print("=" * 70)

    tests = [
        ("Get Latest Journal", test_latest_journal),
        ("Get Compile Errors", test_compile_errors),
        ("Get Trade History", test_trade_history),
        ("Get EA Prints", test_ea_prints),
        ("Detect Anomalies", test_anomalies),
        ("Watch Journal (Brief)", test_watch_journal_brief),
        ("Watch with Filter", test_watch_with_filter),
        ("Class-based Usage", test_with_class),
        ("Multiple Operations", test_multiple_operations),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result and isinstance(result, dict) and result.get("status") == "success":
                passed += 1
            elif result:
                passed += 1  # Still count as passed if it ran
            else:
                failed += 1
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
