# MT5 Scheduler Tool

Schedule and manage MT5 automation tasks based on market sessions and time.

## Features

- ✅ Market session awareness (Asia, London, NY - UTC+7)
- ✅ Multiple scheduling methods (cron, session-based, interval)
- ✅ Automatic market hours detection
- ✅ Holiday and weekend handling
- ✅ Async session waiting
- ✅ Pre-built common schedules
- ✅ Task management and monitoring
- ✅ Background scheduler with APScheduler

## Market Sessions (UTC+7 Bangkok)

- **Asia**: 00:00 - 08:00 (Asian markets)
- **London**: 14:00 - 23:00 (European markets)
- **NY**: 19:00 - 04:00 (American markets, wraps to next day)
- **Overlap**: 19:00 - 23:00 (London-NY overlap, most volatile)

## Installation

```bash
pip install apscheduler pytz
```

## Quick Start

```python
from tools.scheduler import (
    get_current_session,
    schedule_task,
    is_market_open,
    create_default_schedules
)

# Check current session
session = get_current_session()
print(f"Active sessions: {session['sessions']}")

# Schedule a daily task
schedule_task(
    my_function,
    "cron",
    cron_expr="0 6 * * *"  # 06:00 daily
)

# Create default schedules
create_default_schedules()

# Check if market is open
market = is_market_open("XAUUSD")
if market["is_open"]:
    print(f"Market open in: {market['current_session']}")
```

## API Documentation

See full documentation in README.md

## License

Part of OpenClaw MT5 Automation Skill
