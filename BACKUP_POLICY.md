# Backup Policy (Operations)

## Scope
This policy protects live app data for:
- `instance/offline_scoreboard_data.json`
- `instance/ea_tutorial.db` (if present)

## Backup Types
1. In-app/manual backups (Tools tab) before major data operations.
2. Daily ops backup via script:
   - `daily_backup.ps1`
3. Restore points before risky fixes/merges/imports.

## Daily Command
Run from project root:

```powershell
powershell -ExecutionPolicy Bypass -File .\daily_backup.ps1 -ProjectRoot "." -KeepDays 30

## Auto-Schedule (Windows Task Scheduler)
Preferred installer:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_daily_backup_task.ps1 -TaskName "ProjectEA_DailyBackup_2215" -ProjectRoot "C:\Users\sujit\OneDrive\Desktop\Project EA" -Time24h "22:15" -KeepDays 30
```

Optional XML import:

```powershell
schtasks /Create /TN "ProjectEA_DailyBackup_2215" /XML "C:\Users\sujit\OneDrive\Desktop\Project EA\backup_task_daily_2215.xml" /F
```

Run once now (test):

```powershell
schtasks /Run /TN "ProjectEA_DailyBackup_2215"
```

Verify:

```powershell
Get-ScheduledTask -TaskName "ProjectEA_DailyBackup_2215"
Get-ChildItem .\instance\ops_daily_backups\json | Sort LastWriteTime -Desc | Select -First 3
```

## Off-Machine (OneDrive/Cloud) Sync
Create scheduled offsite sync task:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_offsite_sync_task.ps1 -TaskName "ProjectEA_OffsiteSync_2230" -ProjectRoot "C:\Users\sujit\OneDrive\Desktop\Project EA" -OffsiteRoot "C:\Users\sujit\OneDrive\ProjectEA_Offsite_Backups" -Time24h "22:30" -KeepDays 60
```

Run once now:

```powershell
schtasks /Run /TN "ProjectEA_OffsiteSync_2230"
```

Verify:

```powershell
Get-ScheduledTask -TaskName "ProjectEA_OffsiteSync_2230"
Get-ChildItem "C:\Users\sujit\OneDrive\ProjectEA_Offsite_Backups\json" | Sort LastWriteTime -Desc | Select -First 3
```
```

## Output Location
- `instance/ops_daily_backups/json/`
- `instance/ops_daily_backups/db/`

## Retention
- Default: `30` days (`-KeepDays 30`)
- Adjust as needed by policy.

## Mandatory Moments for Extra Backup
1. Before Excel import / historical merge.
2. Before restore/rollback.
3. Before deployment/restart for production.
4. End of each day.

## Restore Guidance
1. Create a pre-restore snapshot of current live file.
2. Restore only minimum required sections when possible.
3. Prefer targeted merge over full rollback.
4. Verify after restore:
   - Scoreboard month tally
   - Leadership/Post Holder/Party data
   - Fees/attendance integrity

## Operational Discipline
1. Never overwrite all data blindly when only one module is broken.
2. Always record source backup filename used for restore.
3. Keep one off-machine copy (cloud/USB) for disaster recovery.
