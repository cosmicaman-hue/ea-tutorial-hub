import unittest

from app.utils.sync_config import (
    DEFAULT_SYNC_SHARED_KEY,
    get_sync_peers,
    is_full_ledger_snapshot,
    is_private_peer_url,
    normalize_peer_urls,
    resolve_sync_shared_key,
)


class SyncConfigTests(unittest.TestCase):
    def test_normalize_peer_urls_preserves_order_and_deduplicates(self):
        self.assertEqual(
            normalize_peer_urls('host-a:5000, https://example.com/;host-a:5000'),
            ['http://host-a:5000', 'https://example.com'],
        )

    def test_get_sync_peers_supports_legacy_environment_name(self):
        self.assertEqual(
            get_sync_peers({'SYNC_PEER': 'server.local:5000'}),
            ['http://server.local:5000'],
        )

    def test_resolve_sync_shared_key_priority(self):
        self.assertEqual(
            resolve_sync_shared_key({
                'SYNC_SHARED_KEY': 'replication-key',
                'SECRET_KEY': 'application-key',
            }),
            'replication-key',
        )
        self.assertEqual(
            resolve_sync_shared_key({'SECRET_KEY': 'application-key'}),
            'application-key',
        )
        self.assertEqual(resolve_sync_shared_key({}), DEFAULT_SYNC_SHARED_KEY)

    def test_private_peer_classification(self):
        self.assertTrue(is_private_peer_url('http://localhost:5000'))
        self.assertTrue(is_private_peer_url('http://192.168.1.20:5000'))
        self.assertTrue(is_private_peer_url('http://classroom.local:5000'))
        self.assertFalse(is_private_peer_url('https://example.com'))

    def test_full_ledger_snapshot_rejects_clipped_views(self):
        self.assertTrue(is_full_ledger_snapshot({'students': []}))
        self.assertFalse(is_full_ledger_snapshot({'sync_scope': 'anonymous-public'}))
        self.assertFalse(is_full_ledger_snapshot({'allowed_months': ['2026-07']}))
        self.assertFalse(is_full_ledger_snapshot(None))


if __name__ == '__main__':
    unittest.main()
