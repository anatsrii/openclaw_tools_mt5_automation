# MT5 File Manager - Requirements

## Python Dependencies

Good news! MT5 File Manager uses only Python standard library:

- `pathlib` - Path handling
- `shutil` - File operations (copy, remove)
- `json` - Configuration parsing
- `datetime` - Timestamps
- `logging` - Error logging
- `os` - System operations

## Installation

No external packages required. Just Python 3.7+:

```bash
python --version  # Check Python version (3.7+)
```

## System Requirements

- **OS:** Windows 7+ (MT5 runs on Windows)
- **Python:** 3.7+
- **Disk Space:** For backups (depends on EA file sizes)
- **Permissions:** Read/write access to MT5 terminal directory

## Configuration

The tool reads MT5 paths from `config/mt5_paths.json`:

```json
{
    "mt5_data_path": "Path to MT5 terminal data directory",
    "mt5_experts": "Path to MQL5/Experts directory"
}
```

If config doesn't exist, it defaults to:
```
C:\Users\[USERNAME]\AppData\Roaming\MetaQuotes\Terminal\
```

## Manual Setup

If automatic detection doesn't work:

1. Find your MT5 terminal data path:
   - Open MT5
   - File → Directory → Tester Data (or similar)
   - Copy the path

2. Update `config/mt5_paths.json`:
   ```json
   {
       "mt5_data_path": "Your/MT5/Path/Here"
   }
   ```

## Disk Space Estimation

For backups:
- Typical EA: 20-100 KB
- 10 backups per EA: 200-1000 KB
- 100 EAs with backups: ~10-100 MB

## Troubleshooting

### "File not found" error
- Verify MT5 is installed
- Check `config/mt5_paths.json` settings
- Ensure EA file exists in Experts directory

### Permission denied errors
- Close MT5 (may lock files)
- Run with Administrator privileges
- Check folder permissions

### Path issues on different Windows versions
- The tool uses UTF-8 encoding
- Supports Unicode characters in filenames
- Long paths (>260 chars) supported on Windows 10+

## Version Compatibility

- Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12 ✓
- MT5 v5.0 and later ✓

## No External Dependencies!

MT5 File Manager is dependency-free. It only uses Python standard library, making it lightweight and easy to deploy.
