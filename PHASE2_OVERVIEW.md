# MT5 Automation - Phase 2: Application Layer

**Version:** 3.0 | สถานะ: ✅ Implemented ทั้งหมดแล้ว

---

## Architecture

```
config/user_config.json          ← ⭐ ตั้งค่าที่นี่ที่เดียว
        │
        ▼
config/config.py (MT5Config)     ← build paths + variables อัตโนมัติ
        │
        ├──────────────────────────────────────┐
        ▼                                      ▼
Phase 1: Infrastructure               Phase 2: Application
─────────────────────────             ─────────────────────────
mt5_process_control  ──────────────→  mt5_developer
mt5_file_manager     ──────────────→  mt5_tester
mt5_log_parser       ──────────────→  mt5_optimizer
mt5_notifier         ──────────────→  mt5_manager
mt5_scheduler        ──────────────→  mt5_operator
```

---

## Tool Details

### 2.1 MT5 Developer ✅
**ไฟล์:** `tools/developer/mt5_developer.py`
**วัตถุประสงค์:** Compile EA พร้อม self-healing และ deploy ลง chart

| Function | Description |
|----------|-------------|
| `compile_ea(ea_name)` | Compile และ return errors list |
| `compile_and_fix(ea_name, max_attempts=3)` | Loop compile จนสำเร็จหรือหมด attempt |
| `deploy_ea(ea_name, symbol, timeframe)` | Attach EA ลง chart ที่ระบุ |

**Dependencies:** mt5_file_manager, mt5_log_parser, mt5_process_control, mt5_notifier

---

### 2.2 MT5 Tester ✅
**ไฟล์:** `tools/tester/mt5_tester.py`
**วัตถุประสงค์:** รัน Strategy Tester แบบ silent และ parse ผลลัพธ์

| Function | Description |
|----------|-------------|
| `run_backtest(ea_name, symbol?, timeframe?, date_from?, date_to?, ...)` | รัน backtest — ถ้าไม่ระบุ args ใช้ค่าจาก `user_config.json` |
| `run_multi_backtest(ea_name, configs)` | รัน backtest หลาย config ต่อเนื่อง sort by PF |
| `get_tester_report(ea_name)` | Parse HTML report คืน stats dict |

**Default values จาก user_config.json:**
- `symbol` → `trading.default_symbol`
- `timeframe` → `trading.default_timeframe`
- `date_from/to` → `trading.default_date_from/to`
- `deposit/leverage` → `backtest.deposit/leverage`
- `timeout` → `backtest.timeout_seconds`

**Dependencies:** mt5_file_manager, mt5_process_control, mt5_log_parser, mt5_notifier

---

### 2.3 MT5 Optimizer ✅
**ไฟล์:** `tools/optimizer/mt5_optimizer.py`
**วัตถุประสงค์:** Parameter optimization + Walk-Forward validation

| Function | Description |
|----------|-------------|
| `run_optimization(ea_name, param_ranges, symbol?, periods?, top_n?)` | รัน optimization คืน top N params |
| `walk_forward_test(ea_name, param_ranges, symbol?, date_from?, date_to?, ...)` | IS optimize → OOS validate หลาย window |

**Walk-Forward Logic:**
```
ช่วงเวลาทั้งหมด ──→ แบ่งเป็น N windows
แต่ละ window:
  ├── IS (In-Sample, 70%) → run_optimization → ได้ best params
  └── OOS (Out-of-Sample, 30%) → run_backtest ด้วย best params

WF Efficiency = avg(OOS PF) / avg(IS PF)
Robust = WF Efficiency ≥ 0.7 (70%)
```

**Default values จาก user_config.json:**
- `symbol` → `trading.default_symbol`
- `periods` → `trading.default_date_from/to`
- `top_n` → `optimization.top_n_results`
- `n_windows` → `optimization.wf_windows`
- `test_ratio` → `optimization.wf_test_ratio`

**Dependencies:** mt5_file_manager, mt5_process_control, mt5_notifier

---

### 2.4 MT5 Manager ✅
**ไฟล์:** `tools/manager/mt5_manager.py`
**วัตถุประสงค์:** System health monitoring และ account management

| Function | Description |
|----------|-------------|
| `get_system_health()` | Aggregate: MT5 status + session + account + active bots |
| `list_active_bots()` | Scan charts ผ่าน MT5 API + win32gui fallback |
| `switch_account(account_id, password, server)` | Switch account + verify login |
| `get_connection_quality()` | เช็ค ping + data availability |

**Health Status Levels:**
- `healthy` — ทุกอย่างปกติ
- `degraded` — MT5 รันแต่ไม่ responsive
- `critical` — MT5 ดับ หรือ margin level ต่ำกว่า 150%

**Dependencies:** mt5_process_control, mt5_notifier, mt5_scheduler, MetaTrader5, pywin32

---

### 2.5 MT5 Operator ✅
**ไฟล์:** `tools/operator/mt5_operator.py`
**วัตถุประสงค์:** Live trade management และ emergency controls

| Function | Description |
|----------|-------------|
| `get_open_positions(symbol?)` | ดู open positions ทั้งหมด พร้อม PnL |
| `close_all_positions(symbol?, comment?)` | ปิดทุก position ทันที + notify |
| `get_account_summary()` | Balance, equity, margin, drawdown% |

**Dependencies:** MetaTrader5, mt5_process_control, mt5_notifier

---

## การใช้งาน Default Values

ตัวอย่างที่ชัดเจนที่สุดของการใช้ `user_config.json` เป็น single source of truth:

```python
# แบบเดิม (ต้องระบุทุกอย่างทุกครั้ง)
run_backtest("SukarEA", "XAUUSDm", 1, "2024.01.01", "2024.12.31")
run_optimization("SukarEA", params, "XAUUSDm", ["2024.01.01", "2024.12.31"], 10)
walk_forward_test("SukarEA", "XAUUSDm", params, "2022.01.01", "2024.12.31", 4, 0.3)

# แบบใหม่ (ใช้ค่า default จาก user_config.json)
run_backtest("SukarEA")
run_optimization("SukarEA", params)
walk_forward_test("SukarEA", params)

# Override เฉพาะค่าที่ต้องการเปลี่ยน
run_backtest("SukarEA", symbol="XAUUSDm.c")
run_backtest("SukarEA", date_from="2025.01.01", date_to="2025.06.30")
```

---

## Installation

```bash
# Phase 2 dependencies
pip install MetaTrader5 pyautogui pywin32
```

Phase 1 dependencies (ถ้ายังไม่ได้ติดตั้ง):
```bash
pip install psutil watchdog APScheduler requests python-dateutil pytz
```

---

## Return Value Pattern

ทุก function ใน Phase 2 คืนค่าในรูปแบบนี้เสมอ:

```python
{
    "status": "success" | "error",
    # ข้อมูล specific ของ function นั้นๆ
    "error": str | None    # None ถ้าสำเร็จ
}
```

ไม่มีการ raise exception ออกมาให้ caller ทุก error จับไว้ภายในแล้ว return เป็น dict

---

## Next Steps

- [ ] เขียน unit tests สำหรับ tester, optimizer, manager (ที่เพิ่ง implement)
- [ ] ทดสอบ run_backtest จริงบนเครื่อง
- [ ] ทดสอบ walk_forward_test จริง
- [ ] ตั้งค่า Telegram notification
- [ ] รัน `python tests/test_all.py`
