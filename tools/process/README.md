# MT5 Process Control Tool

Control and monitor MetaTrader 5 (MT5) process on Windows.

## Overview

The `mt5_process_control` module provides a complete toolkit for managing MT5 process lifecycle on Windows systems. All functions return structured dictionaries with status information—no exceptions are raised to the caller.

## Features

- ✅ Start MT5 with optional account selection
- ✅ Stop MT5 gracefully or forcefully
- ✅ Restart MT5 with configurable wait time
- ✅ Check MT5 process status and responsiveness
- ✅ Background monitoring with auto-restart capability
- ✅ Event notifications via callback functions
- ✅ Thread-safe operations
- ✅ Comprehensive error handling

## Installation

See `REQUIREMENTS.md` for dependency installation.

## Usage

### Basic Usage (Function-based)

```python
from tools.process import start_mt5, stop_mt5, get_mt5_status

# Start MT5
result = start_mt5(minimized=True)
print(f"Status: {result['status']}, PID: {result['pid']}")

# Get status
status = get_mt5_status()
print(f"Running: {status['is_running']}, Responsive: {status['is_responsive']}")

# Stop MT5
result = stop_mt5(force=False)
print(f"Was running: {result['was_running']}")
```

### Advanced Usage (Class-based)

```python
from tools.process import MT5ProcessControl

# Create controller
controller = MT5ProcessControl()

# Start with specific account
result = controller.start_mt5(account_id="12345678")
print(result)

# Restart
result = controller.restart_mt5(wait_seconds=5)
print(f"New PID: {result['new_pid']}")

# Monitor with callback
def on_event(event_type, data):
    print(f"Event: {event_type} - {data}")

controller.watch_mt5(interval=30, auto_restart=True, callback=on_event)

# ... later ...
controller.stop_watch()
```

## API Reference

### start_mt5(account_id=None, minimized=True)

Launch MT5.exe and wait for it to fully load.

**Parameters:**
- `account_id` (str, optional): MT5 account ID/login number
- `minimized` (bool): Launch in minimized window (default: True)

**Returns:**
```python
{
    "status": "success" | "error",
    "pid": int | None,              # Process ID
    "startup_time": float,           # Seconds to load
    "message": str,
    "error": str | None
}
```

**Example:**
```python
result = start_mt5(account_id="12345678")
if result["status"] == "success":
    print(f"MT5 started with PID {result['pid']}")
```

---

### stop_mt5(force=False)

Close the MT5 process.

**Parameters:**
- `force` (bool): Use taskkill for forced termination (default: False)

**Returns:**
```python
{
    "status": "success" | "error",
    "was_running": bool,
    "message": str,
    "error": str | None
}
```

**Example:**
```python
# Graceful close
result = stop_mt5(force=False)

# Force kill if needed
if not result["status"] == "success":
    result = stop_mt5(force=True)
```

---

### restart_mt5(wait_seconds=5)

Stop and restart MT5 process.

**Parameters:**
- `wait_seconds` (int): Wait time between stop and start (default: 5)

**Returns:**
```python
{
    "status": "success" | "error",
    "new_pid": int | None,
    "total_time": float,             # Total restart time
    "message": str,
    "error": str | None
}
```

**Example:**
```python
result = restart_mt5(wait_seconds=3)
print(f"Restarted in {result['total_time']:.1f} seconds")
```

---

### get_mt5_status()

Check if MT5 is running and responsive.

**Returns:**
```python
{
    "is_running": bool,
    "is_responsive": bool,           # Not frozen
    "pid": int | None,
    "uptime_minutes": float,
    "message": str,
    "error": str | None
}
```

**Example:**
```python
status = get_mt5_status()
if status["is_running"]:
    print(f"MT5 running for {status['uptime_minutes']:.1f} minutes")
    if not status["is_responsive"]:
        print("WARNING: MT5 appears to be frozen!")
```

---

### watch_mt5(interval=60, auto_restart=True, callback=None)

Start background monitoring thread.

**Parameters:**
- `interval` (int): Check interval in seconds (default: 60)
- `auto_restart` (bool): Automatically restart if crash detected (default: True)
- `callback` (callable): Callback function(event_type, data) for notifications

**Callback Events:**
- `"crash_detected"`: MT5 process terminated unexpectedly
- `"auto_restart"`: Auto-restart was triggered
- `"unresponsive"`: MT5 window is not responding
- `"watch_error"`: Error occurred in watch loop

**Returns:**
```python
{
    "status": "success" | "error",
    "message": str,
    "error": str | None
}
```

**Example:**
```python
def handle_event(event_type, data):
    if event_type == "crash_detected":
        print(f"MT5 crashed! PID was {data['last_pid']}")
    elif event_type == "auto_restart":
        print(f"Auto-restart #{data['restart_count']} triggered")
    elif event_type == "unresponsive":
        print(f"MT5 not responding (PID {data['pid']})")

watch_mt5(interval=30, auto_restart=True, callback=handle_event)

# ... monitor for a while ...

stop_watch()
```

---

### stop_watch()

Stop the background monitoring thread.

**Returns:**
```python
{
    "status": "success",
    "message": str
}
```

---

## Return Value Structure

All functions return dictionaries with:
- `status`: "success" or "error"
- `message`: Human-readable status message
- `error`: Error details if status is "error", otherwise None
- Additional fields specific to each function

**Key Principle:** Functions never raise exceptions. Check the `status` field and `error` field for error conditions.

## Error Handling

```python
result = start_mt5()

if result["status"] == "success":
    print("MT5 started")
else:
    print(f"Failed to start MT5: {result['error']}")
```

## Example: Monitoring Script

```python
import time
from tools.process import watch_mt5, stop_watch, get_mt5_status

def notification_callback(event_type, data):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {event_type}: {data}")

# Start monitoring
watch_mt5(
    interval=30,           # Check every 30 seconds
    auto_restart=True,     # Auto-restart on crash
    callback=notification_callback
)

# Keep watching
try:
    while True:
        time.sleep(60)
        status = get_mt5_status()
        print(f"Status: {status['message']}")
except KeyboardInterrupt:
    print("Stopping watch...")
    stop_watch()
```

## Configuration Files

The module reads configuration from:
- `config/user_config.json` - ⭐ ไฟล์หลัก แก้ที่นี่ที่เดียว (path, username, terminal_id)
- `config/config.py` - Central config — build paths จาก user_config อัตโนมัติ
- `config/mt5_paths.json` - Backward compat (auto-generated, อย่าแก้ตรงๆ)
- `config/settings.json` - Global settings (logging, timeouts, timezone)

## Dependencies

- Python 3.7+
- `psutil` - Process management
- `pywin32` - Windows-specific operations
- Windows OS (7+)

## Platform Support

- ✅ Windows 7+
- ❌ macOS (requires alternative paths)
- ❌ Linux (MT5 not officially supported)

## Troubleshooting

### MT5 executable not found
- Verify MT5 is installed in the default location
- Update `config/mt5_paths.json` with custom installation path

### Window detection timeout
- MT5 may be slow to load
- Increase `startup_timeout` in `config/settings.json`

### Permission denied on process termination
- Run as Administrator for force kill to work
- Some antivirus software may block process termination

### pywin32 window operations not working
- Ensure `pywin32_postinstall.py -install` was run
- Restart Python after installation

## License

Part of OpenClaw MT5 Automation Skill
