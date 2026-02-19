"""
MT5 Process Control Tool
========================
Start, stop, restart, and monitor MetaTrader 5 process on Windows.

Dependencies: psutil, pywin32
"""

import os
import sys
import time
import subprocess
import threading
from datetime import datetime
from typing import Dict, Optional, Any

try:
    import psutil
except ImportError:
    psutil = None

try:
    import win32gui
    import win32api
    import win32con
except ImportError:
    win32gui = None
    win32api = None
    win32con = None


class MT5ProcessControl:
    """
    Control and monitor MetaTrader 5 processes on Windows.
    """

    # MT5 Configuration
    MT5_PROCESS_NAME = "terminal.exe"
    MT5_WINDOW_CLASS = "MetaTrader 5"
    MT5_EXECUTABLE_PATHS = [
        r"C:\Program Files\MetaTrader 5\terminal.exe",
        r"C:\Program Files (x86)\MetaTrader 5\terminal.exe",
    ]

    def __init__(self, config_path: Optional[str] = None):
        """Initialize MT5 process control."""
        self.config_path = config_path
        self.watch_thread = None
        self.watch_active = False
        self.mt5_process = None

    @staticmethod
    def _get_mt5_exe() -> Optional[str]:
        """Find MT5 executable path."""
        for path in MT5ProcessControl.MT5_EXECUTABLE_PATHS:
            if os.path.exists(path):
                return path
        return None

    @staticmethod
    def _get_mt5_window() -> Optional[int]:
        """Get MT5 main window handle."""
        if not win32gui:
            return None

        try:
            hwnd = win32gui.FindWindow(None, MT5ProcessControl.MT5_WINDOW_CLASS)
            if hwnd != 0:
                return hwnd

            # Try to find by partial title match
            windows = []
            win32gui.EnumWindows(lambda h, x: windows.append((h, win32gui.GetWindowText(h))), None)
            for hwnd, title in windows:
                if "MetaTrader 5" in title:
                    return hwnd
        except Exception:
            pass

        return None

    def start_mt5(self, account_id: Optional[str] = None, minimized: bool = True) -> Dict[str, Any]:
        """
        Launch MT5.exe with optional account parameter.

        Args:
            account_id: Optional account ID/login to pass to MT5
            minimized: Launch in minimized window if True

        Returns:
            {
                "status": "success" | "error",
                "pid": int | None,
                "startup_time": float (seconds),
                "message": str,
                "error": str | None
            }
        """
        start_time = time.time()
        result = {
            "status": "error",
            "pid": None,
            "startup_time": 0.0,
            "message": "",
            "error": None
        }

        try:
            # Check if MT5 already running
            running_pid = self._get_mt5_pid()
            if running_pid:
                result["status"] = "success"
                result["pid"] = running_pid
                result["message"] = f"MT5 already running (PID: {running_pid})"
                return result

            # Find MT5 executable
            mt5_exe = self._get_mt5_exe()
            if not mt5_exe:
                result["error"] = "MT5 executable not found"
                result["message"] = "Could not locate MT5 at known paths"
                return result

            # Build command
            cmd = [mt5_exe]
            if account_id:
                cmd.append(f"/login:{account_id}")

            # Prepare startup info for minimized window
            startup_info = None
            if minimized:
                if sys.platform == "win32":
                    startup_info = subprocess.STARTUPINFO()
                    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startup_info.wShowWindow = 6  # SW_MINIMIZE

            # Launch process
            process = subprocess.Popen(
                cmd,
                startupinfo=startup_info,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Wait for process to be fully loaded
            self.mt5_process = process
            max_wait = 30  # seconds
            wait_increment = 0.5
            window_found = False

            while (time.time() - start_time) < max_wait:
                if self._get_mt5_window():
                    window_found = True
                    break
                time.sleep(wait_increment)

            if window_found:
                result["status"] = "success"
                result["pid"] = process.pid
                result["startup_time"] = time.time() - start_time
                result["message"] = f"MT5 started successfully (PID: {process.pid})"
            else:
                result["error"] = "MT5 window not detected within timeout"
                result["pid"] = process.pid
                result["startup_time"] = time.time() - start_time

        except Exception as e:
            result["error"] = str(e)
            result["message"] = "Exception occurred during MT5 startup"

        return result

    def stop_mt5(self, force: bool = False) -> Dict[str, Any]:
        """
        Close MT5 process.

        Args:
            force: Use taskkill if True (forceful termination)

        Returns:
            {
                "status": "success" | "error",
                "was_running": bool,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "was_running": False,
            "message": "",
            "error": None
        }

        try:
            # Check if running
            running_pid = self._get_mt5_pid()
            if not running_pid:
                result["status"] = "success"
                result["message"] = "MT5 is not running"
                return result

            result["was_running"] = True

            if force:
                # Use taskkill for forced termination
                try:
                    subprocess.run(
                        ["taskkill", "/PID", str(running_pid), "/F"],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    result["status"] = "success"
                    result["message"] = "MT5 terminated forcefully"
                except subprocess.CalledProcessError as e:
                    result["error"] = f"taskkill failed: {str(e)}"
            else:
                # Graceful close using window message
                hwnd = self._get_mt5_window()
                if hwnd and win32gui:
                    try:
                        win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)

                        # Wait for process to terminate
                        max_wait = 10
                        elapsed = 0
                        while elapsed < max_wait:
                            if not self._get_mt5_pid():
                                result["status"] = "success"
                                result["message"] = "MT5 closed gracefully"
                                return result
                            time.sleep(0.5)
                            elapsed += 0.5

                        # If still running, force kill
                        result["error"] = "Graceful close timeout, forcing termination"
                        self.stop_mt5(force=True)
                    except Exception as e:
                        result["error"] = f"Window message failed: {str(e)}"
                else:
                    # Fallback: use psutil
                    if psutil:
                        try:
                            proc = psutil.Process(running_pid)
                            proc.terminate()
                            proc.wait(timeout=5)
                            result["status"] = "success"
                            result["message"] = "MT5 terminated via psutil"
                        except psutil.TimeoutExpired:
                            proc.kill()
                            result["status"] = "success"
                            result["message"] = "MT5 killed after timeout"
                        except Exception as e:
                            result["error"] = str(e)
                    else:
                        result["error"] = "Cannot close: psutil and win32gui unavailable"

        except Exception as e:
            result["error"] = str(e)

        return result

    def restart_mt5(self, wait_seconds: int = 5) -> Dict[str, Any]:
        """
        Stop and restart MT5 process.

        Args:
            wait_seconds: Seconds to wait between stop and start

        Returns:
            {
                "status": "success" | "error",
                "new_pid": int | None,
                "total_time": float,
                "message": str,
                "error": str | None
            }
        """
        start_time = time.time()
        result = {
            "status": "error",
            "new_pid": None,
            "total_time": 0.0,
            "message": "",
            "error": None
        }

        try:
            # Stop MT5
            stop_result = self.stop_mt5(force=False)
            if not stop_result["was_running"]:
                # Not running, just start
                pass

            # Wait
            time.sleep(wait_seconds)

            # Start MT5
            start_result = self.start_mt5()

            result["status"] = start_result["status"]
            result["new_pid"] = start_result["pid"]
            result["total_time"] = time.time() - start_time
            result["message"] = f"MT5 restarted (PID: {start_result['pid']})"
            result["error"] = start_result["error"]

        except Exception as e:
            result["error"] = str(e)
            result["total_time"] = time.time() - start_time

        return result

    def get_mt5_status(self) -> Dict[str, Any]:
        """
        Check MT5 process status and responsiveness.

        Returns:
            {
                "is_running": bool,
                "is_responsive": bool,
                "pid": int | None,
                "uptime_minutes": float,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "is_running": False,
            "is_responsive": False,
            "pid": None,
            "uptime_minutes": 0.0,
            "message": "",
            "error": None
        }

        try:
            pid = self._get_mt5_pid()

            if not pid:
                result["message"] = "MT5 is not running"
                return result

            result["is_running"] = True
            result["pid"] = pid

            # Check responsiveness via window
            hwnd = self._get_mt5_window()
            if hwnd and win32gui:
                try:
                    # Check if window is hung
                    is_responsive = not win32gui.IsHungAppWindow(hwnd)
                    result["is_responsive"] = is_responsive
                except Exception:
                    result["is_responsive"] = True  # Assume responsive if check fails
            else:
                # Assume responsive if we can't check
                result["is_responsive"] = True

            # Calculate uptime
            if psutil:
                try:
                    proc = psutil.Process(pid)
                    create_time = proc.create_time()
                    uptime_seconds = time.time() - create_time
                    result["uptime_minutes"] = uptime_seconds / 60.0
                except Exception:
                    pass

            status_text = "responsive" if result["is_responsive"] else "not responsive"
            result["message"] = f"MT5 running (PID: {pid}, {status_text})"

        except Exception as e:
            result["error"] = str(e)

        return result

    def watch_mt5(
        self,
        interval: int = 60,
        auto_restart: bool = True,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Start background monitoring of MT5 process.

        Args:
            interval: Check interval in seconds
            auto_restart: Automatically restart if MT5 crashes
            callback: Optional callback function(event_type, data) for notifications

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

            self.watch_active = True

            def _watch_loop():
                """Background watch loop."""
                last_pid = None
                restart_count = 0

                while self.watch_active:
                    try:
                        status = self.get_mt5_status()
                        current_pid = status["pid"]

                        # Detect crash
                        if last_pid and not current_pid:
                            if callback:
                                callback("crash_detected", {"last_pid": last_pid})

                            if auto_restart:
                                restart_result = self.restart_mt5()
                                restart_count += 1
                                if callback:
                                    callback("auto_restart", {
                                        "restart_count": restart_count,
                                        "result": restart_result
                                    })

                        # Check responsiveness
                        elif current_pid and not status["is_responsive"]:
                            if callback:
                                callback("unresponsive", {"pid": current_pid})

                        last_pid = current_pid
                        time.sleep(interval)

                    except Exception as e:
                        if callback:
                            callback("watch_error", {"error": str(e)})
                        time.sleep(interval)

            # Start watch thread
            self.watch_thread = threading.Thread(target=_watch_loop, daemon=True)
            self.watch_thread.start()

            result["status"] = "success"
            result["message"] = "MT5 watch started"

        except Exception as e:
            result["error"] = str(e)
            self.watch_active = False

        return result

    def stop_watch(self) -> Dict[str, Any]:
        """
        Stop background monitoring.

        Returns:
            {
                "status": "success" | "error",
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

    def _get_mt5_pid(self) -> Optional[int]:
        """Get MT5 process ID if running."""
        try:
            if psutil:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        if proc.info['name'].lower() == self.MT5_PROCESS_NAME:
                            return proc.info['pid']
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
        except Exception:
            pass

        return None


# Convenience module-level functions
_mt5_control = None


def _get_controller() -> MT5ProcessControl:
    """Get or create MT5ProcessControl instance."""
    global _mt5_control
    if not _mt5_control:
        _mt5_control = MT5ProcessControl()
    return _mt5_control


def start_mt5(account_id: Optional[str] = None, minimized: bool = True) -> Dict[str, Any]:
    """Start MT5 process."""
    return _get_controller().start_mt5(account_id, minimized)


def stop_mt5(force: bool = False) -> Dict[str, Any]:
    """Stop MT5 process."""
    return _get_controller().stop_mt5(force)


def restart_mt5(wait_seconds: int = 5) -> Dict[str, Any]:
    """Restart MT5 process."""
    return _get_controller().restart_mt5(wait_seconds)


def get_mt5_status() -> Dict[str, Any]:
    """Get MT5 status."""
    return _get_controller().get_mt5_status()


def watch_mt5(
    interval: int = 60,
    auto_restart: bool = True,
    callback: Optional[callable] = None
) -> Dict[str, Any]:
    """Start watching MT5."""
    return _get_controller().watch_mt5(interval, auto_restart, callback)


def stop_watch() -> Dict[str, Any]:
    """Stop watching MT5."""
    return _get_controller().stop_watch()


if __name__ == "__main__":
    print("MT5 Process Control Module")
    print("Use: from mt5_process_control import MT5ProcessControl or convenience functions")
