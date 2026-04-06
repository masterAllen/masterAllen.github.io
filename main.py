# 执行同目录下的 main*.py
import os
os.chdir(os.path.dirname(__file__))


import subprocess

# main1.py: 生成目标文件，更新 cache
subprocess.run(['python', f'main1.py'], check=True)

# main3.py: 根据 cache 删除一些文件
subprocess.run(['python', f'main3.py'], check=True)

# main2.py: 处理链接，更新目标文件
subprocess.run(['python', f'main2.py'], check=True)

subprocess.run(['python', f'main3.py'], check=True)

# 归档页面（依赖 main1 的 file_cache，需在 main4 生成导航前执行）
print('RUNNING: gen_archive.py...')
subprocess.run(['python', 'gen_archive.py'], check=True)

for i in range(4, 6):
    print(f'RUNNING: main{i}.py...')
    subprocess.run(['python', f'main{i}.py'], check=True)