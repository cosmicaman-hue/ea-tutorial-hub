# Roll Number Upgrade - Undo & Redo Guide

## ✅ Protection Applied

**Roll propagation logic has been fixed!** Frozen/hardened months (like Feb 2026) will now be protected from roll number upgradations.

---

## 📋 Step-by-Step Process

### Phase 1: Undo Current Roll Changes

#### Step 1: Identify Students to Revert

Students whose rolls were changed for upgradation:
- **Ayush:** Current roll `EA24A01` → Revert to original (if changed)
- **Tanu:** Need to identify current and original roll
- **Others:** Any other students upgraded

#### Step 2: Revert Roll Numbers

**Option A: Manual Revert (Recommended)**
1. Open the application
2. Go to **Student Management** tab
3. For each student:
   - Search for the student
   - Click Edit
   - Change roll number back to original
   - Save

**Option B: Bulk Revert via Script**

I can create a Python script if you provide:
- List of students to revert
- Their current rolls
- Their original rolls

#### Step 3: Verify Feb 2026 After Undo

After reverting:
1. Hard refresh browser (Ctrl+Shift+R)
2. Navigate to Feb 2026 scoreboard
3. **Expected Results:**
   - All students show with their original roll numbers
   - Rehmetun appears at top (not Ayush)
   - AWF deduction applied correctly to Ayush
   - All scores display correctly

---

### Phase 2: Wait for April 2026

**Why Wait?**
- Current month is March 2026
- Roll upgradations should only affect **current month onwards**
- If you upgrade in March, it affects March data
- Better to wait until April 2026 starts

**What Happens in April:**
- April 2026 becomes the current month
- Upgradations will affect April onwards
- March 2026 and earlier remain frozen with old rolls

---

### Phase 3: Redo Upgradations Properly (April 2026)

#### Step 1: Ensure Historical Months are Hardened

Before upgrading, verify these months are frozen:
- Feb 2026 ✓ (already hardened)
- Mar 2026 (should be hardened before April)

**To harden Mar 2026:**
```python
# Run this script in late March or early April
python harden_march_2026.py
```

#### Step 2: Perform Roll Upgradations

**In April 2026:**
1. Open application
2. Go to Student Management
3. For each student to upgrade:
   - Search for student
   - Click Edit
   - Change roll number to new value
   - **Important:** System will now skip frozen months automatically
   - Save

**Example for Ayush:**
- Old roll: `EA24A01`
- New roll: `EA24B16` (or whatever the upgrade is)
- Effective: April 2026 onwards only
- Feb 2026 & Mar 2026: Keep `EA24A01`

#### Step 3: Verify After Upgrade

After upgrading in April:
1. Check **Feb 2026:** Should still show old roll `EA24A01`
2. Check **Mar 2026:** Should still show old roll `EA24A01`
3. Check **Apr 2026:** Should show new roll `EA24B16`
4. Verify scoreboard ordering is correct in all months

---

## 🔧 Technical Details

### What Changed in the Code

**Before (Broken):**
```javascript
const shouldSkip = effectiveMonth && monthKey < effectiveMonth && !isHistoricalMonth;
// This NEVER skipped historical months!
```

**After (Fixed):**
```javascript
const isFrozenMonth = monthFrozen && monthFrozen.hardened === true;
const shouldSkip = (effectiveMonth && monthKey < effectiveMonth) || isFrozenMonth;
// Now ALWAYS skips frozen months for upgradations
```

### Distinction: Upgradation vs Technical Correction

**Upgradation (Class Promotion):**
- Uses `effectiveMonth` parameter
- Skips all months before effectiveMonth
- Skips all frozen/hardened months
- **Use case:** Annual promotions, section changes

**Technical Correction (Data Error Fix):**
- No `effectiveMonth` parameter
- Updates all non-frozen months
- Still respects frozen/hardened months
- **Use case:** Fixing typos, correcting wrong roll numbers

---

## 📊 Current Status

### Feb 2026 Status
- **Data:** 473 scores restored ✓
- **Profiles:** 45 students ✓
- **Frozen:** Yes, hardened ✓
- **Display:** Working (after fix) ✓
- **Issue:** Ayush on top instead of Rehmetun (due to AWF or roll change)

### Protection Status
- **Roll propagation:** Fixed ✓
- **Frozen month check:** Added ✓
- **canMutateMonthSnapshot:** Enhanced ✓

---

## 🎯 Recommended Timeline

### Today (Mar 29, 2026)
1. ✅ Apply roll propagation fix (DONE)
2. ⏳ Undo Ayush and Tanu roll changes
3. ⏳ Verify Feb 2026 displays correctly

### End of March 2026
1. Harden Mar 2026 month
2. Verify all historical months are protected

### April 1-5, 2026
1. Redo roll upgradations properly
2. Verify upgradations only affect April onwards
3. Confirm Feb & Mar remain unchanged

---

## 🔄 Rollback Plan

If issues occur after undoing:

**Restore from backup:**
```powershell
# Restore data file
Copy-Item "instance\offline_scoreboard_data.pre_feb2026_restore_20260329_185911.json" "instance\offline_scoreboard_data.json" -Force

# Restore HTML file
Copy-Item "app\static\offline_scoreboard.html.backup_roll_propagation_fix_20260329_193252" "app\static\offline_scoreboard.html" -Force
```

---

## 📝 Next Steps

1. **Identify all students** whose rolls were changed for upgradation
2. **Provide the list** with current and original rolls
3. **I'll create a revert script** to undo all changes at once
4. **Verify Feb 2026** displays correctly after undo
5. **Wait for April 2026** to redo upgradations properly

---

## ❓ Questions to Answer

1. **Which students had roll changes?**
   - Ayush: `EA24A01` → `?` (what was the new roll?)
   - Tanu: `?` → `?`
   - Others: `?`

2. **What are their original rolls?**
   - Need this to revert correctly

3. **When do you want to redo upgradations?**
   - Recommended: April 2026
   - Alternative: Can do in March if urgent, but affects March data

---

**Ready to proceed with the undo? Please provide the list of students and their roll numbers.**
