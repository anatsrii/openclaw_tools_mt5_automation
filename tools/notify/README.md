# MT5 Notifier Tool

Unified notification gateway for all MetaTrader 5 events across multiple channels.

## Overview

The `mt5_notifier` module provides a centralized notification system supporting:
- Telegram
- Line Notify
- Discord
- Email

Features:
- Severity-based filtering
- Pre-formatted trade, error, and report notifications
- Asynchronous non-blocking sends
- Thread-safe queue-based dispatch
- Configuration-driven channel management

## Features

- ✅ Multi-channel notifications (Telegram, Line, Discord, Email)
- ✅ Severity levels: debug, info, warning, critical
- ✅ Pre-formatted notifications for common events
- ✅ Async/non-blocking message queuing
- ✅ Thread-safe background worker
- ✅ Config-based channel management
- ✅ Connection testing
- ✅ Emoji-rich formatting
- ✅ Error handling with structured results

## Installation

See `REQUIREMENTS.md` for dependencies.

```bash
pip install requests
```

## Configuration

Edit `config/notify_settings.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN",
    "chat_id": "YOUR_CHAT_ID"
  },
  "line": {
    "token": "YOUR_LINE_TOKEN"
  },
  "discord": {
    "webhook_url": "YOUR_WEBHOOK_URL"
  },
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your@email.com",
    "sender_password": "your_password",
    "recipient_email": "recipient@email.com"
  },
  "enabled_channels": ["telegram", "line"],
  "min_severity": "info"
}
```

### Getting Credentials

#### Telegram
1. Create bot with @BotFather
2. Get bot token
3. Send message to bot, get chat ID from `/getUpdates`

#### Line
1. Create Line Notify integration at https://notify-api.line.me/
2. Get access token

#### Discord
1. Create webhook in channel settings
2. Copy webhook URL

#### Email
1. Use Gmail or other SMTP provider
2. For Gmail: Use app-specific password

## API Reference

### send(message, severity="info", channel=None, async_send=True)

Send notification to enabled channels.

**Parameters:**
- `message` (str): Message to send
- `severity` (str): "debug", "info", "warning", "critical" (default: "info")
- `channel` (str): Specific channel or None for all
- `async_send` (bool): Send asynchronously (default: True)

**Returns:**
```python
{
    "status": "queued" | "success" | "skipped" | "error",
    "sent_to": [],
    "failed": [],
    "message": str,
    "error": str | None
}
```

**Example:**
```python
from tools.notify import send

result = send("Trading system started", severity="warning")
print(f"Sent to: {result['sent_to']}")
```

---

### send_trade_alert(action, symbol, volume, entry_price, profit, comment, channel)

Send formatted trade notification.

**Parameters:**
- `action` (str): "BUY", "SELL", "CLOSE", "MODIFY"
- `symbol` (str): Trading symbol
- `volume` (float): Lot size
- `entry_price` (float): Entry price
- `profit` (float): Profit/loss amount
- `comment` (str): Additional comment
- `channel` (str): Specific channel

**Returns:**
```python
{
    "status": "queued" | "success",
    "sent_to": [],
    "failed": [],
    "message": str
}
```

**Example:**
```python
from tools.notify import send_trade_alert

send_trade_alert(
    action="BUY",
    symbol="EURUSD",
    volume=0.1,
    entry_price=1.0850,
    comment="Daily breakout"
)

# Output: 🟢 BUY EURUSD | 0.1 lot | Entry: 1.08 | Daily breakout
```

---

### send_daily_report(total_profit, trade_count, wins, losses, max_drawdown, date, channel)

Send daily trading report.

**Parameters:**
- `total_profit` (float): Total P/L for the day
- `trade_count` (int): Total trades
- `wins` (int): Winning trades
- `losses` (int): Losing trades
- `max_drawdown` (float): Max drawdown percentage
- `date` (str): Report date (or today)
- `channel` (str): Specific channel

**Example:**
```python
from tools.notify import send_daily_report

send_daily_report(
    total_profit=150.50,
    trade_count=5,
    wins=3,
    losses=2,
    max_drawdown=2.5
)

# Output:
# 📊 DAILY REPORT - 2025-02-19
# 💰 Total P/L: +150.50
# 📈 Trades: 5 (3W / 2L)
# 🎯 Win Rate: 60.0%
# 📉 Max Drawdown: 2.50%
```

---

### send_error(source, error_message, ea_name, channel)

Send error notification.

**Parameters:**
- `source` (str): Error source (e.g., "compile", "runtime")
- `error_message` (str): Error message
- `ea_name` (str): Optional EA name
- `channel` (str): Specific channel

**Example:**
```python
from tools.notify import send_error

send_error(
    source="compile",
    error_message="Function not defined",
    ea_name="MyEA"
)

# Output:
# ❌ ERROR | compile
# EA: MyEA
# Message: Function not defined
```

---

### send_bot_status(status, ea_name, details, channel)

Send bot status notification.

**Parameters:**
- `status` (str): "started", "stopped", "crashed", "error"
- `ea_name` (str): EA name
- `details` (str): Additional details
- `channel` (str): Specific channel

**Example:**
```python
from tools.notify import send_bot_status

send_bot_status(
    status="started",
    ea_name="MyRobot",
    details="Connected to account DEMO12345"
)

# Output: ▶️ STARTED | MyRobot
# Connected to account DEMO12345
```

---

### test_connection(channel=None)

Test notification channel connection.

**Parameters:**
- `channel` (str): Channel to test (or all)

**Returns:**
```python
{
    "status": "success" | "partial" | "error",
    "results": {
        "telegram": True,
        "line": False
    },
    "error": str | None
}
```

**Example:**
```python
from tools.notify import test_connection

result = test_connection()
for channel, success in result["results"].items():
    status = "✓" if success else "✗"
    print(f"{status} {channel}")
```

---

### get_enabled_channels()

Get list of enabled notification channels.

**Returns:**
```python
["telegram", "line"]
```

---

## Class-based Usage

```python
from tools.notify import MT5Notifier

# Create notifier with custom config path
notifier = MT5Notifier("/path/to/notify_settings.json")

# Or use default config location
notifier = MT5Notifier()

# Send notifications
notifier.send("Hello", severity="info")
notifier.send_trade_alert("BUY", "EURUSD", 0.1)

# Test channels
result = notifier.test_connection("telegram")

# Set minimum severity filter
notifier.set_min_severity("warning")

# Cleanup (automatic with del)
notifier.stop_worker()
```

## Severity Levels

Messages are only sent if severity >= min_severity config:

```
DEBUG (0) < INFO (1) < WARNING (2) < CRITICAL (3)
```

Example with min_severity="warning":
- DEBUG messages: skipped
- INFO messages: skipped
- WARNING messages: sent
- CRITICAL messages: sent

## Async Design

All notifications use a background queue by default:

```python
# Queued immediately (non-blocking)
send("Long message", async_send=True)

# Wait for processing


# Or synchronous (blocking):
send("Message", async_send=False)
```

## Emoji Reference

- 🟢 Buy
- 🔴 Sell
- ⭐ Close position
- ❌ Error
- ⚠️ Warning
- ℹ️ Info
- ✅ Success
- 💰 Profit
- 📉 Loss
- ▶️ Started
- ⏹️ Stopped
- 💥 Crashed
- 📊 Report
- 📈 Trades

## Examples

### Monitor Trading
```python
from tools.notify import send_trade_alert

def on_trade(action, symbol, volume, price, profit):
    send_trade_alert(
        action=action,
        symbol=symbol,
        volume=volume,
        entry_price=price,
        profit=profit
    )

# on_trade("BUY", "GOLD", 0.1, 2650.50, None)
```

### Daily Report
```python
from tools.notify import send_daily_report
import requests

# Get trading stats
stats = get_daily_stats()

send_daily_report(
    total_profit=stats['profit'],
    trade_count=stats['trades'],
    wins=stats['wins'],
    losses=stats['losses'],
    max_drawdown=stats['drawdown']
)
```

### Error Handling
```python
from tools.notify import send_error

try:
    # Trading logic
    pass
except Exception as e:
    send_error(
        source="trading_engine",
        error_message=str(e),
        ea_name="MyEA"
    )
```

### Multi-Channel
```python
from tools.notify import send

# Send to all enabled channels
send("Important alert", severity="critical")

# Send to specific channel
send("Debug info", severity="debug", channel="telegram")
```

## Error Handling

```python
result = send("Message")

if result["status"] == "queued":
    print("Message queued for delivery")
elif result["status"] == "success":
    print(f"Sent to {result['sent_to']}")
elif result["status"] == "error":
    print(f"Error: {result['error']}")

if result["failed"]:
    print(f"Failed channels: {result['failed']}")
```

## Configuration Tips

### Disable a Channel
```json
{
  "enabled_channels": ["telegram"]
}
```

### Change Minimum Severity
```json
{
  "min_severity": "warning"
}
```

For only critical alerts:
```json
{
  "min_severity": "critical"
}
```

### Multiple Recipients (Telegram)
Create a group, add bot, get group chat ID:
```json
{
  "telegram": {
    "bot_token": "...",
    "chat_id": "-1001234567890"
  }
}
```

## Troubleshooting

### Telegram not working
- Verify bot token is correct
- Verify chat ID is correct
- Send message to bot first
- Check bot is in group/chat

### Line not working
- Verify access token is correct
- Token must be from Line Notify (not Line Login)

### Discord not working
- Verify webhook URL is correct
- Bot must have permission to post in channel

### Email not working
- Verify SMTP server settings
- For Gmail: use app-specific password
- Check firewall/encryption settings

## Performance

- Async sending: ~1ms per message (queued)
- Sync sending: ~500-2000ms per message (blocked)
- Queue processing: ~50ms per message

## Thread Safety

MT5Notifier is thread-safe:
- Multiple threads can call `send()` concurrently
- Message queue ensures order
- Background worker is daemon thread

## Dependencies

- Python 3.7+
- requests (for HTTP APIs)
- Optional: smtplib (for email, included in Python)

## License

Part of OpenClaw MT5 Automation Skill
