let
    SourceFolder = "\\cscso1fsappv01\data\HTOC\Data_Analytics\Data\Threat Assessment Scores\ThreatAssessI_W",
    Today = Date.From(DateTime.LocalNow()),
    WindowStart = Date.AddDays(Today, -4),
    Files = Folder.Contents(SourceFolder),
    Candidates = Table.SelectRows(Files, each let n = [Name], d = Text.Middle(n,16,8) in Text.Length(n) = 29 and Text.Start(n,16) = "ThreatAssessI_W_" and Text.End(n,5) = ".xlsx" and Text.Select(d,{"0".."9"}) = d and [Attributes]?[Hidden]? <> true),
    Dated = Table.AddColumn(Candidates, "File Date", each let d = Text.Middle([Name],16,8) in try #date(Number.FromText(Text.Start(d,4)),Number.FromText(Text.Middle(d,4,2)),Number.FromText(Text.End(d,2))) otherwise null, type date),
    Recent = Table.SelectRows(Dated, each [File Date] <> null and [File Date] >= WindowStart and [File Date] <= Today),
    Extracted = Table.AddColumn(Table.Sort(Recent,{{"File Date",Order.Descending}}), "Reported Indicators", each let
        Book = Excel.Workbook([Content],null,true),
        Sheets = Table.SelectRows(Book, each [Kind] = "Sheet" and Text.Lower(Text.Trim([Item])) = "i&w_yes"),
        Empty = #table(type table [Indicator = text, Explanation = text, Tags = text], {}),
        Promoted = if Table.IsEmpty(Sheets) then Empty else Table.PromoteHeaders(Sheets{0}[Data],[PromoteAllScalars=true]),
        Selected = if not Table.HasColumns(Promoted,"Indicator") then error "An I&W_Yes sheet is missing the Indicator header." else Table.SelectColumns(Promoted,{"Indicator","Explanation","Tags"},MissingField.UseNull),
        Trimmed = Table.TransformColumns(Selected,{{"Indicator", each if _ = null then null else Text.Trim(Text.From(_)), type text}}),
        Clean = Table.SelectRows(Trimmed, each [Indicator] <> null and [Indicator] <> "")
        in Clean),
    Combined = if Table.IsEmpty(Extracted) then #table(type table [Indicator = text, Explanation = text, Tags = text], {}) else Table.Combine(Extracted[Reported Indicators]),
    Unique = Table.Distinct(Table.Buffer(Combined),{"Indicator"}),
    Sorted = Table.Sort(Unique,{{"Indicator",Order.Ascending}})
in Sorted