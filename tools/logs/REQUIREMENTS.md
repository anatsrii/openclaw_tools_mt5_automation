# MT5 Log Parser - Requirements

## Python Dependencies

### Required
Basic MT5 Log Parser uses only Python standard library:
- `re` - Regular expressions for log parsing
- `datetime` - Timestamp handling
- `collections` - Data structures
- `threading` - Real-time monitoring
- `pathlib` - File path handling
- `logging` - Error logging

### Optional
For advanced file monitoring:
```bash
pip install watchdog
```

## Installation

### Minimal (Standard Library Only)
```bash
# No external packages needed!
# Just Python 3.7+
python --version
```

### With Watchdog (Advanced File Watching)
```bash
pip install watchdog
```

## System Requirements

- **OS:** Windows 7+ (MT5 runs on Windows)
- **Python:** 3.7+
- **Disk Space:** For log file scanning (MT5 logs can be 100+ MB)
- **Permissions:** Read access to MT5 terminal directory

## Configuration

The tool reads MT5 paths from `config/mt5_paths.json`:

```json
{
    "mt5_data_path": "Path to MT5 terminal data directory",
    "mt5_logs": "Path to logs directory"
}
```

If config doesn't exist, defaults to:
```
C:\Users\[USERNAME]\AppData\Roaming\MetaQuotes\Terminal\
```

## Manual Setup

If automatic detection doesn't work:

1. Find your MT5 logs directory:
   - Open MT5
   - File → Open Data Folder
   - Look for "logs" subfolder

2. Update `config/mt5_paths.json`:
   ```json
   {
       "mt5_data_path": "Your/MT5/Data/Path/Here"
   }
   ```

## Performance Recommendations

### For Large Log Files
- Use `hours` parameter to limit search range
- Use `filter_keywords` when watching
- Consider reading only recent entries

### For Real-time Monitoring
- Default polling interval (0.5s) is safe
- Increase interval if high CPU usage
- Watch specific keywords to reduce overhead

### Memory Usage
- Reading 100 lines from journal: ~10-50 KB
- Parsing trade history 24 hours: ~100-500 KB
- Real-time monitoring: ~1-5 MB

## Troubleshooting

### "Cannot open log file" error
- MT5 may lock the log file
- Close MT5 briefly or try again
- Run with timeout / retry logic

### Encoding issues
- Parser handles UTF-8 with error tolerance
- Non-UTF-8 characters are skipped
- Timestamps should always be readable

### Performance issues
- Reading very old logs is slow
- Consider limiting `hours` parameter
- Import watchdog if available for better file monitoring

## Version Compatibility

- Python 3.7, 3.8, 3.9, 3.10, 3.11, 3.12 ✓
- MT5 v5.0 and later ✓
- Windows 7, 8, 10, 11 ✓

## Optional Dependencies Explained

### Watchdog
If installed, enables advanced file monitoring:
- Faster real-time monitoring
- Lower CPU usage
- Better reliability for file changes

Without watchdog:
- Falls back to polling (0.5s interval)
- Still works but slightly less efficient
- No functionality loss

## No License/Telemetry

- MT5 Log Parser is dependency-light
- Standard library only for core functionality
- All analysis is local (no external calls)
- No telemetry or tracking

## Development

For development/testing:
```bash
# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows

# Install with optional dependencies
pip install watchdog

# Run tests
python tests/test_mt5_log_parser.py
```
