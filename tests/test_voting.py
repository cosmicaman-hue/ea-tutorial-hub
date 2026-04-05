import unittest
import json
from app.routes.scoreboard import _calculate_election_results

class TestVoting(unittest.TestCase):

    def setUp(self):
        self.election_data = {
            'students': [
                {'id': 1, 'vote_power': 1},
                {'id': 2, 'vote_power': 2},
                {'id': 3, 'vote_power': 3},
            ]
        }

    def test_simple_election(self):
        student_votes = [
            {'candidateId': 1},
            {'candidateId': 1},
            {'candidateId': 2},
        ]
        teacher_votes = []
        results = _calculate_election_results(self.election_data, student_votes, teacher_votes)
        self.assertEqual(results['winner'], 1)
        self.assertFalse(results['tie'])

    def test_tie_election(self):
        student_votes = [
            {'candidateId': 1},
            {'candidateId': 2},
        ]
        teacher_votes = []
        results = _calculate_election_results(self.election_data, student_votes, teacher_votes)
        self.assertIsNone(results['winner'])
        self.assertTrue(results['tie'])

    def test_teacher_vote_changes_outcome(self):
        student_votes = [
            {'candidateId': 1},
            {'candidateId': 1},
            {'candidateId': 2},
        ]
        teacher_votes = [
            {'candidateId': 2},
        ]
        results = _calculate_election_results(self.election_data, student_votes, teacher_votes)
        self.assertEqual(results['winner'], 2)
        self.assertFalse(results['tie'])

    def test_admin_vote_is_ignored(self):
        student_votes = [
            {'candidateId': 1},
        ]
        teacher_votes = [
            {'teacherId': 1, 'candidateId': 2},
        ]
        results = _calculate_election_results(self.election_data, student_votes, teacher_votes)
        self.assertEqual(results['winner'], 1)

if __name__ == '__main__':
    unittest.main()
