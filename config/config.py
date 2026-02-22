"""
MT5 Automation - Central Config
================================
ไฟล์นี้คือ single source of truth สำหรับทุก tool
อ่านค่าจาก user_config.json แล้ว build path ทั้งหมดให้อัตโนมัติ

Usage:
    from config import MT5Config
    cfg = MT5Config()
    print(cfg.experts_path)
    print(cfg.default_symbol)
"""

import json
from pathlib import Path


class MT5Config:
    """
    Central config class — อ่าน user_config.json แล้ว expose ทุก path/variable
    เปลี่ยนแค่ user_config.json ไฟล์เดียว ทั้งระบบอัปเดตทันที
    """

    def __init__(self, user_config_path: str = None):
        # หา user_config.json
        if user_config_path:
            self._user_cfg_path = Path(user_config_path)
        else:
            self._user_cfg_path = Path(__file__).parent / "user_config.json"

        self._cfg = self._load()
        self._build_paths()

    def _load(self) -> dict:
        with open(self._user_cfg_path, encoding="utf-8") as f:
            return json.load(f)

    def _build_paths(self):
        """Build all paths from terminal_id + username อัตโนมัติ"""
        mt5 = self._cfg["mt5"]
        tid = mt5["terminal_id"]
        user = mt5["username"]
        install = mt5["installation_path"]

        # MT5 installation
        self.installation_path   = Path(install)
        terminal_exe_name = mt5.get("terminal_exe", "terminal.exe")
        self.terminal_exe        = self.installation_path / terminal_exe_name
        self.meta_editor_exe     = self.installation_path / "metaeditor64.exe"

        # Terminal data root (AppData)
        self.data_path = Path(
            f"C:\\Users\\{user}\\AppData\\Roaming\\MetaQuotes\\Terminal\\{tid}"
        )

        # Sub-folders
        self.logs_path       = self.data_path / "logs"
        self.tester_path     = self.data_path / "Tester"
        self.mql5_path       = self.data_path / "MQL5"
        self.experts_path    = self.mql5_path / "Experts"
        self.indicators_path = self.mql5_path / "Indicators"
        self.scripts_path    = self.mql5_path / "Scripts"
        self.include_path    = self.mql5_path / "Include"
        self.config_path     = self.data_path / "config"

        # Terminal ID
        self.terminal_id = tid

        # --- Trading variables ---
        trading = self._cfg["trading"]
        self.default_symbol     = trading["default_symbol"]
        self.default_timeframe  = trading["default_timeframe"]
        self.symbols            = trading["symbols"]
        self.default_date_from  = trading["default_date_from"]
        self.default_date_to    = trading["default_date_to"]

        # --- Backtest variables ---
        bt = self._cfg["backtest"]
        self.deposit            = bt["deposit"]
        self.currency           = bt["currency"]
        self.leverage           = bt["leverage"]
        self.model              = bt["model"]
        self.backtest_timeout   = bt["timeout_seconds"]

        # --- Optimization variables ---
        opt = self._cfg["optimization"]
        self.top_n_results      = opt["top_n_results"]
        self.opt_criterion      = opt["criterion"]
        self.wf_windows         = opt["wf_windows"]
        self.wf_test_ratio      = opt["wf_test_ratio"]
        self.wf_efficiency_threshold = opt["wf_efficiency_threshold"]
        self.wf_timeout         = opt["timeout_per_window"]

    def validate(self) -> dict:
        """ตรวจสอบว่า path จริงๆ มีอยู่บนเครื่อง"""
        checks = {
            "terminal.exe":   self.terminal_exe.exists(),
            "data_path":      self.data_path.exists(),
            "experts_path":   self.experts_path.exists(),
            "logs_path":      self.logs_path.exists(),
            "tester_path":    self.tester_path.exists(),
        }
        all_ok = all(checks.values())
        return {"ok": all_ok, "checks": checks}

    def summary(self) -> str:
        """สรุป config ปัจจุบัน"""
        v = self.validate()
        lines = [
            "=== MT5 Config Summary ===",
            f"Terminal ID : {self.terminal_id}",
            f"Install     : {self.installation_path}",
            f"Data path   : {self.data_path}",
            f"Experts     : {self.experts_path}",
            f"Symbol      : {self.default_symbol}  |  TF: M{self.default_timeframe}",
            f"Symbols     : {', '.join(self.symbols)}",
            f"Date range  : {self.default_date_from} → {self.default_date_to}",
            f"Deposit     : {self.deposit} {self.currency}  |  Leverage: 1:{self.leverage}",
            "",
            "=== Path Validation ===",
        ]
        for name, ok in v["checks"].items():
            lines.append(f"  {'✅' if ok else '❌'} {name}")
        lines.append(f"\n{'✅ All paths OK' if v['ok'] else '❌ Some paths missing'}")
        return "\n".join(lines)


# Singleton สำหรับ import ทั่วทั้งโปรเจกต์
_instance = None

def get_config() -> MT5Config:
    """Get global MT5Config instance (singleton)"""
    global _instance
    if _instance is None:
        _instance = MT5Config()
    return _instance


# Shortcuts สำหรับ import ตรงๆ
def cfg() -> MT5Config:
    return get_config()


if __name__ == "__main__":
    config = MT5Config()
    print(config.summary())
