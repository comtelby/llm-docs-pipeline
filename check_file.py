with open(r'C:/Users/ngn/Documents/New OpenCode Project/src/report.py', 'r') as f:
    lines = f.readlines()
for i in range(418, 430):
    print(f'{i+1}: {repr(lines[i])}')