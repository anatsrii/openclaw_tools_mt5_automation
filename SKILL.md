# MT5 Automation Skill - Complete Guide

**OpenClaw Skill:** `mt5_automation`
**Version:** 2.0 (Phase 1 + Phase 2)
**Latest:** Production-ready with 10 integrated tools

---

## 📋 Quick Navigation

- [Overview](#overview) - What this skill does
- [10 Tools](#10-tools-summary) - All tools at a glance
- [Quick Start](#quick-start) - Get started in 5 minutes
- [Workflows](#common-workflows) - Copy-paste examples
- [Config](#configuration) - Setup instructions
- [Troubleshooting](#troubleshooting) - Common issues

---

## Overview

The **MT5 Automation Skill** provides complete system automation for MetaTrader 5:

✅ **Compile & Deploy** - Auto-fix compilation errors, deploy EA to charts
✅ **Backtest** - Run silent backtests with structured results
✅ **Optimize** - Parameter optimization with walk-forward validation
✅ **Trade** - Monitor positions, emergency close, profit/loss tracking
✅ **Monitor** - System health, bot status, account security
✅ **Notify** - Telegram, Line, Discord, Email alerts
✅ **Schedule** - Cron + market session-based scheduling
✅ **Analyze** - Log parsing, trade history, anomaly detection

### Architecture

```
Phase 2 Application Layer (5 tools)
  Developer, Operator, Tester, Optimizer, Manager
         ↓ (imports & uses)
Phase 1 Infrastructure Layer (5 tools)
  Process, Files, Logs, Notifier, Scheduler
```

---

## 10 Tools Summary

### Phase 1: Infrastructure (System Level)

| Tool | Purpose | Install | Key Functions |
|------|---------|---------|---------------|
| **Process Control** | Start/stop/monitor MT5 | Built-in | `start_mt5()`, `stop_mt5()`, `watch_mt5()` |
| **File Manager** | Manage EA + backups | Built-in | `read_ea_file()`, `backup_ea()`, `list_eas()` |
| **Log Parser** | Extract logs + trades | Built-in | `get_journal()`, `get_trades()`, `detect_anomalies()` |
| **Notifier** | Multi-channel alerts | `pip install requests` | `send()`, `send_trade_alert()`, `send_error()` |
| **Scheduler** | Market session + cron | `pip install apscheduler` | `get_session()`, `schedule_task()`, `is_open()` |

### Phase 2: Application (Business Logic)

| Tool | Purpose | Install | Key Functions |
|------|---------|---------|---------------|
| **Developer** | Compile + deploy EA | `pip install pyautogui` | `compile_ea()`, `deploy_ea()` |
| **Operator** | Live position management | `pip install MetaTrader5` | `get_positions()`, `close_all()` |
| **Tester** | Silent backtesting | Built-in | `run_backtest()`, `get_report()` |
| **Optimizer** | Parameter optimization | Built-in | `run_optimization()`, `walk_forward()` |
| **Manager** | System health + bots | Built-in | `get_health()`, `list_bots()` |

---

## Quick Start

### 1. Installation

```bash
# Core tools (no extra install)
cd ~ /.openclaw/tools/mt5_automation/

# Optional dependencies
pip install requests apscheduler MetaTrader5 pyautogui
```

### 2. Configure

Create `config/notify_settings.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "enabled_channels": ["telegram"],
  "min_severity": "info"
}
```

### 3. First Script

```python
from tools.process import start_mt5, get_mt5_status
from tools.notify import send
from tools.scheduler import get_current_session

# Ensure MT5 is running
if not get_mt5_status()["is_running"]:
    start_mt5()

# Check market session
session = get_current_session()
print(f"Session: {session['sessions']}")

# Send notification
send("✅ System online", severity="info")
```

### 4. Run Tests

```bash
python tests/test_all.py
```

---

## Common Workflows

### 🔧 Compile & Deploy EA

```python
from tools.developer import compile_and_fix, deploy_ea

# Compile with auto-fix loop
result = compile_and_fix("MyEA", max_attempts=3)
if result["success"]:
    deploy_ea("MyEA", "EURUSD", 240)  # 4H chart
    print("✅ Deployed!")
else:
    print(f"❌ {len(result['final_errors'])} errors remaining")
```

### 🚨 Emergency Close All

```python
from tools.operator import get_open_positions, close_all_positions
from tools.notify import send

positions = get_open_positions()
total_pnl = positions["total_pnl"]

if total_pnl < -1000:  # Lose more than $1000
    close_all_positions(comment="Risk limit exceeded!")
    send("🚨 Closed all positions!", severity="critical")
```

### 📊 Weekly Report

```python
from tools.logs import get_trade_history
from tools.operator import get_account_summary
from tools.notify import send_daily_report

trades = get_trade_history(hours=24*7)  # 1 week
account = get_account_summary()
wins = len([t for t in trades["trades"] if t["profit"] > 0])

send_daily_report(
    total_profit=sum(t["profit"] for t in trades["trades"]),
    trade_count=len(trades["trades"]),
    wins=wins,
    losses=len(trades["trades"]) - wins
)
```

### ⏰ Schedule Task at Market Open

```python
from tools.scheduler import schedule_task, wait_for_session

def start_trading():
    print("London session opened! Starting EA...")
    # trading logic here

# Option 1: Cron (specific time)
schedule_task(start_trading, "cron", cron_expr="14 * * * 1-5")

# Option 2: Wait for session to open
wait_for_session("London")
start_trading()
```

### 🔍 Continuous Monitoring

```python
from tools.process import watch_mt5
from tools.notify import send

def on_crash(event_type, data):
    if event_type == "crash_detected":
        send("🔴 MT5 crashed!", severity="critical")

# Watch and auto-restart
watch_mt5(interval=60, auto_restart=True, callback=on_crash)
```

---

## Configuration

### MT5 Paths: `config/mt5_paths.json`

Auto-detected on first run to:
- MT5 installation directory
- Terminal data folder
- MQL5 export paths

Manually edit if auto-detection fails:
```json
{
  "mt5_installation_path": "C:\\Program Files\\MetaTrader 5\\",
  "mt5_data_path": "C:\\Users\\YourName\\AppData\\Roaming\\MetaQuotes\\Terminal\\"
}
```

### Notifications: `config/notify_settings.json`

Each channel is optional:
```json
{
  "telegram": {
    "bot_token": "TOKEN",
    "chat_id": "CHAT_ID"
  },
  "line": {"token": "TOKEN"},
  "discord": {"webhook_url": "URL"},
  "email": {
    "smtp_server": "smtp.gmail.com",
    "sender_email": "you@gmail.com",
    "sender_password": "APP_PASSWORD"
  },
  "enabled_channels": ["telegram"],
  "min_severity": "info"
}
```

---

## API Quick Reference

### Process
```python
from tools.process import start_mt5, stop_mt5, get_mt5_status, watch_mt5
```

### Files
```python
from tools.files import read_ea_file, write_ea_file, backup_ea, restore_ea, list_eas
```

### Logs
```python
from tools.logs import get_latest_journal, get_trade_history, detect_anomalies
```

### Notify
```python
from tools.notify import send, send_trade_alert, send_daily_report, send_error
```

### Schedule
```python
from tools.scheduler import get_current_session, schedule_task, is_market_open
```

### Developer
```python
from tools.developer import compile_ea, compile_and_fix, deploy_ea
```

### Operator
```python
from tools.operator import get_open_positions, close_all_positions, get_account_summary
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "MT5 not found" | Update `config/mt5_paths.json` with correct path |
| "Telegram not working" | Run `test_connection("telegram")` to debug |
| "EA won't compile" | Check errors in `get_compile_errors()` output |
| "Backtest stuck" | Verify symbol exists and data is loaded |
| "Position close fails" | Check account status and ask for confirmation |
| "Notifications queue slow" | Disable `async_send=True` to send immediately |
| "Market session wrong" | Verify timezone in `config/settings.json` |

---

## File Structure

```
mt5_automation/
├── SKILL.md                  ← You are here
├── PHASE1_OVERVIEW.md        ← Infrastructure details
├── PHASE2_OVERVIEW.md        ← Application details
├── config/
│   ├── mt5_paths.json        ← Auto-detected paths
│   ├── notify_settings.json  ← Notification config
│   └── settings.json         ← Global settings
├── tools/
│   ├── process/              ← MT5 process control
│   ├── files/                ← File management
│   ├── logs/                 ← Log parsing
│   ├── notify/               ← Notifications
│   ├── scheduler/            ← Task scheduling
│   ├── developer/            ← EA compilation
│   ├── operator/             ← Live trading
│   ├── tester/               ← Backtesting
│   ├── optimizer/            ← Optimization
│   └── manager/              ← System health
└── tests/
    ├── test_all.py           ← Integration tests
    └── test_*.py             ← Individual tool tests
```

---

## Best Practices

1. **Always check MT5 before operations**
   ```python
   status = get_mt5_status()
   if not status["is_running"]:
       start_mt5()
       time.sleep(5)  # Wait to fully load
   ```

2. **Wrap in error handling**
   ```python
   result = compile_ea("MyEA")
   if result["status"] != "success":
       logger.error(result["error"])
       send_error("compile", result["error"])
   ```

3. **Back up before changes**
   ```python
   backup_ea("MyEA", tag="v1.0_before_optimization")
   # ... make changes ...
   ```

4. **Use session-aware scheduling**
   ```python
   task = schedule_task(trade_func, "session_open", session="London")
   ```

5. **Monitor important operations**
   ```python
   watch_mt5(auto_restart=True, callback=alert_on_crash)
   ```

---

## Support

- **Repository:** https://github.com/anatsrii/openclaw_tools_mt5_automation
- **Issues:** Create issue on GitHub
- **Tests:** `python tests/test_all.py`

---

**Version:** 2.0 | **Author:** anatsrii | **License:** MIT

