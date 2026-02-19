#!/usr/bin/env python3
"""
Test script for MT5 File Manager Tool

Test all file management operations.
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tools.files import (
    MT5FileManager,
    read_ea_file,
    write_ea_file,
    list_eas,
    backup_ea,
    restore_ea,
    read_set_file,
    write_set_file,
    clean_old_backups,
    get_directory_tree
)


def print_result(title: str, result: dict):
    """Pretty print result dict."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")

    # Pretty print with formatting
    for key in ["status", "error"]:
        if key in result:
            val = result[key]
            if val:
                print(f"  {key}: {val}")

    # Print other important fields
    exclude_keys = {"status", "error", "content", "params"}
    for key, val in result.items():
        if key not in exclude_keys and val is not None:
            if isinstance(val, (list, dict)):
                print(f"  {key}:")
                print(f"    {json.dumps(val, indent=6, default=str)}")
            else:
                print(f"  {key}: {val}")

    # Print content/params if present
    if "content" in result and result["content"]:
        print(f"  content: {len(result['content'])} bytes")
        print(f"    {result['content'][:100]}...")

    if "params" in result and result["params"]:
        print(f"  params: {len(result['params'])} items")
        for k, v in result["params"].items():
            print(f"    {k} = {v}")


def test_directory_structure():
    """Test getting directory tree."""
    print("\n[TEST 1] Directory Structure")
    result = get_directory_tree()
    print_result("Directory Tree", result)
    return result


def test_write_ea():
    """Test writing EA file."""
    print("\n[TEST 2] Write EA File")

    test_code = """
// Simple test EA
#property strict

void OnStart() {
    Print("Test EA Code");
}
"""

    result = write_ea_file("TestEA_001", test_code, backup=False)
    print_result("Write EA", result)
    return result


def test_read_ea():
    """Test reading EA file."""
    print("\n[TEST 3] Read EA File")
    result = read_ea_file("TestEA_001")
    print_result("Read EA", result)
    return result


def test_backup_ea():
    """Test backing up EA."""
    print("\n[TEST 4] Backup EA")
    result = backup_ea("TestEA_001", tag="test_backup")
    print_result("Backup EA", result)
    return result


def test_list_eas():
    """Test listing EAs."""
    print("\n[TEST 5] List EAs")
    result = list_eas("Experts")
    print_result("List EAs", result)
    return result


def test_write_set():
    """Test writing .set file."""
    print("\n[TEST 6] Write .set File")

    params = {
        "TakeProfit": "100",
        "StopLoss": "50",
        "Lots": "0.1",
        "MagicNumber": "12345"
    }

    result = write_set_file("TestEA_001", "test_profile", params)
    print_result("Write .set File", result)
    return result


def test_read_set():
    """Test reading .set file."""
    print("\n[TEST 7] Read .set File")
    result = read_set_file("TestEA_001", "test_profile")
    print_result("Read .set File", result)
    return result


def test_restore_ea():
    """Test restoring EA."""
    print("\n[TEST 8] Restore EA (Manual Backup)")

    # Create backup first
    backup_result = backup_ea("TestEA_001", tag="before_restore_test")

    if backup_result["status"] == "success":
        # Modify file
        modified_code = """
// Modified test EA
#property strict

void OnStart() {
    Print("Modified Test EA");
}
"""
        write_ea_file("TestEA_001", modified_code, backup=False)

        # Restore
        restore_result = restore_ea("TestEA_001")
        print_result("Restore EA", restore_result)
        return restore_result
    else:
        print("Skipping restore test - backup failed")
        return backup_result


def test_clean_backups():
    """Test cleaning old backups."""
    print("\n[TEST 9] Clean Old Backups")

    # Create multiple backups
    for i in range(5):
        backup_ea("TestEA_001", tag=f"backup_{i}")

    result = clean_old_backups(keep_last=3)
    print_result("Clean Backups", result)
    return result


def test_update_with_backup():
    """Test writing with backup."""
    print("\n[TEST 10] Write with Automatic Backup")

    updated_code = """
// Updated test EA with features
#property strict

void OnStart() {
    Print("Updated Test EA");
}
"""

    result = write_ea_file("TestEA_001", updated_code, backup=True)
    print_result("Write with Backup", result)
    return result


def test_with_class():
    """Test using class directly."""
    print("\n[TEST 11] Class-based Usage")

    manager = MT5FileManager()

    # Get structure
    structure = manager.get_directory_tree()
    print_result("Manager Structure", structure)

    # List EAs
    eas = manager.list_eas("Experts")
    print_result("Manager List EAs", eas)

    return eas


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  MT5 File Manager - Test Suite")
    print("=" * 70)

    tests = [
        ("Directory Structure", test_directory_structure),
        ("Write EA File", test_write_ea),
        ("Read EA File", test_read_ea),
        ("Backup EA", test_backup_ea),
        ("List EAs", test_list_eas),
        ("Write .set File", test_write_set),
        ("Read .set File", test_read_set),
        ("Restore EA", test_restore_ea),
        ("Clean Backups", test_clean_backups),
        ("Write with Backup", test_update_with_backup),
        ("Class-based Usage", test_with_class),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            result = test_func()
            if result and result.get("status") == "success":
                passed += 1
            elif result:
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
