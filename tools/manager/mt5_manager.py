"""MT5 Manager Tool - Phase 2 (Skeleton)

System health and account management.

Imports Phase 1 tools:
- mt5_process_control: MT5 status
- mt5_notifier: Alerts
- mt5_scheduler: Session info
- mt5_operator: Account info
"""

import logging
from typing import Dict, List, Any

from tools.process import get_mt5_status
from tools.notify import send
from tools.scheduler import get_current_session

logger = logging.getLogger(__name__)


class MT5Manager:
    """System health monitoring and management."""

    def __init__(self):
        """Initialize manager."""
        pass

    def get_system_health(self) -> Dict[str, Any]:
        """
        Get complete system health.

        Aggregates Phase 1 tools:
        - mt5_process_control: MT5 status
        - mt5_scheduler: Market session
        - mt5_operator: Account

        Returns: {
            "status": "healthy" | "degraded" | "critical",
            "mt5_running": bool,
            "current_session": str,
            "active_bots": int,
            "connection_quality": str,
            "account_health": dict
        }
        """
        result = {
            "status": "healthy",
            "mt5_running": False,
            "current_session": None,
            "active_bots": 0,
            "connection_quality": "unknown",
            "account_health": {}
        }

        try:
            # Get MT5 status from Phase 1
            mt5_status = get_mt5_status()
            result["mt5_running"] = mt5_status.get("is_running", False)

            # Get session from Phase 1
            session = get_current_session()
            result["current_session"] = ", ".join(session.get("sessions", []))

            # TODO: Get active bots (scan charts)
            # TODO: Get account health

        except Exception as e:
            result["status"] = "critical"
            logger.error(f"Health check error: {str(e)}")

        return result

    def list_active_bots(self) -> Dict[str, Any]:
        """
        List all active EAs on charts.

        Returns: {
            "status": "success" | "error",
            "bots": [
                {"chart": str, "ea_name": str, "symbol": str, "status": str}
            ],
            "error": str | None
        }
        """
        result = {
            "status": "error",
            "bots": [],
            "error": None
        }

        try:
            # TODO: Implement chart scanning
            # Use pyautogui to check Navigator for attached EAs
            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)

        return result

    def switch_account(
        self,
        account_id: str,
        password: str,
        server: str
    ) -> Dict[str, Any]:
        """
        Switch MT5 account.

        Uses: mt5_operator connection

        Args:
            account_id: Account login
            password: Account password
            server: Server name

        Returns: {
            "status": "success" | "error",
            "account_info": dict,
            "error": str | None
        }
        """
        result = {
            "status": "error",
            "account_info": {},
            "error": None
        }

        try:
            # TODO: Implement account switching
            # 1. mt5.login(account_id, password, server)
            # 2. Verify connection
            # 3. Get account info
            result["status"] = "success"
            send(f"✅ Switched to account {account_id}", severity="info")

        except Exception as e:
            result["error"] = str(e)
            send(f"❌ Account switch failed: {str(e)}", severity="critical")

        return result


_manager = None


def _get_manager():
    global _manager
    if not _manager:
        _manager = MT5Manager()
    return _manager


def get_system_health() -> Dict[str, Any]:
    """Get system health."""
    return _get_manager().get_system_health()


def list_active_bots() -> Dict[str, Any]:
    """List active bots."""
    return _get_manager().list_active_bots()


def switch_account(account_id: str, password: str, server: str) -> Dict[str, Any]:
    """Switch account."""
    return _get_manager().switch_account(account_id, password, server)
