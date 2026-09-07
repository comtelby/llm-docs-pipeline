import requests

r = requests.get('http://localhost:8000/export/audit_report_20260903_115959.md?format=docx')
print(f'DOCX: {r.status_code} - {r.headers.get("content-type")}')

r = requests.get('http://localhost:8000/export/audit_report_20260903_115959.md?format=pdf')
print(f'PDF: {r.status_code} - {r.headers.get("content-type")}')

r = requests.get('http://localhost:8000/export/audit_report_20260903_115959.md?format=html')
print(f'HTML: {r.status_code} - {r.headers.get("content-type")}')

r = requests.get('http://localhost:8000/export/audit_report_20260903_115959.md?format=txt')
print(f'TXT: {r.status_code} - {r.headers.get("content-type")}')

r = requests.get('http://localhost:8000/export/audit_report_20260903_115959.md?format=md')
print(f'MD: {r.status_code} - {r.headers.get("content-type")}')