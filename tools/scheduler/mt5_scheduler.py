"""
MT5 Scheduler Tool
==================
Schedule MT5 tasks based on time and market sessions.

Supports multiple scheduling options:
- Cron expressions
- Market session-based scheduling
- Interval-based scheduling
- Market hours tracking

Dependencies: apscheduler, pytz
"""

import uuid
import logging
import threading
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import pytz

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger
except ImportError:
    BackgroundScheduler = None
    CronTrigger = None
    IntervalTrigger = None

logger = logging.getLogger(__name__)


class MarketSession(Enum):
    """Market trading sessions."""
    ASIA = "Asia"
    LONDON = "London"
    NEW_YORK = "NY"


class MT5Scheduler:
    """
    Schedule and manage MT5 automation tasks based on time and market sessions.
    """

    # Market sessions (UTC+7 Bangkok time)
    SESSIONS = {
        MarketSession.ASIA: {
            "name": "Asia",
            "open": time(0, 0),      # 00:00
            "close": time(8, 0),     # 08:00
            "utc_offset": 7
        },
        MarketSession.LONDON: {
            "name": "London",
            "open": time(14, 0),     # 14:00
            "close": time(23, 0),    # 23:00
            "utc_offset": 7
        },
        MarketSession.NEW_YORK: {
            "name": "NY",
            "open": time(19, 0),     # 19:00
            "close": time(4, 0),     # 04:00 next day
            "utc_offset": 7
        }
    }

    # Overlap periods (UTC+7)
    OVERLAP_PERIODS = [
        {
            "name": "London-NY",
            "start": time(19, 0),
            "end": time(23, 0)
        }
    ]

    # Market holidays (YYYY-MM-DD)
    MARKET_HOLIDAYS = [
        # Christmas
        "2025-12-25",
        "2026-12-25",
        # New Year
        "2025-01-01",
        "2026-01-01",
    ]

    def __init__(self, timezone: str = "UTC+7"):
        """
        Initialize MT5 Scheduler.

        Args:
            timezone: Timezone for scheduling (default: UTC+7 for Bangkok)
        """
        self.timezone = pytz.timezone("Asia/Bangkok") if timezone == "UTC+7" else pytz.timezone(timezone)
        self.scheduler = None
        self.tasks = {}
        self._init_scheduler()

    def _init_scheduler(self):
        """Initialize APScheduler."""
        if not BackgroundScheduler:
            logger.warning("APScheduler not available, using basic scheduling")
            return

        self.scheduler = BackgroundScheduler(timezone=self.timezone)
        self.scheduler.start()

    def get_current_session(self) -> Dict[str, Any]:
        """
        Get current active market session(s).

        Returns:
            {
                "status": "success" | "error",
                "sessions": ["London", "NY"],
                "is_overlap": bool,
                "local_time": str,        # ISO format
                "utc_time": str,          # ISO format
                "next_session": str,      # Name of next session
                "minutes_until_next": int,
                "error": str | None
            }
        """
        result = {
            "status": "success",
            "sessions": [],
            "is_overlap": False,
            "local_time": None,
            "utc_time": None,
            "next_session": None,
            "minutes_until_next": 0,
            "error": None
        }

        try:
            # Get current time
            utc_now = datetime.now(pytz.UTC)
            local_now = utc_now.astimezone(self.timezone)

            result["local_time"] = local_now.isoformat()
            result["utc_time"] = utc_now.isoformat()

            # Check which sessions are active
            current_time = local_now.time()

            # Asia session (00:00 - 08:00)
            if time(0, 0) <= current_time < time(8, 0):
                result["sessions"].append("Asia")

            # London session (14:00 - 23:00)
            if time(14, 0) <= current_time < time(23, 0):
                result["sessions"].append("London")

            # NY session (19:00 - 04:00 next day)
            if current_time >= time(19, 0) or current_time < time(4, 0):
                result["sessions"].append("NY")

            # Check for overlap
            if time(19, 0) <= current_time < time(23, 0):
                result["is_overlap"] = True

            # Get next session
            next_session = self._get_next_session(current_time)
            if next_session:
                result["next_session"] = next_session["name"]
                result["minutes_until_next"] = next_session["minutes"]

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error getting current session: {str(e)}")

        return result

    def schedule_task(
        self,
        task_fn: Callable,
        schedule_type: str,
        task_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Schedule a task.

        Args:
            task_fn: Function to execute
            schedule_type: "cron", "session_open", "session_close", "interval"
            task_id: Custom task ID (auto-generated if not provided)
            **kwargs: Schedule-specific arguments
                - cron: "cron_expr" (e.g., "0 6 * * *")
                - session_open: "session" (e.g., "London")
                - session_close: "session"
                - interval: "minutes" (e.g., 5)

        Returns:
            {
                "status": "success" | "error",
                "task_id": str,
                "task_fn": str,
                "schedule": dict,
                "next_run": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "task_id": None,
            "task_fn": task_fn.__name__ if hasattr(task_fn, "__name__") else str(task_fn),
            "schedule": {},
            "next_run": None,
            "error": None
        }

        try:
            if not self.scheduler:
                raise RuntimeError("APScheduler not initialized")

            # Generate task ID
            if not task_id:
                task_id = str(uuid.uuid4())[:8]

            # Schedule based on type
            if schedule_type == "cron":
                cron_expr = kwargs.get("cron_expr")
                if not cron_expr:
                    raise ValueError("cron_expr required for cron scheduling")

                job = self.scheduler.add_job(
                    task_fn,
                    CronTrigger.from_crontab(cron_expr),
                    id=task_id,
                    name=f"{task_id}_{task_fn.__name__}",
                    replace_existing=True
                )
                result["schedule"]["type"] = "cron"
                result["schedule"]["expression"] = cron_expr

            elif schedule_type == "session_open":
                session = kwargs.get("session")
                if not session:
                    raise ValueError("session required for session_open scheduling")

                # Get next session open time
                next_open = self._get_session_open_time(session)

                job = self.scheduler.add_job(
                    task_fn,
                    'cron',
                    day_of_week='0-4',  # Mon-Fri
                    hour=next_open.hour,
                    minute=next_open.minute,
                    id=task_id,
                    name=f"{task_id}_{session}_open",
                    replace_existing=True
                )
                result["schedule"]["type"] = "session_open"
                result["schedule"]["session"] = session

            elif schedule_type == "session_close":
                session = kwargs.get("session")
                if not session:
                    raise ValueError("session required for session_close scheduling")

                next_close = self._get_session_close_time(session)

                job = self.scheduler.add_job(
                    task_fn,
                    'cron',
                    day_of_week='0-4',
                    hour=next_close.hour,
                    minute=next_close.minute,
                    id=task_id,
                    name=f"{task_id}_{session}_close",
                    replace_existing=True
                )
                result["schedule"]["type"] = "session_close"
                result["schedule"]["session"] = session

            elif schedule_type == "interval":
                minutes = kwargs.get("minutes")
                if not minutes:
                    raise ValueError("minutes required for interval scheduling")

                job = self.scheduler.add_job(
                    task_fn,
                    IntervalTrigger(minutes=minutes),
                    id=task_id,
                    name=f"{task_id}_interval_{minutes}m",
                    replace_existing=True
                )
                result["schedule"]["type"] = "interval"
                result["schedule"]["minutes"] = minutes

            else:
                raise ValueError(f"Unknown schedule_type: {schedule_type}")

            # Store task info
            self.tasks[task_id] = {
                "id": task_id,
                "function": task_fn,
                "schedule_type": schedule_type,
                "schedule": result["schedule"],
                "created_at": datetime.now().isoformat()
            }

            result["status"] = "success"
            result["task_id"] = task_id
            if job:
                result["next_run"] = job.next_run_time

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error scheduling task: {str(e)}")

        return result

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel a scheduled task.

        Args:
            task_id: Task ID to cancel

        Returns:
            {
                "status": "success" | "error",
                "task_id": str,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "task_id": task_id,
            "message": "",
            "error": None
        }

        try:
            if not self.scheduler:
                raise RuntimeError("APScheduler not initialized")

            self.scheduler.remove_job(task_id)

            if task_id in self.tasks:
                del self.tasks[task_id]

            result["status"] = "success"
            result["message"] = f"Task {task_id} cancelled"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error cancelling task: {str(e)}")

        return result

    def list_tasks(self) -> Dict[str, Any]:
        """
        List all scheduled tasks.

        Returns:
            {
                "status": "success" | "error",
                "tasks": [
                    {
                        "id": str,
                        "name": str,
                        "schedule": dict,
                        "next_run": str,
                        "created_at": str
                    }
                ],
                "count": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "tasks": [],
            "count": 0,
            "error": None
        }

        try:
            if not self.scheduler:
                raise RuntimeError("APScheduler not initialized")

            jobs = self.scheduler.get_jobs()

            for job in jobs:
                result["tasks"].append({
                    "id": job.id,
                    "name": job.name,
                    "schedule": self.tasks.get(job.id, {}).get("schedule", {}),
                    "next_run": str(job.next_run_time) if job.next_run_time else None,
                    "created_at": self.tasks.get(job.id, {}).get("created_at")
                })

            result["status"] = "success"
            result["count"] = len(result["tasks"])

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error listing tasks: {str(e)}")

        return result

    def is_market_open(self, symbol: str = "XAUUSD") -> Dict[str, Any]:
        """
        Check if market is currently open.

        Args:
            symbol: Trading symbol (default: XAUUSD/GOLD)

        Returns:
            {
                "status": "success" | "error",
                "is_open": bool,
                "current_session": str | None,
                "next_open": str,         # ISO format
                "time_until_open": str,   # HH:MM:SS
                "is_weekend": bool,
                "is_holiday": bool,
                "error": str | None
            }
        """
        result = {
            "status": "success",
            "is_open": False,
            "current_session": None,
            "next_open": None,
            "time_until_open": None,
            "is_weekend": False,
            "is_holiday": False,
            "error": None
        }

        try:
            # Get current time
            utc_now = datetime.now(pytz.UTC)
            local_now = utc_now.astimezone(self.timezone)

            # Check weekend
            if local_now.weekday() >= 5:  # Saturday = 5, Sunday = 6
                result["is_weekend"] = True
                result["next_open"] = self._get_next_opening_time().isoformat()
                return result

            # Check holiday
            date_str = local_now.strftime("%Y-%m-%d")
            if date_str in self.MARKET_HOLIDAYS:
                result["is_holiday"] = True
                result["next_open"] = self._get_next_opening_time().isoformat()
                return result

            # Check if market is open
            session_info = self.get_current_session()
            result["is_open"] = len(session_info["sessions"]) > 0
            result["current_session"] = ", ".join(session_info["sessions"]) if session_info["sessions"] else None

            if not result["is_open"]:
                next_open = self._get_next_opening_time()
                result["next_open"] = next_open.isoformat()

                time_until = next_open - local_now
                hours, remainder = divmod(int(time_until.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                result["time_until_open"] = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Error checking market open: {str(e)}")

        return result

    def wait_for_session(
        self,
        session_name: str,
        check_interval: float = 60.0
    ) -> Dict[str, Any]:
        """
        Wait until specific session opens.

        Args:
            session_name: Session name ("Asia", "London", "NY")
            check_interval: Check interval in seconds

        Returns:
            {
                "status": "success" | "error",
                "session": str,
                "opened_at": str,
                "wait_duration": float,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "session": session_name,
            "opened_at": None,
            "wait_duration": 0.0,
            "error": None
        }

        try:
            start_time = datetime.now(self.timezone)
            session_names = [s.value for s in MarketSession]

            if session_name not in session_names:
                raise ValueError(f"Unknown session: {session_name}")

            # Wait in loop
            while True:
                session_info = self.get_current_session()

                if session_name in session_info["sessions"]:
                    open_time = datetime.now(self.timezone)
                    result["status"] = "success"
                    result["opened_at"] = open_time.isoformat()
                    result["wait_duration"] = (open_time - start_time).total_seconds()
                    return result

                # Wait before next check
                threading.Event().wait(check_interval)

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error waiting for session: {str(e)}")

        return result

    def _get_next_session(self, current_time: time) -> Optional[Dict[str, Any]]:
        """Get next market session."""
        sessions_order = [
            (time(0, 0), "Asia"),
            (time(8, 0), "London"),  # After Asia closes
            (time(14, 0), "London"),
            (time(23, 0), "NY"),     # After London closes
            (time(19, 0), "NY"),
        ]

        for session_time, session_name in sessions_order:
            if current_time < session_time:
                minutes_until = int((datetime.combine(datetime.today(), session_time) -
                                   datetime.combine(datetime.today(), current_time)).total_seconds() / 60)
                return {"name": session_name, "minutes": minutes_until}

        # Next day
        minutes_until = int((24 * 3600 - (datetime.combine(datetime.today(), current_time) -
                                         datetime.combine(datetime.today(), time(0, 0))).total_seconds()) / 60)
        return {"name": "Asia", "minutes": minutes_until}

    def _get_session_open_time(self, session: str) -> time:
        """Get session open time."""
        for sess, info in self.SESSIONS.items():
            if sess.value == session:
                return info["open"]
        return time(0, 0)

    def _get_session_close_time(self, session: str) -> time:
        """Get session close time."""
        for sess, info in self.SESSIONS.items():
            if sess.value == session:
                return info["close"]
        return time(0, 0)

    def _get_next_opening_time(self) -> datetime:
        """Get next market opening time."""
        utc_now = datetime.now(pytz.UTC)
        local_now = utc_now.astimezone(self.timezone)

        # If before Monday 00:00, return Monday 00:00
        if local_now.weekday() == 6:  # Sunday
            days_until_monday = 1
        elif local_now.weekday() > 4:  # Saturday
            days_until_monday = 2 - (local_now.weekday() - 4)
        else:
            days_until_monday = 0

        next_open = local_now + timedelta(days=days_until_monday)
        return next_open.replace(hour=0, minute=0, second=0, microsecond=0)

    def create_default_schedules(self) -> Dict[str, Any]:
        """
        Create recommended default schedules.

        Returns:
            {
                "status": "success",
                "schedules": {task_id: task_info},
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "schedules": {},
            "error": None
        }

        try:
            # Daily report at 06:00
            r1 = self.schedule_task(
                lambda: logger.info("Daily report scheduled"),
                "cron",
                task_id="daily_report",
                cron_expr="0 6 * * *"
            )
            if r1["status"] == "success":
                result["schedules"]["daily_report"] = r1

            # Check MT5 status every 5 minutes
            r2 = self.schedule_task(
                lambda: logger.info("MT5 status check"),
                "interval",
                task_id="mt5_status_check",
                minutes=5
            )
            if r2["status"] == "success":
                result["schedules"]["mt5_status_check"] = r2

            # Pre-market restart Sunday 22:00
            r3 = self.schedule_task(
                lambda: logger.info("Pre-market restart"),
                "cron",
                task_id="premarket_restart",
                cron_expr="0 22 * * 0"
            )
            if r3["status"] == "success":
                result["schedules"]["premarket_restart"] = r3

            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error creating default schedules: {str(e)}")

        return result

    def shutdown(self) -> Dict[str, Any]:
        """
        Shutdown the scheduler.

        Returns:
            {status, message}
        """
        result = {
            "status": "success",
            "message": "Scheduler shutdown complete"
        }

        try:
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()
        except Exception as e:
            result["status"] = "error"
            result["message"] = str(e)

        return result


# Convenience module-level functions
_mt5_scheduler = None


def _get_scheduler(timezone: str = "UTC+7") -> MT5Scheduler:
    """Get or create MT5Scheduler instance."""
    global _mt5_scheduler
    if not _mt5_scheduler:
        _mt5_scheduler = MT5Scheduler(timezone)
    return _mt5_scheduler


def get_current_session() -> Dict[str, Any]:
    """Get current market session."""
    return _get_scheduler().get_current_session()


def schedule_task(
    task_fn: Callable,
    schedule_type: str,
    task_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Schedule a task."""
    return _get_scheduler().schedule_task(task_fn, schedule_type, task_id, **kwargs)


def cancel_task(task_id: str) -> Dict[str, Any]:
    """Cancel a task."""
    return _get_scheduler().cancel_task(task_id)


def list_tasks() -> Dict[str, Any]:
    """List all tasks."""
    return _get_scheduler().list_tasks()


def is_market_open(symbol: str = "XAUUSD") -> Dict[str, Any]:
    """Check if market is open."""
    return _get_scheduler().is_market_open(symbol)


def wait_for_session(session_name: str, check_interval: float = 60.0) -> Dict[str, Any]:
    """Wait for session."""
    return _get_scheduler().wait_for_session(session_name, check_interval)


def create_default_schedules() -> Dict[str, Any]:
    """Create default schedules."""
    return _get_scheduler().create_default_schedules()


if __name__ == "__main__":
    print("MT5 Scheduler Module")
    print("Use: from mt5_scheduler import MT5Scheduler or convenience functions")
