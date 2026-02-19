"""
MT5 File Manager Tool
=====================
Manage MT5-related files: EA source code, compiled files, configs, backups.

Dependencies: pathlib, shutil, json, datetime
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging


# Configure logging
logger = logging.getLogger(__name__)


class MT5FileManager:
    """
    Manage MetaTrader 5 files and resources.
    """

    # MT5 Folder Structure Constants
    EXPERTS_DIR = "MQL5/Experts"
    INDICATORS_DIR = "MQL5/Indicators"
    INCLUDE_DIR = "MQL5/Include"
    TESTER_DIR = "MQL5/Tester"
    LOGS_DIR = "logs"
    PROFILES_DIR = "profiles"
    BACKUPS_DIR = "backups"

    # File Extensions
    EA_EXTENSION = ".mq5"
    COMPILED_EXTENSION = ".ex5"
    SET_EXTENSION = ".set"

    def __init__(self, terminal_data_path: Optional[str] = None):
        """
        Initialize MT5 File Manager.

        Args:
            terminal_data_path: Path to MT5 terminal data directory
        """
        if terminal_data_path:
            self.terminal_path = Path(terminal_data_path)
        else:
            # Try to load from config or use default
            config_path = Path(__file__).parent.parent.parent / "config" / "mt5_paths.json"
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                        # Try different path options
                        self.terminal_path = Path(config.get("mt5_data_path") or
                                                 config.get("mt5_profiles", "").split("\\profiles")[0])
                except Exception:
                    self.terminal_path = Path.home() / "AppData/Roaming/MetaQuotes/Terminal"
            else:
                self.terminal_path = Path.home() / "AppData/Roaming/MetaQuotes/Terminal"

        # Setup key directories
        self.experts_dir = self.terminal_path / self.EXPERTS_DIR
        self.indicators_dir = self.terminal_path / self.INDICATORS_DIR
        self.include_dir = self.terminal_path / self.INCLUDE_DIR
        self.tester_dir = self.terminal_path / self.TESTER_DIR
        self.logs_dir = self.terminal_path / self.LOGS_DIR
        self.profiles_dir = self.terminal_path / self.PROFILES_DIR
        self.backups_dir = self.terminal_path / self.BACKUPS_DIR

        # Create backup directory if it doesn't exist
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def read_ea_file(self, ea_name: str) -> Dict[str, Any]:
        """
        Read EA source code file.

        Args:
            ea_name: EA filename (with or without .mq5 extension)

        Returns:
            {
                "status": "success" | "error",
                "content": str,              # File content
                "path": str,
                "last_modified": str,        # ISO format timestamp
                "size": int,                 # Bytes
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "content": None,
            "path": None,
            "last_modified": None,
            "size": 0,
            "error": None
        }

        try:
            # Ensure .mq5 extension
            if not ea_name.endswith(self.EA_EXTENSION):
                ea_name = ea_name + self.EA_EXTENSION

            ea_path = self.experts_dir / ea_name

            # Check if file exists
            if not ea_path.exists():
                result["error"] = f"File not found: {ea_path}"
                result["path"] = str(ea_path)
                return result

            # Read content
            with open(ea_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get file metadata
            stat = ea_path.stat()
            last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

            result["status"] = "success"
            result["content"] = content
            result["path"] = str(ea_path)
            result["last_modified"] = last_modified
            result["size"] = stat.st_size

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error reading EA file {ea_name}: {str(e)}")

        return result

    def write_ea_file(self, ea_name: str, content: str, backup: bool = True) -> Dict[str, Any]:
        """
        Write EA source code file with optional backup.

        Args:
            ea_name: EA filename (with or without .mq5 extension)
            content: File content to write
            backup: Create backup of previous version

        Returns:
            {
                "status": "success" | "error",
                "path": str,
                "backup_path": str | None,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "path": None,
            "backup_path": None,
            "message": "",
            "error": None
        }

        try:
            # Ensure .mq5 extension
            if not ea_name.endswith(self.EA_EXTENSION):
                ea_name = ea_name + self.EA_EXTENSION

            ea_path = self.experts_dir / ea_name

            # Create backup if file exists and backup requested
            backup_path = None
            if backup and ea_path.exists():
                backup_path = self._create_backup(ea_name)

            # Ensure directory exists
            ea_path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            with open(ea_path, 'w', encoding='utf-8') as f:
                f.write(content)

            result["status"] = "success"
            result["path"] = str(ea_path)
            result["backup_path"] = backup_path
            result["message"] = f"EA file written: {ea_name}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error writing EA file {ea_name}: {str(e)}")

        return result

    def list_eas(self, folder: str = "Experts") -> Dict[str, Any]:
        """
        List all EA files with metadata.

        Args:
            folder: Folder to list ("Experts", "Indicators", "Include")

        Returns:
            {
                "status": "success" | "error",
                "files": [
                    {
                        "name": str,
                        "path": str,
                        "size": int,
                        "last_modified": str,
                        "has_compiled": bool
                    }
                ],
                "count": int,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "files": [],
            "count": 0,
            "error": None
        }

        try:
            # Select directory
            if folder.lower() == "experts":
                directory = self.experts_dir
            elif folder.lower() == "indicators":
                directory = self.indicators_dir
            elif folder.lower() == "include":
                directory = self.include_dir
            else:
                result["error"] = f"Unknown folder: {folder}"
                return result

            # Check if directory exists
            if not directory.exists():
                result["status"] = "success"
                result["message"] = f"Directory does not exist: {directory}"
                return result

            # List .mq5 files
            for mq5_file in directory.glob(f"*{self.EA_EXTENSION}"):
                if mq5_file.is_file():
                    # Check for compiled version
                    ex5_file = mq5_file.with_suffix(self.COMPILED_EXTENSION)
                    has_compiled = ex5_file.exists()

                    # Get metadata
                    stat = mq5_file.stat()
                    last_modified = datetime.fromtimestamp(stat.st_mtime).isoformat()

                    result["files"].append({
                        "name": mq5_file.name,
                        "path": str(mq5_file),
                        "size": stat.st_size,
                        "last_modified": last_modified,
                        "has_compiled": has_compiled
                    })

            result["status"] = "success"
            result["count"] = len(result["files"])
            # Sort by name
            result["files"].sort(key=lambda x: x["name"])

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error listing EAs in {folder}: {str(e)}")

        return result

    def backup_ea(self, ea_name: str, tag: str = "manual") -> Dict[str, Any]:
        """
        Create timestamped backup of EA file.

        Args:
            ea_name: EA filename (with or without .mq5 extension)
            tag: Backup tag (for organization)

        Returns:
            {
                "status": "success" | "error",
                "backup_path": str,
                "timestamp": str,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "backup_path": None,
            "timestamp": None,
            "message": "",
            "error": None
        }

        try:
            # Ensure .mq5 extension
            if not ea_name.endswith(self.EA_EXTENSION):
                ea_name = ea_name + self.EA_EXTENSION

            ea_path = self.experts_dir / ea_name

            # Check if file exists
            if not ea_path.exists():
                result["error"] = f"EA file not found: {ea_path}"
                return result

            backup_path = self._create_backup(ea_name, tag)

            result["status"] = "success"
            result["backup_path"] = backup_path
            result["timestamp"] = datetime.now().isoformat()
            result["message"] = f"Backup created: {backup_path}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error backing up EA {ea_name}: {str(e)}")

        return result

    def restore_ea(self, ea_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """
        Restore EA from backup.

        Args:
            ea_name: EA filename (with or without .mq5 extension)
            version: Specific version to restore (timestamp) or None for latest

        Returns:
            {
                "status": "success" | "error",
                "restored_from": str,
                "message": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "restored_from": None,
            "message": "",
            "error": None
        }

        try:
            # Ensure .mq5 extension
            if not ea_name.endswith(self.EA_EXTENSION):
                ea_name = ea_name + self.EA_EXTENSION

            # Find backup directory
            ea_name_base = ea_name.replace(self.EA_EXTENSION, "")
            backup_ea_dir = self.backups_dir / ea_name_base

            if not backup_ea_dir.exists():
                result["error"] = f"No backups found for {ea_name}"
                return result

            # Find version to restore
            backup_file = None
            if version:
                # Specific version requested
                backup_file = backup_ea_dir / version / ea_name
            else:
                # Find latest backup
                versions = sorted(backup_ea_dir.iterdir(), reverse=True)
                for version_dir in versions:
                    candidate = version_dir / ea_name
                    if candidate.exists():
                        backup_file = candidate
                        break

            if not backup_file or not backup_file.exists():
                result["error"] = f"Backup file not found: {backup_file}"
                return result

            # Restore file
            ea_path = self.experts_dir / ea_name
            shutil.copy2(backup_file, ea_path)

            result["status"] = "success"
            result["restored_from"] = str(backup_file)
            result["message"] = f"Restored from {backup_file}"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error restoring EA {ea_name}: {str(e)}")

        return result

    def read_set_file(self, ea_name: str, profile_name: str) -> Dict[str, Any]:
        """
        Read .set file (EA parameter configuration).

        Args:
            ea_name: EA name (without extension)
            profile_name: Profile/set name

        Returns:
            {
                "status": "success" | "error",
                "params": dict,              # key-value pairs
                "path": str,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "params": {},
            "path": None,
            "error": None
        }

        try:
            # Construct path: ea_name/profile_name.set
            set_path = self.tester_dir / ea_name / (profile_name + self.SET_EXTENSION)

            if not set_path.exists():
                result["error"] = f"Set file not found: {set_path}"
                result["path"] = str(set_path)
                return result

            # Read and parse .set file
            params = {}
            with open(set_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith(';'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        params[key.strip()] = value.strip()

            result["status"] = "success"
            result["params"] = params
            result["path"] = str(set_path)

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error reading set file {ea_name}/{profile_name}: {str(e)}")

        return result

    def write_set_file(self, ea_name: str, profile_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Write .set file (EA parameter configuration).

        Args:
            ea_name: EA name (without extension)
            profile_name: Profile/set name
            params: Parameter dictionary

        Returns:
            {
                "status": "success" | "error",
                "path": str,
                "count": int,                # Parameters written
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "path": None,
            "count": 0,
            "error": None
        }

        try:
            # Construct path
            set_dir = self.tester_dir / ea_name
            set_dir.mkdir(parents=True, exist_ok=True)

            set_path = set_dir / (profile_name + self.SET_EXTENSION)

            # Write parameters
            with open(set_path, 'w', encoding='utf-8') as f:
                f.write("; Strategy Tester Parameters\n")
                f.write(f"; Generated: {datetime.now().isoformat()}\n")
                f.write("; EA: " + ea_name + "\n")
                f.write("; Profile: " + profile_name + "\n\n")

                for key, value in params.items():
                    f.write(f"{key}={value}\n")

            result["status"] = "success"
            result["path"] = str(set_path)
            result["count"] = len(params)

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error writing set file {ea_name}/{profile_name}: {str(e)}")

        return result

    def clean_old_backups(self, keep_last: int = 10) -> Dict[str, Any]:
        """
        Remove old backups, keeping N most recent per EA.

        Args:
            keep_last: Number of recent backups to keep

        Returns:
            {
                "status": "success" | "error",
                "removed_count": int,
                "kept_count": int,
                "summary": dict,             # by EA name
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "removed_count": 0,
            "kept_count": 0,
            "summary": {},
            "error": None
        }

        try:
            if not self.backups_dir.exists():
                result["status"] = "success"
                result["message"] = "No backups directory"
                return result

            # Iterate through each EA's backup directory
            for ea_backup_dir in self.backups_dir.iterdir():
                if not ea_backup_dir.is_dir():
                    continue

                ea_name = ea_backup_dir.name
                versions = sorted(ea_backup_dir.iterdir(), reverse=True)

                removed = 0
                kept = len(versions)

                # Remove old versions
                for version_dir in versions[keep_last:]:
                    try:
                        shutil.rmtree(version_dir)
                        removed += 1
                        kept -= 1
                    except Exception as e:
                        logger.error(f"Error removing backup {version_dir}: {str(e)}")

                result["summary"][ea_name] = {
                    "total": len(versions),
                    "removed": removed,
                    "kept": kept
                }

                result["removed_count"] += removed
                result["kept_count"] += kept

            result["status"] = "success"

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error cleaning backups: {str(e)}")

        return result

    def _create_backup(self, ea_name: str, tag: str = "") -> str:
        """
        Internal method to create backup file.

        Args:
            ea_name: EA filename with extension
            tag: Optional tag for organization

        Returns:
            Path to backup file
        """
        if not ea_name.endswith(self.EA_EXTENSION):
            ea_name = ea_name + self.EA_EXTENSION

        ea_path = self.experts_dir / ea_name
        ea_name_base = ea_name.replace(self.EA_EXTENSION, "")

        # Create backup directory: backups/ea_name/timestamp/
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if tag:
            timestamp = f"{timestamp}_{tag}"

        backup_dir = self.backups_dir / ea_name_base / timestamp
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Copy file
        backup_path = backup_dir / ea_name
        shutil.copy2(ea_path, backup_path)

        return str(backup_path)

    def get_directory_tree(self) -> Dict[str, Any]:
        """
        Get directory structure of MT5 MQL5 folders.

        Returns:
            {
                "status": "success" | "error",
                "structure": dict,
                "error": str | None
            }
        """
        result = {
            "status": "error",
            "structure": {},
            "error": None
        }

        try:
            structure = {
                "terminal_path": str(self.terminal_path),
                "experts": {
                    "path": str(self.experts_dir),
                    "exists": self.experts_dir.exists(),
                    "file_count": len(list(self.experts_dir.glob(f"*{self.EA_EXTENSION}"))) if self.experts_dir.exists() else 0
                },
                "indicators": {
                    "path": str(self.indicators_dir),
                    "exists": self.indicators_dir.exists(),
                    "file_count": len(list(self.indicators_dir.glob(f"*{self.EA_EXTENSION}"))) if self.indicators_dir.exists() else 0
                },
                "include": {
                    "path": str(self.include_dir),
                    "exists": self.include_dir.exists(),
                    "file_count": len(list(self.include_dir.glob("*.mqh"))) if self.include_dir.exists() else 0
                },
                "backups": {
                    "path": str(self.backups_dir),
                    "exists": self.backups_dir.exists(),
                    "backup_count": len(list(self.backups_dir.iterdir())) if self.backups_dir.exists() else 0
                }
            }

            result["status"] = "success"
            result["structure"] = structure

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error getting directory tree: {str(e)}")

        return result


# Convenience module-level functions
_mt5_file_manager = None


def _get_manager(terminal_data_path: Optional[str] = None) -> MT5FileManager:
    """Get or create MT5FileManager instance."""
    global _mt5_file_manager
    if not _mt5_file_manager:
        _mt5_file_manager = MT5FileManager(terminal_data_path)
    return _mt5_file_manager


def read_ea_file(ea_name: str) -> Dict[str, Any]:
    """Read EA file."""
    return _get_manager().read_ea_file(ea_name)


def write_ea_file(ea_name: str, content: str, backup: bool = True) -> Dict[str, Any]:
    """Write EA file."""
    return _get_manager().write_ea_file(ea_name, content, backup)


def list_eas(folder: str = "Experts") -> Dict[str, Any]:
    """List EAs."""
    return _get_manager().list_eas(folder)


def backup_ea(ea_name: str, tag: str = "manual") -> Dict[str, Any]:
    """Backup EA."""
    return _get_manager().backup_ea(ea_name, tag)


def restore_ea(ea_name: str, version: Optional[str] = None) -> Dict[str, Any]:
    """Restore EA from backup."""
    return _get_manager().restore_ea(ea_name, version)


def read_set_file(ea_name: str, profile_name: str) -> Dict[str, Any]:
    """Read .set file."""
    return _get_manager().read_set_file(ea_name, profile_name)


def write_set_file(ea_name: str, profile_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Write .set file."""
    return _get_manager().write_set_file(ea_name, profile_name, params)


def clean_old_backups(keep_last: int = 10) -> Dict[str, Any]:
    """Clean old backups."""
    return _get_manager().clean_old_backups(keep_last)


def get_directory_tree() -> Dict[str, Any]:
    """Get MT5 directory structure."""
    return _get_manager().get_directory_tree()


if __name__ == "__main__":
    print("MT5 File Manager Module")
    print("Use: from mt5_file_manager import MT5FileManager or convenience functions")
