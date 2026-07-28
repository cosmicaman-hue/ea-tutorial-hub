"""Regression tests for the visibility-field merge guard (deliberate-clear case).

The merge engine restores ``active_from_month``/``deactivation_month`` from
whichever side holds them so stale snapshots can't erase historical-visibility
data. But that guard must NOT resurrect a field that a newer record cleared
deliberately — the reactivation path sets ``deactivation_month`` to an
explicit ``null``. Root cause of the 2026-07-28 "reactivated Aamna shows
deactivated again" report: the guard restored the field on the very push that
tried to clear it.
"""
import os
import shutil
import tempfile
import unittest

T_DEACT = '2026-07-01T10:00:00+05:30'   # when the deactivation happened
T_REACT = '2026-07-28T12:00:00+05:30'   # the (newer) reactivation


def _student(sid, updated_at, **fields):
    row = {
        'id': sid,
        'name': f'S{sid}',
        'base_name': f'S{sid}',
        'roll': f'EA25A{sid:02d}',
        'updated_at': updated_at,
    }
    row.update(fields)
    return row


class VisibilityFieldMergeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._old_storage_root = os.environ.get('EA_STORAGE_ROOT')
        cls._tmp = tempfile.mkdtemp(prefix='ea_vis_merge_tests_')
        os.environ['EA_STORAGE_ROOT'] = cls._tmp

        from app.utils import data_paths
        data_paths.reset_cache()
        data_paths.invalidate_data_cache()

        import app.routes.scoreboard as sb
        cls.sb = sb

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
        from app.utils import data_paths
        data_paths.reset_cache()
        data_paths.invalidate_data_cache()
        shutil.rmtree(cls._tmp, ignore_errors=True)

    def _merge_one(self, existing, incoming):
        result = self.sb._merge_students_preserve_active([existing], [incoming])
        self.assertEqual(len(result), 1)
        return result[0]

    def test_reactivation_explicit_null_is_honored(self):
        """THE bug: server holds deactivation_month, the reactivation push
        clears it with explicit null — the clear must survive the merge."""
        existing = _student(5, T_DEACT, active=False, deactivation_month='2026-07')
        incoming = _student(5, T_REACT, active=True, active_from_month='2026-07', deactivation_month=None)

        merged = self._merge_one(existing, incoming)

        self.assertIsNone(merged['deactivation_month'])
        self.assertTrue(merged['active'])

    def test_explicit_empty_string_counts_as_clear(self):
        """The edit-student form submits '' for a blank deactivation month."""
        existing = _student(5, T_DEACT, active=False, deactivation_month='2026-07')
        incoming = _student(5, T_REACT, active=True, deactivation_month='')

        merged = self._merge_one(existing, incoming)

        self.assertEqual(str(merged['deactivation_month'] or '').strip(), '')

    def test_stale_record_missing_key_still_restores(self):
        """Protection retained: a stale/legacy/imported snapshot that simply
        OMITS the key must not erase a deactivation — even if its updated_at
        is newer (import flows bump timestamps without knowing the field)."""
        existing = _student(5, T_DEACT, active=False, deactivation_month='2026-07')
        incoming = _student(5, T_REACT)  # no deactivation_month key at all

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['deactivation_month'], '2026-07')

    def test_newer_value_wins_normally(self):
        """A newer record carrying a DIFFERENT value propagates as before
        (deactivation itself syncing to peers)."""
        existing = _student(5, T_DEACT, active=False, deactivation_month='2026-07')
        incoming = _student(5, T_REACT, active=False, deactivation_month='2026-08')

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['deactivation_month'], '2026-08')

    def test_active_from_month_clear_also_honored(self):
        existing = _student(5, T_DEACT, active_from_month='2026-04')
        incoming = _student(5, T_REACT, active_from_month=None)

        merged = self._merge_one(existing, incoming)

        self.assertIsNone(merged['active_from_month'])

    def test_clear_propagates_against_stale_value_holder(self):
        """After the clear lands, a stale peer still holding the old value must
        not re-introduce it: the cleared record is newer, so the base merge
        keeps its explicit null."""
        existing = _student(5, T_REACT, active=True, deactivation_month=None)
        incoming = _student(5, T_DEACT, active=False, deactivation_month='2026-07')

        merged = self._merge_one(existing, incoming)

        self.assertIsNone(merged['deactivation_month'])
        self.assertTrue(merged['active'])


if __name__ == '__main__':
    unittest.main()
