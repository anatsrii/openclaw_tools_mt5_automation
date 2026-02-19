# MT5 Automation Toolkit - Phase 2: Application Layer

## Overview

Phase 2 provides **5 high-level application tools** that leverage the Phase 1 infrastructure tools.

### Architecture

```
Phase 1 (Infrastructure)          Phase 2 (Application)
├── mt5_process_control    ────→  ├── mt5_developer
├── mt5_file_manager       ────→  ├── mt5_tester
├── mt5_log_parser         ────→  ├── mt5_optimizer
├── mt5_notifier           ────→  ├── mt5_manager
└── mt5_scheduler          ────→  └── mt5_operator
```

## Tool Descriptions

### 2.1: MT5 Developer
**Purpose:** AI-assisted EA coding with self-healing compilation

**Key Functions:**
- `compile_ea()` - Compile and extract errors
- `compile_and_fix()` - Loop until compilation succeeds
- `deploy_ea()` - Attach EA to chart

**Imports:**
- `mt5_file_manager` - Locate EA files
- `mt5_log_parser` - Extract compile errors
- `mt5_process_control` - Ensure MT5 running
- `mt5_notifier` - Send alerts

### 2.2: MT5 Tester
**Purpose:** Run Strategy Tester silently and collect results

**Key Functions:**
- `run_backtest()` - Single backtest execution
- `run_multi_backtest()` - Sequential backtests
- `get_tester_report()` - Parse HTML reports

**Imports:**
- `mt5_file_manager` - Find EA .ex5
- `mt5_process_control` - Launch MT5 with configs
- `mt5_log_parser` - Parse results

### 2.3: MT5 Optimizer
**Purpose:** Parameter optimization with walk-forward analysis

**Key Functions:**
- `run_optimization()` - Single optimization pass
- `walk_forward_test()` - Split IS/OOS, optimize + validate

**Imports:**
- `mt5_file_manager` - Manage EA files
- `mt5_process_control` - Run optimizations
- `mt5_notifier` - Progress alerts

### 2.4: MT5 Manager
**Purpose:** System health and account management

**Key Functions:**
- `get_system_health()` - Aggregate health status
- `list_active_bots()` - Scan active EAs
- `switch_account()` - Change trading account

**Imports:**
- `mt5_process_control` - MT5 status
- `mt5_notifier` - Alerts
- `mt5_scheduler` - Market sessions
- `mt5_operator` - Account info

### 2.5: MT5 Operator
**Purpose:** Live trade management and emergency controls

**Key Functions:**
- `get_open_positions()` - View trades
- `close_all_positions()` - Emergency close
- `get_account_summary()` - Account statistics

**Requires:**
- `MetaTrader5` Python library
- `mt5_notifier` - Trade alerts

## Installation

### Phase 1 Tools (Already Installed)
Located in `tools/` directory:
```python
from tools.process import mt5_process_control
from tools.files import mt5_file_manager
from tools.logs import mt5_log_parser
from tools.notify import mt5_notifier
from tools.scheduler import mt5_scheduler
```

### Phase 2 Tools (New)
Located in `tools/{developer,tester,optimizer,manager,operator}/`
```python
from tools.developer import compile_ea, deploy_ea
from tools.tester import run_backtest
from tools.optimizer import run_optimization, walk_forward_test
from tools.manager import get_system_health
from tools.operator import get_open_positions, close_all_positions
```

### Additional Dependencies

```bash
# For developer tool
pip install pyautogui

# For operator tool
pip install MetaTrader5

# For tester/optimizer
# (Uses existing infrastructure tools)
```

## Usage Example

```python
from tools.developer import compile_and_fix, deploy_ea
from tools.tester import run_backtest
from tools.operator import get_open_positions, close_all_positions
from tools.notifier import send_daily_report

# 1. Develop & compile EA
result = compile_and_fix("MyEA")
if result["success"]:
    deploy_ea("MyEA", "EURUSD", 240)

# 2. Backtest before live
backtest = run_backtest(
    "MyEA", "EURUSD", 240,
    "2024-01-01", "2024-12-31"
)

# 3. Manage live positions
positions = get_open_positions()

# 4. Emergency shutdown
if positions["total_pnl"] < -1000:
    close_all_positions(comment="Risk limit exceeded")

# 5. Daily reporting
send_daily_report(...)
```

## Key Design Principles

1. **Layered Architecture**
   - Phase 1: Infrastructure (low-level system control)
   - Phase 2: Application (business logic)
   - Clean separation of concerns

2. **Reusable Components**
   - All Phase 2 tools import Phase 1 components
   - Consistent error handling
   - Structured result returns

3. **Error Management**
   - All functions return `{status, data, error}`
   - No exceptions thrown to caller
   - Errors logged and notified

4. **Async-Safe Design**
   - Thread-safe background operations
   - Queue-based messaging
   - Non-blocking where possible

5. **Production-Ready**
   - Comprehensive logging
   - Full error handling
   - Monitored execution
   - Automated alerts

## File Structure

```
tools/
├── developer/
│   ├── __init__.py
│   └── mt5_developer.py
├── tester/
│   ├── __init__.py
│   └── mt5_tester.py
├── optimizer/
│   ├── __init__.py
│   └── mt5_optimizer.py
├── manager/
│   ├── __init__.py
│   └── mt5_manager.py
└── operator/
    ├── __init__.py
    └── mt5_operator.py
```

## Next Steps

1. **Complete Implementation**
   - mt5_tester: Backtest execution and parsing
   - mt5_optimizer: Parameter optimization
   - mt5_manager: Bot scanning and health monitoring

2. **Testing**
   - Unit tests for each tool
   - Integration tests between tools
   - End-to-end workflow tests

3. **Documentation**
   - API documentation for each tool
   - Usage examples
   - Best practices guide

## License

Part of OpenClaw MT5 Automation Toolkit
