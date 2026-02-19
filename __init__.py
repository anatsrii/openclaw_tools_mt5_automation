"""MT5 Automation Skill for OpenClaw"""

__version__ = "1.0.0"
__author__ = "OpenClaw"
__description__ = "MetaTrader 5 process automation and management skill"

from .tools.process import MT5Process
from .tools.files import MT5FileManager
from .tools.logs import MT5LogParser
from .tools.notify import MT5Notifier
from .tools.scheduler import MT5Scheduler

__all__ = [
    "MT5Process",
    "MT5FileManager",
    "MT5LogParser",
    "MT5Notifier",
    "MT5Scheduler"
]
