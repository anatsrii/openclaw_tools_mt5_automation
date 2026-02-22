# 🤖 mt5_automation

> **An OpenClaw Skill** — Give your AI agent full control over MetaTrader 5.
> Backtest strategies, optimize parameters, and manage live EAs — just by asking.

---

## What is this?

`mt5_automation` is an **OpenClaw Skill** that lets your AI agent (running inside OpenClaw) operate MetaTrader 5 programmatically.

Instead of clicking through MT5's GUI manually, you simply tell your agent what you want:

```
"Run a backtest for Cash_Collector on XAUUSDm for January 2026"
"Find the best parameter set across M1, M5, and M15"
"Check if MT5 is running and attach the EA to the chart"
```

The agent handles everything — launching MT5, generating configs, waiting for results, parsing reports, and sending you a summary.

---

## What can it do?

| Capability | What the agent can do |
|---|---|
| 🧪 **Backtest** | Run strategy tester headlessly, parse HTML reports into structured data |
| 🔬 **Optimize** | Sweep parameter combinations, rank by profit factor / drawdown |
| 📊 **Report** | Extract win rate, PF, drawdown, trade count from any tester run |
| ⚙️ **Manage EAs** | Deploy EAs to charts, check status, remove |
| 🖥️ **Process control** | Start / stop / health-check MT5 terminal |
| 📁 **File ops** | Find `.ex5` files, read/write `.set` configs, scan Experts folder |
| 📅 **Schedule** | Set up recurring backtests or daily reports via cron |
| 🔔 **Notify** | Get Telegram or console alerts when jobs finish |

---

## How it works

```
You (natural language)
       ↓
  OpenClaw Agent
       ↓
  mt5_automation skill
       ↓
  MetaTrader 5 (headless)
       ↓
  Structured results back to you
```

The skill talks to MT5 via CLI (`terminal64.exe /config:<ini>`) for backtesting, and via the MT5 Python API for live data. All paths and defaults are resolved automatically from your config — **no hardcoded values anywhere in the codebase**.

---

## Setup (one time)

**1. Find your Terminal ID**

In MT5: File → Open Data Folder → copy the hex folder name from the path. Or look here:
```
C:\Users\<you>\AppData\Roaming\MetaQuotes\Terminal\<TERMINAL_ID>\
```

**2. Configure — choose one option**

*Option A: Config file (recommended for local dev)*

```bash
cp config/user_config.example.json config/user_config.json
# then edit user_config.json with your values
```

*Option B: Environment variables (CI/CD or shared machines)*

```bash
# Required
set MT5_TERMINAL_ID=YOUR_TERMINAL_ID
set MT5_USERNAME=YOUR_WINDOWS_USERNAME

# Optional (have defaults)
set MT5_INSTALL_PATH=C:\Program Files\MetaTrader 5
set MT5_TERMINAL_EXE=terminal64.exe
set MT5_SYMBOL=XAUUSDm
set MT5_TIMEFRAME=15
```

Env vars take priority over the config file — useful when you don't want credentials on disk.

**3. Verify everything is found**

```bash
python config/config.py
```

**4. Install dependencies**

```bash
pip install MetaTrader5 psutil pywin32 pyautogui watchdog APScheduler requests python-dateutil
```

**5. Register in OpenClaw**

Add to your `openclaw.json`:
```json
"skills": {
  "entries": {
    "mt5_automation": {
      "enabled": true,
      "path": "path/to/mt5_automation"
    }
  }
}
```

Restart OpenClaw — the skill is ready.

---

## Requirements

- Windows (MT5 is Windows-only)
- Python 3.9+
- MetaTrader 5 installed with a broker account
- OpenClaw running locally

---

## Tool reference

Full documentation → **[SKILL.md](SKILL.md)**

```
tools/
├── tester/      — backtest runner + report parser
├── optimizer/   — parameter sweep + walk-forward
├── manager/     — EA deployment + position control
├── process/     — MT5 start/stop/health
├── files/       — EA file discovery + set configs
├── logs/        — journal + tester log parsing
├── notify/      — Telegram + console alerts
└── scheduler/   — cron job management
```

---

## Notes on backtesting

MT5 **must be closed** before a headless backtest. The skill handles this automatically:

1. Stops MT5 if running
2. Generates a dynamic `.ini` with your parameters
3. Launches MT5 headless via `/config`
4. Waits for the report file to appear on disk
5. Parses HTML → returns structured dict

Reports are saved with timestamps to `MQL5/Reports/` — runs never overwrite each other.
