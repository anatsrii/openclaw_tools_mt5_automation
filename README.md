# mt5_automation

Python automation toolkit for MetaTrader 5 — run backtests, optimize strategies, and manage EA deployments entirely from code without touching the MT5 GUI.

## What it does

- **Backtest** — launch MT5 headless, generate INI configs dynamically, wait for report, parse results into structured dict
- **Optimize** — run parameter sweeps across symbol/timeframe/date combinations, rank results by profit factor
- **Manage** — check MT5 process health, start/stop terminal, monitor EA status
- **Schedule** — cron-based automation for recurring backtests and daily reports
- **Notify** — send alerts (Telegram / console) when jobs finish or errors occur
- **Log parsing** — extract trade stats from MT5 journal and tester HTML reports

All configuration lives in one file — `config/user_config.json`. No hardcoded paths anywhere.

## Requirements

- Python 3.9+
- MetaTrader 5 installed (any broker)
- Windows (MT5 is Windows-only)

```bash
pip install MetaTrader5 psutil pywin32 pyautogui watchdog APScheduler requests python-dateutil
```

## Setup

**1. Find your Terminal ID**

Open MT5 → Tools → Options → Expert Advisors → look at the data folder path, the long hex string is your Terminal ID. Alternatively:

```
%APPDATA%\MetaQuotes\Terminal\<TERMINAL_ID>\
```

**2. Edit `config/user_config.json`**

```json
{
  "mt5": {
    "terminal_id": "YOUR_TERMINAL_ID_HERE",
    "installation_path": "C:\\Program Files\\MetaTrader 5",
    "username": "YOUR_WINDOWS_USERNAME"
  },
  "trading": {
    "default_symbol": "XAUUSDm",
    "default_timeframe": 15,
    "default_date_from": "2026.01.01",
    "default_date_to": "2026.01.31",
    "deposit": 300,
    "currency": "USD",
    "leverage": 200
  },
  "backtest": {
    "timeout": 300
  }
}
```

**3. Verify paths**

```bash
python config/config.py
```

## Usage

```python
from tools.tester.mt5_tester import run_backtest
from tools.optimizer.mt5_optimizer import run_optimization
from tools.process.mt5_process_control import get_mt5_status

# Run a backtest (uses defaults from user_config.json)
result = run_backtest("Advisor\\MyEA\\MyEA_v1")
print(result["profit_factor"], result["drawdown"])

# Override specific params
result = run_backtest(
    "Advisor\\MyEA\\MyEA_v1",
    symbol="EURUSDm",
    date_from="2026.01.01",
    date_to="2026.01.31"
)

# Check MT5 status
status = get_mt5_status()
print(status["is_running"])
```

## Tools

| Tool | Module | Description |
|------|--------|-------------|
| Tester | `tools/tester` | Run backtests, parse HTML reports |
| Optimizer | `tools/optimizer` | Parameter sweeps, walk-forward |
| Manager | `tools/manager` | EA deploy, position management |
| Process | `tools/process` | MT5 start/stop/health check |
| Files | `tools/files` | Find EA files, read/write configs |
| Logs | `tools/logs` | Parse MT5 journal and tester logs |
| Notify | `tools/notify` | Alerts via Telegram or console |
| Scheduler | `tools/scheduler` | Cron jobs for recurring tasks |

## How backtesting works

MT5 must be **closed** before running a headless backtest. The tool will:

1. Stop MT5 if running
2. Generate a dynamic `.ini` file with your parameters
3. Launch `terminal64.exe /config:<ini>`
4. Wait for the HTML report file to appear
5. Parse and return structured results

Each run saves a timestamped report to `MQL5/Reports/` so results never overwrite each other.

## Run tests

```bash
python tests/test_all.py
```
