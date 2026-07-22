"""
data_paths.py — Single source of truth for offline scoreboard data file location.

All modules that need to read/write the offline scoreboard JSON must use
get_data_path() or get_storage_root() instead of hardcoding paths.

Inside Flask:  uses current_app.instance_path as fallback (same as before).
Outside Flask: uses <project_root>/instance/ as fallback.
Priority:
  1) EA_STORAGE_ROOT env var (explicit override)
  2) RENDER_DISK_PATH/ea_tutorial_hub (Render persistent disk)
  3) /var/data/ea_tutorial_hub (common Render / LAN mount)
  4) Flask instance_path or <project_root>/instance/ (fallback)
"""
import os
import json as _json
import threading as _threading
from pathlib import Path

__all__ = [
    'get_storage_root', 'get_data_path', 'get_backup_dir',
    'load_json_data_cached', 'invalidate_data_cache', 'prime_data_cache',
    'get_serialized_response', 'store_serialized_response',
]

_storage_root_cache: str = ''

# ── Offline-data in-memory cache (mtime + size invalidated) ──────────────────
# The offline scoreboard JSON can be >4 MB; re-parsing it on every request is
# the single biggest source of request latency. We cache the parsed dict and
# re-load only when the file's mtime or size changes.
# IMPORTANT: callers must treat the returned dict as read-only. Mutating it
# will corrupt the shared cache. Deep-copy before modification.
_data_cache = {
    'path': None,
    'mtime_ns': 0,
    'size': -1,
    'data': None,
}
_data_cache_lock = _threading.Lock()

# ── Serialized-response cache ────────────────────────────────────────────────
# GET /offline-data spends ~124ms re-serializing the same 13 MB dict on every
# request when nothing changed.  We cache the pre-serialized bytes keyed on
# the same mtime/size as the data cache, so a cache hit returns instantly.
# Invalidated whenever prime_data_cache or invalidate_data_cache is called.
_response_cache = {
    'mtime_ns': 0,
    'size': -1,
    'version': -1,       # server_version from payload (monotonic counter)
    'body': None,        # bytes — pre-serialized JSON response body
    'etag': None,        # str  — ETag header value
}
_response_cache_lock = _threading.Lock()


def _project_instance_path() -> str:
    """Return <project_root>/instance/ for use outside Flask context."""
    # app/utils/data_paths.py  →  app/utils/  →  app/  →  project_root/
    project_root = Path(__file__).resolve().parent.parent.parent
    return str(project_root / 'instance')


def _flask_instance_path() -> str | None:
    """Return Flask's instance_path if we're inside an app context, else None."""
    try:
        from flask import current_app
        # Accessing current_app raises RuntimeError outside request/app context
        _ = current_app._get_current_object()
        return str(current_app.instance_path)
    except Exception:
        return None


def get_storage_root() -> str:
    """
    Choose a durable storage root directory.
    Result is cached after first successful resolution.
    """
    global _storage_root_cache
    if _storage_root_cache:
        return _storage_root_cache

    candidates: list[str] = []

    # 1) Explicit override
    explicit = str(os.getenv('EA_STORAGE_ROOT', '') or '').strip()
    if explicit:
        candidates.append(explicit)

    # 2) Render persistent disk
    render_disk = str(os.getenv('RENDER_DISK_PATH', '') or '').strip()
    if not render_disk:
        render_disk = str(os.getenv('RENDER_DISK_MOUNT_PATH', '') or '').strip()
    if render_disk:
        candidates.append(os.path.join(render_disk, 'ea_tutorial_hub'))

    # 3) Common LAN / Render mount (Only on Linux/macOS)
    if os.name != 'nt':
        candidates.append('/var/data/ea_tutorial_hub')

    # 4) Flask instance_path (if available), else project /instance/
    flask_path = _flask_instance_path()
    if flask_path:
        candidates.append(flask_path)
    candidates.append(_project_instance_path())

    for root in candidates:
        try:
            os.makedirs(root, exist_ok=True)
            if os.path.isdir(root):
                _storage_root_cache = root
                return root
        except Exception:
            continue

    # Last resort
    fallback = _project_instance_path()
    _storage_root_cache = fallback
    return fallback


def get_data_path() -> str:
    """Return the full path to offline_scoreboard_data.json."""
    return os.path.join(get_storage_root(), 'offline_scoreboard_data.json')


def get_backup_dir() -> str:
    """Return the full path to the offline scoreboard backups directory."""
    return os.path.join(get_storage_root(), 'offline_scoreboard_backups')


def reset_cache():
    """Clear the cached storage root (useful for testing or env change)."""
    global _storage_root_cache
    _storage_root_cache = ''


# ── Offline-data cache API ───────────────────────────────────────────────────

def load_json_data_cached():
    """
    Load the offline scoreboard JSON with mtime+size-based caching.

    Returns the parsed dict on success, or None if the file is missing or
    cannot be read/parsed. The returned object is shared — callers MUST NOT
    mutate it. Use copy.deepcopy() before modifying.

    On cache hit: ~zero-cost (single os.stat + dict lookup).
    On cache miss: one file read + json.loads, then populates cache.
    """
    path = get_data_path()
    try:
        st = os.stat(path)
    except OSError:
        return None

    mtime_ns = getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9))
    size = st.st_size

    # Fast path — cache hit.
    cache = _data_cache
    if (cache['data'] is not None
            and cache['path'] == path
            and cache['mtime_ns'] == mtime_ns
            and cache['size'] == size):
        return cache['data']

    # Cache miss — reload (under lock so concurrent requests don't stampede).
    with _data_cache_lock:
        # Re-check after acquiring lock: another thread may have populated it.
        if (cache['data'] is not None
                and cache['path'] == path
                and cache['mtime_ns'] == mtime_ns
                and cache['size'] == size):
            return cache['data']
        try:
            from app.utils.file_operations import SafeFileReader
            data = SafeFileReader.read_json(Path(path), default=None)
            if data is None:
                # Fallback to existing cache if file read/parse fails to protect in-memory state
                return cache['data']
        except Exception:
            return cache['data']
        cache['path'] = path
        cache['mtime_ns'] = mtime_ns
        cache['size'] = size
        cache['data'] = data
        return data


def invalidate_data_cache():
    """Clear the offline-data cache. Call after writes that bypass mtime."""
    with _data_cache_lock:
        _data_cache['path'] = None
        _data_cache['mtime_ns'] = 0
        _data_cache['size'] = -1
        _data_cache['data'] = None
    # Also invalidate the serialized-response cache.
    with _response_cache_lock:
        _response_cache['mtime_ns'] = 0
        _response_cache['size'] = -1
        _response_cache['version'] = -1
        _response_cache['body'] = None
        _response_cache['etag'] = None


def prime_data_cache(data: dict):
    """
    Populate the cache with a freshly-saved payload, so the next read is
    a cache hit instead of forcing a re-parse of the 4+ MB file we just wrote.
    The caller should invoke this AFTER the file has been atomically written,
    so mtime/size reflect the new contents.
    """
    if not isinstance(data, dict):
        return
    path = get_data_path()
    try:
        st = os.stat(path)
    except OSError:
        # File write hasn't landed; bail and let the next reader populate.
        return
    with _data_cache_lock:
        _data_cache['path'] = path
        _data_cache['mtime_ns'] = getattr(st, 'st_mtime_ns', int(st.st_mtime * 1e9))
        _data_cache['size'] = st.st_size
        _data_cache['data'] = data
    # Invalidate response cache — data changed, serialized form is stale.
    with _response_cache_lock:
        _response_cache['mtime_ns'] = 0
        _response_cache['size'] = -1
        _response_cache['version'] = -1
        _response_cache['body'] = None
        _response_cache['etag'] = None


def get_serialized_response(mtime_ns: int, size: int, version: int):
    """
    Return (body_bytes, etag) if the serialized response cache matches the
    given (mtime_ns, size, version), otherwise (None, None).
    """
    with _response_cache_lock:
        rc = _response_cache
        if (rc['body'] is not None
                and rc['mtime_ns'] == mtime_ns
                and rc['size'] == size
                and rc['version'] == version):
            return rc['body'], rc['etag']
    return None, None


def store_serialized_response(mtime_ns: int, size: int, version: int,
                              body: bytes, etag: str):
    """
    Store a pre-serialized response body in the cache.  Call after building
    a full GET /offline-data response so subsequent identical requests skip
    the ~124ms json.dumps + encoding step.
    """
    with _response_cache_lock:
        _response_cache['mtime_ns'] = mtime_ns
        _response_cache['size'] = size
        _response_cache['version'] = version
        _response_cache['body'] = body
        _response_cache['etag'] = etag
