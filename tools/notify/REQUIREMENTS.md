# MT5 Notifier - Requirements

## Python Dependencies

### Core Requirements
```bash
pip install requests
```

The `requests` library is required for HTTP API calls to:
- Telegram Bot API
- Line Notify API
- Discord Webhooks

### Optional Dependencies

For email notifications:
- `smtplib` (included in Python standard library)
- `email` module (included in Python standard library)

## Installation Steps

### 1. Basic Setup
```bash
pip install requests
```

### 2. Telegram Setup (Optional)

1. Talk to @BotFather on Telegram
2. Create a new bot: `/newbot`
3. Copy the bot token
4. Find your chat ID:
   - Send a message to your bot
   - Visit `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find `"id"` in the response (your chat_id)

5. Update `config/notify_settings.json`:
```json
{
  "telegram": {
    "bot_token": "YOUR_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  },
  "enabled_channels": ["telegram"]
}
```

### 3. Line Notify Setup (Optional)

1. Visit https://notify-api.line.me/
2. Click "Log in"
3. Log in with your Line account
4. Click "Create Token"
5. Copy the token

6. Update `config/notify_settings.json`:
```json
{
  "line": {
    "token": "YOUR_TOKEN_HERE"
  },
  "enabled_channels": ["telegram", "line"]
}
```

### 4. Discord Setup (Optional)

1. Go to Discord server settings
2. Click "Webhooks"
3. Click "Create Webhook"
4. Copy webhook URL

5. Update `config/notify_settings.json`:
```json
{
  "discord": {
    "webhook_url": "YOUR_WEBHOOK_URL_HERE"
  },
  "enabled_channels": ["discord"]
}
```

### 5. Email Setup (Optional)

1. Update `config/notify_settings.json`:
```json
{
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your@gmail.com",
    "sender_password": "APP_PASSWORD",
    "recipient_email": "recipient@gmail.com"
  },
  "enabled_channels": ["email"]
}
```

**For Gmail:**
- Enable 2-factor authentication
- Create app-specific password at https://myaccount.google.com/apppasswords
- Use app password (not your main password)

## System Requirements

- **OS:** Windows, macOS, Linux
- **Python:** 3.7+
- **Network:** Internet connection for API calls
- **Firewall:** Allow HTTPS connections to Telegram, Line, Discord APIs

## Version Compatibility

- Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12 ✓
- requests 2.25.0+ ✓

## Troubleshooting

### "ModuleNotFoundError: No module named 'requests'"
```bash
pip install requests
```

### Telegram: "Unauthorized" error
- Check bot token is correct
- Check chat ID is correct
- Make sure bot is in the chat

### Line: "401 Unauthorized"
- Check token is valid
- Token may have expired
- Regenerate token at https://notify-api.line.me/

### Discord: "Webhook is invalid"
- Check webhook URL is correct
- URL must end with `/slack`
- Webhook may have been deleted/regenerated

### Email: "SMTP authentication failed"
- For Gmail: use app password (not main password)
- For other providers: verify SMTP settings
- Check credentials are correct

### Connection timeout
- Check internet connection
- Check firewall allows HTTPS
- Try different SMTP server/port

## Performance Notes

- Telegram/Line/Discord API calls: ~500-2000ms
- Async queuing: ~1ms per message
- Email SMTP: ~2-5 seconds
- Use async_send=True for non-blocking behavior

## Security Notes

1. Never commit `config/notify_settings.json` with real credentials
2. Use environment variables for sensitive data:
   ```python
   import os

   config = {
       "telegram": {
           "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN"),
           "chat_id": os.environ.get("TELEGRAM_CHAT_ID")
       }
   }
   ```

3. For production:
   - Never hardcode credentials
   - Use secure configuration management
   - Use .env files with python-dotenv
   - Restrict file permissions on config file

## Color/Emoji Support

All supported channels handle:
- Emoji characters (✅, ❌, 🟢, 🔴, etc.)
- Unicode text
- HTML formatting (Telegram)
- Markdown formatting (Discord)

## API Rate Limits

- **Telegram:** ~30 messages per second
- **Line Notify:** ~100 messages per hour per token
- **Discord:** ~10 messages per 10 seconds per webhook
- **Gmail SMTP:** ~300 per day

## No External Large Dependencies

MT5 Notifier is lightweight:
- requests: ~300 KB
- No other heavy dependencies
- Total footprint: <1 MB

## Development

```bash
# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# Install dependencies
pip install requests

# Test notifications
python tools/notify/examples.py
```

## License

MIT License - Use freely in projects

## Support

For issues:
1. Check credentials are correct
2. Verify internet connection
3. Check API documentation for specific service
4. Review debug logs
