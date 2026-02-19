# MT5 Log Parser Tool

Parse and analyze MetaTrader 5 log files for trading data, errors, and diagnostics.

## Overview

The `mt5_log_parser` module provides real-time log monitoring and parsing for:
- Journal entry reading and searching
- Compile error extraction
- Trade history analysis
- EA Print() output extraction
- Real-time log monitoring
- Error and anomaly detection

## Features

- ✅ Read latest journal entries with metadata
- ✅ Parse and extract compile errors and warnings
- ✅ Extract trade history with profit/loss
- ✅ Real-time journal monitoring (tail -f)
- ✅ EA Print() output extraction by EA
- ✅ Anomaly detection (connection lost, margin calls, etc.)
- ✅ Keyword-based filtering
- ✅ Full error handling with structured results
- ✅ Configurable time ranges

## Log File Locations

```
MT5 Terminal/
├── logs/
│   ├── 20250219.log   # Today's journal
│   ├── 20250218.log
│   └── ...
└── tester/
    └── logs/          # Strategy tester logs
```

## Installation

See `REQUIREMENTS.md` for dependencies.

```bash
pip install -r tools/logs/REQUIREMENTS.md
```

## API Reference

### get_latest_journal(lines=100)

Read last N lines from today's journal.

**Parameters:**
- `lines` (int): Number of lines to read (default: 100)

**Returns:**
```python
{
    "status": "success" | "error",
    "entries": [
        {
            "timestamp": str,      # ISO format
            "type": str,           # "info", "error", "warning"
            "source": str,         # "Expert", "System", "Account"
            "message": str
        }
    ],
    "file_path": str,
    "total_lines": int,
    "error": str | None
}
```

**Example:**
```python
from tools.logs import get_latest_journal

result = get_latest_journal(lines=50)
for entry in result["entries"]:
    print(f"{entry['timestamp']} [{entry['type']}] {entry['message']}")
```

---

### get_compile_errors(ea_name)

Extract compile errors and warnings for specific EA.

**Parameters:**
- `ea_name` (str): EA name (with or without .mq5)

**Returns:**
```python
{
    "status": "success" | "error",
    "errors": [
        {
            "line": int,           # Line number in source
            "error_code": str,     # Error/warning code
            "message": str,
            "is_error": bool,
            "is_warning": bool
        }
    ],
    "error_count": int,
    "warning_count": int,
    "error": str | None
}
```

**Example:**
```python
from tools.logs import get_compile_errors

result = get_compile_errors("MyEA")
print(f"Errors: {result['error_count']}, Warnings: {result['warning_count']}")
for err in result["errors"]:
    print(f"  Line {err['line']}: {err['message']}")
```

---

### get_trade_history(hours=24)

Extract trade events from journal.

**Parameters:**
- `hours` (int): Look back N hours (default: 24)

**Returns:**
```python
{
    "status": "success" | "error",
    "trades": [
        {
            "time": str,          # ISO format
            "action": str,        # "BUY", "SELL", "CLOSE", etc.
            "symbol": str,
            "volume": float,
            "price": float,
            "profit": float | None
        }
    ],
    "trade_count": int,
    "error": str | None
}
```

**Example:**
```python
from tools.logs import get_trade_history

result = get_trade_history(hours=48)
for trade in result["trades"]:
    profit_str = f"+{trade['profit']}" if trade['profit'] > 0 else str(trade['profit'])
    print(f"{trade['time']} {trade['action']} {trade['symbol']} {trade['volume']} @ {trade['price']} ({profit_str})")
```

---

### get_ea_prints(ea_name, hours=4)

Extract Print() output from specific EA.

**Parameters:**
- `ea_name` (str): EA name (with or without .mq5)
- `hours` (int): Look back N hours (default: 4)

**Returns:**
```python
{
    "status": "success" | "error",
    "prints": [
        {
            "timestamp": str,    # ISO format
            "message": str
        }
    ],
    "count": int,
    "error": str | None
}
```

**Example:**
```python
from tools.logs import get_ea_prints

result = get_ea_prints("MyEA", hours=2)
for print_entry in result["prints"]:
    print(f"{print_entry['timestamp']} | {print_entry['message']}")
```

---

### watch_journal(callback_fn, filter_keywords=None)

Monitor journal file in real-time (like `tail -f`).

**Parameters:**
- `callback_fn` (callable): Function called for each new entry: `callback(entry)`
- `filter_keywords` (list, optional): Only trigger on lines containing keywords
- `check_interval` (float): Check interval in seconds (default: 0.5)

**Callback Entry Structure:**
```python
{
    "timestamp": str,
    "type": str,
    "source": str,
    "message": str
}
```

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
from tools.logs import watch_journal, stop_watch
import time

def on_journal_entry(entry):
    if entry["type"] == "error":
        print(f"❌ ERROR: {entry['message']}")
    elif entry["type"] == "warning":
        print(f"⚠️  WARNING: {entry['message']}")

# Start watching
watch_journal(on_journal_entry, filter_keywords=["error", "warning"])

# Watch for 5 minutes
time.sleep(300)

# Stop watching
stop_watch()
```

---

### detect_anomalies(hours=1)

Detect error conditions in logs.

**Parameters:**
- `hours` (int): Look back N hours (default: 1)

**Returns:**
```python
{
    "status": "success" | "error",
    "anomalies": [
        {
            "type": str,         # connection_lost, invalid_account, margin_call, server_error
            "severity": str,     # "critical", "warning"
            "message": str,
            "timestamp": str,
            "count": int         # How many times detected
        }
    ],
    "error": str | None
}
```

**Example:**
```python
from tools.logs import detect_anomalies

result = detect_anomalies(hours=24)
if result["anomalies"]:
    print("⚠️  ANOMALIES DETECTED:")
    for anomaly in result["anomalies"]:
        severity = "🔴" if anomaly["severity"] == "critical" else "🟡"
        print(f"{severity} {anomaly['type']} ({anomaly['count']}x): {anomaly['message']}")
```

---

### stop_watch()

Stop real-time journal monitoring.

**Returns:**
```python
{
    "status": "success",
    "message": str
}
```

---

## Class-based Usage

```python
from tools.logs import MT5LogParser

# Create parser with custom path
parser = MT5LogParser("/custom/mt5/terminal/path")

# Or use default from config
parser = MT5LogParser()

# Use methods
journal = parser.get_latest_journal(lines=100)
errors = parser.get_compile_errors("MyEA")
trades = parser.get_trade_history(hours=48)
anomalies = parser.detect_anomalies(hours=1)
```

## Log Format

MT5 logs use the format:
```
[2025.02.19 14:30:45.123] message text here
[2025.02.19 14:30:46.456] another message
```

The parser:
- Extracts timestamp and message
- Detects type (error, warning, info)
- Identifies source (Expert, System, Account)
- Converts timestamp to ISO format

## Real-time Monitoring Example

```python
from tools.logs import watch_journal, stop_watch
import time

errors_found = []

def on_entry(entry):
    if entry["type"] == "error":
        errors_found.append(entry)
        print(f"🔴 Error: {entry['message']}")

# Start watching
watch_journal(on_entry)

# Simulate work
time.sleep(60)

# Check results
print(f"Found {len(errors_found)} errors")

# Stop watching
stop_watch()
```

## Advanced: Filtered Monitoring

```python
from tools.logs import watch_journal

def handle_trade_events(entry):
    if "BUY" in entry["message"] or "SELL" in entry["message"]:
        print(f"Trade: {entry['message']}")

# Watch only trade-related entries
watch_journal(
    handle_trade_events,
    filter_keywords=["BUY", "SELL", "CLOSE", "OPEN"]
)
```

## Error Handling

```python
result = get_latest_journal()

if result["status"] == "success":
    print(f"Read {len(result['entries'])} entries")
    for entry in result["entries"]:
        # Process entry
        pass
else:
    print(f"Error: {result['error']}")
```

## Performance Notes

- Journal file can be large (hundreds of MB)
- Reading full history is slower than recent entries
- Real-time monitoring uses polling (0.5s default)
- Consider using filters for monitoring to reduce overhead

## Dependencies

- Python 3.7+
- Standard library (re, datetime, collections, threading, pathlib)
- Optional: watchdog (for advanced file monitoring)

## Detected Anomalies

The `detect_anomalies()` function looks for:
- **connection_lost** - Connection to server lost
- **invalid_account** - Invalid account or password
- **margin_call** - Margin issues
- **server_error** - General server errors

## Troubleshooting

### "Journal not found" error
- Verify MT5 is running (creates journal on startup)
- Journal file name is YYYYMMDD.log (changes daily at midnight)

### Missing trade history
- Trade entries must be logged by MT5
- Check that Expert/OrderLog is enabled in MT5 settings
- Some trade actions may not be logged

### EA Prints not found
- EA must use Print() function
- Print output only shown if "Print" is enabled in MT5
- Ensure EA has been running recently

## Limitations

- Depends on MT5 logging output (can be incomplete)
- Performance degrades with very large log files
- Real-time monitoring has 0.5s latency minimum
- Some trading events may not be logged to journal

## License

Part of OpenClaw MT5 Automation Skill
