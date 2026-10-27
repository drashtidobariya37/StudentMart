"""
WSGI entrypoint for production servers (Gunicorn, Waitress, uWSGI).
Run from project root: gunicorn wsgi:app
"""

import sys
from pathlib import Path

# Ensure both project root AND backend/ are importable
PROJECT_ROOT = Path(__file__).resolve().parent
BACKEND_DIR  = PROJECT_ROOT / "backend"

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from run import app

if __name__ == "__main__":
    app.run()
