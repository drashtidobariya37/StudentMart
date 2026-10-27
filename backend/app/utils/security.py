import os
import time
import uuid
import threading
from werkzeug.utils import secure_filename
from flask import current_app, request

class InMemoryRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""
    def __init__(self):
        self._lock = threading.Lock()
        self._requests = {}

    def is_allowed(self, key: str, max_requests: int = 15, window_seconds: int = 60) -> bool:
        now = time.time()
        with self._lock:
            # Purge older keys periodically
            if len(self._requests) > 1000:
                cutoff = now - 3600
                self._requests = {k: ts for k, ts in self._requests.items() if ts and ts[-1] > cutoff}

            timestamps = self._requests.get(key, [])
            valid_timestamps = [t for t in timestamps if now - t < window_seconds]

            if len(valid_timestamps) >= max_requests:
                self._requests[key] = valid_timestamps
                return False

            valid_timestamps.append(now)
            self._requests[key] = valid_timestamps
            return True

rate_limiter = InMemoryRateLimiter()

def get_client_ip():
    """Extracts client IP safely handling forwarded headers if present."""
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0].strip()
    return request.remote_addr or "127.0.0.1"

def is_allowed_file(filename: str) -> bool:
    """Verifies that filename has an accepted image extension."""
    if "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    allowed = current_app.config.get("ALLOWED_EXTENSIONS", {"png", "jpg", "jpeg", "webp"})
    return ext in allowed

def save_upload_image(file_storage, subfolder: str = "") -> str:
    """
    Validates, renames with a UUID, and saves an uploaded image file.
    Returns relative web path (e.g., 'uploads/abc-def.jpg').
    """
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not is_allowed_file(filename):
        raise ValueError("Invalid file extension. Allowed formats: PNG, JPG, JPEG, WEBP.")

    # Extension extracted safely
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex[:16]}.{ext}"

    target_dir = current_app.config["UPLOAD_FOLDER"]
    if subfolder:
        target_dir = os.path.join(target_dir, subfolder)
    os.makedirs(target_dir, exist_ok=True)

    file_path = os.path.join(target_dir, unique_name)
    file_storage.save(file_path)

    if subfolder:
        return f"uploads/{subfolder}/{unique_name}"
    return f"uploads/{unique_name}"
