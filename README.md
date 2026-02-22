# MT5 Automation — OpenClaw Skill

ระบบ automation ครบวงจรสำหรับ MetaTrader 5

## เริ่มต้นใช้งาน

### 1. ตั้งค่า (แค่ไฟล์เดียว)
แก้ไข `config/user_config.json`:
```json
{
  "mt5": {
    "terminal_id": "YOUR_TERMINAL_ID",
    "installation_path": "C:\\Program Files\\MetaTrader 5",
    "username": "YOUR_WINDOWS_USERNAME"
  },
  "trading": {
    "default_symbol": "XAUUSDm",
    "default_timeframe": 1
  }
}
```

### 2. ตรวจสอบ
```bash
python config/config.py
```

### 3. คู่มือเพิ่มเติม
- **[SKILL.md](SKILL.md)** — คู่มือฉบับเต็ม, workflows, API reference
- **[PHASE2_OVERVIEW.md](PHASE2_OVERVIEW.md)** — รายละเอียด Phase 2 tools

### 4. ติดตั้ง dependencies
```bash
pip install MetaTrader5 psutil pywin32 pyautogui watchdog APScheduler requests python-dateutil
```

### 5. รัน tests
```bash
python tests/test_all.py
```
