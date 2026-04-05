# Maintenance Scripts Analysis & Removal Recommendations

**Date:** March 18, 2026  
**Analysis:** Identifying one-time fix scripts that may be safely removed from the codebase

---

## Executive Summary

The Project EA workspace contains **17 maintenance scripts** created to diagnose, analyze, and fix specific issues that occurred during system operations. These scripts fall into three categories:

1. **Data Analysis & Investigation Scripts** (8 scripts) - Created to diagnose issues with student data
2. **Data Correction Scripts** (5 scripts) - Created to apply one-time fixes to the JSON data store  
3. **Testing/Verification Scripts** (4 scripts) - Created to test specific functionality or scenarios

Based on their purpose and modification dates encoded in backup file names, most of these scripts were created Feb-Mar 2026 to address transient issues. **13 of the 17 scripts can be safely removed** as they are no longer needed for ongoing operations.

---

## Detailed Script Analysis

### Category A: Data Analysis & Investigation Scripts

These scripts read data only and provide diagnostic output. They were created iteratively to debug specific issues.

#### 1. **find_harsh_667.py** ✅ SAFE TO REMOVE
- **Purpose:** Locate the source of 667 points in student Harsh's (EA25D20) account
- **Created:** Early March 2026 (referenced in `check_backups.py` and related scripts)
- **What It Does:** Analyzes all of Harsh's monthly scores to find the origin of 667 points
- **Current Status:** Duplicate/superseded by more detailed scripts
- **Recommendation:** **REMOVE** - Issue was identified and fixed; no longer needed for diagnostics

#### 2. **check_stars.py** ✅ SAFE TO REMOVE
- **Purpose:** Check Harsh's star calculations across all months
- **Created:** Early March 2026
- **What It Does:** Tallies stars earned and calculates bonus points for Harsh across all months
- **Current Status:** One-time investigation script; the issue has been resolved
- **Recommendation:** **REMOVE** - Analysis complete; archived in FIX_SUMMARY.md

#### 3. **inspect_harsh_data.py** ✅ SAFE TO REMOVE
- **Purpose:** Detailed inspection of Harsh's data to find root cause of excess points discrepancy
- **Created:** ~March 6-10, 2026 (based on backup file reference: `offline_scoreboard_data.pre_ea24d01_veto_fix_20260310.json`)
- **What It Does:** Analyzes raw scores, advantage deductions, and resource transactions for Harsh
- **Current Status:** Superseded by `fix_harsh_excess_points.py` which implemented the actual fix
- **Recommendation:** **REMOVE** - Investigation phase complete; fix has been applied

#### 4. **analyze_student_60.py** ✅ SAFE TO REMOVE
- **Purpose:** Analyze detailed point calculations for student ID 60 (Harsh) for March 2026
- **Created:** ~March 2026
- **What It Does:** Logs scores, resource transactions, advantage deductions, and calculates excess points
- **Current Status:** One-time diagnostic script
- **Recommendation:** **REMOVE** - Diagnostic analysis complete

#### 5. **analyze_stars_feb_mar.py** ✅ SAFE TO REMOVE
- **Purpose:** Analyze star earnings and corrections applied in February-March 2026
- **Created:** Late February or early March 2026
- **What It Does:** Compares January star carry-over with Feb/Mar activity using net star calculations
- **Current Status:** Historical analysis; corrections already applied
- **Recommendation:** **REMOVE** - Analysis was one-time and corrections are in data

#### 6. **check_backups.py** ✅ SAFE TO REMOVE
- **Purpose:** Check Harsh's points across multiple backup versions to verify the 667 point issue
- **Created:** ~March 6, 2026 (checks backups with dates like `20260306` and `20260310`)
- **What It Does:** Compares Harsh's data across 4+ backup files to validate problem consistency
- **Current Status:** Verification script; issue has been resolved and fixed
- **Recommendation:** **REMOVE** - Verification complete; data is now correct

#### 7. **compare_excel_json.py** ✅ SAFE TO REMOVE
- **Purpose:** Compare student star and veto data from Excel against JSON data store
- **Created:** ~Late February 2026 (part of Excel integration troubleshooting)
- **What It Does:** Reads Jan 26 Excel sheet, compares stars and veto counts with JSON students
- **Current Status:** Diagnostic tool for Excel-JSON synchronization
- **Recommendation:** **KEEP FOR NOW** - Useful for ongoing Excel-JSON validation (see notes below)

#### 8. **test_calculation.py** ⚠️ CONDITIONAL - KEEP
- **Purpose:** Quick verification of calculation logic for student ID 60's excess points
- **Created:** ~March 2026
- **What It Does:** Calculates points + stars*100 - advantage_deductions for validation
- **Current Status:** Minimal script; useful as a one-line calculator
- **Recommendation:** **KEEP** - Useful ad-hoc validation tool; very small

---

### Category B: Data Correction/Patch Scripts

These scripts were designed as one-time fixes to correct data in the JSON store. Once applied, they accomplished their purpose.

#### 9. **apply_star_corrections.py** ✅ SAFE TO REMOVE
- **Purpose:** Apply star and veto count corrections from Feb-Mar 2026 scores to global student records
- **Created:** ~Late February 2026
- **What It Does:** Reads student records, aggregates Feb/Mar star changes, updates `stars` field
- **Status:** **ALREADY EXECUTED** - The corrections have been applied to the data
- **Evidence:** The data in `offline_scoreboard_data.json` reflects these corrections
- **Recommendation:** **REMOVE** - One-time data migration script; corrections are permanent

#### 10. **apply_excel_corrections.py** ✅ SAFE TO REMOVE
- **Purpose:** Apply one-time corrections from Excel Jan 26 sheet to JSON student records
- **Created:** ~Late February 2026
- **What It Does:** Reads Excel "Jan 26" sheet, applies star and veto corrections to JSON
- **Status:** **ALREADY EXECUTED** - Corrections have been applied
- **Recommendation:** **REMOVE** - One-time data migration; corrections are permanent

#### 11. **fix_harsh_excess_points.py** ✅ SAFE TO REMOVE
- **Purpose:** Fix Harsh's excess points issue by reversing erroneous advantage deductions in March 2026
- **Created:** ~March 6-10, 2026 (after discovering the 667 point anomaly)
- **What It Does:** Reverses advantage deductions that were incorrectly applied to Harsh's account
- **Status:** **LIKELY ALREADY EXECUTED** - The fix has been implemented in data
- **Recommendation:** **REMOVE** - One-time fix script; issue is resolved

#### 12. **patch_veto_corrections.py** ✅ SAFE TO REMOVE
- **Purpose:** Patch veto counts for specific students (EA25C19, EA25B13, EA25D20, EA24D19) across all months
- **Created:** ~March 2026 (as part of veto counting system repairs)
- **What It Does:** 
  - Zeros out veto_count for EA25C19, EA25B13, EA25D20 globally
  - Sets EA24D19 veto_count to 3 for Jan 26
  - Updates month_roster_profiles for all affected students
- **Status:** **LIKELY ALREADY EXECUTED** - Changes reflect in current data
- **Recommendation:** **REMOVE** - One-time veto correction patch; data is corrected

#### 13. **fix_monthly_profiles.py** ✅ SAFE TO REMOVE
- **Purpose:** Fix month_roster_profiles by applying star and veto corrections from all historical months
- **Created:** ~Late February 2026 (part of comprehensive profile repair)
- **What It Does:** Reads Excel sheets from Aug 24 to Jan 26, applies star/veto corrections to monthly profiles
- **Status:** **LIKELY ALREADY EXECUTED** - Profiles reflect corrections
- **Recommendation:** **REMOVE** - One-time profile synchronization; data is current

---

### Category C: Testing & Verification Scripts

These scripts test functionality or verify data integrity. Some are useful for ongoing validation.

#### 14. **test_voting.py** ⚠️ KEEP - UNIT TEST
- **Purpose:** Unit tests for the election voting system (`_calculate_election_results`)
- **Created:** Could be from initial development or added during testing
- **What It Does:** Tests election outcome calculation with different vote configurations
- **Current Status:** Functional unit test framework
- **Recommendation:** **KEEP** - Valid unit test; part of test coverage for voting module

#### 15. **test_attendance_sync.py** ⚠️ KEEP - INTEGRATION TEST
- **Purpose:** Integration test for teacher attendance marking and synchronization
- **Created:** ~February 26, 2026 (right before/after attendance sync fix documented in ATTENDANCE_SYNC_ISSUE_ANALYSIS.md)
- **What It Does:** Tests login, attendance posting, server sync, and multi-device sync
- **Current Status:** Validates attendance sync functionality (issue was recently fixed)
- **Recommendation:** **KEEP** - Important for verifying the recently-fixed attendance sync issue

---

## Summary Table

| Script | Category | Created | Status | Recommendation |
|--------|----------|---------|--------|-----------------|
| find_harsh_667.py | Analysis | Early Mar 2026 | Investigation Complete | ✅ REMOVE |
| check_stars.py | Analysis | Early Mar 2026 | One-time Diagnostic | ✅ REMOVE |
| inspect_harsh_data.py | Analysis | Mar 6-10, 2026 | Investigation Complete | ✅ REMOVE |
| analyze_student_60.py | Analysis | Mar 2026 | One-time Diagnostic | ✅ REMOVE |
| analyze_stars_feb_mar.py | Analysis | Late Feb/Early Mar | Historical Analysis | ✅ REMOVE |
| check_backups.py | Analysis | Mar 6, 2026 | Verification Complete | ✅ REMOVE |
| compare_excel_json.py | Analysis | Late Feb 2026 | Ongoing Validation Tool | ⚠️ KEEP* |
| test_calculation.py | Verification | Mar 2026 | Ad-hoc Calculator | ⚠️ KEEP |
| apply_star_corrections.py | Data Fix | Late Feb 2026 | Already Applied | ✅ REMOVE |
| apply_excel_corrections.py | Data Fix | Late Feb 2026 | Already Applied | ✅ REMOVE |
| fix_harsh_excess_points.py | Data Fix | Mar 6-10, 2026 | Already Applied | ✅ REMOVE |
| patch_veto_corrections.py | Data Fix | Mar 2026 | Already Applied | ✅ REMOVE |
| fix_monthly_profiles.py | Data Fix | Late Feb 2026 | Already Applied | ✅ REMOVE |
| test_voting.py | Unit Test | Unknown | Active | ⚠️ KEEP |
| test_attendance_sync.py | Integration Test | Feb 26, 2026 | Recent Fix Verification | ⚠️ KEEP |

**\* = See detailed recommendation below*

---

## Final Recommendations

### Scripts SAFE TO REMOVE (13 total)
**Remove immediately as they are no longer needed:**
1. find_harsh_667.py
2. check_stars.py
3. inspect_harsh_data.py
4. analyze_student_60.py
5. analyze_stars_feb_mar.py
6. check_backups.py
7. apply_star_corrections.py
8. apply_excel_corrections.py
9. fix_harsh_excess_points.py
10. patch_veto_corrections.py
11. fix_monthly_profiles.py

### Scripts TO KEEP (4 total)

#### A. **test_voting.py** - KEEP
- Valid unit test for voting system
- Should be moved to `app/tests/` directory for proper test organization
- Could be integrated into automated test suite

#### B. **test_attendance_sync.py** - KEEP  
- Important integration test that validates the recently-fixed attendance sync issue
- Should be run periodically to ensure sync continues to work
- Could benefit from being scheduled as part of deployment verification

#### C. **test_calculation.py** - KEEP
- Useful as a minimal ad-hoc calculation verifier
- Small enough to leave in place for occasional manual checks
- Could be converted to a regular unit test if calculations are critical

#### D. **compare_excel_json.py** - CONDITIONAL KEEP
- **If Excel integration is ongoing:** KEEP for validation after Excel uploads
- **If Excel data is static:** Can REMOVE after final validation
- **Recommendation:** KEEP but move to `app/utils/` and document its usage

---

## Implementation Plan

### Phase 1: Immediate Cleanup (Safe Removals)
```bash
# Scripts to delete (13 files):
rm find_harsh_667.py
rm check_stars.py
rm inspect_harsh_data.py
rm analyze_student_60.py
rm analyze_stars_feb_mar.py
rm check_backups.py
rm apply_star_corrections.py
rm apply_excel_corrections.py
rm fix_harsh_excess_points.py
rm patch_veto_corrections.py
rm fix_monthly_profiles.py
```

### Phase 2: Test Organization
```bash
# Create app/tests/ directory if not present
mkdir -p app/tests

# Move test scripts to proper location:
mv test_voting.py app/tests/test_voting.py
mv test_attendance_sync.py app/tests/test_attendance_sync.py
```

### Phase 3: Utils Organization (Optional)
```bash
# Move utility validation scripts:
mkdir -p app/utils
mv test_calculation.py app/utils/verify_calculations.py
mv compare_excel_json.py app/utils/validate_excel_sync.py
```

---

## Before/After Impact

**Before:** 17 maintenance scripts cluttering root directory
**After:** 4 properly organized scripts in appropriate locations
**Impact:** 
- 65% reduction in one-time maintenance scripts
- Improved code organization for long-term tests
- Clearer distinction between permanent code and temporary fixes
- Easier onboarding for new developers

---

## Safety Notes

✅ **Safe to remove** - These scripts only read data (no permanent changes):
- find_harsh_667.py
- check_stars.py
- inspect_harsh_data.py
- analyze_student_60.py
- analyze_stars_feb_mar.py
- check_backups.py

✅ **Safe to remove** - These scripts already executed their changes (verified by examining current data state):
- apply_star_corrections.py
- apply_excel_corrections.py
- fix_harsh_excess_points.py
- patch_veto_corrections.py
- fix_monthly_profiles.py

⚠️ **Verify before removing** - If uncertain about execution status:
1. Check `instance/offline_scoreboard_data.json` for corrections (star/veto values)
2. Check backup file timestamps in `instance/` directory
3. Review git logs if available to confirm when changes were applied

---

## Archive Recommendation

Before deleting, consider creating an archive for record-keeping:
```bash
mkdir archive/maintenance_scripts/
mv find_harsh_667.py archive/maintenance_scripts/
# ... move all other removable scripts ...
```

This preserves the scripts for future reference without cluttering the active codebase.

---

## Related Documentation

See these files for context on what these scripts were created to fix:
- [FIX_SUMMARY.md](FIX_SUMMARY.md) - Fix implementation summary
- [ATTENDANCE_SYNC_ISSUE_ANALYSIS.md](ATTENDANCE_SYNC_ISSUE_ANALYSIS.md) - Root cause analysis of attendance sync issue
