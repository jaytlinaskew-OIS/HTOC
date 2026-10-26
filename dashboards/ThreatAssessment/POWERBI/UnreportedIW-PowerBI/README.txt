UNREPORTED I&W POWER BI DASHBOARD

Open UnreportedIW.pbip in current Power BI Desktop. Keep the project folders together.
In this Desktop installation, enable File > Options and settings > Options > Preview features > Store reports using enhanced metadata format (PBIR), then restart Desktop before opening this project. Enable Power BI Project (PBIP) too if your Desktop version requires it.
Select Refresh. If prompted for the network folder, choose Windows authentication with an account permitted to read it. Credentials are not included in this project.

Scope
The newest strictly named ThreatAssessI_W_YYYYMMDD.xlsx file is chosen by its filename date. ORIG, PreNewFilters, temporary files and differently named backups are excluded. Only the I&W_No worksheet is read. No I&W_Yes records are imported. If Reported I&W? exists, explicitly reported or unknown status values are excluded. Blank or absent status is treated as unreported because the record is on I&W_No. A missing I&W_No sheet or missing required headers causes a visible refresh failure. An empty current sheet stays empty; it never reuses an older nonempty file.

The source Severity and PRISM scores are preserved; no scoring thresholds are invented. High or critical means the source Severity equals High or Critical. Counts are distinct indicator values within the current filters. Average PRISM averages source rows; duplicates are retained for inspection. Category counts can overlap if an indicator has multiple source rows. OpDiv and Partners retain their original comma-separated values. Blank scores remain blank. File and refresh timestamps are local times of the refresh machine.

Refresh
The source parameter SourceFolder uses the UNC equivalent of the supplied Z: drive:
\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W
Every refresh selects the latest dated file again. This is an Import model; files appearing in the folder do not refresh an open report by themselves. In Power BI Desktop, use Home > Refresh. For unattended refresh, publish to Power BI Service and configure an on-premises data gateway with read access to this UNC folder, then set a refresh schedule after the daily export finishes. Service publishing and gateway/schedule configuration have not been performed.
To change the source, use Transform data > Manage parameters > SourceFolder.

Page
One page contains severity/type/indicator filters, snapshot date, four metrics, severity and verdict charts, PRISM scores, the unreported indicator queue, scoring explanations, source context and refresh timestamps. The detail tables scroll horizontally to show additional evidence columns.

This deliverable is a Power BI Project, not a PBIX binary. After opening and refreshing successfully, use Save As to save a PBIX if needed. LatestUnreported.pq provides the query for an existing report.

Validation
See validation.json for source inspection and schema-validation results. File/schema validation does not replace opening and refreshing in Power BI Desktop.

Desktop opening check: the installed app identified this project as PBIR and requested the preview setting above. Live refresh and visual rendering remain unverified until that setting is enabled.
