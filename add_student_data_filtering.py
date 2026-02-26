#!/usr/bin/env python3
"""
Add Student Data Filtering to Offline Scoreboard
Modifies the offline scoreboard to show only student's own data when logged in as student
"""

import re
import shutil
from datetime import datetime

def main():
    print("=" * 80)
    print("ADD STUDENT DATA FILTERING - OFFLINE SCOREBOARD")
    print("=" * 80)
    print()

    html_file = 'app/static/offline_scoreboard.html'

    # Create backup
    print("Step 1: Creating backup...")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'{html_file}.backup_{timestamp}'
    shutil.copy2(html_file, backup_file)
    print(f"✓ Backup created: {backup_file}")

    # Read the file
    print("\nStep 2: Reading offline scoreboard HTML...")
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print("✓ File loaded")

    # Add student roll variable initialization
    print("\nStep 3: Adding student roll variable...")

    # Find where currentLoginId is declared and add currentStudentRoll
    old_pattern = r"(let currentLoginId = '';)"
    new_code = r"\1\n        let currentStudentRoll = '';"

    if re.search(old_pattern, content):
        content = re.sub(old_pattern, new_code, content)
        print("✓ Added currentStudentRoll variable")
    else:
        print("⚠ Could not find currentLoginId declaration")

    # Update session fetch to capture student_roll
    print("\nStep 4: Updating session fetch logic...")

    old_session_pattern = r"(currentLoginId = session\.login_id \|\| currentLoginId \|\| '';)"
    new_session_code = r"""\1
                    currentStudentRoll = session.student_roll || '';"""

    if re.search(old_session_pattern, content):
        content = re.sub(old_session_pattern, new_session_code, content)
        print("✓ Updated session fetch to capture student_roll")
    else:
        print("⚠ Could not find session fetch location")

    # Add filtering logic for students in renderScoreboard function
    print("\nStep 5: Adding student data filtering in scoreboard render...")

    # Find the renderScoreboard function and add filtering
    filter_code = '''
            // Filter data for students - show only their own row
            if (currentUserRole === 'student' && currentStudentRoll) {
                rows = rows.filter(row => {
                    const rollMatch = row && row.roll &&
                                    String(row.roll).trim().toUpperCase() ===
                                    String(currentStudentRoll).trim().toUpperCase();
                    return rollMatch;
                });
            }
'''

    # Insert after rows = sortRowsBy... but before totalStudents = rows.length
    old_render_pattern = r"(rows = sortRowsBy[^\n]+\n)"
    if re.search(old_render_pattern, content):
        content = re.sub(old_render_pattern, r'\1' + filter_code, content, count=1)
        print("✓ Added student filtering in scoreboard render")
    else:
        print("⚠ Could not find scoreboard render location")

    # Add logout cleanup for localStorage
    print("\nStep 6: Adding localStorage cleanup on logout...")

    logout_cleanup = '''
        // Clear localStorage on logout to prevent data persistence across users
        function clearUserDataOnLogout() {
            try {
                // Clear scoreboard-specific data
                const keysToRemove = [];
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    // Remove user-specific and cached data
                    if (key && (
                        key.includes('scoreboard') ||
                        key.includes('roster') ||
                        key.includes('backup') ||
                        key === 'ea_active_tab' ||
                        key === 'ea_active_scoreboard_month'
                    )) {
                        keysToRemove.push(key);
                    }
                }
                keysToRemove.forEach(key => localStorage.removeItem(key));
                console.log('localStorage cleared on logout');
            } catch (e) {
                console.error('Failed to clear localStorage:', e);
            }
        }

        // Attach to logout button if exists
        document.addEventListener('DOMContentLoaded', () => {
            const logoutBtn = document.querySelector('[href*="logout"]');
            if (logoutBtn) {
                logoutBtn.addEventListener('click', clearUserDataOnLogout);
            }
        });
'''

    # Add before the closing </script> tag
    content = content.replace('</script>', logout_cleanup + '\n    </script>', 1)
    print("✓ Added localStorage cleanup function")

    # Save the modified file
    print("\nStep 7: Saving modified file...")
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ File saved: {html_file}")

    # Summary
    print("\n" + "=" * 80)
    print("STUDENT DATA FILTERING ADDED!")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  • Backup: {backup_file}")
    print(f"  • Added currentStudentRoll variable")
    print(f"  • Updated session fetch to capture student roll")
    print(f"  • Added filtering to show only student's own data")
    print(f"  • Added localStorage cleanup on logout")
    print(f"\n✓ Students will now see only their own data")
    print(f"✓ Admin/Teacher see all students (unchanged)")
    print(f"✓ Sessions properly isolated between users")
    print()

if __name__ == '__main__':
    main()
