"""
MT5 Notifier Tool
=================
Unified notification gateway for all MT5 events across multiple channels.

Supports: Telegram, Line Notify, Discord, Email
Uses requests library for HTTP APIs
Threading for non-blocking async sends

Dependencies: requests
"""

import os
import json
import time
import logging
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from queue import Queue
from enum import Enum

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Severity levels for notifications."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    CRITICAL = 3

    def __lt__(self, other):
        if isinstance(other, Severity):
            return self.value < other.value
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, Severity):
            return self.value <= other.value
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Severity):
            return self.value >= other.value
        return NotImplemented


class MT5Notifier:
    """
    Unified notification gateway for MT5 events.
    """

    # Emoji indicators
    EMOJI = {
        "buy": "🟢",
        "sell": "🔴",
        "close": "⭐",
        "error": "❌",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅",
        "profit": "💰",
        "loss": "📉",
        "started": "▶️",
        "stopped": "⏹️",
        "crashed": "💥",
    }

    # Telegram API
    TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

    # Line Notify API
    LINE_NOTIFY_API = "https://notify-api.line.me/api/notify"

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize MT5 Notifier.

        Args:
            config_path: Path to notify_settings.json
        """
        self.config = self._load_config(config_path)
        self.send_queue = Queue()
        self.worker_thread = None
        self.worker_active = False
        self._start_worker()

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load notification configuration."""
        if config_path:
            path = Path(config_path)
        else:
            # Try default location
            path = Path(__file__).parent.parent.parent / "config" / "notify_settings.json"

        if not path.exists():
            logger.warning(f"Config not found: {path}, using defaults")
            return self._default_config()

        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return self._default_config()

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "telegram": {
                "bot_token": "",
                "chat_id": ""
            },
            "line": {
                "token": ""
            },
            "discord": {
                "webhook_url": ""
            },
            "email": {
                "smtp_server": "",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_email": ""
            },
            "enabled_channels": ["telegram"],
            "min_severity": "info",
            "queue_timeout": 5.0
        }

    def send(
        self,
        message: str,
        severity: str = "info",
        channel: Optional[str] = None,
        async_send: bool = True
    ) -> Dict[str, Any]:
        """
        Send notification to enabled channels.

        Args:
            message: Message to send
            severity: "debug", "info", "warning", "critical"
            channel: Send to specific channel (or None for all enabled)
            async_send: Send asynchronously if True

        Returns:
            {
                "status": "queued" | "skipped" | "error",
                "sent_to": [],
                "failed": [],
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "skipped",
            "sent_to": [],
            "failed": [],
            "message": "",
            "error": None
        }

        try:
            # Check severity filter
            min_sev = Severity[self.config.get("min_severity", "info").upper()]
            msg_sev = Severity[severity.upper()]

            if msg_sev < min_sev:
                result["message"] = f"Message severity {severity} below minimum {min_sev.name}"
                return result

            # Get target channels
            if channel:
                channels = [channel]
            else:
                channels = self.config.get("enabled_channels", ["telegram"])

            # Queue for async sending or send directly
            if async_send and self.worker_active:
                self.send_queue.put({
                    "message": message,
                    "severity": severity,
                    "channels": channels,
                    "timestamp": datetime.now()
                })
                result["status"] = "queued"
                result["message"] = f"Queued to {', '.join(channels)}"
            else:
                # Send synchronously
                for ch in channels:
                    try:
                        self._send_to_channel(message, ch, severity)
                        result["sent_to"].append(ch)
                    except Exception as e:
                        result["failed"].append(ch)
                        logger.error(f"Error sending to {ch}: {str(e)}")

                result["status"] = "success" if result["sent_to"] else "error"
                result["message"] = f"Sent to {', '.join(result['sent_to'])}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error in send: {str(e)}")

        return result

    def send_trade_alert(
        self,
        action: str,
        symbol: str,
        volume: float = 0.0,
        entry_price: Optional[float] = None,
        profit: Optional[float] = None,
        comment: str = "",
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send formatted trade notification.

        Args:
            action: "BUY", "SELL", "CLOSE", "MODIFY"
            symbol: Trading symbol
            volume: Lot size
            entry_price: Entry price
            profit: Profit/loss amount
            comment: Additional comment
            channel: Specific channel (or None for all)

        Returns:
            {status, sent_to, failed, message}
        """
        # Determine emoji and severity
        action_upper = action.upper()
        if action_upper == "BUY":
            emoji = self.EMOJI["buy"]
            severity = "info"
        elif action_upper == "SELL":
            emoji = self.EMOJI["sell"]
            severity = "info"
        elif action_upper == "CLOSE":
            emoji = self.EMOJI["close"]
            severity = "warning"
            if profit and profit > 0:
                emoji = self.EMOJI["profit"]
        else:
            emoji = self.EMOJI["info"]
            severity = "info"

        # Build message
        message = f"{emoji} {action_upper} {symbol}"
        if volume > 0:
            message += f" | {volume} lot"
        if entry_price:
            message += f" | Entry: {entry_price:.2f}"
        if profit is not None:
            profit_icon = self.EMOJI["profit"] if profit > 0 else self.EMOJI["loss"]
            message += f" | {profit_icon} {profit:+.2f}"
        if comment:
            message += f" | {comment}"

        return self.send(message, severity=severity, channel=channel)

    def send_daily_report(
        self,
        total_profit: float,
        trade_count: int,
        wins: int = 0,
        losses: int = 0,
        max_drawdown: float = 0.0,
        date: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send daily trading report.

        Args:
            total_profit: Total profit/loss for the day
            trade_count: Number of trades
            wins: Number of winning trades
            losses: Number of losing trades
            max_drawdown: Maximum drawdown
            date: Report date (or today)
            channel: Specific channel

        Returns:
            {status, sent_to, failed, message}
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # Calculate win rate
        win_rate = (wins / trade_count * 100) if trade_count > 0 else 0

        # Determine emoji
        emoji = self.EMOJI["profit"] if total_profit > 0 else self.EMOJI["loss"]

        # Build message
        message = f"📊 DAILY REPORT - {date}\n\n"
        message += f"{emoji} Total P/L: {total_profit:+.2f}\n"
        message += f"📈 Trades: {trade_count} ({wins}W / {losses}L)\n"
        message += f"🎯 Win Rate: {win_rate:.1f}%\n"
        message += f"📉 Max Drawdown: {max_drawdown:.2f}%"

        severity = "warning" if total_profit < 0 else "info"
        return self.send(message, severity=severity, channel=channel)

    def send_error(
        self,
        source: str,
        error_message: str,
        ea_name: Optional[str] = None,
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send error notification.

        Args:
            source: Error source (e.g., "compile", "runtime", "connection")
            error_message: Error message
            ea_name: Optional EA name
            channel: Specific channel

        Returns:
            {status, sent_to, failed, message}
        """
        message = f"{self.EMOJI['error']} ERROR | {source}\n"
        if ea_name:
            message += f"EA: {ea_name}\n"
        message += f"Message: {error_message}"

        return self.send(message, severity="critical", channel=channel)

    def send_bot_status(
        self,
        status: str,
        ea_name: str,
        details: str = "",
        channel: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send bot status notification.

        Args:
            status: "started", "stopped", "crashed", "error"
            ea_name: EA name
            details: Additional details
            channel: Specific channel

        Returns:
            {status, sent_to, failed, message}
        """
        status_lower = status.lower()
        emoji = self.EMOJI.get(status_lower, self.EMOJI["info"])
        severity = "critical" if status_lower == "crashed" else "warning" if status_lower == "error" else "info"

        message = f"{emoji} {status.upper()} | {ea_name}"
        if details:
            message += f"\n{details}"

        return self.send(message, severity=severity, channel=channel)

    def _send_to_channel(self, message: str, channel: str, severity: str = "info"):
        """Send to specific channel."""
        if not requests:
            raise RuntimeError("requests library not installed")

        channel_lower = channel.lower()

        if channel_lower == "telegram":
            self._send_telegram(message)
        elif channel_lower == "line":
            self._send_line(message)
        elif channel_lower == "discord":
            self._send_discord(message)
        elif channel_lower == "email":
            self._send_email(message, severity)
        else:
            raise ValueError(f"Unknown channel: {channel}")

    def _send_telegram(self, message: str):
        """Send via Telegram."""
        config = self.config.get("telegram", {})
        token = config.get("bot_token", "")
        chat_id = config.get("chat_id", "")

        if not token or not chat_id:
            raise ValueError("Telegram token or chat_id not configured")

        url = self.TELEGRAM_API.format(token=token)
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Telegram API error: {response.text}")

    def _send_line(self, message: str):
        """Send via Line Notify."""
        config = self.config.get("line", {})
        token = config.get("token", "")

        if not token:
            raise ValueError("Line token not configured")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {"message": message}

        response = requests.post(self.LINE_NOTIFY_API, headers=headers, data=payload, timeout=5)
        if response.status_code != 200:
            raise Exception(f"Line API error: {response.text}")

    def _send_discord(self, message: str):
        """Send via Discord."""
        config = self.config.get("discord", {})
        webhook_url = config.get("webhook_url", "")

        if not webhook_url:
            raise ValueError("Discord webhook URL not configured")

        payload = {"content": message}
        response = requests.post(webhook_url, json=payload, timeout=5)
        if response.status_code not in [200, 204]:
            raise Exception(f"Discord API error: {response.text}")

    def _send_email(self, message: str, severity: str = "info"):
        """Send via Email."""
        try:
            import smtplib
            from email.mime.text import MIMEText
        except ImportError:
            raise RuntimeError("Email requires Python email/smtplib modules")

        config = self.config.get("email", {})
        smtp_server = config.get("smtp_server", "")
        smtp_port = config.get("smtp_port", 587)
        sender = config.get("sender_email", "")
        password = config.get("sender_password", "")
        recipient = config.get("recipient_email", "")

        if not all([smtp_server, sender, password, recipient]):
            raise ValueError("Email config incomplete")

        # Create message
        msg = MIMEText(message)
        msg["Subject"] = f"MT5 Alert - {severity.upper()}"
        msg["From"] = sender
        msg["To"] = recipient

        # Send
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)

    def _start_worker(self):
        """Start background worker thread."""
        if self.worker_active:
            return

        self.worker_active = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def _worker_loop(self):
        """Background worker loop for async sending."""
        while self.worker_active:
            try:
                item = self.send_queue.get(timeout=1.0)

                for channel in item["channels"]:
                    try:
                        self._send_to_channel(
                            item["message"],
                            channel,
                            item.get("severity", "info")
                        )
                    except Exception as e:
                        logger.error(f"Error sending to {channel}: {str(e)}")

            except Exception:
                pass

    def stop_worker(self):
        """Stop background worker."""
        self.worker_active = False
        if self.worker_thread:
            self.worker_thread.join(timeout=2)

    def test_connection(self, channel: Optional[str] = None) -> Dict[str, Any]:
        """
        Test notification channel connection.

        Args:
            channel: Channel to test (or all enabled)

        Returns:
            {
                "status": "success" | "error",
                "results": {channel: bool},
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "results": {},
            "error": None
        }

        try:
            if channel:
                channels = [channel]
            else:
                channels = self.config.get("enabled_channels", ["telegram"])

            test_message = "🔔 MT5 Notifier Test Message"

            for ch in channels:
                try:
                    self._send_to_channel(test_message, ch)
                    result["results"][ch] = True
                except Exception as e:
                    result["results"][ch] = False
                    logger.error(f"Test failed for {ch}: {str(e)}")

            result["status"] = "success" if all(result["results"].values()) else "partial"

        except Exception as e:
            result["error"] = str(e)

        return result

    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled notification channels."""
        return self.config.get("enabled_channels", ["telegram"])

    def set_min_severity(self, severity: str):
        """Set minimum severity filter."""
        self.config["min_severity"] = severity.lower()

    def __del__(self):
        """Cleanup on destruction."""
        self.stop_worker()


# Convenience module-level functions
_mt5_notifier = None


def _get_notifier(config_path: Optional[str] = None) -> MT5Notifier:
    """Get or create MT5Notifier instance."""
    global _mt5_notifier
    if not _mt5_notifier:
        _mt5_notifier = MT5Notifier(config_path)
    return _mt5_notifier


def send(
    message: str,
    severity: str = "info",
    channel: Optional[str] = None,
    async_send: bool = True
) -> Dict[str, Any]:
    """Send notification."""
    return _get_notifier().send(message, severity, channel, async_send)


def send_trade_alert(
    action: str,
    symbol: str,
    volume: float = 0.0,
    entry_price: Optional[float] = None,
    profit: Optional[float] = None,
    comment: str = "",
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """Send trade alert."""
    return _get_notifier().send_trade_alert(
        action, symbol, volume, entry_price, profit, comment, channel
    )


def send_daily_report(
    total_profit: float,
    trade_count: int,
    wins: int = 0,
    losses: int = 0,
    max_drawdown: float = 0.0,
    date: Optional[str] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """Send daily report."""
    return _get_notifier().send_daily_report(
        total_profit, trade_count, wins, losses, max_drawdown, date, channel
    )


def send_error(
    source: str,
    error_message: str,
    ea_name: Optional[str] = None,
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """Send error notification."""
    return _get_notifier().send_error(source, error_message, ea_name, channel)


def send_bot_status(
    status: str,
    ea_name: str,
    details: str = "",
    channel: Optional[str] = None
) -> Dict[str, Any]:
    """Send bot status notification."""
    return _get_notifier().send_bot_status(status, ea_name, details, channel)


def test_connection(channel: Optional[str] = None) -> Dict[str, Any]:
    """Test notification connection."""
    return _get_notifier().test_connection(channel)


def get_enabled_channels() -> List[str]:
    """Get enabled channels."""
    return _get_notifier().get_enabled_channels()


if __name__ == "__main__":
    print("MT5 Notifier Module")
    print("Use: from mt5_notifier import MT5Notifier or convenience functions")
