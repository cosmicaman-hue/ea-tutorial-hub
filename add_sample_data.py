#!/usr/bin/env python
"""Add sample students for testing the scoring system"""

from app import create_app, db
from app.models import StudentProfile, StudentPoints
from datetime import datetime, timedelta

app = create_app()
app.app_context().push()

# Sample students data
students_data = [
    ('EA24A01', 'Ayush Gupta', '4', 'A'),
    ('EA24A02', 'Ayat Sharma', '4', 'A'),
    ('EA24B01', 'Pari Singh', '4', 'B'),
    ('EA24B02', 'Rahul Kumar', '4', 'B'),
    ('EA24C01', 'Priya Patel', '5', 'C'),
    ('EA24C02', 'Arun Verma', '5', 'C'),
]

print("Adding sample students...")
created_students = []

for roll, name, class_name, group in students_data:
    existing = StudentProfile.query.filter_by(roll_number=roll).first()
    if not existing:
        student = StudentProfile(
            roll_number=roll,
            full_name=name,
            class_name=class_name,
            group=group
        )
        db.session.add(student)
        created_students.append(student)
        print(f"  ✓ {roll} - {name}")
    else:
        created_students.append(existing)
        print(f"  - {roll} - {name} (already exists)")

db.session.commit()

# Add sample points for February 2025
print("\nAdding sample points data...")
today = datetime.now().date()
month_start = today.replace(day=1)

for student in created_students[:3]:  # Add points for first 3 students
    for day in range(1, min(16, today.day + 1)):  # Up to 15th or today
        date_recorded = month_start.replace(day=day)
        
        existing_point = StudentPoints.query.filter_by(
            student_id=student.id,
            date_recorded=date_recorded
        ).first()
        
        if not existing_point:
            points = StudentPoints(
                student_id=student.id,
                date_recorded=date_recorded,
                points=80 + (day % 20) if day % 3 != 0 else 0,
                stars=1 if day % 5 == 0 else 0,
                vetos=0 if day % 7 != 0 else 1,
                recorded_by='admin'
            )
            db.session.add(points)

db.session.commit()
print("✅ Sample data added successfully!")
