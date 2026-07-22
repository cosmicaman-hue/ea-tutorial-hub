import unittest

from app.utils.sync_payloads import payload_for_external_replication


class UncopyableValue:
    def __deepcopy__(self, memo):
        raise RuntimeError('cannot copy')


class ExternalReplicationPayloadTests(unittest.TestCase):
    def test_removes_fee_data_without_mutating_source(self):
        source = {
            'fee_records': [{'id': 1}],
            'students': [
                {'id': 1, 'name': 'A', 'fees': {'due': 10}},
                {'id': 2, 'name': 'B'},
                'invalid-row',
            ],
            'scores': [{'id': 4, 'points': 8}],
        }

        external = payload_for_external_replication(source)

        self.assertNotIn('fee_records', external)
        self.assertNotIn('fees', external['students'][0])
        self.assertEqual(external['scores'], source['scores'])
        self.assertIsNot(external, source)
        self.assertIsNot(external['students'], source['students'])
        self.assertIn('fee_records', source)
        self.assertIn('fees', source['students'][0])

    def test_returns_empty_payload_for_non_mapping_input(self):
        self.assertEqual(payload_for_external_replication(None), {})
        self.assertEqual(payload_for_external_replication([]), {})

    def test_preserves_legacy_shallow_fallback_when_deepcopy_fails(self):
        source = {
            'fee_records': [{'id': 1}],
            'students': [{'id': 1, 'fees': {'due': 10}}],
            'uncopyable': UncopyableValue(),
        }

        external = payload_for_external_replication(source)

        self.assertNotIn('fee_records', external)
        self.assertIs(external['students'], source['students'])
        self.assertIn('fees', external['students'][0])
        self.assertIn('fee_records', source)


if __name__ == '__main__':
    unittest.main()
