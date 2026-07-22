import ipaddress
import os
import re
from collections.abc import Iterable, Mapping
from urllib.parse import urlparse

DEFAULT_SYNC_SHARED_KEY = 'EA_SYNC_KEY_917511_2026'


def normalize_peer_urls(values):
    if isinstance(values, str):
        candidates = re.split(r'[,;\s]+', values.strip())
    elif isinstance(values, Iterable) and not isinstance(values, (bytes, bytearray, Mapping)):
        candidates = values
    else:
        return []

    peers = []
    seen = set()
    for candidate in candidates:
        peer = str(candidate or '').strip()
        if not peer:
            continue
        if not re.match(r'^https?://', peer, re.IGNORECASE):
            peer = f'http://{peer}'
        peer = peer.rstrip('/')
        if peer not in seen:
            seen.add(peer)
            peers.append(peer)
    return peers


def get_sync_peers(environ=None):
    env = os.environ if environ is None else environ
    return normalize_peer_urls(env.get('SYNC_PEERS', '') or env.get('SYNC_PEER', ''))


def resolve_sync_shared_key(environ=None):
    env = os.environ if environ is None else environ
    return str(
        env.get('SYNC_SHARED_KEY', '')
        or env.get('SECRET_KEY', '')
        or DEFAULT_SYNC_SHARED_KEY
    ).strip()


def is_private_peer_url(peer_url):
    if not peer_url:
        return False
    try:
        hostname = urlparse(str(peer_url)).hostname or ''
    except (TypeError, ValueError):
        return False
    host = hostname.strip().lower()
    if not host:
        return False
    if host in ('localhost', '127.0.0.1', '::1'):
        return True
    try:
        address = ipaddress.ip_address(host)
        return address.is_private or address.is_loopback
    except ValueError:
        return host.endswith('.local') or host.endswith('.lan')


def is_full_ledger_snapshot(payload):
    return (
        isinstance(payload, dict)
        and payload.get('sync_scope') != 'anonymous-public'
        and not payload.get('allowed_months')
    )
