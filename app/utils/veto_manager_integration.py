#!/usr/bin/env python3
"""
VETO Manager Integration
Integrates the main VETO Manager with the Flask app for API access.
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


class VetoManagerIntegration:
    """Integrates with the main VETO Manager for Flask app access"""
    
    def __init__(self, data_path: Path = Path('instance/offline_scoreboard_data.json')):
        self.data_path = data_path
        self.balances: Dict[str, VetoBalance] = {}
        self._lock = threading.Lock()
        self._load_from_hardenend_data()
    
    def _load_from_hardenend_data(self):
        """Load VETO data from hardened veto_tracking"""
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
            
            # Load student balances from hardened data
            for roll, student_data in veto_tracking.get('students', {}).items():
                self.balances[roll] = VetoBalance(
                    roll=roll,
                    name=student_data.get('name', 'Unknown'),
                    individual_vetos=student_data.get('individual_vetos', 0),
                    role_vetos=student_data.get('role_vetos', 0),
                    total_vetos=student_data.get('total_vetos', 0),
                    used_vetos=student_data.get('used_vetos', 0)
                )
            
            print(f"✓ Loaded {len(self.balances)} student VETO balances")
            
        except Exception as e:
            print(f"❌ Error loading VETO data: {e}")
    
    def _save_usage(self, roll: str, used_count: int, reason: str):
        """Save VETO usage to the main data file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update veto_tracking
            if roll in data['veto_tracking']['students']:
                data['veto_tracking']['students'][roll]['used_vetos'] += used_count
                data['veto_tracking']['students'][roll]['remaining_vetos'] -= used_count
                data['veto_tracking']['students'][roll]['last_used'] = datetime.now().isoformat()
            
            # Add to usage log
            usage_entry = {
                'timestamp': datetime.now().isoformat(),
                'roll': roll,
                'name': self.balances[roll].name,
                'vetos_used': used_count,
                'remaining_after': self.balances[roll].remaining_vetos,
                'reason': reason,
                'action': 'veto_used'
            }
            data['veto_tracking']['usage_log'].append(usage_entry)
            
            # Update main student record
            for student in data.get('students', []):
                if student.get('roll') == roll:
                    student['used_veto_count'] = data['veto_tracking']['students'][roll]['used_vetos']
                    break
            
            # Save atomically
            with self._lock:
                with open(self.data_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            print(f"❌ Error saving VETO usage: {e}")
    
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
        """Use VETOs with deduction from global counter"""
        can_use, msg = self.can_use_veto(roll, count)
        if not can_use:
            return False, msg
        
        with self._lock:
            balance = self.balances[roll]
            if balance.use_vetos(count):
                # Save to main data file
                self._save_usage(roll, count, reason)
                return True, f"✓ {count} VETO(s) used. Remaining: {balance.remaining_vetos}"
            
            return False, "Failed to use VETOs"
    
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


# Global instance
_veto_manager = None
_manager_lock = threading.Lock()


def get_veto_manager() -> VetoManagerIntegration:
    """Get global VETO manager instance"""
    global _veto_manager
    if _veto_manager is None:
        with _manager_lock:
            if _veto_manager is None:
                _veto_manager = VetoManagerIntegration()
    return _veto_manager


def main():
    """Test the VETO manager integration"""
    manager = get_veto_manager()
    
    print("=" * 60)
    print("VETO MANAGER INTEGRATION STATUS")
    print("=" * 60)
    
    status = manager.get_system_status()
    print(f"Status: {status['status']}")
    
    if status['status'] == 'active':
        print(f"Students: {status['total_students']}")
        print(f"With VETOs: {status['students_with_vetos']}")
        print(f"Allocated: {status['total_vetos_allocated']}")
        print(f"Used: {status['total_vetos_used']}")
        print(f"Remaining: {status['total_vetos_remaining']}")
        
        print("\nTop VETO Holders:")
        for holder in manager.get_top_holders(5):
            print(f"  {holder['name']}: {holder['remaining_vetos']}/{holder['total_vetos']}")
        
        print("\nRecent Usage:")
        for usage in manager.get_recent_usage(5):
            print(f"  {usage.get('timestamp', '')[:19]} | {usage.get('name', 'Unknown')} used {usage.get('vetos_used', 0)}")
    else:
        print(f"Message: {status.get('message', 'Unknown error')}")
        print("\nTo initialize the VETO system, run:")
        print("  python veto_manager.py")


if __name__ == '__main__':
    main()
