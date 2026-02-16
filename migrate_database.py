#!/usr/bin/env python
"""
Database Migration Script for Project EA
Adds indexes, constraints, and optimizations for better performance and data integrity

Run this script to upgrade your existing database:
    python migrate_database.py

IMPORTANT: This script creates a backup before making changes.
"""

import os
import sys
import shutil
from datetime import datetime
from sqlalchemy import create_engine, text, inspect, Index
from sqlalchemy.exc import OperationalError, IntegrityError

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, StudentProfile, StudentPoints, StudentLeaderboard, MonthlyPointsSummary
from app.models.user import ActivityLog


def backup_database():
    """Create a backup of the database before migration"""
    db_path = os.path.join('instance', 'ea_tutorial.db')
    if not os.path.exists(db_path):
        print("[WARNING] Database not found at instance/ea_tutorial.db")
        return False

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = os.path.join('instance', 'database_backups')
    os.makedirs(backup_dir, exist_ok=True)

    backup_path = os.path.join(backup_dir, f'ea_tutorial_backup_{timestamp}.db')

    try:
        shutil.copy2(db_path, backup_path)
        backup_size = os.path.getsize(backup_path) / 1024  # KB
        print(f"[SUCCESS] Database backup created: {backup_path} ({backup_size:.1f} KB)")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create backup: {str(e)}")
        return False


def check_existing_indexes(engine):
    """Check what indexes already exist"""
    inspector = inspect(engine)
    existing_indexes = {}

    for table_name in ['student_points', 'student_leaderboard', 'monthly_points_summary',
                       'activity_logs', 'student_profiles', 'users']:
        try:
            indexes = inspector.get_indexes(table_name)
            existing_indexes[table_name] = [idx['name'] for idx in indexes]
        except:
            existing_indexes[table_name] = []

    return existing_indexes


def add_indexes(app):
    """Add performance indexes to database tables"""
    print("\n[INDEXES] Adding Database Indexes...")

    with app.app_context():
        engine = db.engine
        existing_indexes = check_existing_indexes(engine)

        indexes_to_create = [
            # StudentPoints indexes for fast queries
            {
                'name': 'idx_student_points_student_date',
                'table': 'student_points',
                'columns': ['student_id', 'date_recorded'],
                'model': StudentPoints,
                'index_obj': Index('idx_student_points_student_date',
                                  StudentPoints.student_id,
                                  StudentPoints.date_recorded)
            },
            {
                'name': 'idx_student_points_date',
                'table': 'student_points',
                'columns': ['date_recorded'],
                'model': StudentPoints,
                'index_obj': Index('idx_student_points_date', StudentPoints.date_recorded)
            },

            # StudentLeaderboard indexes
            {
                'name': 'idx_leaderboard_year_month',
                'table': 'student_leaderboard',
                'columns': ['year', 'month'],
                'model': StudentLeaderboard,
                'index_obj': Index('idx_leaderboard_year_month',
                                  StudentLeaderboard.year,
                                  StudentLeaderboard.month)
            },
            {
                'name': 'idx_leaderboard_student_year_month',
                'table': 'student_leaderboard',
                'columns': ['student_id', 'year', 'month'],
                'model': StudentLeaderboard,
                'index_obj': Index('idx_leaderboard_student_year_month',
                                  StudentLeaderboard.student_id,
                                  StudentLeaderboard.year,
                                  StudentLeaderboard.month)
            },

            # ActivityLog indexes
            {
                'name': 'idx_activity_timestamp',
                'table': 'activity_logs',
                'columns': ['timestamp'],
                'model': ActivityLog,
                'index_obj': Index('idx_activity_timestamp', ActivityLog.timestamp)
            },
            {
                'name': 'idx_activity_user_timestamp',
                'table': 'activity_logs',
                'columns': ['user_id', 'timestamp'],
                'model': ActivityLog,
                'index_obj': Index('idx_activity_user_timestamp',
                                  ActivityLog.user_id,
                                  ActivityLog.timestamp)
            },

            # User indexes
            {
                'name': 'idx_user_login_id',
                'table': 'users',
                'columns': ['login_id'],
                'model': User,
                'index_obj': Index('idx_user_login_id', User.login_id)
            },

            # StudentProfile indexes
            {
                'name': 'idx_student_profile_roll',
                'table': 'student_profiles',
                'columns': ['roll_number'],
                'model': StudentProfile,
                'index_obj': Index('idx_student_profile_roll', StudentProfile.roll_number)
            },
            {
                'name': 'idx_student_profile_class',
                'table': 'student_profiles',
                'columns': ['class_name'],
                'model': StudentProfile,
                'index_obj': Index('idx_student_profile_class', StudentProfile.class_name)
            },
        ]

        created_count = 0
        skipped_count = 0

        for idx_info in indexes_to_create:
            table_name = idx_info['table']
            idx_name = idx_info['name']

            # Check if index already exists
            if idx_name in existing_indexes.get(table_name, []):
                print(f"  [SKIP] {idx_name} - Already exists")
                skipped_count += 1
                continue

            try:
                # Create the index
                idx_info['index_obj'].create(engine)
                print(f"  [OK] {idx_name} - Created on {table_name}({', '.join(idx_info['columns'])})")
                created_count += 1
            except OperationalError as e:
                if 'already exists' in str(e).lower():
                    print(f"  [SKIP] {idx_name} - Already exists (detected via error)")
                    skipped_count += 1
                else:
                    print(f"  [WARN] {idx_name} - Error: {str(e)}")
            except Exception as e:
                print(f"  [ERROR] {idx_name} - Failed: {str(e)}")

        print(f"\n[SUMMARY] Index Summary: {created_count} created, {skipped_count} skipped")


def add_unique_constraints(app):
    """Add unique constraints to prevent duplicate data"""
    print("\n[CONSTRAINTS] Adding Unique Constraints...")

    with app.app_context():
        engine = db.engine

        # Check if constraint already exists
        inspector = inspect(engine)

        try:
            # Get existing constraints on student_points
            constraints = inspector.get_unique_constraints('student_points')
            constraint_names = [c['name'] for c in constraints]

            if '_student_date_points_uc' in constraint_names:
                print("  [SKIP] student_points(student_id, date_recorded) - Already exists")
            else:
                # Add unique constraint to student_points (student_id, date_recorded)
                # This prevents duplicate point entries for the same student on the same date
                with engine.connect() as conn:
                    # For SQLite, we need to check if data will violate the constraint
                    result = conn.execute(text("""
                        SELECT student_id, date_recorded, COUNT(*) as cnt
                        FROM student_points
                        GROUP BY student_id, date_recorded
                        HAVING COUNT(*) > 1
                    """))
                    duplicates = result.fetchall()

                    if duplicates:
                        print(f"  [WARN] Found {len(duplicates)} duplicate entries that need cleanup:")
                        for dup in duplicates[:5]:  # Show first 5
                            print(f"      Student {dup[0]}, Date {dup[1]}: {dup[2]} entries")

                        # Clean up duplicates (keep latest by id)
                        print("  [CLEANUP] Cleaning up duplicates (keeping latest entry)...")
                        for dup in duplicates:
                            student_id, date_recorded = dup[0], dup[1]
                            conn.execute(text("""
                                DELETE FROM student_points
                                WHERE id NOT IN (
                                    SELECT MAX(id)
                                    FROM student_points
                                    WHERE student_id = :sid AND date_recorded = :date
                                )
                                AND student_id = :sid AND date_recorded = :date
                            """), {"sid": student_id, "date": date_recorded})
                        conn.commit()
                        print(f"  [OK] Cleaned up {len(duplicates)} duplicate entries")

                    # Now add the unique constraint
                    # Note: SQLite doesn't support ALTER TABLE ADD CONSTRAINT
                    # We need to create a unique index instead
                    conn.execute(text("""
                        CREATE UNIQUE INDEX IF NOT EXISTS _student_date_points_uc
                        ON student_points(student_id, date_recorded)
                    """))
                    conn.commit()
                    print("  [OK] student_points(student_id, date_recorded) - Unique constraint added")
        except Exception as e:
            print(f"  [ERROR] Failed to add unique constraint: {str(e)}")


def optimize_database(app):
    """Run database optimization commands"""
    print("\n[OPTIMIZE] Optimizing Database...")

    with app.app_context():
        engine = db.engine

        try:
            with engine.connect() as conn:
                # Analyze tables for query optimizer
                conn.execute(text("ANALYZE"))
                print("  [OK] Database statistics updated (ANALYZE)")

                # Vacuum to reclaim space and defragment
                # Note: VACUUM cannot run inside a transaction
                conn.execute(text("VACUUM"))
                print("  [OK] Database vacuumed and defragmented")

                conn.commit()
        except Exception as e:
            print(f"  [WARN] Optimization warning: {str(e)}")


def verify_migrations(app):
    """Verify that migrations were successful"""
    print("\n[VERIFY] Verifying Migrations...")

    with app.app_context():
        engine = db.engine
        existing_indexes = check_existing_indexes(engine)

        # Expected indexes
        expected = {
            'student_points': ['idx_student_points_student_date', 'idx_student_points_date', '_student_date_points_uc'],
            'student_leaderboard': ['idx_leaderboard_year_month', 'idx_leaderboard_student_year_month'],
            'activity_logs': ['idx_activity_timestamp', 'idx_activity_user_timestamp'],
            'users': ['idx_user_login_id'],
            'student_profiles': ['idx_student_profile_roll', 'idx_student_profile_class']
        }

        all_good = True
        for table, expected_idx in expected.items():
            existing = existing_indexes.get(table, [])
            missing = [idx for idx in expected_idx if idx not in existing]

            if missing:
                print(f"  [WARN] {table}: Missing indexes {missing}")
                all_good = False
            else:
                print(f"  [OK] {table}: All indexes present")

        if all_good:
            print("\n[SUCCESS] All migrations verified successfully!")
        else:
            print("\n[WARN] Some migrations may have failed - check warnings above")


def main():
    """Main migration function"""
    print("=" * 70)
    print("PROJECT EA - DATABASE MIGRATION SCRIPT")
    print("Adds indexes, constraints, and optimizations")
    print("=" * 70)

    # Create Flask app
    app = create_app()

    # Step 1: Backup
    print("\n[STEP 1] Creating Database Backup...")
    if not backup_database():
        print("\n[ERROR] Migration aborted - could not create backup")
        return 1

    # Step 2: Add indexes
    print("\n[STEP 2] Adding Performance Indexes...")
    try:
        add_indexes(app)
    except Exception as e:
        print(f"\n[ERROR] Error adding indexes: {str(e)}")
        import traceback
        traceback.print_exc()

    # Step 3: Add unique constraints
    print("\n[STEP 3] Adding Unique Constraints...")
    try:
        add_unique_constraints(app)
    except Exception as e:
        print(f"\n[ERROR] Error adding constraints: {str(e)}")
        import traceback
        traceback.print_exc()

    # Step 4: Optimize
    print("\n[STEP 4] Optimizing Database...")
    try:
        optimize_database(app)
    except Exception as e:
        print(f"\n[WARN] Optimization warning: {str(e)}")

    # Step 5: Verify
    print("\n[STEP 5] Verifying Migrations...")
    try:
        verify_migrations(app)
    except Exception as e:
        print(f"\n[WARN] Verification error: {str(e)}")

    print("\n" + "=" * 70)
    print("[SUCCESS] MIGRATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Test the application: python run.py")
    print("2. Check logs for any errors")
    print("3. Monitor query performance")
    print("4. Database backup available in instance/database_backups/")
    print("\n")

    return 0


if __name__ == '__main__':
    exit(main())
