import json
import tempfile
import unittest
from pathlib import Path

from app.utils.file_operations import SafeFileReader, atomic_write_json


class AtomicWriteJsonTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_supports_compact_output(self):
        target = self.root / 'ledger.json'
        payload = {'students': [{'id': 1}], 'scores': []}

        atomic_write_json(target, payload, separators=(',', ':'))

        self.assertEqual(json.loads(target.read_text(encoding='utf-8')), payload)
        self.assertNotIn('\n', target.read_text(encoding='utf-8'))

    def test_preserves_existing_file_on_serialization_failure(self):
        target = self.root / 'ledger.json'
        original = {'server_version': 7}
        atomic_write_json(target, original)

        with self.assertRaises(TypeError):
            atomic_write_json(target, {'invalid': object()})

        self.assertEqual(json.loads(target.read_text(encoding='utf-8')), original)
        self.assertEqual(list(self.root.glob('*.tmp')), [])

    def test_reader_preserves_explicit_none_fallback(self):
        missing = self.root / 'missing.json'
        self.assertIsNone(SafeFileReader.read_json(missing, default=None))

        corrupt = self.root / 'corrupt.json'
        corrupt.write_text('{invalid', encoding='utf-8')
        self.assertIsNone(SafeFileReader.read_json(corrupt, default=None))

    def test_creates_backup_when_requested(self):
        target = self.root / 'ledger.json'
        atomic_write_json(target, {'version': 1})

        atomic_write_json(target, {'version': 2}, backup=True)

        backup = self.root / 'ledger.json.backup'
        self.assertEqual(json.loads(target.read_text(encoding='utf-8')), {'version': 2})
        self.assertEqual(json.loads(backup.read_text(encoding='utf-8')), {'version': 1})


if __name__ == '__main__':
    unittest.main()
