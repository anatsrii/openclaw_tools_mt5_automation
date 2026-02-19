#!/usr/bin/env python3
"""
MT5 File Manager - Usage Examples

Practical examples of file management operations.
"""

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


# ==============================================================================
# EXAMPLE 1: Simple Read and List
# ==============================================================================
def example_read_list():
    """Example: Read EA and list files."""
    print("\n=== Example 1: Read and List ===")

    # List all EAs
    result = list_eas("Experts")
    if result["status"] == "success":
        print(f"Found {result['count']} EA files")
        for file in result["files"]:
            status = "✓" if file["has_compiled"] else "✗"
            print(f"  {status} {file['name']} ({file['size']} bytes)")

    # Read specific EA
    if result["files"]:
        ea_name = result["files"][0]["name"]
        content = read_ea_file(ea_name)
        if content["status"] == "success":
            print(f"\nRead: {content['path']}")
            print(f"Size: {content['size']} bytes")
            print(f"Modified: {content['last_modified']}")


# ==============================================================================
# EXAMPLE 2: Create and Backup
# ==============================================================================
def example_create_backup():
    """Example: Create new EA and backup."""
    print("\n=== Example 2: Create and Backup ===")

    # EA source code
    ea_code = """
// My Trading Robot
#property strict
#property copyright "2025"
#property version   "1.0"

void OnStart() {
    Print("EA started");
}

void OnTick() {
    // Trading logic here
}
"""

    # Write EA
    result = write_ea_file("MyRobot", ea_code, backup=False)
    print(f"Created: {result['path']}")

    # Backup it
    backup = backup_ea("MyRobot", tag="v1.0_initial")
    if backup["status"] == "success":
        print(f"Backed up: {backup['backup_path']}")


# ==============================================================================
# EXAMPLE 3: Strategy Tester Parameters
# ==============================================================================
def example_set_files():
    """Example: Manage strategy tester parameters."""
    print("\n=== Example 3: Strategy Tester Profiles ===")

    # Define profiles
    profiles = {
        "aggressive": {
            "TakeProfit": "150",
            "StopLoss": "30",
            "LotSize": "1.0",
            "MagicNumber": "1001"
        },
        "conservative": {
            "TakeProfit": "50",
            "StopLoss": "100",
            "LotSize": "0.1",
            "MagicNumber": "1002"
        },
        "scalper": {
            "TakeProfit": "20",
            "StopLoss": "15",
            "LotSize": "0.5",
            "MagicNumber": "1003"
        }
    }

    # Write profiles
    for profile_name, params in profiles.items():
        result = write_set_file("MyRobot", profile_name, params)
        print(f"Profile '{profile_name}': {result['count']} params")

    # Read profile
    result = read_set_file("MyRobot", "aggressive")
    if result["status"] == "success":
        print(f"\nAggressive profile settings:")
        for key, val in result["params"].items():
            print(f"  {key} = {val}")


# ==============================================================================
# EXAMPLE 4: Backup and Restore
# ==============================================================================
def example_backup_restore():
    """Example: Backup versions and restore."""
    print("\n=== Example 4: Version Control ===")

    # Create multiple versions
    versions = {
        "v1.0": "// Version 1\nvoid OnStart() { Print('v1.0'); }",
        "v1.1": "// Version 1.1\nvoid OnStart() { Print('v1.1'); }",
        "v1.2": "// Version 1.2\nvoid OnStart() { Print('v1.2'); }",
    }

    for version, code in versions.items():
        write_ea_file("VersionedEA", code, backup=False)
        backup_ea("VersionedEA", tag=version)
        print(f"Created and backed up: {version}")

    # Restore to v1.0
    result = restore_ea("VersionedEA", version="*v1.0")
    if result["status"] == "success":
        print(f"\nRestored to: {result['restored_from']}")


# ==============================================================================
# EXAMPLE 5: Directory Management
# ==============================================================================
def example_directory_management():
    """Example: Explore MT5 directory structure."""
    print("\n=== Example 5: Directory Structure ===")

    result = get_directory_tree()
    if result["status"] == "success":
        struct = result["structure"]

        print(f"\nTerminal Path: {struct['terminal_path']}")
        print(f"\nMQL5 Folders:")
        print(f"  Experts:     {struct['experts']['file_count']} files")
        print(f"  Indicators:  {struct['indicators']['file_count']} files")
        print(f"  Include:     {struct['include']['file_count']} files")
        print(f"\nBackups:      {struct['backups']['backup_count']} EAs")


# ==============================================================================
# EXAMPLE 6: Batch Operations
# ==============================================================================
def example_batch_operations():
    """Example: Batch file operations."""
    print("\n=== Example 6: Batch Operations ===")

    # Get all EAs
    eas = list_eas("Experts")
    if eas["status"] == "success":
        print(f"Processing {eas['count']} EA files...\n")

        uncompiled = []
        large_files = []

        for file in eas["files"]:
            # Track uncompiled
            if not file["has_compiled"]:
                uncompiled.append(file["name"])

            # Track large files
            if file["size"] > 50000:  # > 50 KB
                large_files.append((file["name"], file["size"]))

        print(f"Uncompiled EAs: {len(uncompiled)}")
        for name in uncompiled[:5]:
            print(f"  - {name}")
        if len(uncompiled) > 5:
            print(f"  ... and {len(uncompiled) - 5} more")

        print(f"\nLarge files (>50KB): {len(large_files)}")
        for name, size in large_files[:5]:
            print(f"  - {name} ({size // 1024} KB)")


# ==============================================================================
# EXAMPLE 7: Cleanup and Maintenance
# ==============================================================================
def example_cleanup():
    """Example: Backup cleanup."""
    print("\n=== Example 7: Backup Maintenance ===")

    # Check current backups
    result = get_directory_tree()
    if result["status"] == "success":
        backup_count = result["structure"]["backups"]["backup_count"]
        print(f"Total EAs with backups: {backup_count}")

    # Clean old backups
    result = clean_old_backups(keep_last=5)
    if result["status"] == "success":
        print(f"\nCleanup Summary:")
        print(f"  Removed: {result['removed_count']} backups")
        print(f"  Kept: {result['kept_count']} backups")

        for ea_name, stats in result["summary"].items():
            print(f"\n  {ea_name}:")
            print(f"    Total: {stats['total']}, Removed: {stats['removed']}, Kept: {stats['kept']}")


# ==============================================================================
# EXAMPLE 8: Advanced Class Usage
# ==============================================================================
def example_advanced_class():
    """Example: Advanced class-based usage."""
    print("\n=== Example 8: Class-based Workflow ===")

    # Create manager
    manager = MT5FileManager()

    # 1. Get directory info
    info = manager.get_directory_tree()
    print(f"Terminal: {info['structure']['terminal_path']}")

    # 2. List and analyze
    eas = manager.list_eas("Experts")
    if eas["files"]:
        largest = max(eas["files"], key=lambda x: x["size"])
        print(f"\nLargest EA: {largest['name']} ({largest['size']} bytes)")

    # 3. Read and backup
    ea_name = "MyEA"
    read_result = manager.read_ea_file(ea_name)
    if read_result["status"] == "success":
        print(f"\nRead: {ea_name}")
        print(f"Size: {read_result['size']} bytes")

        # Create backup
        backup = manager.backup_ea(ea_name, tag="before_modifications")
        print(f"Backup: {backup['timestamp']}")

    # 4. Set up test profiles
    test_params = {
        "TakeProfit": "100",
        "StopLoss": "50",
        "Hours": "8"
    }
    manager.write_set_file(ea_name, "test", test_params)
    print(f"\nSet file created: {ea_name}/test.set")


# ==============================================================================
# Main
# ==============================================================================
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("MT5 File Manager - Examples")
    print("=" * 60)

    examples = [
        ("Read and List", example_read_list),
        ("Create and Backup", example_create_backup),
        ("Strategy Tester", example_set_files),
        ("Backup and Restore", example_backup_restore),
        ("Directory Management", example_directory_management),
        ("Batch Operations", example_batch_operations),
        ("Cleanup", example_cleanup),
        ("Advanced Class", example_advanced_class),
    ]

    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")

    while True:
        try:
            choice = input("\nSelect example (1-8) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                break

            idx = int(choice) - 1
            if 0 <= idx < len(examples):
                try:
                    examples[idx][1]()
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
