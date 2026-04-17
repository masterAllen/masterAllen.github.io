"""在各 asset 子目录写入 rawdir.txt，记录对应原始文件路径。"""
import os

os.chdir(os.path.dirname(__file__))

import utils
import settings
from utils.config_parser import ConfigParser


def main() -> None:
    configs = ConfigParser()
    assetdir = settings.assetdir
    if not os.path.exists(assetdir):
        return
    asset_subdirs = set(os.listdir(assetdir))
    for rawfile_pth in configs.file_cache:
        if not os.path.isfile(rawfile_pth):
            continue
        for name in asset_subdirs:
            now_asset_dir = utils.asset_link(rawfile_pth, name, makedir=False)
            if os.path.exists(now_asset_dir):
                asset_file = utils.abspath(os.path.join(now_asset_dir, "rawdir.txt"))
                with open(asset_file, "w", encoding="utf-8") as f:
                    f.write(rawfile_pth)


if __name__ == "__main__":
    main()
