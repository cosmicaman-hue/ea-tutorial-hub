#!/usr/bin/env python3
"""
VETO System Migration Script
Migrates from complex veto tracking to simplified state machine pattern.
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from app.utils.veto_system import get_veto_system, VetoState


def migrate_veto_system():
    """Migrate existing veto data to new simplified system"""
    data_path = Path('instance/offline_scoreboard_data.json')
    
    if not data_path.exists():
        print("❌ No existing data file found")
        return False
    
    # Create backup
    backup_path = Path(f'instance/offline_scoreboard_data.migration_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    shutil.copy2(data_path, backup_path)
    print(f"✓ Backup created: {backup_path.name}")
    
    try:
        # Load existing data
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Get students list
        students = data.get('students', [])
        if not students:
            print("❌ No students found in data")
            return False
        
        # Initialize new VETO system
        veto_system = get_veto_system()
        
        # Migrate student data
        migrated_students = []
        for student in students:
            migrated_student = {
                'id': student.get('id', ''),
                'name': student.get('name', ''),
                'roll': student.get('id', ''),
                'class': student.get('class', ''),
                'points': student.get('points', 0),
                'stars': student.get('stars', 0),
                'veto_count': student.get('veto_count', 0),
                'role_veto_count': student.get('role_veto_count', 0)
            }
            migrated_students.append(migrated_student)
        
        # Initialize new system
        if veto_system.initialize_from_students(migrated_students):
            print(f"✓ Migrated {len(migrated_students)} students to new VETO system")
            
            # Show migration summary
            status = veto_system.get_system_status()
            print(f"\nMigration Summary:")
            print(f"  State: {status['state']}")
            print(f"  Students with VETOs: {status['students_with_vetos']}")
            print(f"  Total VETOs allocated: {status['total_vetos_allocated']}")
            
            # Clean up old veto tracking data
            if 'veto_tracking' in data:
                del data['veto_tracking']
                print("✓ Removed old veto_tracking data")
            
            # Save updated data
            with open(data_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print("✓ Migration completed successfully")
            return True
        else:
            print("❌ Failed to initialize new VETO system")
            return False
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        # Restore backup on failure
        shutil.copy2(backup_path, data_path)
        print(f"✓ Restored backup due to failure")
        return False


def main():
    """Run migration"""
    print("=" * 60)
    print("VETO SYSTEM MIGRATION")
    print("=" * 60)
    
    if migrate_veto_system():
        print("\n✅ Migration completed successfully!")
        print("Old complex veto system has been replaced with simplified state machine.")
    else:
        print("\n❌ Migration failed!")
        print("Check the error messages above and restore from backup if needed.")


if __name__ == '__main__':
    main()
