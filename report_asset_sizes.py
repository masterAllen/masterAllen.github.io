"""打印 asset 目录下各子类型文件夹占用（MB）。"""
import os

os.chdir(os.path.dirname(__file__))

import settings


def main() -> None:
    asset_dir = settings.assetdir
    if not os.path.exists(asset_dir):
        return
    print("asset 目录各子目录容量(MB):")
    for subdir in os.listdir(asset_dir):
        subdir_path = os.path.join(asset_dir, subdir)
        if not os.path.isdir(subdir_path):
            continue
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(subdir_path):
            for fname in filenames:
                fpath = os.path.join(dirpath, fname)
                if os.path.isfile(fpath):
                    total_size += os.path.getsize(fpath)
        print(f"{subdir}: {total_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()
