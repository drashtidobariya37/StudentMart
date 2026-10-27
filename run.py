"""
Student Mart - Multi-College Student Marketplace
Main application execution entrypoint.

Run from project root: python run.py
"""

import os
import sys
from pathlib import Path

# ── Ensure both project root AND backend/ are in sys.path ─────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent          # student_mart/
BACKEND_DIR  = PROJECT_ROOT / "backend"                 # student_mart/backend/

for p in [str(PROJECT_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app import create_app
from app.models import db, User
from seed_data import seed_database

app = create_app()

def initialize_database():
    """Ensures database is initialized and populated with sample data on first run."""
    with app.app_context():
        try:
            user_count = User.query.count()
            if user_count == 0:
                print("[INIT] Database is empty. Running database seeder...")
                seed_database()
        except Exception:
            print("[INIT] Fresh setup detected. Initializing schema and seed data...")
            seed_database()

if __name__ == "__main__":
    initialize_database()
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    host = os.environ.get("HOST", "127.0.0.1")

    if "--public" in sys.argv or "--network" in sys.argv:
        host = "0.0.0.0"

    # Detect local LAN IP for convenient mobile device preview
    lan_ip = "127.0.0.1"
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print(f"\n========================================================")
    print(f"  STUDENT MART - Campus Marketplace Server Running!")
    print(f"  Local computer:     http://127.0.0.1:{port}")
    if host == "0.0.0.0":
        print(f"  Mobile / Network:   http://{lan_ip}:{port}")
    else:
        print(f"  Mobile sharing:     Run 'python run.py --public'")
        print(f"                      then open http://{lan_ip}:{port} on phone")
    print(f"--------------------------------------------------------")
    print(f"  Admin credentials:  admin@studentmart.campus / Admin@123")
    print(f"  Gujarat Seller:     aarav.sharma@nirmauni.ac.in / Student@123")
    print(f"  Gujarat Buyer:      sneha.patel@daiict.ac.in / Student@123")
    print(f"========================================================\n")
    app.run(host=host, port=port, debug=debug, use_reloader=False)
