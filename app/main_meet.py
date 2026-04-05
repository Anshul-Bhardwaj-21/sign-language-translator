"""
Entry point for Meet-style UI testing.

Run with: streamlit run app/main_meet.py
"""

import sys
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from ui_meet import main_meet_ui

if __name__ == "__main__":
    main_meet_ui()