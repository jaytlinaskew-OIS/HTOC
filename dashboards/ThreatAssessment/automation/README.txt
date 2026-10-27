HTOC I&W DASHBOARD - AUTOMATIC DESKTOP DISPLAY

Use "Open Live I&W Dashboard" in the Dashboard folder to start or resume the live display. Use "Pause Live I&W Dashboard" to pause the scheduled checks and close only the managed display window.

The editable original remains:
\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W\Dashboard\Dashobard.pbix

The live display is a separate, automation-owned PBIX on this computer. Make layout, theme, measure, and hover changes in the original and save them there. The updater detects saved changes and applies them to the display on the next successful update. Changes made directly in the live copy are temporary and may be discarded when it reloads.

HOW IT UPDATES
Windows task: HTOC I&W Dashboard - Update Data
Frequency: every minute and at this user's logon.
Runs while this computer is awake, the user is signed in, and the network source is accessible. No stored password or cloud publishing is used. After a new report is detected, model validation and reopening Power BI take additional time. The live window may close and reopen briefly; its temporary filter selections reset.

Sources:
\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W
Only exact filenames ThreatAssessI_W_YYYYMMDD.xlsx are considered. The newest filename date up to today determines the current snapshot. Backup/ORIG/temporary files, subfolders, invalid dates, and future-dated files are ignored.

- Current Indicators: I&W_No from the latest report. Rows explicitly marked reported are excluded. Blank reporting status is inferred from the sheet. An empty latest sheet means zero current Indicators; an older nonempty report is never substituted.
- Partner blocks: unique Indicator/partner links rebuilt from the Partners field of the current records.
- Reported list: unique Indicators from I&W_Yes sheets in reports dated today and the four preceding calendar days. The newest row supplies its assessment notes/tags when an Indicator occurs in several reports. A missing I&W_Yes sheet is treated as empty.
- Data Date: filename date of the current snapshot. Last updated: time the data was successfully loaded, not the time the file was checked.

GUARDS
The updater checks file stability, required columns, unique current Indicators, numeric values, and the 0-1000 PRISM range. It preserves the original report layout byte-for-byte, all DAX measures, and the partner relationship. Every replacement is tested with native Power BI Desktop and DAX queries for counts, scores, and partner filtering. Missing embedded model files or unreadable/changing workbooks cause a failed update with the last good display retained. Overlapping updater runs are prevented. The original is never overwritten by this automation.

Managed display backups are kept in its local Live\Deprecated directory. The existing scheduler configuration and runner were backed up before deployment.

LOCAL FILES
This desktop app redirects AppData. The scheduler uses the physical Windows path so it can access the same files:
C:\Users\jaskew\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HTOC\IWDashboard

managed-config.json          Source/original/display locations
managed-state.json           Last successful sources, counts, and native validation
managed-status.json          Latest check result or failure
managed-refresh.log          Rotating detailed update/error log
managed-task-output.log      Scheduled runner output
Live\HTOC I&W Dashboard.pbix  Automatically refreshed display copy

EDITING AND MAINTENANCE
Open/Pause shortcuts manage the existing Windows task; they do not modify the original dashboard. The updater closes only the process it launched and recorded, never other Power BI windows. Manually opening extra copies is unnecessary. Use the original for editing and the managed window for display.

If Python, Power BI Desktop, this app, or the computer changes, verify the runner/runtime paths and rerun install_managed_refresh.ps1 from the automation source folder. This local implementation depends on the currently tested Power BI Desktop version (2.139). Run the native validation tests after upgrading it. Power BI Desktop does not provide an unattended Import refresh service; this setup updates a separate PBIX and reloads its owned display window. It does not publish or update a Power BI Service report.

SIDE PANELS AND ASSESSMENT NOTES
Two equal-height rounded rails share the left side: Reported I&W Last 5 Days above Partners. Only one panel opens at a time: opening one closes the other. Each expanded panel is 200 pixels wide and spans the 512-pixel content height below the header. In Power BI Desktop editing mode use Ctrl+click on the chevron. The three drawer arrangements keep the table, assessment notes, and PRISM chart clear of the drawers. Partner selections remain active when its drawer is collapsed.

Indicator Assessment Notes shows one assessment at a time. Without an Indicator selection it uses the highest PRISM score in the current partner filter; Indicator text in ascending order breaks score ties. Clicking an Indicator in the details table replaces the default assessment with that Indicator's source Explanation. Native Power BI chart/table selections follow its normal interaction rules. An automated reload restores the initial collapsed view and current top Indicator.

EMPTY CURRENT SNAPSHOT
When the loaded report contains zero unreported Indicators, the Indicator Details status reads "No I&W Indicators to report today". The usual count and partner context return when Indicators are available. A zero-result filter on a populated report does not incorrectly trigger this report-wide message.
