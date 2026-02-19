# MT5 Process Control - Requirements

## Python Dependencies

These dependencies are required to run the MT5 Process Control tool:

```
psutil>=5.8.0
pywin32>=302
```

## Installation

Install required packages:

```bash
pip install psutil pywin32
```

## Windows-specific Setup

After installing pywin32, you may need to run the post-install script:

```bash
python -m pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

Or using the Windows COM registration:

```bash
pywin32_postinstall.py -install
```

## Features Requiring Libraries

- **Process Management**: `psutil`
  - Get MT5 process ID
  - Check process existence
  - Terminate process
  - Monitor CPU/memory usage

- **Window Management**: `pywin32` (win32gui, win32api)
  - Find MT5 window
  - Send window messages (WM_CLOSE)
  - Check window responsiveness
  - Bring window to foreground

## Fallback Behavior

If libraries are not available:
- Basic process control still works via subprocess/taskkill
- Some advanced features (window-specific operations) will be skipped
- The function will still return structured results with error information

## Version Information

- Python: 3.7+
- Target OS: Windows 7+
- MT5 Version: Any (tested with MT5 5.0+)
