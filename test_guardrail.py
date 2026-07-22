import os
import sys
from app import create_app
from app.routes.scoreboard import _merge_teacher_scores, _merge_scores_superset

app = create_app()
with app.app_context():
    # Test case 1: Normal teacher points modification
    existing_data = {
        'students': [{'id': 1, 'roll': 'EA25T01'}],
        'scores': [{
            'id': 100,
            'studentId': 1,
            'date': '2026-05-21',
            'points': 5,
            'stars': 0,
            'vetos': 0,
            'month': '2026-05',
            'updated_at': '2026-05-21T10:00:00Z'
        }]
    }
    incoming_data = {
        'students': [{'id': 1, 'roll': 'EA25T01'}],
        'scores': [{
            'studentId': 1,
            'date': '2026-05-21',
            'points': 8,  # normal change (+3)
            'notes': 'Normal performance bump',
            'recordedBy': 'teacher',
            'updated_at': '2026-05-21T11:00:00Z'
        }]
    }
    merged_scores = _merge_teacher_scores(existing_data, incoming_data)
    print("Normal teacher merge points:", merged_scores[0]['points']) # Should be 8

    # Test case 2: Suspicious/abrupt teacher points modification
    incoming_data_suspicious = {
        'students': [{'id': 1, 'roll': 'EA25T01'}],
        'scores': [{
            'studentId': 1,
            'date': '2026-05-21',
            'points': 50,  # abrupt change (+42)
            'notes': 'Hacked scores!',
            'recordedBy': 'teacher',
            'updated_at': '2026-05-21T11:00:00Z'
        }]
    }
    merged_scores_susp = _merge_teacher_scores(existing_data, incoming_data_suspicious)
    print("Suspicious teacher merge points:", merged_scores_susp[0]['points']) # Should be 8 + 15 = 23 (clamped!)
 
    # Test case 3: Extremely out of bounds new points
    existing_empty = {
        'students': [{'id': 1, 'roll': 'EA25T01'}],
        'scores': []
    }
    incoming_data_out_of_bounds = {
        'students': [{'id': 1, 'roll': 'EA25T01'}],
        'scores': [{
            'studentId': 1,
            'date': '2026-05-21',
            'points': 200,  # out of bounds
            'recordedBy': 'teacher',
            'updated_at': '2026-05-21T11:00:00Z'
        }]
    }
    merged_new_out = _merge_teacher_scores(existing_empty, incoming_data_out_of_bounds)
    print("New out of bounds points:", merged_new_out[0]['points']) # Should be 50 (clamped to max ceiling!)
    
    # Test case 4: Superset merge abrupt points and star changes
    existing_scores_superset = [{
        'id': 200,
        'studentId': 1,
        'date': '2026-05-21',
        'points': 10,
        'stars': 2,
        'vetos': 1,
        'month': '2026-05',
        'updated_at': '2026-05-21T10:00:00Z'
    }]
    incoming_scores_superset = [{
        'id': 200,
        'studentId': 1,
        'date': '2026-05-21',
        'points': 100,  # abrupt change
        'stars': 10,   # abrupt change (+8)
        'vetos': 1,
        'month': '2026-05',
        'updated_at': '2026-05-21T11:00:00Z'
    }]
    merged_superset = _merge_scores_superset(existing_scores_superset, incoming_scores_superset)
    print("Superset merge points:", merged_superset[0]['points'])  # Should be 10 + 15 = 25
    print("Superset merge stars:", merged_superset[0]['stars'])   # Should preserve 2 (delta stars > 5)
