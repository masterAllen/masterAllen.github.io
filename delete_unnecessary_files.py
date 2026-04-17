"""
删除生成目录里「与 cache / 当前 md 引用不一致」的内容：
1. docs 中不在 file_cache 的文件（跳过 asset、javascripts 等）
2. asset 中未被任何 md 引用的文件
3. docs 下空目录
"""
import os

os.chdir(os.path.dirname(__file__))

import utils
import settings
from utils.config_parser import ConfigParser


def _notcheck_dirpaths(docsdir: str) -> list[str]:
    notcheck_dirnames = ["asset", "javascripts", "stylesheets", "归档"]
    return [utils.abspath(os.path.join(docsdir, dirname)) for dirname in notcheck_dirnames]


def delete_stale_docs_files(configs, docsdir: str) -> None:
    generated_files = set()
    for file in configs.file_cache:
        generated_files.add(utils.abspath(configs.file_cache[file][1]))
    generated_files.update(configs.get_all_pages_files())
    generated_files.update(configs.get_all_link_output_files())

    notcheck_dirpaths = _notcheck_dirpaths(docsdir)
    for root, dirs, files in os.walk(docsdir):
        for file in files:
            file_path = utils.abspath(os.path.join(root, file))
            if any(os.path.commonpath([file_path, dirpath]) == dirpath for dirpath in notcheck_dirpaths):
                continue
            if file_path not in generated_files:
                print(f"删除不在 configs 中的文件: {file_path}")
                os.remove(file_path)


def collect_asset_paths_from_docs(docsdir: str) -> set[str]:
    asset_files: set[str] = set()
    for root, dirs, files in os.walk(docsdir):
        for file in files:
            if not file.endswith(".md"):
                continue
            webfile_pth = utils.abspath(os.path.join(root, file))
            with open(webfile_pth, "r", encoding="utf-8") as f:
                content = f.read()
            matches = utils.extract_links(content)
            for _url_start, _url_end, link_url, is_html in matches:
                if utils.check_url_type(link_url) == "web":
                    continue
                if is_html:
                    link_url = link_url[3:]
                asset_abs = utils.abspath(os.path.join(os.path.dirname(webfile_pth), link_url))
                asset_files.add(asset_abs)
    return asset_files


def delete_orphan_assets(assetdir: str, asset_files: set[str]) -> None:
    for root, dirs, files in os.walk(assetdir):
        for file in files:
            asset_file = utils.abspath(os.path.join(root, file))
            if asset_file not in asset_files:
                if "rawdir" not in asset_file:
                    print(f"删除不在 asset_files 中的文件: {asset_file}")
                os.remove(asset_file)


def remove_empty_dirs_under_docs(docsdir: str) -> None:
    for root, dirs, files in os.walk(docsdir):
        for d in dirs:
            p = os.path.join(root, d)
            if len(os.listdir(p)) == 0:
                os.rmdir(p)


def main() -> None:
    configs = ConfigParser()
    docsdir = utils.abspath(settings.docsdir)
    delete_stale_docs_files(configs, docsdir)
    asset_files = collect_asset_paths_from_docs(docsdir)
    delete_orphan_assets(settings.assetdir, asset_files)
    remove_empty_dirs_under_docs(docsdir)


if __name__ == "__main__":
    main()
