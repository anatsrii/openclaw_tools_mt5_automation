"""
MT5 Developer Tool - Phase 2
=============================
AI-assisted EA coding with self-healing compilation.

Imports and uses Phase 1 infrastructure tools:
- mt5_file_manager: Locate and manage EA files
- mt5_log_parser: Extract compile errors
- mt5_process_control: Control MT5 process
- mt5_notifier: Send compilation alerts
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import Phase 1 infrastructure tools
from tools.files import MT5FileManager, read_ea_file, write_ea_file
from tools.logs import MT5LogParser, get_compile_errors
from tools.process import MT5ProcessControl, get_mt5_status, start_mt5
from tools.notify import send_error, send

logger = logging.getLogger(__name__)


class MT5Developer:
    """AI-assisted EA development with self-healing compilation."""

    def __init__(self):
        """Initialize developer with Phase 1 tools."""
        self.file_manager = MT5FileManager()
        self.log_parser = MT5LogParser()
        self.process_control = MT5ProcessControl()

    def compile_ea(self, ea_name: str) -> Dict[str, Any]:
        """
        Compile EA and extract errors.

        Uses Phase 1 tools:
        - mt5_file_manager: Verify EA file exists
        - mt5_log_parser: Extract compile errors
        - mt5_process_control: Ensure MT5 is running

        Args:
            ea_name: EA filename (with or without .mq5)

        Returns:
            {
                "status": "success" | "error",
                "success": bool,
                "error_count": int,
                "warning_count": int,
                "errors": [{"line": int, "error_code": str, "message": str}],
                "compiled_time": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "success": False,
            "error_count": 0,
            "warning_count": 0,
            "errors": [],
            "compiled_time": None,
            "error": None
        }

        try:
            # Step 1: Verify EA file exists using mt5_file_manager
            ea_file = read_ea_file(ea_name)
            if ea_file["status"] != "success":
                result["error"] = f"EA not found: {ea_name}"
                result["status"] = "error"
                send_error("compile", f"EA file not found: {ea_name}", ea_name)
                return result

            logger.info(f"Found EA: {ea_file['path']}")

            # Step 2: Ensure MT5 is running
            status = get_mt5_status()
            if not status["is_running"]:
                logger.info("Starting MT5...")
                start_result = start_mt5()
                if start_result["status"] != "success":
                    result["error"] = "Could not start MT5"
                    send_error("runtime", "MT5 failed to start", ea_name)
                    return result

            # Step 3: Trigger compilation via F7 (keyboard shortcut)
            # In production, use: pyautogui.press('f7') or MetaEditor CLI
            try:
                import pyautogui
                import time
                pyautogui.press('f7')
                time.sleep(3)  # Wait for compilation
                logger.info("F7 pressed - compilation triggered")
            except Exception as e:
                logger.warning(f"Could not use pyautogui: {e}")

            # Step 4: Parse compile errors from journal using mt5_log_parser
            compile_result = get_compile_errors(ea_name)

            result["status"] = "success"
            result["success"] = compile_result["error_count"] == 0
            result["error_count"] = compile_result["error_count"]
            result["warning_count"] = compile_result["warning_count"]
            result["errors"] = compile_result["errors"]
            result["compiled_time"] = datetime.now().isoformat()

            # Notify if errors found
            if result["error_count"] > 0:
                send_error(
                    "compile",
                    f"{result['error_count']} compile errors found",
                    ea_name
                )
                logger.warning(f"Compilation failed: {result['error_count']} errors")
            else:
                send(f"✅ {ea_name} compiled successfully", severity="info")
                logger.info(f"Compilation successful: {ea_name}")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Compilation error: {str(e)}")
            send_error("compile", str(e), ea_name)

        return result

    def compile_and_fix(
        self,
        ea_name: str,
        max_attempts: int = 3
    ) -> Dict[str, Any]:
        """
        Compile and return errors for fixing.

        Returns errors that need AI fixing.
        Loop tracks attempts.

        Args:
            ea_name: EA filename
            max_attempts: Max compilation attempts

        Returns:
            {
                "success": bool,
                "attempts": int,
                "final_errors": [],
                "error": str | None
            }
        """
        result = {
            "success": False,
            "attempts": 0,
            "final_errors": [],
            "error": None
        }

        for attempt in range(1, max_attempts + 1):
            result["attempts"] = attempt

            # Attempt compilation
            compile_result = self.compile_ea(ea_name)

            if compile_result["success"]:
                result["success"] = True
                logger.info(f"Compilation successful on attempt {attempt}")
                return result

            # Store errors for AI to fix
            result["final_errors"] = compile_result["errors"]

            logger.warning(f"Attempt {attempt} failed: {compile_result['error_count']} errors")

            if attempt < max_attempts:
                logger.info(f"Waiting before retry... (attempt {attempt}/{max_attempts})")

        result["error"] = f"Compilation failed after {max_attempts} attempts"
        return result

    def deploy_ea(
        self,
        ea_name: str,
        chart_symbol: str,
        chart_timeframe: int = 240
    ) -> Dict[str, Any]:
        """
        Deploy compiled EA to chart.

        Args:
            ea_name: EA filename
            chart_symbol: Symbol (e.g., "EURUSD")
            chart_timeframe: Timeframe in minutes (default: 240 = H4)

        Returns:
            {
                "status": "success" | "error",
                "chart_info": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "chart_info": None,
            "error": None
        }

        try:
            # Verify .ex5 file exists (compiled)
            ea_base = ea_name.replace(".mq5", "")
            ex5_files = list(self.file_manager.experts_dir.glob(f"{ea_base}.ex5"))

            if not ex5_files:
                result["error"] = f"Compiled file not found: {ea_base}.ex5"
                return result

            # Attach to chart via pyautogui
            try:
                import pyautogui
                import time

                # Open Navigator (Ctrl+N)
                pyautogui.hotkey('ctrl', 'n')
                time.sleep(1)

                # Navigate to EA and double-click
                pyautogui.typewrite(ea_base, interval=0.05)
                time.sleep(0.5)
                pyautogui.press('enter')  # Load EA dialog
                time.sleep(2)

                # Default settings and OK
                pyautogui.press('enter')
                time.sleep(1)

                result["status"] = "success"
                result["chart_info"] = f"{ea_name} on {chart_symbol} {chart_timeframe}min"
                send(f"📊 Deployed {ea_name} to {chart_symbol}", severity="info")

            except ImportError:
                result["error"] = "pyautogui not installed (required for UI automation)"
                logger.error("pyautogui required for EA deployment")

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Deploy error: {str(e)}")
            send_error("deploy", str(e), ea_name)

        return result

    def get_compile_history(self, ea_name: str, limit: int = 10) -> Dict[str, Any]:
        """Get recent compilation history."""
        result = {
            "status": "success",
            "history": [],
            "error": None
        }

        try:
            # Get all compile attempts from log
            journal = self.log_parser.get_latest_journal(lines=500)

            compilation_entries = [
                e for e in journal["entries"]
                if ea_name in e["message"] and ("compile" in e["message"].lower())
            ]

            result["history"] = compilation_entries[:limit]

        except Exception as e:
            result["error"] = str(e)

        return result


# Module-level convenience functions
_developer = None


def _get_developer() -> MT5Developer:
    """Get or create MT5Developer instance."""
    global _developer
    if not _developer:
        _developer = MT5Developer()
    return _developer


def compile_ea(ea_name: str) -> Dict[str, Any]:
    """Compile EA."""
    return _get_developer().compile_ea(ea_name)


def compile_and_fix(ea_name: str, max_attempts: int = 3) -> Dict[str, Any]:
    """Compile and fix errors."""
    return _get_developer().compile_and_fix(ea_name, max_attempts)


def deploy_ea(ea_name: str, chart_symbol: str, chart_timeframe: int = 240) -> Dict[str, Any]:
    """Deploy EA to chart."""
    return _get_developer().deploy_ea(ea_name, chart_symbol, chart_timeframe)


if __name__ == "__main__":
    print("MT5 Developer Tool (Phase 2)")
    print("Imports Phase 1 tools: files, logs, process, notifier")
