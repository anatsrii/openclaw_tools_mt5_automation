"""
MT5 Optimizer Tool - Phase 2
==============================
Parameter optimization with walk-forward analysis.

Imports Phase 1 tools:
- mt5_file_manager: Manage EA files and .set files
- mt5_process_control: Run MT5 optimization silently
- mt5_notifier: Notify on optimization complete
"""

import json
import os
import re
import time
import logging
import configparser
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from tools.files import MT5FileManager
from tools.process import MT5ProcessControl, get_mt5_status
from tools.notify import send

logger = logging.getLogger(__name__)


class MT5Optimizer:
    """Parameter optimization with walk-forward testing."""

    def __init__(self):
        self.file_manager = MT5FileManager()
        self.process_control = MT5ProcessControl()

        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        from config.config import get_config
        _cfg = get_config()

        self.mt5_exe   = _cfg.terminal_exe
        self.data_path = _cfg.data_path
        self.cfg       = _cfg

    def _write_optimization_ini(
        self,
        ea_name: str,
        symbol: str,
        timeframe: int,
        date_from: str,
        date_to: str,
        param_ranges: Dict[str, Tuple],
        criterion: int = 0
    ) -> Path:
        """
        Write optimization .ini config.

        param_ranges: {"param_name": (min, max, step)}
        criterion: 0=Balance max, 1=Drawdown min, 2=ProfitFactor, 3=Sharpe
        """
        # Sanitize ea_name for filename (replace path separators)
        safe_ea_name = ea_name.replace("\\", "_").replace("/", "_")
        ini_path = self.data_path / f"optimize_{safe_ea_name}_{symbol}.ini"

        config = configparser.ConfigParser()
        config["Tester"] = {
            "Expert": ea_name,
            "Symbol": symbol,
            "Period": str(timeframe),
            "Optimization": "1",           # Enable optimization
            "OptimizationCriterion": str(criterion),
            "Model": "1",                  # 1-min OHLC (faster)
            "FromDate": date_from,
            "ToDate": date_to,
            "ForwardMode": "0",
            "Deposit": str(self.cfg.deposit),
            "Currency": self.cfg.currency,
            "Leverage": str(self.cfg.leverage),
        }

        # Write param ranges to [TesterInputs] section
        config["TesterInputs"] = {}
        for param, (min_val, max_val, step) in param_ranges.items():
            # Format: "param_name=value||min||max||step||enabled"
            config["TesterInputs"][param] = f"{min_val}||{min_val}||{max_val}||{step}||1"

        with open(ini_path, "w") as f:
            config.write(f)

        logger.info(f"Wrote optimization ini: {ini_path}")
        return ini_path

    def _parse_optimization_results(self) -> List[Dict]:
        """
        Parse optimization results from MT5 cache.
        MT5 saves results as XML/CSV in Tester folder.
        """
        results = []
        tester_path = self.data_path / "Tester"

        # Look for optimization cache files
        cache_files = sorted(
            tester_path.glob("*.xml") if tester_path.exists() else [],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        if not cache_files:
            # Try CSV format
            cache_files = sorted(
                tester_path.glob("*.csv") if tester_path.exists() else [],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )

        if not cache_files:
            logger.warning("No optimization result files found")
            return results

        result_file = cache_files[0]
        logger.info(f"Parsing optimization results: {result_file}")

        try:
            with open(result_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Simple CSV parse (MT5 optimization results are CSV)
            lines = content.strip().split("\n")
            if len(lines) < 2:
                return results

            headers = [h.strip() for h in lines[0].split(",")]

            for line in lines[1:]:
                values = [v.strip() for v in line.split(",")]
                if len(values) == len(headers):
                    row = dict(zip(headers, values))
                    try:
                        results.append({
                            "params": {k: v for k, v in row.items()
                                       if k not in ("Result", "Trades", "Profit", "DD%")},
                            "profit_factor": float(row.get("Profit Factor", 0) or 0),
                            "net_profit": float(row.get("Profit", 0) or 0),
                            "drawdown": float(row.get("DD%", 0) or 0),
                            "total_trades": int(row.get("Trades", 0) or 0),
                        })
                    except (ValueError, KeyError):
                        continue

        except Exception as e:
            logger.error(f"Error parsing optimization results: {str(e)}")

        return results

    def _run_mt5_optimization(self, ini_path: Path, timeout: int = 1800) -> bool:
        """Launch MT5 and run optimization silently."""
        status = get_mt5_status()
        if status.get("is_running"):
            self.process_control.stop_mt5(force=False)
            time.sleep(3)

        cmd = [str(self.mt5_exe), f"/config:{ini_path}"]
        logger.info(f"Starting optimization: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd)

        start_time = time.time()
        while proc.poll() is None:
            if time.time() - start_time > timeout:
                proc.terminate()
                logger.error(f"Optimization timeout after {timeout}s")
                return False
            time.sleep(10)

        return True

    def run_optimization(
        self,
        ea_name: str,
        param_ranges: Dict[str, Tuple],
        symbol: str,
        periods: List[str],
        top_n: int = 10,
        criterion: int = 0,
        timeout: int = 1800
    ) -> Dict[str, Any]:
        """
        Run parameter optimization silently.

        Args:
            ea_name: EA to optimize
            param_ranges: {"param": (min, max, step)}
            symbol: Symbol (e.g. "XAUUSDm")
            periods: [date_from, date_to] e.g. ["2024.01.01", "2024.12.31"]
            top_n: Return top N parameter sets
            criterion: 0=Balance, 1=Drawdown, 2=ProfitFactor, 3=Sharpe
            timeout: Max seconds

        Returns:
            {status, top_params (sorted best→worst), total_combinations, error}
        """
        result = {
            "status": "error",
            "top_params": [],
            "total_combinations": 0,
            "ea_name": ea_name,
            "symbol": symbol,
            "error": None
        }

        try:
            date_from = periods[0] if len(periods) > 0 else "2024.01.01"
            date_to = periods[1] if len(periods) > 1 else "2024.12.31"

            # Write ini
            ini_path = self._write_optimization_ini(
                ea_name, symbol, 1, date_from, date_to, param_ranges, criterion
            )

            # Run MT5 optimization
            send(f"⚙️ Optimization started: {ea_name} {symbol}", severity="info")
            success = self._run_mt5_optimization(ini_path, timeout)

            if not success:
                result["error"] = "Optimization timeout or failed"
                return result

            # Parse results
            all_results = self._parse_optimization_results()
            result["total_combinations"] = len(all_results)

            # Sort by profit factor, return top N
            all_results.sort(key=lambda x: x.get("profit_factor", 0), reverse=True)
            result["top_params"] = all_results[:top_n]
            result["status"] = "success"

            best_pf = result["top_params"][0]["profit_factor"] if result["top_params"] else 0
            send(
                f"✅ Optimization done: {ea_name} | {len(all_results)} combos | Best PF={best_pf:.2f}",
                severity="info"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Optimization error: {str(e)}")
            send(f"❌ Optimization failed: {ea_name} | {str(e)}", severity="critical")

        return result

    def _split_walk_forward_windows(
        self,
        date_from: str,
        date_to: str,
        n_windows: int,
        test_ratio: float
    ) -> List[Dict]:
        """
        Split date range into IS/OOS windows for walk-forward.

        Returns list of:
          {"is_from", "is_to", "oos_from", "oos_to"}
        """
        fmt = "%Y.%m.%d"
        start = datetime.strptime(date_from, fmt)
        end = datetime.strptime(date_to, fmt)
        total_days = (end - start).days

        window_days = total_days // n_windows
        oos_days = int(window_days * test_ratio)
        is_days = window_days - oos_days

        windows = []
        cursor = start
        for i in range(n_windows):
            is_from = cursor
            is_to = is_from + timedelta(days=is_days)
            oos_from = is_to + timedelta(days=1)
            oos_to = oos_from + timedelta(days=oos_days)

            if oos_to > end:
                oos_to = end

            windows.append({
                "window": i + 1,
                "is_from": is_from.strftime(fmt),
                "is_to": is_to.strftime(fmt),
                "oos_from": oos_from.strftime(fmt),
                "oos_to": oos_to.strftime(fmt),
            })

            cursor = oos_from
            if cursor >= end:
                break

        return windows

    def walk_forward_test(
        self,
        ea_name: str,
        symbol: str,
        param_ranges: Dict[str, Tuple],
        date_from: str = "2022.01.01",
        date_to: str = "2024.12.31",
        n_windows: int = 4,
        test_ratio: float = 0.3,
        timeout_per_window: int = 900
    ) -> Dict[str, Any]:
        """
        Walk-forward optimization and out-of-sample validation.

        Splits data into N windows, optimizes on IS portion,
        validates on OOS portion for each window.

        Args:
            ea_name: EA name
            symbol: Symbol
            param_ranges: Params to optimize
            date_from / date_to: Full date range
            n_windows: Number of walk-forward windows
            test_ratio: OOS ratio (0.3 = 30%)
            timeout_per_window: Seconds per optimization

        Returns:
            {status, wf_efficiency, windows, best_params, summary, error}
        """
        result = {
            "status": "error",
            "wf_efficiency": 0.0,
            "windows": [],
            "best_params": {},
            "summary": {},
            "error": None
        }

        try:
            windows = self._split_walk_forward_windows(
                date_from, date_to, n_windows, test_ratio
            )

            send(
                f"⚙️ Walk-Forward started: {ea_name} | {n_windows} windows",
                severity="info"
            )

            window_results = []
            for window in windows:
                logger.info(f"Window {window['window']}: IS {window['is_from']}→{window['is_to']} | OOS {window['oos_from']}→{window['oos_to']}")

                # 1. Optimize on IS period
                opt = self.run_optimization(
                    ea_name, param_ranges, symbol,
                    [window["is_from"], window["is_to"]],
                    top_n=1,
                    timeout=timeout_per_window
                )

                best_params = opt["top_params"][0] if opt["top_params"] else {}
                is_pf = best_params.get("profit_factor", 0)

                # 2. Validate best params on OOS period
                # Build set file from best params
                oos_pf = 0.0
                if best_params:
                    set_path = self._write_params_set_file(ea_name, best_params.get("params", {}))
                    from tools.tester import run_backtest
                    oos_result = run_backtest(
                        ea_name, symbol, 1,
                        window["oos_from"], window["oos_to"],
                        set_file=str(set_path),
                        timeout=300
                    )
                    oos_pf = oos_result.get("profit_factor", 0)

                window_results.append({
                    **window,
                    "is_profit_factor": is_pf,
                    "oos_profit_factor": oos_pf,
                    "best_params": best_params.get("params", {}),
                    "efficiency": (oos_pf / is_pf) if is_pf > 0 else 0
                })

            # Calculate WF efficiency (avg OOS PF / avg IS PF)
            avg_is = sum(w["is_profit_factor"] for w in window_results) / len(window_results)
            avg_oos = sum(w["oos_profit_factor"] for w in window_results) / len(window_results)
            wf_efficiency = (avg_oos / avg_is) if avg_is > 0 else 0

            # Best params = from the window with highest OOS PF
            best_window = max(window_results, key=lambda w: w["oos_profit_factor"])

            result["status"] = "success"
            result["wf_efficiency"] = round(wf_efficiency, 4)
            result["windows"] = window_results
            result["best_params"] = best_window["best_params"]
            result["summary"] = {
                "n_windows": len(window_results),
                "avg_is_pf": round(avg_is, 4),
                "avg_oos_pf": round(avg_oos, 4),
                "wf_efficiency": round(wf_efficiency, 4),
                "is_robust": wf_efficiency >= 0.7,
            }

            send(
                f"✅ Walk-Forward done: {ea_name} | WF efficiency={wf_efficiency:.2f} | {'Robust ✅' if wf_efficiency >= 0.7 else 'Not robust ⚠️'}",
                severity="info"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Walk-forward error: {str(e)}")
            send(f"❌ Walk-Forward failed: {ea_name} | {str(e)}", severity="critical")

        return result

    def _write_params_set_file(self, ea_name: str, params: Dict) -> Path:
        """Write .set file from param dict for OOS validation."""
        set_path = self.data_path / f"{ea_name}_wf_oos.set"
        lines = []
        for key, value in params.items():
            lines.append(f"{key}={value}")
        with open(set_path, "w") as f:
            f.write("\n".join(lines))
        return set_path


# Module-level singleton
_optimizer = None


def _get_optimizer() -> MT5Optimizer:
    global _optimizer
    if not _optimizer:
        _optimizer = MT5Optimizer()
    return _optimizer


def run_optimization(
    ea_name: str,
    param_ranges: Dict[str, Tuple],
    symbol: str = None,
    periods: List[str] = None,
    top_n: int = None
) -> Dict[str, Any]:
    """Run optimization — ถ้าไม่ระบุ symbol/periods/top_n จะใช้ค่า default จาก user_config.json"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.config import get_config
    _cfg = get_config()
    return _get_optimizer().run_optimization(
        ea_name, param_ranges,
        symbol  or _cfg.default_symbol,
        periods or [_cfg.default_date_from, _cfg.default_date_to],
        top_n   or _cfg.top_n_results
    )


def walk_forward_test(
    ea_name: str,
    param_ranges: Dict[str, Tuple],
    symbol: str = None,
    date_from: str = None,
    date_to: str = None,
    n_windows: int = None,
    test_ratio: float = None
) -> Dict[str, Any]:
    """Walk-forward test — ถ้าไม่ระบุ จะใช้ค่า default จาก user_config.json"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from config.config import get_config
    _cfg = get_config()
    return _get_optimizer().walk_forward_test(
        ea_name,
        symbol    or _cfg.default_symbol,
        param_ranges,
        date_from or _cfg.default_date_from,
        date_to   or _cfg.default_date_to,
        n_windows or _cfg.wf_windows,
        test_ratio or _cfg.wf_test_ratio
    )


if __name__ == "__main__":
    print("MT5 Optimizer Tool (Phase 2)")
    print("Usage: run_optimization('SukarEA', {'tp': (20,100,5)}, 'XAUUSDm', ['2024.01.01','2024.12.31'])")
