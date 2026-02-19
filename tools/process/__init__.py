"""MT5 Process Control Tools"""

from .mt5_process_control import (
    MT5ProcessControl,
    start_mt5,
    stop_mt5,
    restart_mt5,
    get_mt5_status,
    watch_mt5,
    stop_watch
)

# Backward compatibility alias
MT5Process = MT5ProcessControl

__all__ = [
    "MT5ProcessControl",
    "MT5Process",
    "start_mt5",
    "stop_mt5",
    "restart_mt5",
    "get_mt5_status",
    "watch_mt5",
    "stop_watch"
]
