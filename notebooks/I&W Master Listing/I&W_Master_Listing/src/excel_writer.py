def fill_excel_sheet(file_path, sheet_name, htoc_ip_pairs, date_str):
    import pandas as pd
    from openpyxl import load_workbook

    columns = [
        "Partner", "I_W Description", "I_W#", "Indicator Disposition Code",
        "Indicator Disposition Code Description", "Secondary Indicator Disposition Code",
        "Secondary Indicator Disposition Code Description", "Tertiary Indicator Disposition Code",
        "Tertiary Indicator Disposition Code Description", "Comment", "Bi-Weekly Date",
        "Technique", "Malware", "Threat Actor", "Aliases", "Vulnerability", "Actor Tag",
        "Sector", "Real Organization", "Threat Actor Country", "I&W Serial", "Affected Partners"
    ]
    
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except FileNotFoundError:
        df = pd.DataFrame(columns=columns)
    
    if df.empty:
        df = pd.DataFrame(columns=columns)
    else:
        missing_cols = [col for col in columns if col not in df.columns]
        for col in missing_cols:
            df[col] = ""
        df = df[columns]

    added = set()
    for pair in htoc_ip_pairs:
        ip_htoc = pair['HTOC_Like_Data']
        ip = pair['IP_Like_Data']
        keyword_found = pair['Keyword']
        unique_key = (ip_htoc, ip, keyword_found)
        if unique_key in added:
            continue
        added.add(unique_key)
        test_input = [
            keyword_found,
            ip_htoc,
            ip,
            "",
            "",
            "", "", "", "", "", date_str, "",
            "", "", "", "", "", "", "", "", "", ""
        ]
        new_row = dict(zip(columns, test_input))
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    df.drop_duplicates(subset=["Partner", "I_W Description", "I_W#"], inplace=True, ignore_index=True)

    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)

    wb = load_workbook(file_path)
    ws = wb[sheet_name]
    for col in ws.columns:
        max_length = 0
        col_letter = col[0].column_letter
        for cell in col:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = (max_length + 2)
        ws.column_dimensions[col_letter].width = adjusted_width
    wb.save(file_path)
    print("Data saved to Excel with auto-spaced columns.")