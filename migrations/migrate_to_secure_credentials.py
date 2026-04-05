#!/usr/bin/env python3
"""
Secure Credential Migration Script
Safely migrates environment variable passwords to encrypted storage.
Preserves all existing data and credentials.
"""
import os
import json
from pathlib import Path
from datetime import datetime
from app.utils.secrets_manager import get_secrets_manager, get_credential_provider


def backup_env_variables():
    """Create backup of current environment variables"""
    env_backup = {
        'timestamp': datetime.now().isoformat(),
        'credentials': {}
    }
    
    # Backup relevant environment variables
    env_vars = ['ADMIN_PASSWORD', 'TEACHER_PASSWORD', 'EA_JOIN_CODE']
    for var in env_vars:
        value = os.getenv(var, '')
        if value:
            env_backup['credentials'][var] = value
    
    # Save backup file
    backup_file = Path('instance/env_backup.json')
    backup_file.parent.mkdir(exist_ok=True)
    backup_file.write_text(json.dumps(env_backup, indent=2))
    backup_file.chmod(0o600)  # Read/write for owner only
    
    print(f"✓ Environment variables backed up to: {backup_file}")
    return backup_file


def migrate_credentials():
    """Migrate credentials from environment to secure storage"""
    print("=" * 60)
    print("SECURE CREDENTIAL MIGRATION")
    print("=" * 60)
    
    # Create backup first
    backup_file = backup_env_variables()
    
    try:
        # Initialize secrets manager
        manager = get_secrets_manager()
        provider = get_credential_provider()
        
        migrated_count = 0
        
        # Check and migrate admin password
        admin_env = os.getenv('ADMIN_PASSWORD', '')
        if admin_env:
            admin_secure = provider.get_admin_password()
            if admin_secure and admin_secure != 'ChangeAdminPass123!':
                print(f"✓ Admin password already securely stored")
            else:
                manager.set_credential('admin_password', admin_env, {
                    'source': 'environment',
                    'migrated_at': datetime.now().isoformat(),
                    'previous_backup': str(backup_file)
                })
                print(f"✓ Admin password migrated to secure storage")
                migrated_count += 1
        
        # Check and migrate teacher password
        teacher_env = os.getenv('TEACHER_PASSWORD', '')
        if teacher_env:
            teacher_secure = provider.get_teacher_password()
            if teacher_secure and teacher_secure != 'ChangeTeacherPass123!':
                print(f"✓ Teacher password already securely stored")
            else:
                manager.set_credential('teacher_password', teacher_env, {
                    'source': 'environment',
                    'migrated_at': datetime.now().isoformat(),
                    'previous_backup': str(backup_file)
                })
                print(f"✓ Teacher password migrated to secure storage")
                migrated_count += 1
        
        # Check and migrate join code
        join_env = os.getenv('EA_JOIN_CODE', '')
        if join_env:
            join_secure = provider.get_join_code()
            if join_secure:
                print(f"✓ Join code already securely stored")
            else:
                manager.set_credential('join_code', join_env, {
                    'source': 'environment',
                    'migrated_at': datetime.now().isoformat(),
                    'previous_backup': str(backup_file)
                })
                print(f"✓ Join code migrated to secure storage")
                migrated_count += 1
        
        # Show migration summary
        print(f"\nMigration Summary:")
        print(f"  Credentials migrated: {migrated_count}")
        print(f"  Backup location: {backup_file}")
        
        # Show current status
        status = manager.get_status()
        print(f"\nSecure Storage Status:")
        print(f"  Total credentials: {status['credentials_count']}")
        print(f"  Version: {status['version']}")
        print(f"  Created: {status['created_at']}")
        
        # List stored credentials (without values)
        credentials = manager.list_credentials()
        print(f"\nStored Credentials:")
        for cred in credentials:
            print(f"  - {cred}")
        
        print(f"\n✅ Migration completed successfully!")
        print(f"📝 Backup saved to: {backup_file}")
        print(f"🔐 Credentials now stored securely with encryption")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"📁 Your backup is available at: {backup_file}")
        return False


def verify_migration():
    """Verify that migration was successful"""
    print("\n" + "=" * 60)
    print("MIGRATION VERIFICATION")
    print("=" * 60)
    
    try:
        provider = get_credential_provider()
        
        # Test admin password
        admin_pass = provider.get_admin_password()
        print(f"Admin password accessible: {'✓' if admin_pass else '❌'}")
        
        # Test teacher password
        teacher_pass = provider.get_teacher_password()
        print(f"Teacher password accessible: {'✓' if teacher_pass else '❌'}")
        
        # Test join code
        join_code = provider.get_join_code()
        print(f"Join code accessible: {'✓' if join_code else '✓ (optional)'}")
        
        # Check if defaults are still being used
        if admin_pass == 'ChangeAdminPass123!':
            print("⚠️  WARNING: Still using default admin password!")
        
        if teacher_pass == 'ChangeTeacherPass123!':
            print("⚠️  WARNING: Still using default teacher password!")
        
        print("\n✅ Verification completed")
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")


def show_next_steps():
    """Show recommended next steps"""
    print("\n" + "=" * 60)
    print("RECOMMENDED NEXT STEPS")
    print("=" * 60)
    
    print("\n1. 🔄 Update Environment Variables:")
    print("   You can now remove these from your .env file:")
    print("   - ADMIN_PASSWORD")
    print("   - TEACHER_PASSWORD") 
    print("   - EA_JOIN_CODE")
    
    print("\n2. 🔐 Change Default Passwords:")
    print("   If still using defaults, update them via:")
    print("   - Admin panel → User management")
    print("   - Or use the credential rotation API")
    
    print("\n3. 📋 Test Login:")
    print("   Verify that Admin and Teacher can still login")
    
    print("\n4. 💾 Backup Secure Storage:")
    print("   Backup the 'instance/secrets' folder regularly")
    
    print("\n5. 🗑️  Clean Up (Optional):")
    print("   After confirming everything works, you can")
    print("   remove password environment variables")


def main():
    """Run the complete migration process"""
    success = migrate_credentials()
    
    if success:
        verify_migration()
        show_next_steps()
        
        print(f"\n🎉 MIGRATION COMPLETE!")
        print(f"Your credentials are now securely encrypted and protected.")
    else:
        print(f"\n❌ MIGRATION FAILED!")
        print(f"Check the error messages above and retry.")


if __name__ == '__main__':
    main()
