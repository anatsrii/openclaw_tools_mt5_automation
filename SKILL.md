# MT5 Automation Skill

## Overview
OpenClaw skill for MetaTrader 5 (MT5) process automation, file management, logging, notifications, and task scheduling.

## Features

### Process Control (`tools/process/`)
- Launch and manage MT5 processes
- Control MT5 terminal instances
- Monitor process status and health
- Handle process termination safely

### File Management (`tools/files/`)
- Manage MT5 data files
- Handle trading data export/import
- File operations within MT5 directories
- Backup and restore functionality

### Log Parsing (`tools/logs/`)
- Parse MT5 log files
- Extract trading activity
- Analyze error logs
- Generate log reports

### Notifications (`tools/notify/`)
- Send alerts on trading events
- Email notifications
- System notifications
- Custom notification handlers

### Task Scheduler (`tools/scheduler/`)
- Schedule MT5 automation tasks
- Manage recurring jobs
- Handle task dependencies
- Monitor scheduled tasks

## Configuration

### MT5 Paths (`config/mt5_paths.json`)
- Installation directory: `C:\Program Files\MetaTrader 5\`
- Data directory: `C:\Users\JML-PC\.openclaw\tools\metatrader5`

### Settings (`config/settings.json`)
- Global automation settings
- Default behaviors
- Logging configuration
- Notification settings

## Installation

Located at: `c:\Users\JML-PC\.openclaw\tools\mt5_automation`

## Usage

Import and use the skill components:
```python
from tools.process import MT5Process
from tools.files import MT5FileManager
from tools.logs import MT5LogParser
from tools.notify import MT5Notifier
from tools.scheduler import MT5Scheduler
```

## Testing

Run tests from the `tests/` directory to validate functionality.
