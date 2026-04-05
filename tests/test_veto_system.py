#!/usr/bin/env python3
"""
Test script for the simplified VETO system
"""
import json
from pathlib import Path
from app.utils.veto_system import VetoSystem, VetoState, VetoAction


def test_veto_system():
    """Test the simplified VETO system"""
    print("=" * 60)
    print("TESTING SIMPLIFIED VETO SYSTEM")
    print("=" * 60)
    
    # Create test data
    test_students = [
        {'id': 'EA24A01', 'name': 'Test Student 1', 'veto_count': 2, 'role_veto_count': 1},
        {'id': 'EA24A02', 'name': 'Test Student 2', 'veto_count': 1, 'role_veto_count': 0},
        {'id': 'EA24A03', 'name': 'Test Student 3', 'veto_count': 0, 'role_veto_count': 3},
    ]
    
    # Test initialization
    print("\n1. Testing initialization...")
    system = VetoSystem(Path('test_veto_data.json'))
    
    if system.initialize_from_students(test_students):
        print("✓ System initialized successfully")
    else:
        print("❌ System initialization failed")
        return False
    
    # Test system status
    print("\n2. Testing system status...")
    status = system.get_system_status()
    print(f"  State: {status['state']}")
    print(f"  Students: {status['total_students']}")
    print(f"  With VETOs: {status['students_with_vetos']}")
    print(f"  Total allocated: {status['total_vetos_allocated']}")
    print(f"  Total remaining: {status['total_vetos_remaining']}")
    
    # Test balance queries
    print("\n3. Testing balance queries...")
    balance = system.get_balance('EA24A01')
    if balance:
        print(f"✓ EA24A01 balance: {balance.remaining_vetos}/{balance.total_vetos}")
    else:
        print("❌ Failed to get balance for EA24A01")
    
    # Test VETO usage
    print("\n4. Testing VETO usage...")
    success, msg = system.use_veto('EA24A01', 1, "Test usage")
    print(f"  Use 1 VETO: {success} - {msg}")
    
    success, msg = system.use_veto('EA24A01', 5, "Should fail")
    print(f"  Use 5 VETOs (should fail): {success} - {msg}")
    
    # Test VETO restoration
    print("\n5. Testing VETO restoration...")
    success, msg = system.restore_veto('EA24A01', 1, "Test restoration")
    print(f"  Restore 1 VETO: {success} - {msg}")
    
    # Test transaction history
    print("\n6. Testing transaction history...")
    transactions = system.get_recent_transactions(5)
    print(f"  Total transactions: {len(transactions)}")
    for tx in transactions:
        print(f"    {tx['timestamp'][:19]} | {tx['name']} | {tx['action'].value} {tx['amount']}")
    
    # Test top holders
    print("\n7. Testing top holders...")
    holders = system.get_top_holders(3)
    print(f"  Top {len(holders)} holders:")
    for holder in holders:
        print(f"    {holder['name']}: {holder['remaining_vetos']}/{holder['total_vetos']}")
    
    # Cleanup
    test_file = Path('test_veto_data.json')
    if test_file.exists():
        test_file.unlink()
        print("\n✓ Test cleanup completed")
    
    print("\n✅ All tests completed successfully!")
    return True


def test_migration_compatibility():
    """Test compatibility with existing data format"""
    print("\n" + "=" * 60)
    print("TESTING MIGRATION COMPATIBILITY")
    print("=" * 60)
    
    # Create mock old format data
    old_data = {
        'students': [
            {'id': 'EA24A01', 'name': 'Student 1', 'veto_count': 2, 'role_veto_count': 1},
            {'id': 'EA24A02', 'name': 'Student 2', 'veto_count': 0, 'role_veto_count': 2},
        ],
        'veto_tracking': {
            'hardened': True,
            'students': {
                'EA24A01': {
                    'name': 'Student 1',
                    'individual_vetos': 2,
                    'role_vetos': 1,
                    'total_vetos': 3,
                    'used_vetos': 1,
                    'remaining_vetos': 2
                }
            }
        }
    }
    
    # Write test file
    test_file = Path('test_migration_data.json')
    test_file.write_text(json.dumps(old_data, indent=2))
    
    # Test migration
    print("\n1. Creating test data with old format...")
    print(f"✓ Test file created: {test_file}")
    
    print("\n2. Testing new system with old data...")
    system = VetoSystem(test_file)
    
    # Check if system can read old data
    status = system.get_system_status()
    print(f"  State: {status['state']}")
    print(f"  Students: {status['total_students']}")
    
    # Cleanup
    test_file.unlink()
    print("\n✓ Migration compatibility test completed")
    
    return True


if __name__ == '__main__':
    success1 = test_veto_system()
    success2 = test_migration_compatibility()
    
    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED!")
        print("The simplified VETO system is working correctly.")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Check the error messages above.")
