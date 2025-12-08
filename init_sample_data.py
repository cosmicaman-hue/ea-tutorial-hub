#!/usr/bin/env python
"""
Initialize sample data for EA Tutorial Hub
Run this script to populate the database with sample data for testing
"""

from app import create_app, db
from app.models import User, StudentProfile, Quiz, QuizQuestion
from datetime import datetime, date

def init_sample_data():
    app = create_app()
    
    with app.app_context():
        # Clear existing data
        print("Clearing existing data...")
        db.drop_all()
        db.create_all()
        print("[OK] Database reset complete")
        
        # Create admin user
        print("\nCreating admin user...")
        admin = User(login_id='Admin', role='admin', first_login=False)
        admin.set_password('admin123')
        db.session.add(admin)
        print("[OK] Admin created: Admin (password: admin123)")
        
        # Create sample teacher
        print("\nCreating sample teacher...")
        teacher = User(login_id='Teacher', role='teacher', first_login=False)
        teacher.set_password('teacher123')
        
        teacher_profile = StudentProfile(
            user_id=None,  # Will be set after user is committed
            first_name='Rajesh',
            second_name='Kumar',
            third_name='Singh',
            date_of_birth=date(1990, 5, 15),
            gender='Male',
            religion='Hindu',
            nationality='India',
            school_name='Delhi Public School',
            class_name='Faculty',
            section='N/A',
            contact_number_1='9876543210',
            contact_number_2='9876543211',
            email='teacher@dps.com',
            village_area='Delhi',
            post_office='Delhi',
            district='Delhi',
            state='Delhi',
            pin_code='110001',
            hobbies='Teaching, Mentoring',
            improvement_areas='Technology, Online Teaching'
        )
        teacher.student_profile = teacher_profile
        
        db.session.add(teacher)
        db.session.commit()
        print("[OK] Teacher created: Teacher (password: teacher123)")
        
        # Create sample students
        print("\nCreating sample students...")
        student_data = [
            {
                'login_id': 'EA24C01',
                'name': ['Amit', 'Sharma', 'Singh'],
                'dob': date(2008, 3, 20),
                'class': '10',
                'section': 'A',
                'contact': '9111111111'
            },
            {
                'login_id': 'EA24D02',
                'name': ['Priya', 'Verma', 'Gupta'],
                'dob': date(2008, 7, 10),
                'class': '10',
                'section': 'B',
                'contact': '9222222222'
            },
            {
                'login_id': 'EA24E03',
                'name': ['Rohit', 'Patel', 'Joshi'],
                'dob': date(2009, 1, 15),
                'class': '9',
                'section': 'A',
                'contact': '9333333333'
            }
        ]
        
        for std in student_data:
            student = User(login_id=std['login_id'], role='student', first_login=False)
            student.set_password('student123')
            
            profile = StudentProfile(
                first_name=std['name'][0],
                second_name=std['name'][1],
                third_name=std['name'][2],
                date_of_birth=std['dob'],
                gender='Male' if std['name'][0] in ['Amit', 'Rohit'] else 'Female',
                religion='Hindu',
                nationality='India',
                school_name='Delhi Public School',
                class_name=f"Class {std['class']}",
                section=std['section'],
                contact_number_1=std['contact'],
                contact_number_2='',
                email=f"{std['login_id'].lower()}@school.local",
                village_area='Delhi',
                post_office='Delhi',
                district='Delhi',
                state='Delhi',
                pin_code='110001',
                hobbies='Cricket, Reading',
                improvement_areas='Mathematics, English',
                blood_group='O+',
                aadhar_number='123456789012'
            )
            student.student_profile = profile
            db.session.add(student)
            print(f"[OK] Student created: {std['login_id']} (password: student123)")
        
        db.session.commit()
        
        # Create sample quizzes
        print("\nCreating sample quizzes...")
        
        quiz1 = Quiz(
            title='Mathematics - Algebra Basics',
            description='Test your knowledge on basic algebra concepts including variables, expressions, and equations.',
            subject='Mathematics',
            class_level='Class 9',
            duration_minutes=30,
            total_points=100,
            passing_score=40,
            is_active=True,
            allow_retake=True,
            show_results=True
        )
        
        # Add questions to quiz1
        questions1 = [
            QuizQuestion(
                quiz=quiz1,
                question_text='What is the value of x if 2x + 5 = 15?',
                question_type='multiple_choice',
                points=10,
                option_a='2',
                option_b='5',
                option_c='10',
                option_d='15',
                correct_answer='B',
                explanation='Solving: 2x + 5 = 15 -> 2x = 10 -> x = 5'
            ),
            QuizQuestion(
                quiz=quiz1,
                question_text='Simplify: 3a + 2a - a',
                question_type='multiple_choice',
                points=10,
                option_a='4a',
                option_b='5a',
                option_c='6a',
                option_d='2a',
                correct_answer='A',
                explanation='3a + 2a - a = 5a - a = 4a'
            ),
            QuizQuestion(
                quiz=quiz1,
                question_text='Is -5 < -3? (True or False)',
                question_type='true_false',
                points=10,
                option_a='True',
                option_b='False',
                correct_answer='True',
                explanation='On a number line, -5 is to the left of -3, so -5 < -3'
            ),
            QuizQuestion(
                quiz=quiz1,
                question_text='Solve: x/2 = 8',
                question_type='multiple_choice',
                points=10,
                option_a='4',
                option_b='8',
                option_c='16',
                option_d='32',
                correct_answer='C',
                explanation='x/2 = 8 -> x = 8 x 2 = 16'
            ),
            QuizQuestion(
                quiz=quiz1,
                question_text='What is the coefficient of x in the expression 5x + 3?',
                question_type='multiple_choice',
                points=10,
                option_a='3',
                option_b='5',
                option_c='8',
                option_d='15',
                correct_answer='B',
                explanation='The coefficient is the number multiplying the variable x, which is 5'
            )
        ]
        
        for q in questions1:
            db.session.add(q)
        
        db.session.add(quiz1)
        db.session.commit()
        print("[OK] Quiz 1 created: Mathematics - Algebra Basics")
        
        # Create second quiz
        quiz2 = Quiz(
            title='Science - Basic Physics',
            description='Test your understanding of basic physics concepts and laws.',
            subject='Science',
            class_level='Class 10',
            duration_minutes=45,
            total_points=100,
            passing_score=50,
            is_active=True,
            allow_retake=True,
            show_results=True
        )
        
        questions2 = [
            QuizQuestion(
                quiz=quiz2,
                question_text='What is the SI unit of force?',
                question_type='multiple_choice',
                points=10,
                option_a='Joule',
                option_b='Newton',
                option_c='Watt',
                option_d='Pascal',
                correct_answer='B',
                explanation='Newton (N) is the SI unit of force. It is defined as kg.m.s^-2'
            ),
            QuizQuestion(
                quiz=quiz2,
                question_text='Velocity is a scalar quantity. (True or False)',
                question_type='true_false',
                points=10,
                option_a='True',
                option_b='False',
                correct_answer='False',
                explanation='Velocity is a vector quantity because it has both magnitude and direction. Speed is scalar.'
            )
        ]
        
        for q in questions2:
            db.session.add(q)
        
        db.session.add(quiz2)
        db.session.commit()
        print("[OK] Quiz 2 created: Science - Basic Physics")
        
        print("\n" + "="*50)
        print("[OK] SAMPLE DATA INITIALIZATION COMPLETE!")
        print("="*50)
        print("\nYou can now login with:")
        print("  Admin:    Admin / admin123")
        print("  Teacher:  Teacher / teacher123")
        print("  Student:  EA24C01 / student123")
        print("           EA24D02 / student123")
        print("           EA24E03 / student123")
        print("\nStart the application with: python run.py")

if __name__ == '__main__':
    init_sample_data()
