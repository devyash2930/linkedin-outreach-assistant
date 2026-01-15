"""
Configuration loader for the outreach tool.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


_config_cache: Dict[str, Any] = {}


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent


def load_config(config_name: str = "config") -> Dict[str, Any]:
    """
    Load a configuration file.
    
    Args:
        config_name: Name of config file (without .yaml extension)
    
    Returns:
        Configuration dictionary
    """
    global _config_cache
    
    if config_name in _config_cache:
        return _config_cache[config_name]
    
    config_path = get_project_root() / "config" / f"{config_name}.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    _config_cache[config_name] = config
    return config


def get_data_dir(subdir: str = None) -> Path:
    """Get path to data directory."""
    data_dir = get_project_root() / "data"
    if subdir:
        data_dir = data_dir / subdir
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_db_path() -> Path:
    """Get path to SQLite database."""
    config = load_config()
    db_path = config.get("database", {}).get("path", "data/outreach.db")
    return get_project_root() / db_path
