"""MT5 Operator - Package Init"""

from .mt5_operator import (
    MT5Operator,
    get_open_positions,
    close_all_positions,
    get_account_summary
)

__all__ = [
    "MT5Operator",
    "get_open_positions",
    "close_all_positions",
    "get_account_summary"
]
