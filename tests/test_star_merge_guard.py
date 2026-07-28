"""Regression tests for the stars_updated_at merge guard.

Covers the defensive fix for the "should be N, shows M" class of stale-sync
star regressions: a sync-bumped ``updated_at`` on a stale snapshot must not
overwrite a genuinely newer ``student.stars`` balance. See AI_AGENT_MEMORY.md
entry 32 (2026-07-25).
"""
import os
import shutil
import tempfile
import unittest

T1 = '2026-07-01T10:00:00+05:30'
T2 = '2026-07-10T10:00:00+05:30'
T3 = '2026-07-20T10:00:00+05:30'


def _student(sid, stars, updated_at, stars_updated_at=None):
    row = {
        'id': sid,
        'name': f'S{sid}',
        'base_name': f'S{sid}',
        'roll': f'EA25A{sid:02d}',
        'stars': stars,
        'updated_at': updated_at,
    }
    if stars_updated_at is not None:
        row['stars_updated_at'] = stars_updated_at
    return row


class StarMergeGuardTests(unittest.TestCase):
    """_merge_students_preserve_active: star balance comes from the record
    with the newer stars_updated_at, not the newer sync-bumped updated_at."""

    @classmethod
    def setUpClass(cls):
        cls._old_storage_root = os.environ.get('EA_STORAGE_ROOT')
        cls._tmp = tempfile.mkdtemp(prefix='ea_star_guard_tests_')
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

    def test_stale_sync_with_bumped_updated_at_cannot_lower_stars(self):
        """Core regression: stale peer snapshot has FEWER stars but a NEWER
        sync-bumped updated_at. The genuine local balance must survive."""
        existing = _student(5, stars=11, updated_at=T2, stars_updated_at=T2)
        incoming = _student(5, stars=8, updated_at=T3, stars_updated_at=T1)

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['stars'], 11)
        self.assertEqual(merged['stars_updated_at'], T2)

    def test_genuinely_newer_incoming_stars_win(self):
        """A real star mutation from a peer (newer stars_updated_at) must
        propagate — the guard must not freeze balances."""
        existing = _student(5, stars=8, updated_at=T1, stars_updated_at=T1)
        incoming = _student(5, stars=11, updated_at=T2, stars_updated_at=T2)

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['stars'], 11)
        self.assertEqual(merged['stars_updated_at'], T2)

    def test_legacy_records_fall_back_to_updated_at(self):
        """Records predating stars_updated_at keep the old timestamp-winner
        behavior (fallback chain stars_updated_at -> updated_at)."""
        existing = _student(5, stars=8, updated_at=T1)
        incoming = _student(5, stars=11, updated_at=T2)

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['stars'], 11)
        self.assertNotIn('stars_updated_at', merged)

    def test_negative_stars_clamped_to_zero(self):
        existing = _student(5, stars=5, updated_at=T1, stars_updated_at=T1)
        incoming = _student(5, stars=-3, updated_at=T2, stars_updated_at=T2)

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['stars'], 0)

    def test_star_guard_does_not_clobber_other_fields(self):
        """The guard touches only stars/stars_updated_at; other fields still
        follow the normal updated_at winner (stale-sync base merge)."""
        existing = _student(5, stars=11, updated_at=T2, stars_updated_at=T2)
        existing['active_from_month'] = '2026-04'
        incoming = _student(5, stars=8, updated_at=T3, stars_updated_at=T1)
        incoming['points'] = 42

        merged = self._merge_one(existing, incoming)

        self.assertEqual(merged['stars'], 11)
        self.assertEqual(merged['points'], 42)
        self.assertEqual(merged['active_from_month'], '2026-04')


class UpsertScoreDeltaStarStampTests(unittest.TestCase):
    """_upsert_score_delta: star deltas stamp stars_updated_at on the student
    ledger record; points-only deltas must not (avoids false 'newer star'
    signals)."""

    @classmethod
    def setUpClass(cls):
        import app.routes.scoreboard as sb
        cls.sb = sb

    def _snapshot(self, stars_updated_at=None):
        student = {'id': 5, 'name': 'S5', 'roll': 'EA25A05'}
        if stars_updated_at is not None:
            student['stars_updated_at'] = stars_updated_at
        return {'students': [student], 'scores': []}

    def test_star_delta_stamps_student_stars_updated_at(self):
        snapshot = self._snapshot()

        self.sb._upsert_score_delta(snapshot, 5, '2026-07-15', '2026-07', delta_stars=-1, note='veto')

        stamp = snapshot['students'][0].get('stars_updated_at')
        self.assertTrue(stamp, 'stars_updated_at must be set after a star delta')
        self.assertGreater(self.sb._parse_sync_stamp(stamp), 0)
        self.assertEqual(snapshot['scores'][0]['stars'], -1)

    def test_points_only_delta_does_not_stamp(self):
        snapshot = self._snapshot()

        self.sb._upsert_score_delta(snapshot, 5, '2026-07-15', '2026-07', delta_points=3)

        self.assertNotIn('stars_updated_at', snapshot['students'][0])
        self.assertEqual(snapshot['scores'][0]['points'], 3)
        self.assertEqual(snapshot['scores'][0]['stars'], 0)

    def test_existing_stamp_preserved_on_points_only_delta(self):
        snapshot = self._snapshot(stars_updated_at=T1)

        self.sb._upsert_score_delta(snapshot, 5, '2026-07-15', '2026-07', delta_points=3)

        self.assertEqual(snapshot['students'][0]['stars_updated_at'], T1)

    def test_new_score_row_created_when_absent(self):
        snapshot = self._snapshot()

        target = self.sb._upsert_score_delta(snapshot, 5, '2026-07-15', '2026-07', delta_stars=1)

        self.assertIsNotNone(target)
        self.assertEqual(len(snapshot['scores']), 1)
        self.assertEqual(snapshot['scores'][0]['studentId'], 5)
        self.assertEqual(snapshot['scores'][0]['month'], '2026-07')

    def test_star_delta_only_stamps_matching_student(self):
        snapshot = self._snapshot()
        snapshot['students'].append({'id': 6, 'name': 'S6', 'roll': 'EA25A06'})

        self.sb._upsert_score_delta(snapshot, 5, '2026-07-15', '2026-07', delta_stars=-1)

        self.assertIn('stars_updated_at', snapshot['students'][0])
        self.assertNotIn('stars_updated_at', snapshot['students'][1])


if __name__ == '__main__':
    unittest.main()
