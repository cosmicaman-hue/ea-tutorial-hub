#!/usr/bin/env python3
"""
Unified VETO Manager - Single Source of Truth
Fixes the dual tracking issue by using veto_tracking as the authoritative source.
All VETO operations go through this manager.
"""
import json
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class VetoBalance:
    """Student VETO balance"""
    roll: str
    name: str
    individual_vetos: int = 0
    role_vetos: int = 0
    total_vetos: int = 0
    used_vetos: int = 0
    
    @property
    def remaining_vetos(self) -> int:
        return max(0, self.total_vetos - self.used_vetos)
    
    def can_use(self, count: int) -> bool:
        return self.remaining_vetos >= count > 0
    
    def use_vetos(self, count: int) -> bool:
        if self.can_use(count):
            self.used_vetos += count
            return True
        return False
    
    def restore_vetos(self, count: int) -> bool:
        if count > 0 and self.used_vetos >= count:
            self.used_vetos -= count
            return True
        return False


class UnifiedVetoManager:
    """
    Unified VETO manager with single source of truth.
    - veto_tracking is the authoritative source
    - students[] array is synced from veto_tracking
    - All operations are atomic and thread-safe
    """
    
    def __init__(self, data_path: Path = Path('instance/offline_scoreboard_data.json')):
        self.data_path = data_path
        self.balances: Dict[str, VetoBalance] = {}
        self._lock = threading.Lock()
        self._load_from_hardened_data()
    
    def _load_from_hardened_data(self):
        """Load VETO data from hardened veto_tracking (single source of truth)"""
        try:
            if not self.data_path.exists():
                print("⚠️ VETO data file not found. Run veto_manager.py first.")
                return
            
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            veto_tracking = data.get('veto_tracking', {})
            
            if not veto_tracking.get('hardened'):
                print("⚠️ VETO system not hardened. Run veto_manager.py first.")
                return
            
            # Load student balances from hardened data (single source of truth)
            for roll, student_data in veto_tracking.get('students', {}).items():
                self.balances[roll] = VetoBalance(
                    roll=roll,
                    name=student_data.get('name', 'Unknown'),
                    individual_vetos=student_data.get('individual_vetos', 0),
                    role_vetos=student_data.get('role_vetos', 0),
                    total_vetos=student_data.get('total_vetos', 0),
                    used_vetos=student_data.get('used_vetos', 0)
                )
            
            print(f"✓ Loaded {len(self.balances)} student VETO balances from authoritative source")
            
        except Exception as e:
            print(f"❌ Error loading VETO data: {e}")
    
    def _save_atomically(self, operation_name: str = ""):
        """
        Save VETO state atomically to file.
        Ensures veto_tracking and students[] stay in sync.
        """
        try:
            with self._lock:
                # Read current data
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update veto_tracking (authoritative source)
                veto_tracking = data.get('veto_tracking', {})
                for roll, balance in self.balances.items():
                    veto_tracking['students'][roll] = {
                        'name': balance.name,
                        'individual_vetos': balance.individual_vetos,
                        'role_vetos': balance.role_vetos,
                        'total_vetos': balance.total_vetos,
                        'used_vetos': balance.used_vetos,
                        'remaining_vetos': balance.remaining_vetos,
                        'last_updated': datetime.now().isoformat()
                    }
                
                # Sync students[] array from veto_tracking
                for student in data.get('students', []):
                    roll = student.get('roll', '')
                    if roll in self.balances:
                        balance = self.balances[roll]
                        # Sync individual and role VETOs
                        student['veto_count'] = balance.individual_vetos
                        student['role_veto_count'] = balance.role_vetos
                        student['used_veto_count'] = balance.used_vetos
                
                # Write atomically
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                if operation_name:
                    print(f"✓ {operation_name} - Data saved atomically")
                    
        except Exception as e:
            print(f"❌ Error saving VETO data: {e}")
    
    def get_balance(self, roll: str) -> Optional[VetoBalance]:
        """Get VETO balance for a student"""
        return self.balances.get(roll)
    
    def can_use_veto(self, roll: str, count: int) -> Tuple[bool, str]:
        """Check if student can use VETOs"""
        if count <= 0:
            return False, "Invalid VETO count"
        
        balance = self.get_balance(roll)
        if not balance:
            return False, f"Student {roll} not found"
        
        if balance.can_use(count):
            return True, f"OK: {balance.remaining_vetos} VETOs available"
        else:
            return False, f"Insufficient VETOs. Available: {balance.remaining_vetos}, Requested: {count}"
    
    def use_veto(self, roll: str, count: int, reason: str = "") -> Tuple[bool, str]:
        """
        Use VETOs with atomic deduction from global counter.
        Thread-safe and atomic operation.
        """
        can_use, msg = self.can_use_veto(roll, count)
        if not can_use:
            return False, msg
        
        with self._lock:
            # Double-check within lock (prevent race condition)
            balance = self.balances[roll]
            if not balance.can_use(count):
                return False, f"Insufficient VETOs (race condition detected)"
            
            # Deduct VETOs
            balance.use_vetos(count)
            
            # Save atomically
            self._save_atomically(f"VETO used by {roll}: {count}V ({reason})")
            
            # Log usage
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                usage_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'roll': roll,
                    'name': balance.name,
                    'vetos_used': count,
                    'remaining_after': balance.remaining_vetos,
                    'reason': reason,
                    'action': 'veto_used'
                }
                data['veto_tracking']['usage_log'].append(usage_entry)
                
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Warning: Could not log usage: {e}")
            
            return True, f"✓ {count} VETO(s) used. Remaining: {balance.remaining_vetos}"
    
    def restore_veto(self, roll: str, count: int, reason: str = "admin_restoration") -> Tuple[bool, str]:
        """
        Restore VETOs (admin function).
        Thread-safe and atomic operation with audit trail.
        """
        if count <= 0:
            return False, "Invalid VETO count"
        
        balance = self.get_balance(roll)
        if not balance:
            return False, f"Student {roll} not found"
        
        with self._lock:
            if balance.used_vetos < count:
                return False, f"Cannot restore more than used ({balance.used_vetos})"
            
            # Restore VETOs
            balance.restore_vetos(count)
            
            # Save atomically
            self._save_atomically(f"VETO restored for {roll}: {count}V ({reason})")
            
            # Log restoration
            try:
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                restoration_entry = {
                    'timestamp': datetime.now().isoformat(),
                    'roll': roll,
                    'name': balance.name,
                    'vetos_restored': count,
                    'remaining_after': balance.remaining_vetos,
                    'reason': reason,
                    'action': 'veto_restored'
                }
                data['veto_tracking']['usage_log'].append(restoration_entry)
                
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            except Exception as e:
                print(f"⚠️ Warning: Could not log restoration: {e}")
            
            return True, f"✓ {count} VETO(s) restored. Remaining: {balance.remaining_vetos}"
    
    def get_system_status(self) -> Dict:
        """Get complete VETO system status"""
        if not self.balances:
            return {
                'status': 'not_initialized',
                'message': 'Run veto_manager.py to initialize the VETO system'
            }
        
        total_allocated = sum(b.total_vetos for b in self.balances.values())
        total_used = sum(b.used_vetos for b in self.balances.values())
        total_remaining = sum(b.remaining_vetos for b in self.balances.values())
        
        return {
            'status': 'active',
            'total_students': len(self.balances),
            'students_with_vetos': len([b for b in self.balances.values() if b.total_vetos > 0]),
            'total_vetos_allocated': total_allocated,
            'total_vetos_used': total_used,
            'total_vetos_remaining': total_remaining
        }
    
    def get_top_holders(self, limit: int = 10) -> List[Dict]:
        """Get top VETO holders by remaining VETOs"""
        sorted_balances = sorted(
            [b for b in self.balances.values() if b.total_vetos > 0],
            key=lambda x: x.remaining_vetos,
            reverse=True
        )
        return [asdict(b) for b in sorted_balances[:limit]]
    
    def get_recent_usage(self, limit: int = 20) -> List[Dict]:
        """Get recent VETO usage from the log"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            usage_log = data.get('veto_tracking', {}).get('usage_log', [])
            recent = sorted(usage_log, key=lambda x: x.get('timestamp', ''), reverse=True)[:limit]
            return recent
            
        except Exception as e:
            print(f"❌ Error getting usage log: {e}")
            return []
    
    def verify_consistency(self) -> Tuple[bool, List[str]]:
        """
        Verify that veto_tracking and students[] are in sync.
        Returns (is_consistent, list_of_issues)
        """
        issues = []
        
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            veto_tracking = data.get('veto_tracking', {})
            students = data.get('students', [])
            
            # Check each student
            for student in students:
                roll = student.get('roll', '')
                if not roll:
                    continue
                
                veto_data = veto_tracking.get('students', {}).get(roll, {})
                if not veto_data:
                    issues.append(f"Student {roll} missing from veto_tracking")
                    continue
                
                # Check individual VETOs
                student_individual = student.get('veto_count', 0)
                veto_individual = veto_data.get('individual_vetos', 0)
                if student_individual != veto_individual:
                    issues.append(f"Student {roll}: individual VETOs mismatch ({student_individual} vs {veto_individual})")
                
                # Check role VETOs
                student_role = student.get('role_veto_count', 0)
                veto_role = veto_data.get('role_vetos', 0)
                if student_role != veto_role:
                    issues.append(f"Student {roll}: role VETOs mismatch ({student_role} vs {veto_role})")
            
            is_consistent = len(issues) == 0
            return is_consistent, issues
            
        except Exception as e:
            return False, [f"Error checking consistency: {e}"]


# Global instance
_veto_manager = None
_manager_lock = threading.Lock()


def get_unified_veto_manager() -> UnifiedVetoManager:
    """Get global unified VETO manager instance"""
    global _veto_manager
    if _veto_manager is None:
        with _manager_lock:
            if _veto_manager is None:
                _veto_manager = UnifiedVetoManager()
    return _veto_manager


def main():
    """Test the unified VETO manager"""
    manager = get_unified_veto_manager()
    
    print("=" * 60)
    print("UNIFIED VETO MANAGER STATUS")
    print("=" * 60)
    
    status = manager.get_system_status()
    print(f"Status: {status['status']}")
    
    if status['status'] == 'active':
        print(f"Students: {status['total_students']}")
        print(f"With VETOs: {status['students_with_vetos']}")
        print(f"Allocated: {status['total_vetos_allocated']}")
        print(f"Used: {status['total_vetos_used']}")
        print(f"Remaining: {status['total_vetos_remaining']}")
        
        # Verify consistency
        print("\nVerifying consistency...")
        is_consistent, issues = manager.verify_consistency()
        if is_consistent:
            print("✓ veto_tracking and students[] are in sync")
        else:
            print("❌ Inconsistencies found:")
            for issue in issues:
                print(f"  - {issue}")
        
        print("\nTop VETO Holders:")
        for holder in manager.get_top_holders(5):
            print(f"  {holder['name']}: {holder['remaining_vetos']}/{holder['total_vetos']}")
        
        print("\nRecent Usage:")
        for usage in manager.get_recent_usage(5):
            print(f"  {usage.get('timestamp', '')[:19]} | {usage.get('name', 'Unknown')} {usage.get('action', '')} {usage.get('vetos_used', usage.get('vetos_restored', 0))}")
    else:
        print(f"Message: {status.get('message', 'Unknown error')}")


if __name__ == '__main__':
    main()
