"""
MT5 Automation - Central Config
================================
Single source of truth สำหรับทุก tool

Priority ของการอ่านค่า (สูง → ต่ำ):
  1. Environment variables  (MT5_TERMINAL_ID, MT5_USERNAME, ...)
  2. user_config.json       (สำหรับ dev บนเครื่องตัวเอง)
  3. Default values         (fallback)

Setup:
  Option A — แก้ config/user_config.json (copy จาก user_config.example.json)
  Option B — set environment variables (CI/CD หรือเครื่อง shared)

Usage:
    from config.config import get_config
    cfg = get_config()
    print(cfg.experts_path)
    print(cfg.default_symbol)
"""

import os
import json
from pathlib import Path


# ------------------------------------------------------------------
# Environment variable names
# ------------------------------------------------------------------
ENV = {
    "terminal_id":       "MT5_TERMINAL_ID",
    "installation_path": "MT5_INSTALL_PATH",
    "username":          "MT5_USERNAME",
    "terminal_exe":      "MT5_TERMINAL_EXE",
    "default_symbol":    "MT5_SYMBOL",
    "default_timeframe": "MT5_TIMEFRAME",
}


class MT5Config:
    """
    Central config — env vars override user_config.json
    เปลี่ยนแค่ user_config.json หรือ set env var ทั้งระบบอัปเดตทันที
    """

    def __init__(self, user_config_path: str = None):
        self._user_cfg_path = (
            Path(user_config_path)
            if user_config_path
            else Path(__file__).parent / "user_config.json"
        )
        self._cfg = self._load()
        self._build_paths()

    def _load(self) -> dict:
        """โหลด user_config.json (ถ้าไม่มีไฟล์ใช้ dict ว่าง)"""
        if self._user_cfg_path.exists():
            with open(self._user_cfg_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _get(self, env_key: str, json_keys: list, default=None):
        """
        อ่านค่าโดย priority: env var → user_config.json → default

        env_key:   key ใน ENV dict
        json_keys: list ของ key path ใน json เช่น ["mt5", "terminal_id"]
        default:   fallback ถ้าไม่เจอ
        """
        # 1. env var
        env_name = ENV.get(env_key)
        if env_name and os.environ.get(env_name):
            return os.environ[env_name]

        # 2. user_config.json
        node = self._cfg
        for k in json_keys:
            if isinstance(node, dict) and k in node:
                node = node[k]
            else:
                node = None
                break
        if node is not None:
            return node

        # 3. default
        return default

    def _build_paths(self):
        """Build all paths จาก config"""

        # --- MT5 core ---
        tid     = self._get("terminal_id",       ["mt5", "terminal_id"],       "")
        user    = self._get("username",           ["mt5", "username"],          "")
        install = self._get("installation_path",  ["mt5", "installation_path"], "C:\\Program Files\\MetaTrader 5")
        exe     = self._get("terminal_exe",       ["mt5", "terminal_exe"],      "terminal64.exe")

        self.terminal_id         = tid
        self.installation_path   = Path(install)
        self.terminal_exe        = self.installation_path / exe
        self.meta_editor_exe     = self.installation_path / "metaeditor64.exe"

        # Terminal data path — build จาก username + terminal_id
        if user and tid:
            self.data_path = Path(f"C:\\Users\\{user}\\AppData\\Roaming\\MetaQuotes\\Terminal\\{tid}")
        else:
            self.data_path = Path(os.environ.get("MT5_DATA_PATH", ""))

        # Sub-folders
        self.logs_path       = self.data_path / "logs"
        self.tester_path     = self.data_path / "Tester"
        self.mql5_path       = self.data_path / "MQL5"
        self.experts_path    = self.mql5_path / "Experts"
        self.indicators_path = self.mql5_path / "Indicators"
        self.scripts_path    = self.mql5_path / "Scripts"
        self.include_path    = self.mql5_path / "Include"
        self.config_path     = self.data_path / "config"

        # --- Trading ---
        self.default_symbol    = self._get("default_symbol",    ["trading", "default_symbol"],    "XAUUSDm")
        self.default_timeframe = int(self._get("default_timeframe", ["trading", "default_timeframe"], 15))
        self.symbols           = self._get(None,                 ["trading", "symbols"],           [self.default_symbol])
        self.default_date_from = self._get(None,                 ["trading", "default_date_from"], "2026.01.01")
        self.default_date_to   = self._get(None,                 ["trading", "default_date_to"],   "2026.01.31")

        # --- Backtest ---
        bt                   = self._cfg.get("backtest", {})
        self.deposit         = bt.get("deposit",          300)
        self.currency        = bt.get("currency",         "USD")
        self.leverage        = bt.get("leverage",         200)
        self.model           = bt.get("model",            1)
        self.backtest_timeout = bt.get("timeout_seconds", 300)

        # --- Optimization ---
        opt                         = self._cfg.get("optimization", {})
        self.top_n_results          = opt.get("top_n_results",          10)
        self.opt_criterion          = opt.get("criterion",              2)
        self.wf_windows             = opt.get("wf_windows",             4)
        self.wf_test_ratio          = opt.get("wf_test_ratio",          0.3)
        self.wf_efficiency_threshold = opt.get("wf_efficiency_threshold", 0.7)
        self.wf_timeout             = opt.get("timeout_per_window",     900)

    def validate(self) -> dict:
        checks = {
            "terminal.exe": self.terminal_exe.exists(),
            "data_path":    self.data_path.exists(),
            "experts_path": self.experts_path.exists(),
            "logs_path":    self.logs_path.exists(),
            "tester_path":  self.tester_path.exists(),
        }
        return {"ok": all(checks.values()), "checks": checks}

    def summary(self) -> str:
        v = self._env_sources()
        lines = [
            "=== MT5 Config Summary ===",
            f"Terminal ID : {self.terminal_id or '(not set)'}",
            f"Install     : {self.installation_path}",
            f"Data path   : {self.data_path}",
            f"Experts     : {self.experts_path}",
            f"Symbol      : {self.default_symbol}  |  TF: M{self.default_timeframe}",
            f"Date range  : {self.default_date_from} → {self.default_date_to}",
            f"Deposit     : {self.deposit} {self.currency}  |  1:{self.leverage}",
            "",
            "=== Sources ===",
        ]
        for key, source in v.items():
            lines.append(f"  {key:<20} ← {source}")

        val = self.validate()
        lines += ["", "=== Path Validation ==="]
        for name, ok in val["checks"].items():
            lines.append(f"  {'✅' if ok else '❌'} {name}")
        lines.append(f"\n{'✅ All paths OK' if val['ok'] else '❌ Some paths missing'}")
        return "\n".join(lines)

    def _env_sources(self) -> dict:
        """บอกว่าแต่ละค่ามาจากไหน (env var หรือ json)"""
        result = {}
        for key, env_name in ENV.items():
            if os.environ.get(env_name):
                result[key] = f"env:{env_name}"
            else:
                result[key] = "user_config.json"
        return result


# ------------------------------------------------------------------
# Singleton
# ------------------------------------------------------------------
_instance = None


def get_config() -> MT5Config:
    global _instance
    if _instance is None:
        _instance = MT5Config()
    return _instance


def cfg() -> MT5Config:
    return get_config()


if __name__ == "__main__":
    print(MT5Config().summary())
