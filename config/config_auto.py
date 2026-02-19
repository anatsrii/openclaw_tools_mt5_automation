"""MT5 Path Auto-Detection and Validation

Automatically detects MT5 installation paths and Terminal ID.
Falls back to user configuration if auto-detection fails.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Tuple, Optional
import hashlib

logger = logging.getLogger(__name__)


class MT5PathDetector:
    """Detect and validate MT5 paths."""

    def __init__(self, config_path: Path = None):
        """
        Initialize detector.

        Args:
            config_path: Path to mt5_paths.json (auto-detect if None)
        """
        if config_path is None:
            config_path = Path(__file__).parent / 'mt5_paths.json'
        self.config_path = config_path
        self.config = {}

    def detect_mt5_installation(self) -> Optional[Path]:
        """
        Auto-detect MT5 installation path.

        Checks standard Windows locations:
        - C:\\Program Files\\MetaTrader 5\\
        - C:\\Program Files (x86)\\MetaTrader 5\\

        Returns:
            Path to MT5 installation or None
        """
        candidates = [
            Path('C:\\Program Files\\MetaTrader 5'),
            Path('C:\\Program Files (x86)\\MetaTrader 5'),
        ]

        for path in candidates:
            if (path / 'terminal.exe').exists():
                logger.info(f"Found MT5 at: {path}")
                return path
            if (path / 'terminal64.exe').exists():
                logger.info(f"Found MT5 (64-bit) at: {path}")
                return path

        logger.warning("MT5 installation not found in standard locations")
        return None

    def detect_terminal_data_path(self) -> Optional[Path]:
        """
        Auto-detect MT5 Terminal data folder.

        Checks: C:\\Users\\USERNAME\\AppData\\Roaming\\MetaQuotes\\Terminal\\

        Returns:
            Path to Terminal data folder or None
        """
        username = os.getenv('USERNAME', 'User')
        candidates = [
            Path(f'C:\\Users\\{username}\\AppData\\Roaming\\MetaQuotes\\Terminal'),
            Path(f'C:\\Users\\{username}\\AppData\\Roaming\\MetaQuotes\\'),
        ]

        for path in candidates:
            if path.exists() and (path / 'MQL5').exists():
                logger.info(f"Found Terminal data at: {path}")
                return path

        logger.warning("Terminal data folder not found in standard location")
        return None

    def detect_terminal_id(self, terminal_data_path: Path) -> Optional[str]:
        """
        Extract Terminal ID from terminal.ini.

        The Terminal ID is based on the RID (Registration ID) in terminal.ini.
        Returns a hash of the directory path for unique identification.

        Args:
            terminal_data_path: Path to Terminal data folder

        Returns:
            Terminal ID (hash of path) or None
        """
        try:
            terminal_ini = terminal_data_path / 'terminal.ini'
            if not terminal_ini.exists():
                logger.warning(f"terminal.ini not found at {terminal_ini}")
                # Generate ID from folder path
                path_hash = hashlib.md5(str(terminal_data_path).encode()).hexdigest()[:8]
                logger.info(f"Generated Terminal ID from path: {path_hash}")
                return path_hash

            # Read RID from terminal.ini
            with open(terminal_ini, 'r') as f:
                content = f.read()
                # Look for RID= line (Registration ID)
                for line in content.split('\n'):
                    if line.startswith('RID='):
                        rid = line.split('=')[1].strip()
                        logger.info(f"Found Terminal RID: {rid}")
                        return rid

            # Fallback: generate from path
            path_hash = hashlib.md5(str(terminal_data_path).encode()).hexdigest()[:8]
            logger.info(f"Generated Terminal ID from path: {path_hash}")
            return path_hash

        except Exception as e:
            logger.error(f"Error detecting Terminal ID: {str(e)}")
            return None

    def validate_paths(self, config: Dict[str, str]) -> Tuple[bool, str]:
        """
        Validate all detected paths.

        Args:
            config: Configuration with paths

        Returns:
            (is_valid, error_message)
        """
        errors = []

        # Check MT5 installation
        mt5_path = config.get('mt5_installation_path')
        if not mt5_path or not Path(mt5_path).exists():
            errors.append(f"MT5 installation not found at: {mt5_path}")

        # Check Terminal data
        terminal_path = config.get('mt5_data_path')
        if not terminal_path or not Path(terminal_path).exists():
            errors.append(f"Terminal data not found at: {terminal_path}")

        # Check MQL5 experts
        experts_path = config.get('mt5_experts')
        if experts_path and not Path(experts_path).exists():
            logger.warning(f"Experts folder not found at: {experts_path}")

        if errors:
            return False, "; ".join(errors)
        return True, ""

    def auto_detect(self) -> Dict[str, str]:
        """
        Fully auto-detect MT5 configuration.

        Returns:
            Configuration dictionary with detected paths
        """
        config = {}

        # Detect MT5 installation
        mt5_path = self.detect_mt5_installation()
        if mt5_path:
            config['mt5_installation_path'] = str(mt5_path)
            config['mt5_terminalini'] = str(mt5_path / 'config' / 'terminal.ini')
        else:
            config['mt5_installation_path'] = ""
            config['mt5_terminalini'] = ""

        # Detect Terminal data path
        terminal_data = self.detect_terminal_data_path()
        if terminal_data:
            config['mt5_data_path'] = str(terminal_data)

            # Detect Terminal ID
            terminal_id = self.detect_terminal_id(terminal_data)
            config['terminal_id'] = terminal_id or ""

            # Set MQL5 paths
            config['mt5_experts'] = str(terminal_data / 'MQL5' / 'Experts')
            config['mt5_indicators'] = str(terminal_data / 'MQL5' / 'Indicators')
            config['mt5_scripts'] = str(terminal_data / 'MQL5' / 'Scripts')
            config['mt5_profiles'] = str(terminal_data / 'profiles')
            config['mt5_logs'] = str(terminal_data / 'logs')
        else:
            config['mt5_data_path'] = ""
            config['terminal_id'] = ""
            config['mt5_experts'] = ""
            config['mt5_indicators'] = ""
            config['mt5_scripts'] = ""
            config['mt5_profiles'] = ""
            config['mt5_logs'] = ""

        return config

    def load_or_detect(self) -> Dict[str, str]:
        """
        Load config from file or auto-detect if missing/invalid.

        Returns:
            Configuration dictionary
        """
        # Try to load existing config
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    self.config = json.load(f)
                logger.info(f"Loaded config from {self.config_path}")

                # Validate
                is_valid, error = self.validate_paths(self.config)
                if is_valid:
                    return self.config
                else:
                    logger.warning(f"Config validation failed: {error}")
                    logger.info("Attempting auto-detection...")

            except Exception as e:
                logger.warning(f"Error loading config: {str(e)}")
                logger.info("Attempting auto-detection...")

        # Auto-detect
        logger.info("Auto-detecting MT5 paths...")
        self.config = self.auto_detect()

        # Validate
        is_valid, error = self.validate_paths(self.config)
        if not is_valid:
            logger.error(f"Auto-detection failed: {error}")

        # Save to file
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f"Saved auto-detected config to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}")

        return self.config

    def get_config(self) -> Dict[str, str]:
        """Get current configuration."""
        if not self.config:
            self.load_or_detect()
        return self.config


# Global detector instance
_detector = None


def get_detector() -> MT5PathDetector:
    """Get global detector instance."""
    global _detector
    if _detector is None:
        _detector = MT5PathDetector()
    return _detector


def get_mt5_config() -> Dict[str, str]:
    """Get MT5 configuration (load or auto-detect)."""
    return get_detector().load_or_detect()


def get_mt5_path(key: str, default: str = "") -> str:
    """
    Get MT5 path by key.

    Args:
        key: Path key (e.g., 'mt5_installation_path')
        default: Default value if key not found

    Returns:
        Path string
    """
    config = get_mt5_config()
    return config.get(key, default)


if __name__ == '__main__':
    # Test auto-detection
    logging.basicConfig(level=logging.INFO)

    detector = MT5PathDetector()
    config = detector.load_or_detect()

    print("\n" + "=" * 70)
    print("  MT5 Path Auto-Detection Results")
    print("=" * 70)

    for key, value in config.items():
        exists = Path(value).exists() if value else False
        status = "✅" if exists else "❌" if value else "⚠️"
        print(f"{status} {key}: {value}")

    is_valid, error = detector.validate_paths(config)
    print(f"\nValidation: {'✅ PASS' if is_valid else '❌ FAIL'}")
    if error:
        print(f"Errors: {error}")

    print("=" * 70)
