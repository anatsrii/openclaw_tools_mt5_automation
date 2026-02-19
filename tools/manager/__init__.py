"""MT5 Manager - Phase 2 Tool"""

from .mt5_manager import (
    MT5Manager,
    get_system_health,
    list_active_bots,
    switch_account
)

__all__ = [
    "MT5Manager",
    "get_system_health",
    "list_active_bots",
    "switch_account"
]
