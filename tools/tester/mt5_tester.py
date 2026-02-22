"""
MT5 Tester Tool - Phase 2
==========================
Run Strategy Tester silently and collect structured results.

Flow ที่ถูกต้อง:
  1. MT5 ต้องปิดอยู่ก่อน (headless mode)
  2. Generate INI แบบ dynamic (path, symbol, dates, report ทุกอย่าง)
  3. Launch: terminal64.exe /config:<ini>  → MT5 รัน backtest แล้วปิดตัวเอง
  4. รอ report file ปรากฏ (ไม่ใช่รอ process exit อย่างเดียว)
  5. Parse HTML report → return structured dict
"""

import re
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from tools.files import MT5FileManager
from tools.process import MT5ProcessControl, get_mt5_status
from tools.logs import MT5LogParser
from tools.notify import send

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.config import get_config

logger = logging.getLogger(__name__)

TIMEFRAME_MAP = {
    1: 1, 5: 5, 15: 15, 30: 30,
    60: 60, 240: 240, 1440: 1440
}


class MT5Tester:
    """Run backtests silently via CLI and collect structured results."""

    def __init__(self):
        self.file_manager    = MT5FileManager()
        self.process_control = MT5ProcessControl()
        self.log_parser      = MT5LogParser()
        self.cfg             = get_config()

        # Dynamic paths — ทุกอย่างมาจาก config ไม่มี hardcode
        self.mt5_exe     = self.cfg.terminal_exe
        self.data_path   = self.cfg.data_path
        self.tester_path = self.cfg.tester_path
        self.reports_dir = self.data_path / "MQL5" / "Reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # INI Generation — dynamic ทุก field
    # ------------------------------------------------------------------
    def _generate_ini(
        self,
        ea_name: str,
        symbol: str,
        timeframe: int,
        date_from: str,
        date_to: str,
        set_file: Optional[str],
        model: int,
        report_path: Path,
    ) -> Path:
        """
        Generate backtest INI file แบบ dynamic ทุก field.
        ไม่มีค่า hardcode — ทุกอย่างมาจาก params หรือ user_config.json

        report_path: absolute path ที่ MT5 จะ save .htm report
        """
        # INI ใช้ relative path จาก MQL5\Experts สำหรับ Expert field
        # แต่ Report ใช้ path สัมพัทธ์จาก data_path
        try:
            report_rel = report_path.relative_to(self.data_path)
        except ValueError:
            report_rel = report_path  # fallback ใช้ absolute ถ้า relative ไม่ได้

        lines = [
            "[Tester]",
            f"Expert={ea_name}",
            f"Symbol={symbol}",
            f"Period={TIMEFRAME_MAP.get(timeframe, timeframe)}",
            f"Model={model}",
            f"Optimization=0",
            f"ForwardMode=0",
            f"FromDate={date_from}",
            f"ToDate={date_to}",
            f"Deposit={self.cfg.deposit}",
            f"Currency={self.cfg.currency}",
            f"Leverage={self.cfg.leverage}",
            f"ExecutionMode=0",
            f"Report={report_rel}",
            f"ReplaceReport=0",
            f"SheetName={Path(ea_name).stem}",
        ]

        if set_file:
            lines.append(f"Inputs={set_file}")

        ini_content = "\n".join(lines) + "\n"

        # INI path — ตั้งชื่อตาม ea + timestamp ไม่ทับกัน
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = ea_name.replace("\\", "_").replace("/", "_")
        ini_path  = self.data_path / f"bt_{safe_name}_{timestamp}.ini"
        ini_path.write_text(ini_content, encoding="utf-8")

        logger.info(f"Generated INI: {ini_path}")
        logger.debug(f"INI content:\n{ini_content}")
        return ini_path

    def _dynamic_report_path(self, ea_name: str) -> Path:
        """
        Generate unique report path ด้วย timestamp — ไม่มีทับกันเลย
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = Path(ea_name).stem
        return self.reports_dir / f"{safe_name}_{timestamp}.htm"

    # ------------------------------------------------------------------
    # รอ report file ปรากฏ (reliable กว่ารอ process exit อย่างเดียว)
    # ------------------------------------------------------------------
    def _wait_for_report(self, report_path: Path, timeout: int) -> bool:
        """
        Poll จนกว่า report file จะปรากฏและ size ไม่เปลี่ยนแปลง
        (MT5 อาจยังเขียนไฟล์อยู่ รอให้เสร็จจริงๆ)
        """
        logger.info(f"Waiting for report: {report_path}")
        deadline   = time.time() + timeout
        last_size  = -1

        while time.time() < deadline:
            if report_path.exists():
                size = report_path.stat().st_size
                if size > 0 and size == last_size:
                    logger.info(f"Report ready: {report_path} ({size} bytes)")
                    return True
                last_size = size
            time.sleep(3)

        logger.warning(f"Timeout waiting for report after {timeout}s")
        return False

    # ------------------------------------------------------------------
    # Parse HTML Report
    # ------------------------------------------------------------------
    def _parse_report(self, report_path: Path) -> Dict[str, Any]:
        """Parse HTML backtest report → structured dict"""
        stats = {
            "profit_factor": 0.0,
            "drawdown": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "recovery_factor": 0.0,
            "sharpe_ratio": 0.0,
            "report_path": str(report_path),
        }

        if not report_path.exists():
            logger.error(f"Report not found: {report_path}")
            return stats

        try:
            content = report_path.read_text(encoding="utf-8", errors="ignore")

            patterns = {
                "profit_factor":   r"Profit Factor\s*<[^>]+>\s*([0-9.]+)",
                "drawdown":        r"Maximal [Dd]rawdown.*?([0-9]+\.[0-9]+)%",
                "total_trades":    r"Total Trades\s*<[^>]+>\s*([0-9]+)",
                "net_profit":      r"Total Net Profit\s*<[^>]+>\s*([0-9.-]+)",
                "recovery_factor": r"Recovery Factor\s*<[^>]+>\s*([0-9.]+)",
                "sharpe_ratio":    r"Sharpe Ratio\s*<[^>]+>\s*([0-9.]+)",
            }
            for key, pattern in patterns.items():
                m = re.search(pattern, content)
                if m:
                    stats[key] = float(m.group(1))

            won_match = re.search(r"Profit Trades.*?([0-9]+)\s*\(([0-9.]+)%\)", content)
            if won_match:
                stats["win_rate"] = float(won_match.group(2))

            logger.info(
                f"Parsed: PF={stats['profit_factor']} | "
                f"DD={stats['drawdown']}% | Trades={stats['total_trades']}"
            )
        except Exception as e:
            logger.error(f"Parse error: {e}")

        return stats

    # ------------------------------------------------------------------
    # run_backtest — flow ที่ถูกต้อง
    # ------------------------------------------------------------------
    def run_backtest(
        self,
        ea_name: str,
        symbol: str,
        timeframe: int,
        date_from: str,
        date_to: str,
        set_file: Optional[str] = None,
        model: int = 1,
        timeout: int = 300,
    ) -> Dict[str, Any]:
        """
        Run backtest แบบ headless ผ่าน CLI

        Flow ที่ถูก:
          MT5 ปิดอยู่ → สร้าง INI → Launch terminal64.exe /config:xxx
          → MT5 รัน backtest → ปิดตัวเอง → รอ report → parse

        Args:
            ea_name:   "Advisor\\Gem\\Cash_Collector_v3_3"
            symbol:    "XAUUSDm"
            timeframe: นาที (1, 5, 15, ...)
            date_from: "2026.01.01"
            date_to:   "2026.01.31"
            set_file:  path ของ .set file (optional)
            model:     0=Every tick, 1=1min OHLC, 2=Open price
            timeout:   วินาที (default 300)

        Returns:
            dict พร้อม status, stats, report_path, error
        """
        result = {
            "status": "error",
            "ea_name": ea_name,
            "symbol": symbol,
            "timeframe": timeframe,
            "date_from": date_from,
            "date_to": date_to,
            "profit_factor": 0.0,
            "drawdown": 0.0,
            "total_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "recovery_factor": 0.0,
            "sharpe_ratio": 0.0,
            "report_path": None,
            "error": None,
        }

        try:
            # 1. ตรวจว่า MT5 ปิดอยู่ — ถ้ายังเปิด ต้องปิดก่อน (headless ต้องการ)
            status = get_mt5_status()
            if status.get("is_running"):
                logger.info("MT5 is running — stopping for headless backtest...")
                self.process_control.stop_mt5(force=False)
                time.sleep(5)  # รอให้ process ตายจริงๆ

            # 2. Dynamic report path — timestamp ไม่ทับกัน
            report_path = self._dynamic_report_path(ea_name)

            # 3. Generate INI แบบ dynamic
            ini_path = self._generate_ini(
                ea_name, symbol, timeframe,
                date_from, date_to,
                set_file, model, report_path,
            )
            result["report_path"] = str(report_path)

            # 4. Launch MT5 headless — /config สั่งให้รัน backtest แล้วปิดตัวเอง
            cmd = [str(self.mt5_exe), f"/config:{ini_path}"]
            logger.info(f"Launching: {' '.join(cmd)}")
            proc = subprocess.Popen(cmd)

            # 5. รอ process จบ + รอ report ปรากฏ (สองอย่างพร้อมกัน)
            process_done   = False
            report_timeout = timeout + 60  # report อาจเขียนหลัง process ปิด

            start = time.time()
            while time.time() - start < report_timeout:
                # เช็ค process
                if not process_done and proc.poll() is not None:
                    logger.info(f"MT5 exited (code={proc.returncode}) after {time.time()-start:.0f}s")
                    process_done = True

                # เช็ค report
                if report_path.exists() and report_path.stat().st_size > 0:
                    # รออีกนิดให้ MT5 เขียนเสร็จ
                    time.sleep(2)
                    break

                # Timeout process
                if not process_done and (time.time() - start) > timeout:
                    logger.warning(f"Process timeout {timeout}s — terminating")
                    proc.terminate()
                    result["error"] = f"Timeout after {timeout}s"
                    return result

                time.sleep(3)

            # 6. Parse report
            if not report_path.exists():
                result["error"] = f"Report not found: {report_path}"
                logger.error(result["error"])
                return result

            stats = self._parse_report(report_path)
            result.update(stats)
            result["status"] = "success"

            logger.info(f"Backtest complete: {ea_name} | PF={result['profit_factor']:.2f}")
            send(
                f"✅ Backtest: {Path(ea_name).stem} {symbol} "
                f"| PF={result['profit_factor']:.2f} "
                f"| DD={result['drawdown']:.1f}% "
                f"| Trades={result['total_trades']}",
                severity="info",
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Backtest error: {e}", exc_info=True)
            send(f"❌ Backtest failed: {Path(ea_name).stem} | {e}", severity="warning")

        return result

    # ------------------------------------------------------------------
    # run_multi_backtest
    # ------------------------------------------------------------------
    def run_multi_backtest(
        self, ea_name: str, configs: List[Dict]
    ) -> Dict[str, Any]:
        """
        รัน backtest หลาย config ต่อเนื่อง sorted by profit_factor

        configs: list ของ dict ที่มี keys: symbol, timeframe,
                 date_from, date_to, set_file, model, timeout
        """
        result = {"status": "success", "results": [], "best": None, "error": None}

        for i, cfg in enumerate(configs):
            logger.info(f"Config {i+1}/{len(configs)}: {cfg}")
            bt = self.run_backtest(
                ea_name   = ea_name,
                symbol    = cfg.get("symbol",    self.cfg.default_symbol),
                timeframe = cfg.get("timeframe", self.cfg.default_timeframe),
                date_from = cfg.get("date_from", self.cfg.default_date_from),
                date_to   = cfg.get("date_to",   self.cfg.default_date_to),
                set_file  = cfg.get("set_file"),
                model     = cfg.get("model",     1),
                timeout   = cfg.get("timeout",   self.cfg.backtest_timeout),
            )
            result["results"].append(bt)

        result["results"].sort(key=lambda x: x.get("profit_factor", 0), reverse=True)
        if result["results"]:
            result["best"] = result["results"][0]
            send(
                f"📊 Multi-backtest ({len(configs)} runs) | "
                f"Best PF={result['best']['profit_factor']:.2f}",
                severity="info",
            )

        return result

    # ------------------------------------------------------------------
    # get_tester_report — parse existing report ไม่ต้องรัน backtest
    # ------------------------------------------------------------------
    def get_tester_report(
        self, ea_name: str, report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Parse existing report file

        Args:
            ea_name:     ชื่อ EA (สำหรับ search report ถ้าไม่ระบุ path)
            report_path: path ของ .htm file โดยตรง (optional)
        """
        result = {"status": "error", "stats": {}, "error": None}
        try:
            if report_path:
                path = Path(report_path)
            else:
                # หา report ล่าสุดของ EA นี้
                safe_name = Path(ea_name).stem
                candidates = sorted(
                    self.reports_dir.glob(f"{safe_name}_*.htm"),
                    key=lambda f: f.stat().st_mtime,
                    reverse=True,
                )
                if not candidates:
                    result["error"] = f"No report found for {ea_name}"
                    return result
                path = candidates[0]

            result["stats"] = self._parse_report(path)
            result["status"] = "success"
        except Exception as e:
            result["error"] = str(e)

        return result


# ------------------------------------------------------------------
# Module-level convenience functions
# ------------------------------------------------------------------
_tester: Optional[MT5Tester] = None


def _get_tester() -> MT5Tester:
    global _tester
    if not _tester:
        _tester = MT5Tester()
    return _tester


def run_backtest(
    ea_name: str,
    symbol: str    = None,
    timeframe: int = None,
    date_from: str = None,
    date_to: str   = None,
    set_file: str  = None,
    model: int     = None,
    timeout: int   = None,
) -> Dict[str, Any]:
    """
    รัน backtest — ถ้าไม่ระบุ args จะใช้ค่า default จาก user_config.json

    ตัวอย่าง:
        run_backtest("Advisor\\Gem\\Cash_Collector_v3_3")
        run_backtest("Advisor\\Gem\\Cash_Collector_v3_3", date_from="2026.01.01")
    """
    cfg = get_config()
    return _get_tester().run_backtest(
        ea_name   = ea_name,
        symbol    = symbol    or cfg.default_symbol,
        timeframe = timeframe or cfg.default_timeframe,
        date_from = date_from or cfg.default_date_from,
        date_to   = date_to   or cfg.default_date_to,
        set_file  = set_file,
        model     = model     if model is not None else 1,
        timeout   = timeout   or cfg.backtest_timeout,
    )


def run_multi_backtest(ea_name: str, configs: List[Dict]) -> Dict[str, Any]:
    return _get_tester().run_multi_backtest(ea_name, configs)


def get_tester_report(
    ea_name: str, report_path: Optional[str] = None
) -> Dict[str, Any]:
    return _get_tester().get_tester_report(ea_name, report_path)


if __name__ == "__main__":
    print("MT5 Tester Tool (Phase 2)")
    print("Usage:")
    print('  run_backtest("Advisor\\\\Gem\\\\Cash_Collector_v3_3")')
    print('  run_backtest("Advisor\\\\Gem\\\\Cash_Collector_v3_3", symbol="XAUUSDm.c")')
