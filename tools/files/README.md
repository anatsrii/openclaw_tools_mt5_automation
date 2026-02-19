# MT5 File Manager Tool

Manage MetaTrader 5 files: EA source code, compiled files, configuration, and backups.

## Overview

The `mt5_file_manager` module provides complete file management for MT5 development workflows including:
- Reading and writing EA source code (.mq5 files)
- Backing up and restoring EA versions
- Managing strategy tester parameter files (.set files)
- Automatic backup management with cleanup
- Directory structure navigation

## Features

- ✅ Read EA source code with metadata
- ✅ Write EA files with automatic backup
- ✅ List EAs with compilation status
- ✅ Create timestamped backups
- ✅ Restore from specific or latest backup
- ✅ Manage .set files for strategy tester
- ✅ Clean old backups automatically
- ✅ Full error handling with structured results
- ✅ UTF-8 encoding support for international characters

## Directory Structure

```
MT5 Terminal/
├── MQL5/
│   ├── Experts/           # EA files (.mq5, .ex5)
│   ├── Indicators/        # Indicator files
│   ├── Include/           # Header files (.mqh)
│   └── Tester/           # .set files for backtesting
├── logs/                 # MT5 log files
├── profiles/             # User profiles
└── backups/              # Backup directory (created by manager)
    └── [EA_NAME]/
        └── [TIMESTAMP]/  # Versioned backups
            └── [EA_NAME].mq5
```

## Installation

See `REQUIREMENTS.md` for dependencies.

```bash
pip install -r tools/files/REQUIREMENTS.md
```

## API Reference

### read_ea_file(ea_name)

Read EA source code.

**Parameters:**
- `ea_name` (str): EA filename (with or without .mq5)

**Returns:**
```python
{
    "status": "success" | "error",
    "content": str,              # File content
    "path": str,
    "last_modified": str,        # ISO format
    "size": int,                 # Bytes
    "error": str | None
}
```

**Example:**
```python
from tools.files import read_ea_file

result = read_ea_file("MyEA")
if result["status"] == "success":
    print(f"Size: {result['size']} bytes")
    print(result["content"][:200])  # First 200 chars
```

---

### write_ea_file(ea_name, content, backup=True)

Write EA source code with optional backup.

**Parameters:**
- `ea_name` (str): EA filename
- `content` (str): File content to write
- `backup` (bool): Create backup of previous version (default: True)

**Returns:**
```python
{
    "status": "success" | "error",
    "path": str,
    "backup_path": str | None,    # Path if backup created
    "message": str,
    "error": str | None
}
```

**Example:**
```python
from tools.files import write_ea_file

code = """
#property strict
void OnTick() {
    // EA logic here
}
"""

result = write_ea_file("MyEA", code, backup=True)
print(f"Written: {result['path']}")
if result['backup_path']:
    print(f"Backup: {result['backup_path']}")
```

---

### list_eas(folder="Experts")

List all EA/Indicator files with metadata.

**Parameters:**
- `folder` (str): "Experts", "Indicators", or "Include" (default: "Experts")

**Returns:**
```python
{
    "status": "success" | "error",
    "files": [
        {
            "name": str,
            "path": str,
            "size": int,
            "last_modified": str,    # ISO format
            "has_compiled": bool     # .ex5 exists
        }
    ],
    "count": int,
    "error": str | None
}
```

**Example:**
```python
from tools.files import list_eas

result = list_eas("Experts")
for file in result["files"]:
    status = "✓" if file["has_compiled"] else "✗"
    print(f"{status} {file['name']} ({file['size']} bytes)")
```

---

### backup_ea(ea_name, tag="manual")

Create timestamped backup of EA.

**Parameters:**
- `ea_name` (str): EA filename
- `tag` (str): Backup tag for organization (default: "manual")

**Returns:**
```python
{
    "status": "success" | "error",
    "backup_path": str,
    "timestamp": str,             # ISO format
    "message": str,
    "error": str | None
}
```

**Example:**
```python
from tools.files import backup_ea

result = backup_ea("MyEA", tag="before_optimization")
print(f"Backup: {result['backup_path']}")
print(f"Time: {result['timestamp']}")
```

---

### restore_ea(ea_name, version=None)

Restore EA from backup.

**Parameters:**
- `ea_name` (str): EA filename
- `version` (str, optional): Specific version (timestamp) or None for latest

**Returns:**
```python
{
    "status": "success" | "error",
    "restored_from": str,         # Backup file path
    "message": str,
    "error": str | None
}
```

**Example:**
```python
from tools.files import restore_ea

# Restore latest
result = restore_ea("MyEA")

# Restore specific version
result = restore_ea("MyEA", version="20250219_143025_before_test")
```

---

### read_set_file(ea_name, profile_name)

Read .set file (Strategy Tester parameters).

**Parameters:**
- `ea_name` (str): EA name
- `profile_name` (str): Profile name (without .set)

**Returns:**
```python
{
    "status": "success" | "error",
    "params": dict,               # key-value pairs
    "path": str,
    "error": str | None
}
```

**Example:**
```python
from tools.files import read_set_file

result = read_set_file("MyEA", "profile1")
if result["status"] == "success":
    for key, value in result["params"].items():
        print(f"{key} = {value}")
```

---

### write_set_file(ea_name, profile_name, params)

Write .set file with parameters.

**Parameters:**
- `ea_name` (str): EA name
- `profile_name` (str): Profile name
- `params` (dict): Parameter key-value pairs

**Returns:**
```python
{
    "status": "success" | "error",
    "path": str,
    "count": int,                 # Parameters written
    "error": str | None
}
```

**Example:**
```python
from tools.files import write_set_file

params = {
    "TakeProfit": "100",
    "StopLoss": "50",
    "RiskPercent": "2",
    "Magic": "12345"
}

result = write_set_file("MyEA", "conservative", params)
print(f"Written {result['count']} parameters")
```

---

### clean_old_backups(keep_last=10)

Remove old backups, keeping N most recent per EA.

**Parameters:**
- `keep_last` (int): Number of recent backups to keep (default: 10)

**Returns:**
```python
{
    "status": "success" | "error",
    "removed_count": int,
    "kept_count": int,
    "summary": dict,              # by EA name
    "error": str | None
}
```

**Example:**
```python
from tools.files import clean_old_backups

result = clean_old_backups(keep_last=5)
print(f"Removed: {result['removed_count']}")
print(f"Summary: {result['summary']}")
```

---

### get_directory_tree()

Get MT5 directory structure and file counts.

**Returns:**
```python
{
    "status": "success" | "error",
    "structure": {
        "terminal_path": str,
        "experts": {
            "path": str,
            "exists": bool,
            "file_count": int
        },
        "indicators": {...},
        "include": {...},
        "backups": {
            "path": str,
            "exists": bool,
            "backup_count": int
        }
    },
    "error": str | None
}
```

**Example:**
```python
from tools.files import get_directory_tree

result = get_directory_tree()
structure = result["structure"]
print(f"Terminal: {structure['terminal_path']}")
print(f"EAs: {structure['experts']['file_count']}")
print(f"Backups: {structure['backups']['backup_count']}")
```

---

## Class-based Usage

```python
from tools.files import MT5FileManager

# Create manager with custom path
manager = MT5FileManager("/custom/mt5/terminal/path")

# Or use default from config
manager = MT5FileManager()

# Use methods
result = manager.read_ea_file("MyEA")
result = manager.backup_ea("MyEA", tag="v1.0")
result = manager.list_eas("Experts")
```

## Backup Directory Structure

```
backups/
├── MyEA/
│   ├── 20250219_143025_manual/
│   │   └── MyEA.mq5
│   ├── 20250219_150230/
│   │   └── MyEA.mq5
│   └── 20250219_151500_before_test/
│       └── MyEA.mq5
└── AnotherEA/
    ├── 20250218_100000_manual/
    │   └── AnotherEA.mq5
    └── 20250219_090000/
        └── AnotherEA.mq5
```

## Error Handling

All functions return structured results. Check the `status` field:

```python
result = read_ea_file("MyEA")

if result["status"] == "success":
    # Process result
    print(result["content"])
else:
    # Handle error
    print(f"Error: {result['error']}")
```

## Best Practices

### 1. Always Backup Before Writing
```python
# Write automatically creates backup
result = write_ea_file("MyEA", new_code, backup=True)
assert result["backup_path"] is not None
```

### 2. Use Descriptive Tags
```python
backup_ea("MyEA", tag="before_adding_features")
backup_ea("MyEA", tag="v2.1_release")
```

### 3. Clean Backups Regularly
```python
# Keep 10 most recent backups per EA
clean_old_backups(keep_last=10)
```

### 4. Check Compilation Status
```python
eas = list_eas()
uncompiled = [f for f in eas["files"] if not f["has_compiled"]]
print(f"Uncompiled: {len(uncompiled)}")
```

### 5. Organize .set Files
```python
# Create profiles for different strategies
write_set_file("MyEA", "aggressive", aggressive_params)
write_set_file("MyEA", "conservative", conservative_params)
```

## Configuration

The manager reads MT5 paths from `config/mt5_paths.json`:

```json
{
    "mt5_experts": "C:\\Users\\...\\Terminal\\MQL5\\Experts",
    "mt5_data_path": "C:\\Users\\...\\Terminal"
}
```

## Dependencies

- Python 3.7+
- Standard library only (pathlib, shutil, json, datetime, logging)

## Platform Support

- ✅ Windows 7+
- ⚠️ macOS (requires custom MT5 paths)
- ⚠️ Linux (not officially supported by MT5)

## Logging

The module logs errors to the Python logger:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mt5_file_manager")
```

## License

Part of OpenClaw MT5 Automation Skill
