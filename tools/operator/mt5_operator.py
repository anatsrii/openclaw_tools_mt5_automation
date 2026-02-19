"""
MT5 Operator Tool - Phase 2
=============================
Live trade management and emergency controls.

Requires: pip install MetaTrader5

Imports Phase 1 tools:
- mt5_process_control: Ensure MT5 running
- mt5_notifier: Send trade alerts
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    import MetaTrader5 as mt5
except ImportError:
    mt5 = None

from tools.process import get_mt5_status, start_mt5
from tools.notify import send_trade_alert, send

logger = logging.getLogger(__name__)


class MT5Operator:
    """Live trade operations and emergency controls."""

    def __init__(self):
        """Initialize operator."""
        if not mt5:
            raise RuntimeError("MetaTrader5 library required: pip install MetaTrader5")

        self.account_info = None
        self._connect()

    def _connect(self):
        """Connect to MT5."""
        if not mt5.initialize():
            raise RuntimeError("Failed to initialize MT5 connection")
        self.account_info = mt5.account_info()
        logger.info(f"Connected to MT5 account {self.account_info.login}")

    def get_open_positions(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all open positions.

        Uses Phase 1: mt5_process_control to ensure MT5 is running

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            {
                "status": "success" | "error",
                "positions": [
                    {
                        "ticket": int,
                        "symbol": str,
                        "action": str,           # BUY or SELL
                        "volume": float,
                        "entry_price": float,
                        "current_price": float,
                        "profit": float,
                        "pnl_percent": float,
                        "open_time": str,
                        "comment": str
                    }
                ],
                "total_pnl": float,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "positions": [],
            "total_pnl": 0.0,
            "error": None
        }

        try:
            positions = mt5.positions_get(symbol=symbol)

            if not positions:
                result["status"] = "success"
                return result

            total_pnl = 0.0

            for pos in positions:
                symbol_info = mt5.symbol_info(pos.symbol)
                current_price = symbol_info.bid if pos.type == 0 else symbol_info.ask

                pnl = (current_price - pos.price_open) * pos.volume * (1 if pos.type == 0 else -1)
                pnl_percent = (pnl / (pos.price_open * pos.volume)) * 100

                result["positions"].append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "action": "BUY" if pos.type == 0 else "SELL",
                    "volume": pos.volume,
                    "entry_price": pos.price_open,
                    "current_price": current_price,
                    "profit": pnl,
                    "pnl_percent": pnl_percent,
                    "open_time": datetime.fromtimestamp(pos.time).isoformat(),
                    "comment": pos.comment
                })

                total_pnl += pnl

            result["status"] = "success"
            result["total_pnl"] = total_pnl

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error getting positions: {str(e)}")

        return result

    def close_all_positions(
        self,
        symbol: Optional[str] = None,
        comment: str = "emergency"
    ) -> Dict[str, Any]:
        """
        Close all or symbol-specific positions.

        Uses Phase 1: mt5_notifier to alert

        Args:
            symbol: Close only this symbol (or all if None)
            comment: Close comment

        Returns:
            {
                "status": "success" | "error",
                "closed_count": int,
                "total_pnl": float,
                "closed_positions": [],
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "closed_count": 0,
            "total_pnl": 0.0,
            "closed_positions": [],
            "error": None
        }

        try:
            positions = mt5.positions_get(symbol=symbol)

            if not positions:
                result["status"] = "success"
                return result

            for pos in positions:
                # Close position
                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": pos.symbol,
                    "volume": pos.volume,
                    "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                    "position": pos.ticket,
                    "comment": comment
                }

                result_trade = mt5.order_send(request)

                if result_trade.retcode == mt5.TRADE_RETCODE_DONE:
                    result["closed_count"] += 1
                    result["closed_positions"].append(pos.symbol)

                    # Notify
                    send_trade_alert(
                        "CLOSE",
                        pos.symbol,
                        volume=pos.volume,
                        comment=comment
                    )

            result["status"] = "success"
            final_positions = self.get_open_positions()
            result["total_pnl"] = final_positions.get("total_pnl", 0.0)

            # Send alert
            if result["closed_count"] > 0:
                send(f"🚨 Closed {result['closed_count']} positions", severity="critical")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error closing positions: {str(e)}")
            send(f"❌ Error closing positions: {str(e)}", severity="critical")

        return result

    def get_account_summary(self) -> Dict[str, Any]:
        """
        Get account statistics.

        Returns:
            {
                "status": "success" | "error",
                "account": {
                    "login": int,
                    "balance": float,
                    "equity": float,
                    "margin": float,
                    "free_margin": float,
                    "margin_percent": float,
                    "drawdown_percent": float
                },
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "account": {},
            "error": None
        }

        try:
            info = mt5.account_info()

            if info:
                margin_percent = (info.margin / info.account_equity * 100) if info.account_equity > 0 else 0
                drawdown = ((info.account_equity - info.balance) / info.balance * 100) if info.balance > 0 else 0

                result["account"] = {
                    "login": info.login,
                    "balance": info.balance,
                    "equity": info.account_equity,
                    "margin": info.margin,
                    "free_margin": info.margin_free,
                    "margin_percent": margin_percent,
                    "drawdown_percent": drawdown
                }
                result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)

        return result


# Module functions
_operator = None


def _get_operator() -> MT5Operator:
    """Get or create MT5Operator instance."""
    global _operator
    if not _operator:
        _operator = MT5Operator()
    return _operator


def get_open_positions(symbol: Optional[str] = None) -> Dict[str, Any]:
    """Get open positions."""
    return _get_operator().get_open_positions(symbol)


def close_all_positions(symbol: Optional[str] = None, comment: str = "emergency") -> Dict[str, Any]:
    """Close all positions."""
    return _get_operator().close_all_positions(symbol, comment)


def get_account_summary() -> Dict[str, Any]:
    """Get account summary."""
    return _get_operator().get_account_summary()


if __name__ == "__main__":
    print("MT5 Operator Tool (Phase 2)")
    print("Requires: pip install MetaTrader5")
