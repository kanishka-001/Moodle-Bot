"""
Moodle-Bot: Automated AI-summarized Moodle notifications delivered directly to WhatsApp.
"""

import sys
from pathlib import Path

__version__ = "0.1.0"


def main():
    """CLI entry point to run the Moodle Bot Streamlit application."""
    import subprocess

    app_path = Path(__file__).parent / "web" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)] + sys.argv[1:]
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\nMoodle-Bot stopped.")


if __name__ == "__main__":
    main()
