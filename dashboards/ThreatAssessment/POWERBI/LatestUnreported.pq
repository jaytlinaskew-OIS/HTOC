let
    SourceFolder = "\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true],
    LatestFile = let
    Files = Folder.Contents(SourceFolder),
    Candidates = Table.SelectRows(Files, each
        let n = [Name], d = Text.Middle(n, 16, 8)
        in Text.Length(n) = 29 and Text.Start(n, 16) = "ThreatAssessI_W_"
            and Text.End(n, 5) = ".xlsx" and Text.Select(d, {"0".."9"}) = d
            and [Attributes]?[Hidden]? <> true),
    Dated = Table.AddColumn(Candidates, "Snapshot Date", each
        let d = Text.Middle([Name],16,8)
        in try #date(Number.FromText(Text.Start(d,4)),Number.FromText(Text.Middle(d,4,2)),Number.FromText(Text.End(d,2))) otherwise null, type date),
    Valid = Table.SelectRows(Dated, each [Snapshot Date] <> null),
    Sorted = Table.Sort(Valid, {{"Snapshot Date", Order.Descending}, {"Name", Order.Descending}}),
    Latest = if Table.IsEmpty(Sorted) then error "No valid ThreatAssessI_W_YYYYMMDD.xlsx snapshot found in SourceFolder." else Sorted{0}
in Latest,
    UnreportedSnapshot = let
    Workbook = Excel.Workbook(LatestFile[Content], null, true),
    NoSheets = Table.SelectRows(Workbook, each [Kind] = "Sheet" and Text.Lower(Text.Trim([Item])) = "i&w_no"),
    Raw = if Table.RowCount(NoSheets) <> 1 then error "Latest workbook must contain exactly one I&W_No worksheet. No fallback to a prior snapshot or reported worksheet is allowed." else NoSheets{0}[Data],
    Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true]),
    Checked = if not Table.HasColumns(Headers, {"Indicator", "PRISM Score", "Severity"}) then error "I&W_No is missing required Indicator, PRISM Score, or Severity headers." else Headers,
    WithStatus = if Table.HasColumns(Checked, "Reported I&W?") then Checked else Table.AddColumn(Checked, "Reported I&W?", each "No", type text),
    Unreported = Table.SelectRows(WithStatus, each
        let v = Record.Field(_, "Reported I&W?"), s = if v = null then "" else Text.Lower(Text.Trim(Text.From(v)))
        in List.Contains({"", "no", "n", "false", "0", "unreported", "not reported"}, s)),
    Nonblank = Table.SelectRows(Unreported, each [Indicator] <> null and Text.Trim(Text.From([Indicator])) <> ""),
    Selected = Table.SelectColumns(Nonblank, ["Indicator", "Host IP", "Last Observed", "Indicator Type", "VirusTotal Malicious Score", "GTI Verdict", "GTI Threat Score", "GTI Severity", "Mandiant", "Observation Yearly Count", "ThreatConnect Rating", "Observation Penalty Multiplier", "Botnet Flag", "False Positives", "Partners", "incidents/events", "Threat Actor", "Tagging Boost", "Tagging Boost Reason", "CAL Score", "ThreatConnect Score", "PRISM Score", "Severity", "Explanation", "Associated Groups", "Tags", "OpDiv"], MissingField.UseNull),
    Numbers = Table.TransformColumns(Selected, {{"VirusTotal Malicious Score", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"GTI Threat Score", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"Mandiant", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"Observation Yearly Count", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"ThreatConnect Rating", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"Observation Penalty Multiplier", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"Botnet Flag", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"False Positives", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"Tagging Boost", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"CAL Score", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"ThreatConnect Score", each if _ = null then null else Number.From(_, "en-US"), type number},
        {"PRISM Score", each if _ = null then null else Number.From(_, "en-US"), type number}}),
    Texts = Table.TransformColumns(Numbers, {{"Indicator", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Host IP", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Indicator Type", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"GTI Verdict", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"GTI Severity", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Partners", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"incidents/events", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Threat Actor", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Tagging Boost Reason", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Severity", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Explanation", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Associated Groups", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"Tags", each if _ = null then null else Text.From(_, "en-US"), type text},
        {"OpDiv", each if _ = null then null else Text.From(_, "en-US"), type text}}),
    Dates = Table.TransformColumns(Texts, {{"Last Observed", each if _ = null or _ = "" then null else DateTime.From(_, "en-US"), type datetime}}),
    Severity = Table.TransformColumns(Dates, {{"Severity", each if _ = null or Text.Trim(_) = "" then "Unknown" else Text.Proper(Text.Trim(_)), type text}}),
    Rank = Table.AddColumn(Severity, "Severity Rank", each if [Severity] = "Critical" then 1 else if [Severity] = "High" then 2 else if [Severity] = "Medium" then 3 else if [Severity] = "Low" then 4 else if [Severity] = "Informational" then 5 else 6, Int64.Type),
    Status = Table.AddColumn(Rank, "Reported I&W?", each "No", type text),
    Snapshot = Table.AddColumn(Status, "Snapshot Date", each LatestFile[Snapshot Date], type date),
    File = Table.AddColumn(Snapshot, "Source File", each LatestFile[Name], type text)
in File
in
    UnreportedSnapshot
