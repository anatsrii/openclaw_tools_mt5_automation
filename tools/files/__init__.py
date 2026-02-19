"""MT5 File Management Tools"""

from .mt5_file_manager import (
    MT5FileManager,
    read_ea_file,
    write_ea_file,
    list_eas,
    backup_ea,
    restore_ea,
    read_set_file,
    write_set_file,
    clean_old_backups,
    get_directory_tree
)

__all__ = [
    "MT5FileManager",
    "read_ea_file",
    "write_ea_file",
    "list_eas",
    "backup_ea",
    "restore_ea",
    "read_set_file",
    "write_set_file",
    "clean_old_backups",
    "get_directory_tree"
]
