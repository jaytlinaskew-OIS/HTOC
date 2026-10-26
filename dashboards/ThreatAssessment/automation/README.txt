STATUS: Scheduled task disabled at user request. Automatic background updates are not active. Use Power BI Refresh to load the newest daily file.

I&W DASHBOARD AUTOMATIC DATA UPDATES

The dashboard file is Dashobard.pbix in the ThreatAssessI_W source folder.
Windows task: HTOC I&W Dashboard - Update Data
Checks: every minute, and at this user's logon. Runs only while this computer is on, awake, signed in, and able to access the network folder.

The updater chooses the latest strictly named ThreatAssessI_W_YYYYMMDD.xlsx file by its filename date. It imports only I&W_No and excludes any row explicitly marked as reported. Missing or blank reporting status is inferred from the I&W_No sheet. Backups and ORIG files are ignored. A newest file with no matching records clears the data; it never falls back to an older nonempty file. A changing or unreadable file is retried on the next check.

Only the saved PBIX's cached data is updated. The report layout is preserved. An already-open Power BI screen does not automatically reload a changed PBIX file. Configure the display refresh separately when the display location is selected. For a published Power BI report, configure gateway access and automatic semantic-model refresh; this local file updater does not publish or refresh a cloud report.

The last good PBIX is kept as Dashobard.auto-refresh-backup.pbix. A failed refresh keeps the current file and records the error in the local log.

Updater state and rotating logs:
C:\Users\jaskew\AppData\Local\HTOC\IWDashboard

To stop: open Windows Task Scheduler, locate HTOC I&W Dashboard - Update Data, and disable it. Re-enable to resume. No passwords are stored by the updater.

Tests passed with October 19 (two records), October 20 (zero records), October 21 (one record), and an unchanged-file check. The visible page has no filter controls and includes simple definitions for each displayed metric.
