# 执行同目录下的 main*.py
import os
os.chdir(os.path.dirname(__file__))

import subprocess
for i in range(1, 4):
    subprocess.run(['python', f'main{i}.py'])

import settings
# 统计 asset 目录下的各个子目录容量大小
asset_dir = settings.assetdir
if os.path.exists(asset_dir):
    print("asset 目录各子目录容量(MB):")
    for subdir in os.listdir(asset_dir):
        subdir_path = os.path.join(asset_dir, subdir)
        if os.path.isdir(subdir_path):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(subdir_path):
                for fname in filenames:
                    fpath = os.path.join(dirpath, fname)
                    if os.path.isfile(fpath):
                        total_size += os.path.getsize(fpath)
            print(f"{subdir}: {total_size / (1024*1024):.2f} MB")
