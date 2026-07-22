import unittest

from app import _configured_process_workers


class ProcessWorkerConfigurationTests(unittest.TestCase):
    def test_defaults_to_one_worker(self):
        self.assertEqual(_configured_process_workers({}), 1)

    def test_reads_web_concurrency(self):
        self.assertEqual(_configured_process_workers({'WEB_CONCURRENCY': '4'}), 4)

    def test_reads_gunicorn_worker_arguments(self):
        self.assertEqual(
            _configured_process_workers({'GUNICORN_CMD_ARGS': '--bind 0.0.0.0:5000 --workers=3'}),
            3,
        )
        self.assertEqual(_configured_process_workers({'GUNICORN_CMD_ARGS': '-w 2'}), 2)

    def test_uses_highest_valid_worker_count(self):
        self.assertEqual(
            _configured_process_workers({
                'WEB_CONCURRENCY': '2',
                'GUNICORN_WORKERS': '5',
                'GUNICORN_CMD_ARGS': '--workers 3',
            }),
            5,
        )

    def test_ignores_invalid_worker_counts(self):
        self.assertEqual(
            _configured_process_workers({
                'WEB_CONCURRENCY': 'invalid',
                'GUNICORN_WORKERS': '',
            }),
            1,
        )


if __name__ == '__main__':
    unittest.main()
