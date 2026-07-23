"""Regression tests for ledger reliability paths."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest


class PidIsRunningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from run import _pid_is_running
        cls._pid_is_running = staticmethod(_pid_is_running)

    def test_live_python_child_detected(self):
        proc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(15)'])
        try:
            time.sleep(0.3)
            self.assertTrue(self._pid_is_running(proc.pid))
        finally:
            proc.terminate()
            proc.wait()

    def test_dead_pid_not_running(self):
        proc = subprocess.Popen([sys.executable, '-c', 'pass'])
        dead_pid = proc.pid
        proc.wait()
        del proc
        time.sleep(0.3)
        self.assertFalse(self._pid_is_running(dead_pid))

    @unittest.skipUnless(os.name == 'nt', 'Windows-only PID reuse guard')
    def test_non_python_process_treated_as_reused_pid(self):
        proc = subprocess.Popen(
            ['cmd.exe', '/c', 'ping -n 10 127.0.0.1 > NUL'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        try:
            time.sleep(0.3)
            self.assertFalse(self._pid_is_running(proc.pid))
        finally:
            proc.terminate()

    def test_garbage_input_not_running(self):
        self.assertFalse(self._pid_is_running('abc'))
        self.assertFalse(self._pid_is_running(0))
        self.assertFalse(self._pid_is_running(-5))


class LedgerSaveReliabilityTests(unittest.TestCase):
    """Exercises the real save/load/recovery paths against a temp storage root."""

    @classmethod
    def setUpClass(cls):
        cls._old_storage_root = os.environ.get('EA_STORAGE_ROOT')
        cls._tmp = tempfile.mkdtemp(prefix='ea_ledger_tests_')
        os.environ['EA_STORAGE_ROOT'] = cls._tmp

        from app.utils import data_paths
        data_paths.reset_cache()
        data_paths.invalidate_data_cache()

        from app import app
        import app.routes.scoreboard as sb
        cls.app = app
        cls.sb = sb
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
        resolved = self.data_paths.get_data_path()
        if not resolved.startswith(self._tmp):
            raise RuntimeError(f'Ledger path escaped temp root: {resolved!r}')
        self.ctx = self.app.app_context()
        self.ctx.push()
        self.seed = {
            'students': [{'id': i, 'name': f'S{i}', 'roll': f'R{i}'} for i in range(30)],
            'scores': [],
        }
        self.sb._save_offline_data(dict(self.seed))

    def tearDown(self):
        self.ctx.pop()

    def test_save_succeeds_when_backup_fails(self):
        path = self.sb._offline_data_path()
        before_version = (self.sb._load_offline_data() or {}).get('server_version')
        original = self.sb._backup_offline_file

        def _boom(*args, **kwargs):
            raise OSError('disk full (simulated)')

        self.sb._backup_offline_file = _boom
        try:
            saved = self.sb._save_offline_data(dict(self.seed))
        finally:
            self.sb._backup_offline_file = original
        self.assertTrue(os.path.exists(path))
        self.assertEqual(saved.get('server_version'), before_version + 1)

    def test_verify_backup_copy_removes_truncated_copy(self):
        src = os.path.join(self._tmp, 'src.json')
        bad = os.path.join(self._tmp, 'bad.json')
        with open(src, 'w') as f:
            f.write('x' * 1000)
        with open(bad, 'w') as f:
            f.write('x' * 500)
        self.assertFalse(self.sb._verify_backup_copy(src, bad))
        self.assertFalse(os.path.exists(bad))

    def test_verify_backup_copy_accepts_full_copy(self):
        src = os.path.join(self._tmp, 'src2.json')
        good = os.path.join(self._tmp, 'good2.json')
        with open(src, 'w') as f:
            f.write('x' * 1000)
        shutil.copy2(src, good)
        self.assertTrue(self.sb._verify_backup_copy(src, good))
        self.assertTrue(os.path.exists(good))

    def test_corrupted_ledger_recovers_and_persists(self):
        path = self.sb._offline_data_path()
        backup_dir = self.sb._offline_backup_dir()
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(path, os.path.join(backup_dir, 'offline_scoreboard_testbackup.json'))

        with open(path, 'w', encoding='utf-8') as f:
            f.write('{"students": [')
        self.data_paths.invalidate_data_cache()

        recovered = self.sb._load_offline_data()
        self.assertIsInstance(recovered, dict)
        self.assertEqual(len(recovered.get('students', [])), 30)

        with open(path, 'r', encoding='utf-8') as f:
            on_disk = json.load(f)
        self.assertEqual(len(on_disk.get('students', [])), 30)


if __name__ == '__main__':
    unittest.main()
