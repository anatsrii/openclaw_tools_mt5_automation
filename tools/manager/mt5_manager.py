"""
MT5 Manager Tool - Phase 2
============================
System health monitoring, bot status tracking, and account management.

Imports Phase 1 tools:
- mt5_process_control: MT5 status
- mt5_notifier: Alerts
- mt5_scheduler: Session info
"""

import logging
import time
from typing import Dict, List, Any, Optional

from tools.process import get_mt5_status, start_mt5
from tools.notify import send
from tools.scheduler import get_current_session

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

try:
    import win32gui
    import win32con
    import win32api
except ImportError:
    win32gui = None

logger = logging.getLogger(__name__)


class MT5Manager:
    """System health monitoring and account management."""

    def __init__(self):
        pass

    def get_system_health(self) -> Dict[str, Any]:
        """
        Aggregate system health from all Phase 1 tools.

        Returns:
            {status, mt5_running, mt5_responsive, current_session,
             is_market_open, account_health, active_bots, error}
        """
        result = {
            "status": "healthy",
            "mt5_running": False,
            "mt5_responsive": False,
            "current_session": "Unknown",
            "is_market_open": False,
            "account_health": {},
            "active_bots": 0,
            "issues": []
        }

        try:
            # 1. MT5 process status
            mt5_status = get_mt5_status()
            result["mt5_running"] = mt5_status.get("is_running", False)
            result["mt5_responsive"] = mt5_status.get("is_responsive", False)

            if not result["mt5_running"]:
                result["status"] = "critical"
                result["issues"].append("MT5 is not running")
            elif not result["mt5_responsive"]:
                result["status"] = "degraded"
                result["issues"].append("MT5 is running but not responding")

            # 2. Market session
            session_info = get_current_session()
            sessions = session_info.get("sessions", [])
            result["current_session"] = ", ".join(sessions) if sessions else "Off-market"
            result["is_market_open"] = len(sessions) > 0

            # 3. Account health (if MT5 connected)
            if result["mt5_running"] and mt5:
                account = self._get_account_health()
                result["account_health"] = account
                if account.get("margin_level_percent", 100) < 150:
                    result["status"] = "critical"
                    result["issues"].append(f"Low margin level: {account.get('margin_level_percent', 0):.0f}%")

            # 4. Active bots count
            bots = self.list_active_bots()
            result["active_bots"] = len(bots.get("bots", []))

        except Exception as e:
            result["status"] = "critical"
            result["issues"].append(f"Health check error: {str(e)}")
            logger.error(f"Health check error: {str(e)}")

        return result

    def _get_account_health(self) -> Dict[str, Any]:
        """Get account health metrics via MT5 API."""
        health = {}
        try:
            if not mt5.initialize():
                return {"error": "MT5 not connected"}

            info = mt5.account_info()
            if info:
                margin_level = (info.equity / info.margin * 100) if info.margin > 0 else 9999
                health = {
                    "login": info.login,
                    "balance": info.balance,
                    "equity": info.equity,
                    "margin": info.margin,
                    "free_margin": info.margin_free,
                    "margin_level_percent": margin_level,
                    "drawdown_percent": round(
                        (1 - info.equity / info.balance) * 100, 2
                    ) if info.balance > 0 else 0,
                    "server": info.server,
                    "currency": info.currency,
                    "leverage": info.leverage,
                }
        except Exception as e:
            health = {"error": str(e)}
        return health

    def list_active_bots(self) -> Dict[str, Any]:
        """
        List all EAs currently attached to charts.

        Uses MT5 Python API to scan open charts and their EAs.

        Returns:
            {status, bots: [{chart_id, symbol, timeframe, ea_name, is_active}], error}
        """
        result = {
            "status": "error",
            "bots": [],
            "error": None
        }

        try:
            if not mt5:
                result["error"] = "MetaTrader5 library not installed"
                return result

            if not mt5.initialize():
                result["error"] = "MT5 not connected"
                return result

            # Get all symbols with open positions (proxy for active charts)
            positions = mt5.positions_get()
            symbols_with_positions = set()
            if positions:
                for pos in positions:
                    symbols_with_positions.add(pos.symbol)

            # Get active orders too
            orders = mt5.orders_get()
            if orders:
                for order in orders:
                    symbols_with_positions.add(order.symbol)

            # Check terminal info for EA activity
            terminal_info = mt5.terminal_info()
            bots = []

            # MT5 doesn't expose chart EA info directly via API
            # Use win32gui to scan window titles as fallback
            if win32gui:
                bots = self._scan_charts_win32()
            else:
                # Fallback: report symbols with open positions as "active"
                for symbol in symbols_with_positions:
                    bots.append({
                        "chart_id": None,
                        "symbol": symbol,
                        "timeframe": "Unknown",
                        "ea_name": "Active (position open)",
                        "is_active": True,
                        "source": "positions"
                    })

            result["status"] = "success"
            result["bots"] = bots
            logger.info(f"Found {len(bots)} active charts/bots")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"list_active_bots error: {str(e)}")

        return result

    def _scan_charts_win32(self) -> List[Dict]:
        """Scan MT5 window titles to detect charts and EAs."""
        bots = []

        def enum_handler(hwnd, ctx):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                # MT5 chart windows have format: "SYMBOL,TF (EA Name)"
                if "," in title and ("Expert" in title or "EA" in title or "Bot" in title):
                    parts = title.split(",")
                    symbol = parts[0].strip()
                    rest = parts[1] if len(parts) > 1 else ""
                    # Extract timeframe and EA name
                    tf_match = rest.split(" ")[0] if rest else "M1"
                    ea_match = rest[rest.find("(")+1:rest.find(")")] if "(" in rest else "Unknown"
                    bots.append({
                        "chart_id": hwnd,
                        "symbol": symbol,
                        "timeframe": tf_match,
                        "ea_name": ea_match,
                        "is_active": True,
                        "source": "win32"
                    })

        win32gui.EnumWindows(enum_handler, None)
        return bots

    def switch_account(
        self,
        account_id: int,
        password: str,
        server: str,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Switch MT5 to a different trading account.

        Args:
            account_id: Account login number
            password: Account password
            server: Broker server name
            timeout: Seconds to wait for connection

        Returns:
            {status, account_info, error}
        """
        result = {
            "status": "error",
            "account_info": {},
            "error": None
        }

        try:
            if not mt5:
                result["error"] = "MetaTrader5 library not installed"
                return result

            # Initialize MT5
            if not mt5.initialize():
                result["error"] = "Failed to initialize MT5"
                return result

            # Login to new account
            logger.info(f"Switching to account {account_id} on {server}")
            login_result = mt5.login(account_id, password=password, server=server)

            if not login_result:
                error_code = mt5.last_error()
                result["error"] = f"Login failed: {error_code}"
                send(f"❌ Account switch failed: {account_id} | Error: {error_code}", severity="critical")
                return result

            # Wait for connection to stabilize
            time.sleep(2)

            # Verify connection
            account_info = mt5.account_info()
            if account_info and account_info.login == account_id:
                result["status"] = "success"
                result["account_info"] = {
                    "login": account_info.login,
                    "balance": account_info.balance,
                    "equity": account_info.equity,
                    "server": account_info.server,
                    "currency": account_info.currency,
                    "leverage": account_info.leverage,
                    "is_demo": "demo" in account_info.server.lower()
                }
                is_demo = result["account_info"]["is_demo"]
                acct_type = "DEMO" if is_demo else "REAL"
                send(
                    f"✅ Switched to {acct_type} account {account_id} | Balance: {account_info.balance:.2f} {account_info.currency}",
                    severity="info"
                )
                logger.info(f"Successfully switched to {acct_type} account {account_id}")
            else:
                result["error"] = "Login appeared to succeed but account verification failed"
                send(f"⚠️ Account switch verification failed: {account_id}", severity="warning")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"switch_account error: {str(e)}")
            send(f"❌ Account switch error: {str(e)}", severity="critical")

        return result

    def get_connection_quality(self) -> Dict[str, Any]:
        """
        Check MT5 connection quality to broker.

        Returns:
            {status, ping_ms, is_connected, bars_available, error}
        """
        result = {
            "status": "error",
            "ping_ms": None,
            "is_connected": False,
            "bars_available": 0,
            "error": None
        }

        try:
            if not mt5 or not mt5.initialize():
                result["error"] = "MT5 not connected"
                return result

            terminal_info = mt5.terminal_info()
            if terminal_info:
                result["is_connected"] = terminal_info.connected
                result["ping_ms"] = getattr(terminal_info, "ping_last", None)

            # Check data availability (XAUUSDm M1)
            rates = mt5.copy_rates_from_pos("XAUUSDm", mt5.TIMEFRAME_M1, 0, 10)
            result["bars_available"] = len(rates) if rates is not None else 0
            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)

        return result


# Module-level singleton
_manager = None


def _get_manager() -> MT5Manager:
    global _manager
    if not _manager:
        _manager = MT5Manager()
    return _manager


def get_system_health() -> Dict[str, Any]:
    """Get full system health."""
    return _get_manager().get_system_health()


def list_active_bots() -> Dict[str, Any]:
    """List all active bots/charts."""
    return _get_manager().list_active_bots()


def switch_account(account_id: int, password: str, server: str) -> Dict[str, Any]:
    """Switch MT5 account."""
    return _get_manager().switch_account(account_id, password, server)


def get_connection_quality() -> Dict[str, Any]:
    """Check connection quality."""
    return _get_manager().get_connection_quality()


if __name__ == "__main__":
    print("MT5 Manager Tool (Phase 2)")
    health = get_system_health()
    print(f"System status: {health['status']}")
    print(f"MT5 running: {health['mt5_running']}")
    print(f"Session: {health['current_session']}")
