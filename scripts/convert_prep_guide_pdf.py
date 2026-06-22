# convert_prep_guide_pdf.py
import os
import re
import subprocess
import markdown

md_path = "/home/abhishek/Projects/wifi-monitor/interview_prep_guide.md"
html_path = "/home/abhishek/Projects/wifi-monitor/interview_prep_guide.html"
pdf_dir = "/home/abhishek/Projects/wifi-monitor"

def main():
    if not os.path.exists(md_path):
        print(f"Error: Markdown guide not found at {md_path}")
        return

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace mermaid block with a clean text flowchart for PDF
    mermaid_block = """```mermaid
graph TD
    A[Browser UI / SSE Client] -->|HTTP Requests| B(Flask App Server)
    C[Background Monitor Thread] -->|Executes subprocesses| D[ping / nmcli / speedtest]
    D -->|Writes results| E[(SQLite Database)]
    B -->|Reads results| E
    B -->|Yields real-time events| A
```"""

    text_flowchart = """
<div class="flowchart">
  <h3>System Architecture Flow</h3>
  <div class="flow-box">
    <strong>1. Client Tier (Browser UI)</strong><br>
    &bull; Vanilla JS SPA listens to Server-Sent Events (SSE) stream at <code>/api/stream</code>.<br>
    &bull; Renders charts using Chart.js; captures user inputs for direct Wi-Fi configuration.
  </div>
  <div class="flow-arrow">&darr; REST Requests & SSE Connections</div>
  <div class="flow-box">
    <strong>2. Server Tier (Flask Application)</strong><br>
    &bull; Background scheduler thread polls ping metrics; stores them in SQLite.<br>
    &bull; API controllers run shell commands in subprocesses on demand.
  </div>
  <div class="flow-arrow">&darr; Shell Execution</div>
  <div class="flow-box">
    <strong>3. OS Tier & Persistence (Linux & SQLite)</strong><br>
    &bull; Direct utilities: <code>ping</code>, <code>nmcli</code>, <code>speedtest-cli</code>, <code>ip</code>.<br>
    &bull; Stores logs in SQLite (<code>results.db</code>) with automatic read/write safety buffers.
  </div>
</div>
"""
    content = content.replace(mermaid_block, text_flowchart)

    # Convert markdown to html body
    html_body = markdown.markdown(content, extensions=['tables', 'fenced_code'])

    # Premium print stylesheet for high-quality PDF layout
    styled_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Wi-Fi Monitor - Interview Prep Guide</title>
<style>
    @page {{
        size: A4;
        margin: 2cm;
    }}
    body {{
        font-family: 'Inter', Helvetica, Arial, sans-serif;
        color: #1f2937;
        line-height: 1.6;
        font-size: 10.5pt;
    }}
    h1, h2, h3, h4 {{
        color: #111827;
        font-weight: 700;
        margin-top: 18pt;
        margin-bottom: 8pt;
        page-break-after: avoid;
    }}
    h1 {{
        font-size: 22pt;
        border-bottom: 2px solid #6366f1;
        padding-bottom: 6pt;
        color: #4f46e5;
    }}
    h2 {{
        font-size: 15pt;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 4pt;
        margin-top: 24pt;
    }}
    h3 {{
        font-size: 12pt;
        color: #4f46e5;
    }}
    p {{
        margin-top: 0;
        margin-bottom: 10pt;
    }}
    ul, ol {{
        margin-top: 0;
        margin-bottom: 10pt;
        padding-left: 20pt;
    }}
    li {{
        margin-bottom: 4pt;
    }}
    code {{
        font-family: Consolas, Monaco, monospace;
        background-color: #f3f4f6;
        color: #1f2937;
        padding: 2pt 4pt;
        border-radius: 4px;
        font-size: 9.5pt;
    }}
    pre {{
        background-color: #1f2937;
        color: #f9fafb;
        padding: 12pt;
        border-radius: 6px;
        overflow-x: auto;
        margin-top: 8pt;
        margin-bottom: 12pt;
        page-break-inside: avoid;
    }}
    pre code {{
        background-color: transparent;
        color: inherit;
        padding: 0;
        font-size: 9pt;
    }}
    table {{
        width: 100%;
        border-collapse: collapse;
        margin-top: 10pt;
        margin-bottom: 15pt;
        page-break-inside: avoid;
    }}
    th, td {{
        border: 1px solid #d1d5db;
        padding: 8pt 10pt;
        text-align: left;
        font-size: 10pt;
    }}
    th {{
        background-color: #f9fafb;
        font-weight: 600;
        color: #374151;
    }}
    tr:nth-child(even) {{
        background-color: #f9fafb;
    }}
    blockquote {{
        border-left: 4px solid #6366f1;
        background-color: #f5f3ff;
        padding: 10pt 12pt;
        margin: 12pt 0;
        color: #374151;
        border-radius: 0 4px 4px 0;
    }}
    blockquote p {{
        margin-bottom: 0;
    }}
    .flowchart {{
        border: 1px solid #e5e7eb;
        background-color: #f9fafb;
        padding: 15pt;
        border-radius: 8px;
        margin: 15pt 0;
        text-align: center;
        page-break-inside: avoid;
    }}
    .flowchart h3 {{
        margin-top: 0;
        color: #111827;
    }}
    .flow-box {{
        border: 1px solid #d1d5db;
        background-color: #ffffff;
        padding: 10pt;
        border-radius: 6px;
        display: inline-block;
        width: 80%;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }}
    .flow-arrow {{
        margin: 8pt 0;
        font-size: 14pt;
        color: #9ca3af;
        font-weight: bold;
    }}
    hr {{
        border: 0;
        border-top: 1px solid #e5e7eb;
        margin: 20pt 0;
    }}
</style>
</head>
<body>
    {html_body}
</body>
</html>
"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(styled_html)
    print(f"Generated HTML successfully at {html_path}")

    # Convert to PDF using headless LibreOffice
    print("Converting HTML to PDF via LibreOffice...")
    cmd = [
        "/snap/bin/libreoffice",
        "--headless",
        "--convert-to", "pdf",
        "--outdir", pdf_dir,
        html_path
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("LibreOffice output:", res.stdout)
        pdf_file = os.path.join(pdf_dir, "interview_prep_guide.pdf")
        if os.path.exists(pdf_file):
            print(f"Success! PDF generated at {pdf_file}")
        else:
            print("Error: PDF file was not created.")
    except Exception as e:
        print(f"Failed to run LibreOffice conversion: {e}")
    finally:
        if os.path.exists(html_path):
            os.remove(html_path)
            print(f"Cleaned up temporary HTML file: {html_path}")

if __name__ == "__main__":
    main()
