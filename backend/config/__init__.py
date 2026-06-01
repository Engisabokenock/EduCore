import os
import warnings
from pathlib import Path

try:
    from .settings import *
except Exception as exc:
    warnings.warn(f'Config import error: {exc}')

LOG_DIR = Path(BASE_DIR) / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)
