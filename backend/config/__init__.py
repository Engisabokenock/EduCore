import os
import warnings
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent

try:
    from .settings import *  # noqa: F401,F403
    BASE_DIR = BASE_DIR if 'BASE_DIR' in dir() else _BASE_DIR
except Exception as exc:
    warnings.warn(f'Config import error: {exc}')

LOG_DIR = _BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
