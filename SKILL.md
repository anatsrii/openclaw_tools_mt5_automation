# MT5 Automation Skill - Complete Guide

**OpenClaw Skill:** `mt5_automation`
**Version:** 3.0 (Central Config + Completed Phase 2)
**Updated:** 2026-02

---

## 📋 Quick Navigation

- [Overview](#overview)
- [Quick Setup](#quick-setup) ← เริ่มที่นี่
- [user_config.json](#user_configjson--ไฟล์ตั้งค่าหลัก) ← แก้ไฟล์เดียวจบ
- [10 Tools](#10-tools-summary)
- [Workflows](#common-workflows)
- [API Reference](#api-quick-reference)
- [Troubleshooting](#troubleshooting)

---

## Overview

ระบบ automation ครบวงจรสำหรับ MetaTrader 5 บน Windows

```
✅ Compile & Deploy   — เขียน/แก้ EA, compile, deploy ลง chart
✅ Backtest           — รัน Strategy Tester แบบ silent
✅ Optimize           — หา parameter ที่ดีที่สุด + Walk-Forward
✅ Trade              — ดู position, emergency close, PnL
✅ Monitor            — สุขภาพระบบ, bot status, account
✅ Notify             — Telegram, Line, Email
✅ Schedule           — Cron + market session-based
✅ Analyze            — อ่าน log, trade history, anomaly detection
```

### Architecture

```
┌─────────────────────────────────────────────┐
│          user_config.json                   │  ← แก้ที่นี่ที่เดียว
│   (symbol, path, terminal_id, dates, ...)   │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│          config/config.py                   │  ← build paths อัตโนมัติ
└──────────────────┬──────────────────────────┘
                   │
       ┌───────────┴────────────┐
       ▼                        ▼
Phase 1: Infrastructure    Phase 2: Application
  process, files, logs       developer, tester,
  notify, scheduler          optimizer, manager,
                             operator
```

---

## Quick Setup

### 1. ติดตั้ง Dependencies

```bash
pip install MetaTrader5 psutil pywin32 pyautogui watchdog APScheduler requests python-dateutil
```

### 2. ตั้งค่า (แค่ไฟล์เดียว)

แก้ไขที่ `config/user_config.json` เท่านั้น:

```json
{
  "mt5": {
    "terminal_id": "ใส่ Terminal ID ของคุณ",
    "installation_path": "C:\\Program Files\\MetaTrader 5",
    "username": "ชื่อ Windows user ของคุณ"
  },
  "trading": {
    "default_symbol": "XAUUSDm",
    "default_timeframe": 1
  }
}
```

> **หา Terminal ID:** เปิด `C:\Users\[username]\AppData\Roaming\MetaQuotes\Terminal\`
> โฟลเดอร์ชื่อยาวๆ ที่อยู่ในนั้นคือ Terminal ID

### 3. ตั้งค่า Telegram (optional)

แก้ `config/notify_settings.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "enabled_channels": ["telegram"]
}
```

### 4. Validate

```bash
python config/config.py
```

ผลลัพธ์ที่ควรเห็น:
```
=== MT5 Config Summary ===
Terminal ID : D0E82...FF075 (your terminal ID)
Install     : C:\Program Files\MetaTrader 5
...
=== Path Validation ===
  ✅ terminal.exe
  ✅ data_path
  ✅ experts_path
  ✅ All paths OK
```

### 5. รัน Tests

```bash
python tests/test_all.py
```

---

## `user_config.json` — ไฟล์ตั้งค่าหลัก

> แก้ไฟล์นี้ไฟล์เดียว ทั้งระบบอัปเดตทันที ไม่ต้องแตะโค้ดอื่น

```json
{
  "mt5": {
    "terminal_id": "YOUR_TERMINAL_ID",               ← Terminal ID
    "installation_path": "C:\\Program Files\\MetaTrader 5", ← ที่ติดตั้ง MT5
    "username": "YOUR_WINDOWS_USERNAME"                  ← Windows username
  },

  "trading": {
    "default_symbol": "XAUUSDm",      ← คู่เหรียญ default
    "default_timeframe": 1,           ← TF เป็นนาที (1=M1, 5=M5, ...)
    "symbols": ["XAUUSDm", "XAUUSDm.c"], ← รายการคู่เหรียญทั้งหมด
    "default_date_from": "2024.01.01",   ← วันเริ่ม backtest
    "default_date_to": "2024.12.31"      ← วันสิ้นสุด backtest
  },

  "backtest": {
    "deposit": 10000,      ← เงินทุนจำลอง (USD)
    "currency": "USD",
    "leverage": 100,       ← leverage
    "model": 1,            ← 0=Every tick, 1=1min OHLC, 2=Open price
    "timeout_seconds": 300 ← timeout ต่อ 1 backtest
  },

  "optimization": {
    "top_n_results": 10,            ← คืนผลลัพธ์ top N
    "criterion": 2,                 ← 0=Balance, 1=DD, 2=ProfitFactor, 3=Sharpe
    "wf_windows": 4,               ← จำนวน window สำหรับ Walk-Forward
    "wf_test_ratio": 0.3,          ← สัดส่วน Out-of-Sample (30%)
    "wf_efficiency_threshold": 0.7, ← เกณฑ์ "robust" (70%)
    "timeout_per_window": 900       ← timeout ต่อ 1 window (วินาที)
  }
}
```

### กรณีที่ต้องแก้ไข

| สถานการณ์ | แก้ key ไหน |
|-----------|-------------|
| เปลี่ยนโบรกเกอร์ (Terminal ID ใหม่) | `mt5.terminal_id` |
| ย้ายเครื่อง / reinstall MT5 | `mt5.installation_path`, `mt5.username` |
| เปลี่ยนคู่เหรียญที่ test | `trading.default_symbol`, `trading.symbols` |
| เปลี่ยนช่วงเวลา backtest | `trading.default_date_from/to` |
| เปลี่ยน capital สำหรับ test | `backtest.deposit`, `backtest.leverage` |
| ปรับ Walk-Forward windows | `optimization.wf_windows` |

---

## 10 Tools Summary

### Phase 1: Infrastructure

| Tool | Purpose | Key Functions |
|------|---------|---------------|
| **process** | Start/stop/monitor MT5 | `start_mt5()`, `stop_mt5()`, `watch_mt5()` |
| **files** | จัดการไฟล์ EA + backup | `read_ea_file()`, `backup_ea()`, `list_eas()` |
| **logs** | อ่าน journal + trade log | `get_latest_journal()`, `get_trade_history()`, `detect_anomalies()` |
| **notify** | ส่ง alert ทุกช่องทาง | `send()`, `send_trade_alert()`, `send_daily_report()` |
| **scheduler** | Market session + cron | `get_current_session()`, `schedule_task()`, `is_market_open()` |

### Phase 2: Application

| Tool | Purpose | Key Functions | สถานะ |
|------|---------|---------------|--------|
| **developer** | Compile + deploy EA | `compile_ea()`, `compile_and_fix()`, `deploy_ea()` | ✅ |
| **tester** | Silent backtesting | `run_backtest()`, `run_multi_backtest()`, `get_tester_report()` | ✅ |
| **optimizer** | Parameter optimization + WF | `run_optimization()`, `walk_forward_test()` | ✅ |
| **manager** | System health + account | `get_system_health()`, `list_active_bots()`, `switch_account()` | ✅ |
| **operator** | Live trade management | `get_open_positions()`, `close_all_positions()`, `get_account_summary()` | ✅ |

---

## Common Workflows

### 🔧 Compile & Deploy EA

```python
from tools.developer import compile_and_fix, deploy_ea

result = compile_and_fix("SukarEA", max_attempts=3)
if result["success"]:
    deploy_ea("SukarEA", "XAUUSDm", 1)  # M1 chart
    print("✅ Deployed!")
else:
    print(f"❌ Errors: {result['final_errors']}")
```

---

### 📊 Backtest (ใช้ค่า default จาก user_config.json)

```python
from tools.tester import run_backtest

# ใช้ค่า default ทั้งหมด (XAUUSDm, M1, ช่วงวันที่ที่ตั้งไว้)
result = run_backtest("SukarEA")

# Override เฉพาะบางค่า
result = run_backtest("SukarEA", symbol="XAUUSDm.c", date_from="2025.01.01")

print(f"PF={result['profit_factor']:.2f} | DD={result['drawdown']:.1f}% | Trades={result['total_trades']}")
```

---

### ⚙️ Optimize + Walk-Forward

```python
from tools.optimizer import run_optimization, walk_forward_test

param_ranges = {
    "TakeProfit":  (20, 100, 5),   # min, max, step
    "StopLoss":    (10, 60, 5),
    "FastEMA":     (5, 20, 1),
    "SlowEMA":     (20, 50, 5),
}

# Optimize (ใช้ symbol + dates จาก user_config)
opt = run_optimization("SukarEA", param_ranges)
print(f"Best PF: {opt['top_params'][0]['profit_factor']}")

# Walk-Forward (ใช้ค่า default ทั้งหมด)
wf = walk_forward_test("SukarEA", param_ranges)
print(f"WF Efficiency: {wf['wf_efficiency']:.2f}")
print(f"Robust: {'✅' if wf['summary']['is_robust'] else '⚠️ ไม่แนะนำใช้ live'}")
```

---

### 🚨 Emergency Close All

```python
from tools.operator import get_open_positions, close_all_positions
from tools.notify import send

positions = get_open_positions()
if positions["total_pnl"] < -500:
    result = close_all_positions(comment="Risk limit exceeded")
    send(f"🚨 Closed {result['closed_count']} positions", severity="critical")
```

---

### 🩺 System Health Check

```python
from tools.manager import get_system_health, list_active_bots

health = get_system_health()
print(f"Status    : {health['status']}")          # healthy / degraded / critical
print(f"MT5       : {'✅' if health['mt5_running'] else '❌'}")
print(f"Session   : {health['current_session']}")
print(f"Active EAs: {health['active_bots']}")

if health["issues"]:
    for issue in health["issues"]:
        print(f"⚠️  {issue}")
```

---

### ⏰ Schedule Task

```python
from tools.scheduler import schedule_task, wait_for_session
from tools.tester import run_backtest

# รัน backtest ทุกวันตี 4
def weekly_backtest():
    run_backtest("SukarEA")

schedule_task(weekly_backtest, "cron", cron_expr="0 4 * * 1")  # ทุกวันจันทร์ ตี 4

# รอ London session เปิด
wait_for_session("London")
print("London opened!")
```

---

### 🔄 Continuous Monitoring

```python
from tools.process import watch_mt5
from tools.notify import send

def on_crash(event_type, data):
    if event_type == "crash_detected":
        send("🔴 MT5 crashed! Restarting...", severity="critical")

watch_mt5(interval=60, auto_restart=True, callback=on_crash)
```

---

## API Quick Reference

```python
# Infrastructure (Phase 1)
from tools.process    import start_mt5, stop_mt5, restart_mt5, get_mt5_status, watch_mt5
from tools.files      import read_ea_file, write_ea_file, backup_ea, restore_ea, list_eas
from tools.logs       import get_latest_journal, get_trade_history, detect_anomalies, get_compile_errors
from tools.notify     import send, send_trade_alert, send_daily_report, send_error
from tools.scheduler  import get_current_session, schedule_task, is_market_open, wait_for_session

# Application (Phase 2)
from tools.developer  import compile_ea, compile_and_fix, deploy_ea
from tools.tester     import run_backtest, run_multi_backtest, get_tester_report
from tools.optimizer  import run_optimization, walk_forward_test
from tools.manager    import get_system_health, list_active_bots, switch_account, get_connection_quality
from tools.operator   import get_open_positions, close_all_positions, get_account_summary

# Central Config
from config.config    import get_config
cfg = get_config()
print(cfg.default_symbol)   # XAUUSDm
print(cfg.experts_path)     # Path object
```

---

## Configuration Files

| ไฟล์ | วัตถุประสงค์ | แก้เองได้? |
|------|------------|-----------|
| `config/user_config.json` | ตั้งค่าทั้งหมด (symbol, path, dates, ...) | ✅ แก้ที่นี่เท่านั้น |
| `config/config.py` | อ่าน user_config แล้ว build paths | ❌ อย่าแก้ |
| `config/mt5_paths.json` | Paths สำหรับ backward compat | ❌ auto-generated |
| `config/notify_settings.json` | Telegram/Line tokens | ✅ ใส่ token ของตัวเอง |
| `config/settings.json` | Logging, scheduler settings | ✅ ถ้าต้องการ |

---

## File Structure

```
mt5_automation/
├── SKILL.md                    ← คู่มือนี้
├── PHASE2_OVERVIEW.md          ← รายละเอียด Phase 2
├── config/
│   ├── user_config.json        ← ⭐ แก้ที่นี่ที่เดียว
│   ├── config.py               ← central config (อย่าแก้)
│   ├── config_auto.py          ← auto-detect paths
│   ├── mt5_paths.json          ← auto-generated
│   ├── notify_settings.json    ← ใส่ Telegram token
│   └── settings.json           ← logging, timezone
├── tools/
│   ├── process/                ← MT5 process control
│   ├── files/                  ← file management
│   ├── logs/                   ← log parsing
│   ├── notify/                 ← notifications
│   ├── scheduler/              ← task scheduling
│   ├── developer/              ← EA compilation
│   ├── operator/               ← live trading
│   ├── tester/                 ← backtesting
│   ├── optimizer/              ← optimization
│   └── manager/                ← system health
└── tests/
    ├── test_all.py
    └── test_*.py
```

---

## Best Practices

**1. เช็ค MT5 ก่อนทำงานทุกครั้ง**
```python
from tools.process import get_mt5_status, start_mt5
status = get_mt5_status()
if not status["is_running"]:
    start_mt5()
```

**2. Backup ก่อนแก้ EA**
```python
backup_ea("SukarEA", tag="before_optimization")
```

**3. ใช้ Walk-Forward ก่อน live เสมอ**
```python
wf = walk_forward_test("SukarEA", param_ranges)
if not wf["summary"]["is_robust"]:
    print("⚠️ ไม่แนะนำ — WF efficiency ต่ำกว่า 70%")
```

**4. ตั้ง Emergency Monitor**
```python
watch_mt5(auto_restart=True, callback=on_crash)
```

---

## Troubleshooting

| ปัญหา | วิธีแก้ |
|-------|---------|
| "MT5 not found" | เช็ค `mt5.installation_path` ใน `user_config.json` |
| "Terminal data not found" | เช็ค `mt5.terminal_id` และ `mt5.username` |
| "Telegram not working" | เช็ค `notify_settings.json` — bot_token และ chat_id |
| "Backtest timeout" | เพิ่ม `backtest.timeout_seconds` ใน `user_config.json` |
| "No report found" | ตรวจว่า MT5 run backtest จบแล้ว / เช็ค `mt5_tester` path |
| "MT5 API not connected" | รัน `pip install MetaTrader5` และเปิด MT5 ก่อน |
| "Wrong session time" | เช็ค `timezone: Asia/Bangkok` ใน `settings.json` |

---

**Version:** 3.0 | **Author:** anatsrii | **License:** MIT
