import os
import pandas as pd
from datetime import datetime
from docx import Document

# File paths
TEMPLATE_PATH = r"z:\\HTOC\\HTOC Reports\\I&W Reports\\5. I&W Staging\\I&W Report Template.docx"
#OUTPUT_DIR = r"z:\\HTOC\\HTOC Reports\\I&W Reports\\5. I&W Staging\\Generated Reports"
OUTPUT_DIR = r"C:\Users\jaskew\Documents\project_repository\notebooks\I&W Reporting\Generated_reports"

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def consolidate_sources(vt_df, otx_df):
    """ Consolidate links from both DataFrames for each search term. """
    # Collect links from VirusTotal
    vt_links = vt_df.groupby('search_term')['link'].apply(lambda x: ', '.join(x.dropna())).reset_index()
    vt_links.columns = ['search_term', 'vt_links']

    # Collect links from OTX
    otx_links = otx_df.groupby('search_term')['link'].apply(lambda x: ', '.join(x.dropna())).reset_index()
    otx_links.columns = ['search_term', 'otx_links']

    # Merge the two link sets
    consolidated = pd.merge(vt_links, otx_links, on='search_term', how='outer')

    # Combine the links, handling NaN values
    consolidated['sources'] = consolidated[['vt_links', 'otx_links']].fillna('').apply(
        lambda x: ', '.join(filter(None, x)), axis=1
    )

    return consolidated[['search_term', 'sources']]

def extract_date(timestamp):
    """ Extract only the date from the timestamp. """
    if pd.isna(timestamp) or timestamp == 'N/A':
        return 'N/A'
    
    # Handle datetime object or string
    try:
        # Attempt to parse as a datetime object
        if isinstance(timestamp, str):
            timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
        return timestamp.strftime("%Y-%m-%d")
    except Exception:
        return 'N/A'

def populate_table(table, data):
    """ Populate a Word table with the given data. """
    # Iterate over data and populate rows
    for index, row in data.iterrows():
        # Insert a new row before the last row (template row)
        new_row = table.add_row().cells
        new_row[0].text = str(row.get('search_term', 'N/A'))
        new_row[1].text = str(row.get('base_type', 'N/A'))
        new_row[2].text = extract_date(row.get('timestamp_vt', 'N/A'))
        new_row[3].text = str(row.get('observed_by_otx', 'N/A'))
        new_row[4].text = str(row.get('notes', ''))

def fill_word_template(template_path, output_path, df):
    """ Fill the template with data and place sources outside the table. """
    if not os.path.exists(template_path):
        print(f"Template not found: {template_path}")
        return

    try:
        doc = Document(template_path)

        # Populate the table
        table = None
        for tbl in doc.tables:
            if "Indicators/Identifiers" in tbl.rows[0].cells[0].text:
                table = tbl
                break

        if table:
            populate_table(table, df)

        # Find and replace `{{sources}}` placeholder outside the table
        for para in doc.paragraphs:
            if "{{sources}}" in para.text:
                all_sources = ', '.join(df['sources'].dropna().unique())
                para.text = para.text.replace("{{sources}}", all_sources)

        # Save the modified document
        doc.save(output_path)
        print(f"Saved report: {output_path}")

    except Exception as e:
        print(f"Error while generating report: {e}")

def generate_report(vt_df, otx_df):
    """ Main function to handle report generation. """
    # Combine the DataFrames and drop duplicates
    combined_df = pd.merge(vt_df, otx_df, on='search_term', how='outer', suffixes=('_vt', '_otx'))
    
    # Consolidate sources
    sources_df = consolidate_sources(vt_df, otx_df)

    # Merge sources into the combined DataFrame
    combined_df = pd.merge(combined_df, sources_df, on='search_term', how='inner')
    
    # Define output file path
    current_date = pd.Timestamp.now().strftime("%Y-%m-%d")
    output_file = os.path.join(OUTPUT_DIR, f"I&W_Report_{current_date}.docx")

    # Fill the template table with data
    fill_word_template(TEMPLATE_PATH, output_file, combined_df)
