"""
MT5 Log Parser Tool
===================
Read and parse MT5 log files for errors, trades, and compile results.

Dependencies: re, datetime, collections, (optional: watchdog)
"""

import os
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from collections import deque
import logging
import threading

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

logger = logging.getLogger(__name__)


class MT5LogParser:
    """
    Parse MetaTrader 5 log files for trading data, errors, and diagnostics.
    """

    # Log patterns
    # Standard MT5 log format: [2025.02.19 14:30:45.123] message
    LOG_ENTRY_PATTERN = re.compile(
        r'\[(\d{4}\.\d{2}\.\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3})\]\s+(.+)'
    )

    # Error/Warning patterns
    ERROR_PATTERN = re.compile(r"error\s+(\d+):\s+(.+)", re.IGNORECASE)
    WARNING_PATTERN = re.compile(r"warning\s+(\d+):\s+(.+)", re.IGNORECASE)
    COMPILE_ERROR_PATTERN = re.compile(
        r"'(.+?)'\s+-\s+(\d+):(\d+):\s+(.+)"
    )

    # Trade patterns
    TRADE_PATTERN = re.compile(
        r"(buy|sell|buyat|sellat|close|modify|open|position)\s+(.+?)\s+(\d+\.?\d*)\s+(.+?)\s+at\s+([\d.]+)",
        re.IGNORECASE
    )
    PROFIT_PATTERN = re.compile(r"(profit|loss):\s+([\d.+-]+)", re.IGNORECASE)

    # Anomaly patterns
    ANOMALIES = {
        "connection_lost": re.compile(r"connection lost|disconnect", re.IGNORECASE),
        "invalid_account": re.compile(r"invalid account|invalid password", re.IGNORECASE),
        "margin_call": re.compile(r"margin|insufficient|margin call", re.IGNORECASE),
        "server_error": re.compile(r"error|failed|socket", re.IGNORECASE),
    }

    def __init__(self, terminal_data_path: Optional[str] = None):
        """
        Initialize MT5 Log Parser.

        Args:
            terminal_data_path: Path to MT5 terminal data directory
        """
        if terminal_data_path:
            self.terminal_path = Path(terminal_data_path)
        else:
            # Try to load from config
            config_path = Path(__file__).parent.parent.parent / "config" / "mt5_paths.json"
            if config_path.exists():
                try:
                    import json
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        self.terminal_path = Path(config.get("mt5_data_path", ""))
                except Exception:
                    self.terminal_path = Path.home() / "AppData/Roaming/MetaQuotes/Terminal"
            else:
                self.terminal_path = Path.home() / "AppData/Roaming/MetaQuotes/Terminal"

        # Setup log directories
        self.logs_dir = self.terminal_path / "logs"
        self.tester_logs_dir = self.terminal_path / "tester" / "logs"

        # Watch state
        self.watch_active = False
        self.watch_thread = None
        self.last_position = {}

    def get_latest_journal(self, lines: int = 100) -> Dict[str, Any]:
        """
        Read last N lines from today's journal.

        Args:
            lines: Number of lines to read (default: 100)

        Returns:
            {
                "status": "success" | "error",
                "entries": [
                    {
                        "timestamp": str,      # ISO format
                        "type": str,           # "info", "error", "warning"
                        "source": str,         # "Expert", "System", etc.
                        "message": str
                    }
                ],
                "file_path": str,
                "total_lines": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "entries": [],
            "file_path": None,
            "total_lines": 0,
            "error": None
        }

        try:
            # Get today's journal file
            today = datetime.now().strftime("%Y%m%d")
            journal_path = self.logs_dir / f"{today}.log"

            if not journal_path.exists():
                result["error"] = f"Journal not found: {journal_path}"
                return result

            # Read file
            with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()

            result["total_lines"] = len(all_lines)

            # Parse last N lines
            for line in all_lines[-lines:]:
                entry = self._parse_log_line(line)
                if entry:
                    result["entries"].append(entry)

            result["status"] = "success"
            result["file_path"] = str(journal_path)

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error reading journal: {str(e)}")

        return result

    def get_compile_errors(self, ea_name: str) -> Dict[str, Any]:
        """
        Parse compile errors for specific EA.

        Args:
            ea_name: EA name (with or without .mq5)

        Returns:
            {
                "status": "success" | "error",
                "errors": [
                    {
                        "line": int,
                        "error_code": str,
                        "message": str,
                        "is_error": bool,
                        "is_warning": bool
                    }
                ],
                "error_count": int,
                "warning_count": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "errors": [],
            "error_count": 0,
            "warning_count": 0,
            "error": None
        }

        try:
            # Get today's journal
            today = datetime.now().strftime("%Y%m%d")
            journal_path = self.logs_dir / f"{today}.log"

            if not journal_path.exists():
                result["error"] = f"Journal not found: {journal_path}"
                return result

            # Normalize EA name
            if not ea_name.endswith(".mq5"):
                ea_name = ea_name + ".mq5"

            # Read and parse
            with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Look for compile errors
            in_compile_section = False
            for line in content.split('\n'):
                # Check if this is a compile section for our EA
                if ea_name in line and "compile" in line.lower():
                    in_compile_section = True

                if in_compile_section:
                    # Try to match error/warning patterns
                    error_match = self.ERROR_PATTERN.search(line)
                    warning_match = self.WARNING_PATTERN.search(line)
                    compile_match = self.COMPILE_ERROR_PATTERN.search(line)

                    if error_match or compile_match:
                        if compile_match:
                            file, line_num, col, msg = compile_match.groups()
                            result["errors"].append({
                                "line": int(line_num),
                                "error_code": col,
                                "message": msg.strip(),
                                "is_error": True,
                                "is_warning": False
                            })
                            result["error_count"] += 1
                        elif error_match:
                            code, msg = error_match.groups()
                            result["errors"].append({
                                "line": None,
                                "error_code": code,
                                "message": msg.strip(),
                                "is_error": True,
                                "is_warning": False
                            })
                            result["error_count"] += 1

                    elif warning_match:
                        code, msg = warning_match.groups()
                        result["errors"].append({
                            "line": None,
                            "error_code": code,
                            "message": msg.strip(),
                            "is_error": False,
                            "is_warning": True
                        })
                        result["warning_count"] += 1

            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error parsing compile errors: {str(e)}")

        return result

    def get_trade_history(self, hours: int = 24) -> Dict[str, Any]:
        """
        Extract trade events from journal.

        Args:
            hours: Look back N hours (default: 24)

        Returns:
            {
                "status": "success" | "error",
                "trades": [
                    {
                        "time": str,          # ISO format
                        "action": str,        # "BUY", "SELL", "CLOSE"
                        "symbol": str,
                        "volume": float,
                        "price": float,
                        "profit": float | None
                    }
                ],
                "trade_count": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "trades": [],
            "trade_count": 0,
            "error": None
        }

        try:
            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Read logs from the last few days
            for day_offset in range(max(hours // 24 + 1, 3)):
                log_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y%m%d")
                journal_path = self.logs_dir / f"{log_date}.log"

                if not journal_path.exists():
                    continue

                with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        entry = self._parse_log_line(line)
                        if not entry:
                            continue

                        # Check if entry is after cutoff
                        try:
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if entry_time < cutoff_time:
                                continue
                        except ValueError:
                            continue

                        # Look for trade patterns
                        trade = self._extract_trade(entry["message"])
                        if trade:
                            trade["time"] = entry["timestamp"]
                            result["trades"].append(trade)

            result["status"] = "success"
            result["trade_count"] = len(result["trades"])

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error parsing trade history: {str(e)}")

        return result

    def get_ea_prints(self, ea_name: str, hours: int = 4) -> Dict[str, Any]:
        """
        Extract Print() output from specific EA.

        Args:
            ea_name: EA name (with or without .mq5)
            hours: Look back N hours (default: 4)

        Returns:
            {
                "status": "success" | "error",
                "prints": [
                    {
                        "timestamp": str,    # ISO format
                        "message": str
                    }
                ],
                "count": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "prints": [],
            "count": 0,
            "error": None
        }

        try:
            # Normalize EA name
            if ea_name.endswith(".mq5"):
                ea_name = ea_name[:-4]

            # Calculate cutoff time
            cutoff_time = datetime.now() - timedelta(hours=hours)

            # Read logs
            for day_offset in range(max(hours // 24 + 1, 2)):
                log_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y%m%d")
                journal_path = self.logs_dir / f"{log_date}.log"

                if not journal_path.exists():
                    continue

                with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        # Look for EA section
                        if f"[{ea_name}]" in line or ea_name in line.lower():
                            entry = self._parse_log_line(line)
                            if entry:
                                try:
                                    entry_time = datetime.fromisoformat(entry["timestamp"])
                                    if entry_time >= cutoff_time:
                                        result["prints"].append({
                                            "timestamp": entry["timestamp"],
                                            "message": entry["message"]
                                        })
                                except ValueError:
                                    pass

            result["status"] = "success"
            result["count"] = len(result["prints"])

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error parsing EA prints: {str(e)}")

        return result

    def watch_journal(
        self,
        callback_fn: Callable,
        filter_keywords: Optional[List[str]] = None,
        check_interval: float = 0.5
    ) -> Dict[str, Any]:
        """
        Monitor journal file in real-time.

        Args:
            callback_fn: Function to call for each new entry: callback(entry)
            filter_keywords: Only trigger on lines containing these keywords
            check_interval: Check interval in seconds

        Returns:
            {
                "status": "success" | "error",
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "message": "",
            "error": None
        }

        try:
            if self.watch_active:
                result["status"] = "success"
                result["message"] = "Watch already active"
                return result

            # Get today's journal
            today = datetime.now().strftime("%Y%m%d")
            journal_path = self.logs_dir / f"{today}.log"

            if not journal_path.exists():
                result["error"] = f"Journal not found: {journal_path}"
                return result

            self.watch_active = True
            self.last_position[str(journal_path)] = 0

            def _watch_loop():
                """Background watch loop."""
                while self.watch_active:
                    try:
                        # Get current file size
                        current_size = journal_path.stat().st_size
                        last_pos = self.last_position.get(str(journal_path), 0)

                        if current_size > last_pos:
                            # New content added
                            with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                                f.seek(last_pos)
                                new_lines = f.readlines()
                                self.last_position[str(journal_path)] = f.tell()

                            for line in new_lines:
                                # Apply keyword filter
                                if filter_keywords:
                                    if not any(kw.lower() in line.lower() for kw in filter_keywords):
                                        continue

                                # Parse and callback
                                entry = self._parse_log_line(line)
                                if entry:
                                    try:
                                        callback_fn(entry)
                                    except Exception as e:
                                        logger.error(f"Callback error: {str(e)}")

                        time.sleep(check_interval)

                    except Exception as e:
                        logger.error(f"Watch loop error: {str(e)}")
                        time.sleep(check_interval)

            # Start watch thread
            self.watch_thread = threading.Thread(target=_watch_loop, daemon=True)
            self.watch_thread.start()

            result["status"] = "success"
            result["message"] = "Journal watch started"

        except Exception as e:
            result["error"] = str(e)
            self.watch_active = False

        return result

    def stop_watch(self) -> Dict[str, Any]:
        """
        Stop watching journal.

        Returns:
            {
                "status": "success",
                "message": str
            }
        """
        result = {
            "status": "success",
            "message": "Watch stopped"
        }

        self.watch_active = False

        if self.watch_thread:
            self.watch_thread.join(timeout=2)

        return result

    def detect_anomalies(self, hours: int = 1) -> Dict[str, Any]:
        """
        Detect error conditions in logs.

        Args:
            hours: Look back N hours (default: 1)

        Returns:
            {
                "status": "success" | "error",
                "anomalies": [
                    {
                        "type": str,         # connection_lost, invalid_account, etc.
                        "severity": str,     # "critical", "warning"
                        "message": str,
                        "timestamp": str,
                        "count": int
                    }
                ],
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "anomalies": [],
            "error": None
        }

        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            anomaly_counts = {}

            # Read logs
            for day_offset in range(max(hours // 24 + 1, 1)):
                log_date = (datetime.now() - timedelta(days=day_offset)).strftime("%Y%m%d")
                journal_path = self.logs_dir / f"{log_date}.log"

                if not journal_path.exists():
                    continue

                with open(journal_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        entry = self._parse_log_line(line)
                        if not entry:
                            continue

                        # Check timestamp
                        try:
                            entry_time = datetime.fromisoformat(entry["timestamp"])
                            if entry_time < cutoff_time:
                                continue
                        except ValueError:
                            continue

                        # Check for anomalies
                        for anomaly_type, pattern in self.ANOMALIES.items():
                            if pattern.search(entry["message"]):
                                if anomaly_type not in anomaly_counts:
                                    anomaly_counts[anomaly_type] = {
                                        "count": 0,
                                        "last_message": entry["message"],
                                        "last_time": entry["timestamp"]
                                    }
                                anomaly_counts[anomaly_type]["count"] += 1

            # Format results
            for anomaly_type, data in anomaly_counts.items():
                severity = "critical" if data["count"] > 5 else "warning"

                result["anomalies"].append({
                    "type": anomaly_type,
                    "severity": severity,
                    "message": data["last_message"],
                    "timestamp": data["last_time"],
                    "count": data["count"]
                })

            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error detecting anomalies: {str(e)}")

        return result

    def _parse_log_line(self, line: str) -> Optional[Dict[str, str]]:
        """Parse single log line."""
        match = self.LOG_ENTRY_PATTERN.match(line)
        if not match:
            return None

        timestamp_str, message = match.groups()

        # Convert timestamp to ISO format
        try:
            dt = datetime.strptime(timestamp_str, "%Y.%m.%d %H:%M:%S.%f")
            iso_time = dt.isoformat()
        except ValueError:
            iso_time = timestamp_str

        # Determine type
        msg_lower = message.lower()
        if "error" in msg_lower:
            msg_type = "error"
        elif "warning" in msg_lower:
            msg_type = "warning"
        else:
            msg_type = "info"

        # Extract source
        source = "System"
        if "[Expert" in message:
            source = "Expert"
        elif "[Account" in message:
            source = "Account"

        return {
            "timestamp": iso_time,
            "type": msg_type,
            "source": source,
            "message": message.strip()
        }

    def _extract_trade(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract trade info from message."""
        match = self.TRADE_PATTERN.search(message)
        if not match:
            return None

        action, symbol, volume, _, price = match.groups()

        # Look for profit
        profit_match = self.PROFIT_PATTERN.search(message)
        profit = None
        if profit_match:
            profit = float(profit_match.group(2))

        return {
            "action": action.upper(),
            "symbol": symbol.strip(),
            "volume": float(volume),
            "price": float(price),
            "profit": profit
        }


# Convenience module-level functions
_mt5_log_parser = None


def _get_parser(terminal_data_path: Optional[str] = None) -> MT5LogParser:
    """Get or create MT5LogParser instance."""
    global _mt5_log_parser
    if not _mt5_log_parser:
        _mt5_log_parser = MT5LogParser(terminal_data_path)
    return _mt5_log_parser


def get_latest_journal(lines: int = 100) -> Dict[str, Any]:
    """Get latest journal entries."""
    return _get_parser().get_latest_journal(lines)


def get_compile_errors(ea_name: str) -> Dict[str, Any]:
    """Get compile errors for EA."""
    return _get_parser().get_compile_errors(ea_name)


def get_trade_history(hours: int = 24) -> Dict[str, Any]:
    """Get trade history."""
    return _get_parser().get_trade_history(hours)


def get_ea_prints(ea_name: str, hours: int = 4) -> Dict[str, Any]:
    """Get EA Print() statements."""
    return _get_parser().get_ea_prints(ea_name, hours)


def watch_journal(
    callback_fn: Callable,
    filter_keywords: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Watch journal in real-time."""
    return _get_parser().watch_journal(callback_fn, filter_keywords)


def stop_watch() -> Dict[str, Any]:
    """Stop watching journal."""
    return _get_parser().stop_watch()


def detect_anomalies(hours: int = 1) -> Dict[str, Any]:
    """Detect anomalies in logs."""
    return _get_parser().detect_anomalies(hours)


if __name__ == "__main__":
    print("MT5 Log Parser Module")
    print("Use: from mt5_log_parser import MT5LogParser or convenience functions")
