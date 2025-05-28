import os
import pandas as pd
from datetime import datetime
from extract_pptx import extract_text_and_tables_from_pptx
from excel_writer import fill_excel_sheet

def main():
    # Automatically select the most recent folder in the parent directory with format YYYYMMDD
    parent_dir = os.path.dirname(r'Z:\HTOC\Data_Analytics\I_W\20231121')
    date_folders = [f for f in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, f)) and f.isdigit() and len(f) == 8]
    
    if date_folders:
        pptx_dir = os.path.join(parent_dir, sorted(date_folders)[-1])
    else:
        pptx_dir = r'Z:\HTOC\Data_Analytics\I_W\20231121'
    
    pptx_files = [f for f in os.listdir(pptx_dir) if f.lower().endswith('.pptx')]
    
    keywords = ['CDC', 'NIH', 'FDA', 'HRSA', 'VA', 'CMS', 'IHS', 'DHA']
    filtered_pptx_files = [f for f in pptx_files if any(k in f for k in keywords)]
    
    htoc_ip_pairs = []
    
    for pptx_file in filtered_pptx_files:
        slides_content, tables, ip_like_data, htoc_like_data = extract_text_and_tables_from_pptx(os.path.join(pptx_dir, pptx_file))
        
        # Assign each HTOC-like value with all associated IP-like values
        current_htoc = None
        for table in tables:
            for row in table:
                htoc_matches = [cell for cell in row if 'HTOC-' in cell]
                if htoc_matches:
                    current_htoc = htoc_matches[0]
                ip_matches = [cell for cell in row if "[" in cell and "]" in cell and "." in cell]
                if current_htoc and ip_matches:
                    for ip in ip_matches:
                        htoc_ip_pairs.append({
                            'HTOC_Like_Data': current_htoc,
                            'IP_Like_Data': ip,
                            'Keyword': next((keyword for keyword in keywords if keyword in pptx_file), None)
                        })
    
    # Extract the date from the pptx_file's folder
    folder_date_str = os.path.basename(pptx_dir)
    folder_date = datetime.strptime(folder_date_str, "%Y%m%d")
    date_str = folder_date.strftime("%m/%d/%Y")
    
    # Write to Excel
    fill_excel_sheet(r'Z:\HTOC\Data_Analytics\I_W\MasterProcessing\Master.xlsx', 'Master Sheet', htoc_ip_pairs, date_str)

if __name__ == "__main__":
    main()