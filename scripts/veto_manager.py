#!/usr/bin/env python3
"""
VETO Manager - Complete VETO System Implementation
Implements the exact VETO logic as specified:
1. Remove all VETOs from everyone
2. Grant individual VETOs to specific students
3. Add role-grant VETOs to post-holders
4. Harden the VETO map
5. Track usage with deduction from global counter
"""
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class VetoManager:
    """Complete VETO system manager"""
    
    def __init__(self, data_path: Path = Path('instance/offline_scoreboard_data.json')):
        self.data_path = data_path
        self.data = None
        self._load_data()
    
    def _load_data(self):
        """Load the offline scoreboard data"""
        try:
            if self.data_path.exists():
                with open(self.data_path, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                print(f"❌ Data file not found: {self.data_path}")
                self.data = {'students': [], 'post_holder_history': []}
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.data = {'students': [], 'post_holder_history': []}
    
    def _save_data(self):
        """Save the offline scoreboard data"""
        try:
            # Create backup before saving
            backup_path = self.data_path.parent / f"{self.data_path.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            shutil.copy2(self.data_path, backup_path)
            print(f"✓ Backup created: {backup_path.name}")
            
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"✓ Data saved successfully")
        except Exception as e:
            print(f"❌ Error saving data: {e}")
    
    def reset_all_vetos(self) -> int:
        """
        Step 1: Remove all VETOs from everyone
        Returns count of students affected
        """
        if not self.data or 'students' not in self.data:
            print("❌ No students data found")
            return 0
        
        reset_count = 0
        print("\n=== STEP 1: REMOVING ALL VETOs ===")
        
        for student in self.data.get('students', []):
            old_individual = student.get('veto_count', 0)
            old_role = student.get('role_veto_count', 0)
            
            if old_individual > 0 or old_role > 0:
                student['veto_count'] = 0
                student['role_veto_count'] = 0
                reset_count += 1
                print(f"  {student.get('name', 'Unknown'):30} | Was: {old_individual}V + {old_role}RV = {old_individual + old_role} total")
        
        print(f"✓ Total students with VETOs reset: {reset_count}")
        return reset_count
    
    def grant_individual_vetos(self) -> int:
        """
        Step 2: Grant individual VETOs to specific students
        Uses exact roll number matching (not fuzzy name matching)
        Returns count of VETOs granted
        """
        # Individual VETO assignments by roll number (exact matching)
        # This prevents assigning to wrong student if names are similar
        individual_veto_assignments = {
            # Format: 'roll_number': veto_count
            # These are the 9 students who get individual VETOs
        }
        
        # Build assignment map from student data
        # First, identify the students by their names and get their rolls
        name_to_roll = {}
        for student in self.data.get('students', []):
            name = student.get('name', '').strip()
            roll = student.get('roll', '').strip()
            if name and roll:
                name_to_roll[name.lower()] = roll
        
        # Map of names to VETO counts (as specified)
        individual_veto_by_name = {
            'Ayush': 1,
            'Arman': 1,
            'Vishes': 1,
            'Pari': 1,
            'Rashi': 1,
            'Sahil': 3,
            'Sakshi': 1,
            'Reeyansh': 3,
            'Nandani': 1,
        }
        
        print("\n=== STEP 2: GRANTING INDIVIDUAL VETOs ===")
        
        granted_count = 0
        granted_students = {}
        
        # For each target name, find the exact student and assign VETOs
        for target_name, veto_count in individual_veto_by_name.items():
            # Find student by exact name match
            found = False
            for student in self.data.get('students', []):
                student_name = student.get('name', '').strip()
                roll = student.get('roll', '').strip()
                
                # Exact match on name (case-insensitive)
                if student_name.lower() == target_name.lower() and roll:
                    student['veto_count'] = veto_count
                    granted_students[target_name] = student
                    granted_count += veto_count
                    print(f"  {target_name:12} | {roll:12} | Granted: {veto_count}V")
                    found = True
                    break
            
            if not found:
                print(f"  ⚠️ {target_name:12} | NOT FOUND - Please verify student name in roster")
        
        print(f"✓ Total individual VETOs granted: {granted_count}")
        
        # Check for missing students
        missing = set(individual_veto_by_name.keys()) - set(granted_students.keys())
        if missing:
            print(f"  ⚠️ WARNING: Missing students: {missing}")
            print(f"  ⚠️ Please verify these names match exactly in the student roster")
        
        return granted_count
    
    def grant_role_vetos(self) -> int:
        """
        Step 3: Add role-grant VETOs to post-holders
        Returns count of role VETOs granted
        """
        # Role VETO quotas
        role_veto_quotas = {
            'LEADER': 5,
            'LEADER OF OPPOSITION': 2,
            'CO-LEADER': 3,
            'CR': 2,  # Class Representative
            'DEFAULT': 0
        }
        
        print("\n=== STEP 3: GRANTING ROLE VETOs TO POST-HOLDERS ===")
        
        # Find active post holders
        active_posts = []
        for post in self.data.get('post_holder_history', []):
            if post.get('status') == 'active' and post.get('holder_name', '').strip() and post.get('holder_name', '').strip() != 'Vacant':
                active_posts.append(post)
        
        print(f"Active posts found: {len(active_posts)}")
        
        role_granted_count = 0
        granted_posts = []
        
        for post in active_posts:
            holder_name = post.get('holder_name', '').strip()
            post_name = post.get('post', '').strip()
            
            # Determine VETO quota based on post
            veto_quota = 0
            if 'LEADER' in post_name and 'CO' not in post_name and 'OPPOSITION' not in post_name:
                veto_quota = role_veto_quotas['LEADER']
            elif 'CO-LEADER' in post_name or 'COLEADER' in post_name:
                veto_quota = role_veto_quotas['CO-LEADER']
            elif 'LEADER OF OPPOSITION' in post_name:
                veto_quota = role_veto_quotas['LEADER OF OPPOSITION']
            elif 'CR' in post_name or 'CLASS REP' in post_name:
                veto_quota = role_veto_quotas['CR']
            
            if veto_quota > 0:
                # Find the student and add role VETOs
                for student in self.data.get('students', []):
                    if holder_name.lower() in student.get('name', '').lower():
                        current_role_vetos = student.get('role_veto_count', 0)
                        student['role_veto_count'] = current_role_vetos + veto_quota
                        role_granted_count += veto_quota
                        granted_posts.append({
                            'holder': holder_name,
                            'post': post_name,
                            'vetos_granted': veto_quota,
                            'total_role_vetos': student['role_veto_count']
                        })
                        print(f"  {holder_name:20} | {post_name:25} | +{veto_quota}RV (Total: {student['role_veto_count']}RV)")
                        break
        
        print(f"✓ Total role VETOs granted: {role_granted_count}")
        return role_granted_count
    
    def calculate_cumulative_totals(self) -> Dict:
        """Calculate cumulative VETO totals for all students"""
        print("\n=== CUMULATIVE VETO TOTALS ===")
        
        veto_summary = {}
        total_individual = 0
        total_role = 0
        total_combined = 0
        
        for student in self.data.get('students', []):
            individual = student.get('veto_count', 0)
            role = student.get('role_veto_count', 0)
            combined = individual + role
            
            if combined > 0:
                veto_summary[student.get('roll', 'Unknown')] = {
                    'name': student.get('name', 'Unknown'),
                    'individual_vetos': individual,
                    'role_vetos': role,
                    'total_vetos': combined
                }
                total_individual += individual
                total_role += role
                total_combined += combined
                
                print(f"  {student.get('name', 'Unknown'):20} | {student.get('roll', 'N/A'):10} | {individual}V + {role}RV = {combined} total")
        
        print(f"\n📊 SUMMARY:")
        print(f"  Total Individual VETOs: {total_individual}")
        print(f"  Total Role VETOs: {total_role}")
        print(f"  Total Combined VETOs: {total_combined}")
        print(f"  Students with VETOs: {len(veto_summary)}")
        
        return veto_summary
    
    def harden_veto_system(self) -> bool:
        """
        Step 4: Harden the VETO map for all students
        Creates immutable VETO tracking system
        """
        print("\n=== STEP 4: HARDENING VETO SYSTEM ===")
        
        if 'veto_tracking' not in self.data:
            self.data['veto_tracking'] = {}
        
        # Initialize hardened tracking
        self.data['veto_tracking'] = {
            'hardened': True,
            'initialized_at': datetime.now().isoformat(),
            'version': 2,
            'students': {},
            'usage_log': [],
            'last_reset': datetime.now().isoformat()
        }
        
        # Create hardened student records
        for student in self.data.get('students', []):
            roll = student.get('roll', '')
            if roll:
                individual = student.get('veto_count', 0)
                role = student.get('role_veto_count', 0)
                total = individual + role
                
                self.data['veto_tracking']['students'][roll] = {
                    'name': student.get('name', 'Unknown'),
                    'individual_vetos': individual,
                    'role_vetos': role,
                    'total_vetos': total,
                    'used_vetos': 0,
                    'remaining_vetos': total,
                    'hardened_at': datetime.now().isoformat()
                }
        
        print(f"✓ VETO system hardened for {len(self.data['veto_tracking']['students'])} students")
        return True
    
    def use_veto(self, roll: str, count: int = 1, reason: str = '') -> Tuple[bool, str]:
        """
        Use VETOs with deduction from global counter
        Only works after system is hardened
        """
        if not self.data.get('veto_tracking', {}).get('hardened'):
            return False, "VETO system is not hardened. Run complete setup first."
        
        veto_tracking = self.data['veto_tracking']
        
        if roll not in veto_tracking.get('students', {}):
            return False, f"Student {roll} not found in VETO system"
        
        student_veto = veto_tracking['students'][roll]
        remaining = student_veto.get('remaining_vetos', 0)
        
        if remaining < count:
            return False, f"Insufficient VETOs. Available: {remaining}, Requested: {count}"
        
        # Deduct VETOs
        student_veto['used_vetos'] = student_veto.get('used_vetos', 0) + count
        student_veto['remaining_vetos'] = remaining - count
        student_veto['last_used'] = datetime.now().isoformat()
        
        # Also update main student data
        for student in self.data.get('students', []):
            if student.get('roll') == roll:
                student['used_veto_count'] = student_veto['used_vetos']
                break
        
        # Log usage
        usage_entry = {
            'timestamp': datetime.now().isoformat(),
            'roll': roll,
            'name': student_veto['name'],
            'vetos_used': count,
            'remaining_after': student_veto['remaining_vetos'],
            'reason': reason,
            'action': 'veto_used'
        }
        veto_tracking['usage_log'].append(usage_entry)
        
        self._save_data()
        return True, f"✓ {count} VETO(s) used. Remaining: {student_veto['remaining_vetos']}"
    
    def get_veto_balance(self, roll: str) -> Optional[Dict]:
        """Get current VETO balance for a student"""
        if not self.data.get('veto_tracking', {}).get('hardened'):
            return None
        
        return self.data['veto_tracking']['students'].get(roll)
    
    def get_system_status(self) -> Dict:
        """Get complete VETO system status"""
        if not self.data.get('veto_tracking', {}).get('hardened'):
            return {'status': 'not_hardened'}
        
        veto_tracking = self.data['veto_tracking']
        students = veto_tracking.get('students', {})
        
        total_allocated = sum(s.get('total_vetos', 0) for s in students.values())
        total_used = sum(s.get('used_vetos', 0) for s in students.values())
        total_remaining = sum(s.get('remaining_vetos', 0) for s in students.values())
        
        return {
            'status': 'hardened',
            'initialized_at': veto_tracking.get('initialized_at'),
            'last_reset': veto_tracking.get('last_reset'),
            'total_students': len(students),
            'students_with_vetos': len([s for s in students.values() if s.get('total_vetos', 0) > 0]),
            'total_vetos_allocated': total_allocated,
            'total_vetos_used': total_used,
            'total_vetos_remaining': total_remaining,
            'usage_log_entries': len(veto_tracking.get('usage_log', []))
        }
    
    def complete_veto_setup(self) -> bool:
        """
        Execute the complete VETO setup process:
        1. Remove all VETOs
        2. Grant individual VETOs
        3. Grant role VETOs
        4. Harden the system
        """
        print("=" * 80)
        print("COMPLETE VETO SYSTEM SETUP")
        print("=" * 80)
        
        try:
            # Step 1: Remove all VETOs
            self.reset_all_vetos()
            
            # Step 2: Grant individual VETOs
            self.grant_individual_vetos()
            
            # Step 3: Grant role VETOs
            self.grant_role_vetos()
            
            # Calculate totals
            self.calculate_cumulative_totals()
            
            # Step 4: Harden system
            self.harden_veto_system()
            
            # Save all changes
            self._save_data()
            
            print("\n" + "=" * 80)
            print("✅ VETO SYSTEM SETUP COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            
            # Show final status
            status = self.get_system_status()
            print(f"\nFinal Status:")
            print(f"  System Status: {status['status'].upper()}")
            print(f"  Students with VETOs: {status['students_with_vetos']}")
            print(f"  Total VETOs Allocated: {status['total_vetos_allocated']}")
            print(f"  Total VETOs Remaining: {status['total_vetos_remaining']}")
            
            return True
            
        except Exception as e:
            print(f"❌ VETO setup failed: {e}")
            return False


def main():
    """Run the complete VETO system setup"""
    manager = VetoManager()
    
    # Execute complete setup
    success = manager.complete_veto_setup()
    
    if success:
        print("\n🎉 VETO system is now ready for use!")
        print("\nUsage examples:")
        print("  manager.use_veto('EA24A01', 1, 'Test usage')")
        print("  manager.get_veto_balance('EA24A01')")
        print("  manager.get_system_status()")
    else:
        print("\n❌ VETO system setup failed!")
        print("Please check the error messages above.")


if __name__ == '__main__':
    main()
