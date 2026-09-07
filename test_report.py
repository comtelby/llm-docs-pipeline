import requests
import time

# First send a prompt
r = requests.post('http://localhost:8000/chat', data={'prompt': 'Проанализируй ИТ инфраструктуру. Используй шаблон template_kspd.md', 'model': 'qwen2.5-coder:7b'})
print('Chat:', r.status_code, r.json())

# Then generate report
r = requests.post('http://localhost:8000/generate-report')
print('Generate:', r.status_code)
if r.status_code == 200:
    print(r.json())
    # Wait a bit for generation
    time.sleep(30)
    # Check if report was generated
    r = requests.get('http://localhost:8000/reports')
    print('Reports:', r.json())