"""Regression tests for SPA shell cache headers (ETag revalidation).

The /scoreboard/offline shell is ~3.1 MB. It must revalidate every load
(no-cache + ETag -> 304 when unchanged), while Jinja pages without an
explicit policy keep the no-store safety net.
"""
import os
import shutil
import tempfile
import unittest


class CacheHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_storage_root = os.environ.get('EA_STORAGE_ROOT')
        cls._tmp = tempfile.mkdtemp(prefix='ea_cache_header_tests_')
        os.environ['EA_STORAGE_ROOT'] = cls._tmp

        from app.utils import data_paths
        data_paths.reset_cache()
        data_paths.invalidate_data_cache()

        # Dedicated app instance: serving requests flips Flask's "first request"
        # flag, and doing that on the shared package-level app would break later
        # imports of run.py (its @app.shell_context_processor registration must
        # happen before the shared app ever serves a request).
        from app import create_app
        cls.app = create_app()
        cls.data_paths = data_paths

        resolved = data_paths.get_data_path()
        if not resolved.startswith(cls._tmp):
            raise RuntimeError(
                f'REFUSING TO RUN: ledger path {resolved!r} escaped the temp root {cls._tmp!r}. '
                'Real data would be at risk.'
            )

    @classmethod
    def tearDownClass(cls):
        if cls._old_storage_root is None:
            os.environ.pop('EA_STORAGE_ROOT', None)
        else:
            os.environ['EA_STORAGE_ROOT'] = cls._old_storage_root
        cls.data_paths.reset_cache()
        cls.data_paths.invalidate_data_cache()
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def setUp(self):
        self.client = self.app.test_client()

    def test_offline_shell_uses_etag_revalidation_not_no_store(self):
        resp = self.client.get('/scoreboard/offline')
        self.assertEqual(resp.status_code, 200)
        cc = resp.headers.get('Cache-Control', '')
        self.assertIn('no-cache', cc)
        self.assertNotIn('no-store', cc)
        self.assertTrue(resp.headers.get('ETag'), 'send_file must emit an ETag')

    def test_offline_shell_returns_304_on_matching_etag(self):
        first = self.client.get('/scoreboard/offline')
        etag = first.headers.get('ETag')
        self.assertTrue(etag)

        second = self.client.get('/scoreboard/offline', headers={'If-None-Match': etag})
        self.assertEqual(second.status_code, 304)
        self.assertEqual(len(second.get_data()), 0)

    def test_jinja_pages_keep_no_store_safety_net(self):
        resp = self.client.get('/auth/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('no-store', resp.headers.get('Cache-Control', ''))


if __name__ == '__main__':
    unittest.main()
