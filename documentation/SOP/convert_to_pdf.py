import os
import sys
import markdown
from xhtml2pdf import pisa

SOP_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_DIR = os.path.join(SOP_DIR, "PDF")
os.makedirs(PDF_DIR, exist_ok=True)

CSS = """
@page {
    size: A4;
    margin: 2cm 2.2cm 2cm 2.2cm;
}
body {
    font-family: Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.5;
    color: #1a1a1a;
}
h1 {
    font-size: 18pt;
    color: #003366;
    border-bottom: 2px solid #003366;
    padding-bottom: 6px;
    margin-top: 0;
}
h2 {
    font-size: 13pt;
    color: #003366;
    border-bottom: 1px solid #cccccc;
    padding-bottom: 3px;
    margin-top: 18px;
}
h3 {
    font-size: 11pt;
    color: #1a1a1a;
    margin-top: 12px;
}
h4 {
    font-size: 10pt;
    color: #333;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0;
    font-size: 9pt;
}
th {
    background-color: #003366;
    color: #ffffff;
    padding: 6px 8px;
    text-align: left;
}
td {
    padding: 5px 8px;
    border: 1px solid #cccccc;
}
tr:nth-child(even) td {
    background-color: #f2f6fb;
}
code {
    font-family: "Courier New", monospace;
    font-size: 8.5pt;
    background-color: #f4f4f4;
    padding: 1px 4px;
    border-radius: 3px;
}
pre {
    background-color: #f4f4f4;
    border: 1px solid #dddddd;
    border-left: 4px solid #003366;
    padding: 10px 12px;
    font-family: "Courier New", monospace;
    font-size: 8pt;
    line-height: 1.4;
    overflow-x: auto;
    white-space: pre-wrap;
    word-wrap: break-word;
}
pre code {
    background: none;
    padding: 0;
    border-radius: 0;
}
blockquote {
    border-left: 4px solid #003366;
    margin: 10px 0;
    padding: 6px 12px;
    background-color: #f0f4fa;
    color: #333;
    font-style: italic;
}
ul, ol {
    margin: 6px 0;
    padding-left: 20px;
}
li {
    margin-bottom: 3px;
}
hr {
    border: none;
    border-top: 1px solid #cccccc;
    margin: 14px 0;
}
a {
    color: #003366;
}
"""

def md_to_pdf(md_path, pdf_path):
    with open(md_path, "r", encoding="utf-8") as f:
        md_content = f.read()

    html_body = markdown.markdown(
        md_content,
        extensions=["tables", "fenced_code", "nl2br", "sane_lists"]
    )

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>{CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""

    with open(pdf_path, "wb") as pdf_file:
        result = pisa.CreatePDF(html, dest=pdf_file, encoding="utf-8")

    if result.err:
        print(f"  ERROR: {os.path.basename(md_path)} — {result.err}")
        return False
    return True


def main():
    md_files = [f for f in os.listdir(SOP_DIR) if f.endswith(".md")]
    if not md_files:
        print("No .md files found.")
        return

    print(f"Converting {len(md_files)} file(s) to PDF...\n")
    success, failed = 0, 0

    for md_file in sorted(md_files):
        md_path = os.path.join(SOP_DIR, md_file)
        pdf_name = os.path.splitext(md_file)[0] + ".pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_name)

        print(f"  {md_file}  ->  PDF/{pdf_name}")
        if md_to_pdf(md_path, pdf_path):
            success += 1
        else:
            failed += 1

    print(f"\nDone. {success} succeeded, {failed} failed.")
    print(f"PDFs saved to: {PDF_DIR}")


if __name__ == "__main__":
    main()
