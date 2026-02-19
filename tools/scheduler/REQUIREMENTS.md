# MT5 Scheduler - Requirements

## Python Dependencies

```bash
pip install apscheduler pytz
```

### Core Requirements

- **apscheduler** (4.10.0+) - Background task scheduling
  - Provides cron, interval, and date-based triggers
  - Manages job queuing and execution

- **pytz** (2023.3+) - Timezone handling
  - Market session timezone conversion
  - UTC to local time conversion

## Installation Steps

### 1. Install Dependencies
```bash
pip install apscheduler>=4.10.0 pytz>=2023.3
```

### 2. Verify Installation
```python
import apscheduler
import pytz
print(f"APScheduler: {apscheduler.__version__}")
print(f"pytz: {pytz.__version__}")
```

## Python Version

- Python 3.7+
- Tested with 3.8, 3.9, 3.10, 3.11, 3.12

## System Requirements

- **OS**: Windows, macOS, Linux
- **CPU**: Minimal (light background thread)
- **Memory**: <50 MB for typical usage
- **Networking**: None required (local operation)

## Upgrade

To upgrade APScheduler to latest version:
```bash
pip install --upgrade apscheduler
```

## Troubleshooting

### "No module named 'apscheduler'"
```bash
pip install apscheduler
```

### "No module named 'pytz'"
```bash
pip install pytz
```

### Scheduler doesn't run tasks
- Check if scheduler.start() was called
- Verify system time is correct
- Check timezone configuration

## Optional: Advanced Scheduling

For more advanced features, consider:
- **python-cron** for complex cron expressions
- **schedule** library (simpler alternative)

## Development

For development mode:
```bash
pip install -e .
pip install apscheduler pytz
```

## License

APScheduler: MIT License
pytz: MIT License
