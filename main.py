# 执行同目录下的 main*.py
import os
os.chdir(os.path.dirname(__file__))


import subprocess
subprocess.run(['python', f'main3.py'], check=True)

for i in range(1, 6):
    print(f'RUNNING: main{i}.py...')
    subprocess.run(['python', f'main{i}.py'], check=True)