import requests

r = requests.post('http://localhost:8000/chat', data={'prompt': 'test', 'model': 'qwen2.5-coder:7b'})
print(r.status_code, r.json())