'''
完成之后，对目录进行一些处理：
1. 删除不再 configs 中的文件
2. 删除空目录
3. 删除 asset 中不需要的资源
3. 把前端相关文件（javascripts、stylesheets、partials）复制到对应的目录
4. 统计 asset 目录下的各个子目录容量大小
'''

import os
import shutil

import utils
import settings

from configParser import ConfigParser


configs = ConfigParser()

srcdir = utils.abspath(settings.srcdir)
docsdir = utils.abspath(settings.docsdir)

# 删除不在 configs 中的文件
generated_files = set()
for file in configs.file_cache:
    generated_files.add(utils.abspath(configs.file_cache[file][1]))

# 有些文件夹不进行检查...
notcheck_dirnames = ['asset', 'javascripts', 'stylesheets']
notcheck_dirpaths = [utils.abspath(os.path.join(docsdir, dirname)) for dirname in notcheck_dirnames]

for root, dirs, files in os.walk(docsdir):
    for file in files:
        file_path = utils.abspath(os.path.join(root, file))

        # 检查是否在 asset_dir 中
        if any(os.path.commonpath([file_path, dirpath]) == dirpath for dirpath in notcheck_dirpaths):
            # print(f'跳过文件: {file_path}')
            continue

        if file_path not in generated_files:
            print(f'删除不在 configs 中的文件: {file_path}')
            os.remove(file_path)

# 删除资源目录，先遍历各个目录文件，提取出资源链接
asset_files = set()
for root, dirs, files in os.walk(settings.docsdir):
    for file in files:
        if file.endswith('.md'):
            webfile_pth = utils.abspath(os.path.join(root, file))
            with open(webfile_pth, 'r', encoding='utf-8') as f:
                content = f.read()

            matches = utils.extract_links(content)
            for url_start, url_end, link_url, is_html in matches:
                # 如果是 HTML 链接，那么去除前面的 ../ 才是真正的路径
                if is_html:
                    link_url = link_url[3:]
                asset_abs = utils.abspath(os.path.join(os.path.dirname(webfile_pth), link_url))
                asset_files.add(asset_abs)

# 遍历 asset，检查是否有文件不在 asset_files 中
for root, dirs, files in os.walk(settings.assetdir):
    for file in files:
        asset_file = utils.abspath(os.path.join(root, file))
        if asset_file not in asset_files:
            print(f'删除不在 asset_files 中的文件: {asset_file}')
            os.remove(asset_file)


# 遍历目标目录，删除空目录
for root, dirs, files in os.walk(docsdir):
    for dir in dirs:
        if len(os.listdir(os.path.join(root, dir))) == 0:
            os.rmdir(os.path.join(root, dir))


# 把 overrides 中的 javascripts 和 stylesheets 文件夹内容复制到 docs 目录
overrides_dir = settings.overrides_dir
for subdir in ['javascripts', 'stylesheets']:
    src_subdir = os.path.join(overrides_dir, subdir)
    dst_subdir = os.path.join(settings.docsdir, subdir)
    os.makedirs(dst_subdir, exist_ok=True)
    utils.copy(src_subdir, dst_subdir)

# 把 overrides 中的 partials 文件夹内容复制到 partials 目录
# UPDATE: 这个就是用于评论的，offline 不需要
src_subdir = os.path.join(overrides_dir, 'partials')
if os.path.exists(src_subdir):
    dst_subdir = os.path.join(settings.dstdir, 'overrides', 'partials')
    os.makedirs(dst_subdir, exist_ok=True)
    utils.copy(src_subdir, dst_subdir)

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