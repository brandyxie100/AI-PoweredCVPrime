"""
Pytest configuration and shared fixtures.

Sets PYTHONPATH so that ``app`` package is importable from tests.

Author: brandyxie
Email:  brandyxie100@qq.com
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
