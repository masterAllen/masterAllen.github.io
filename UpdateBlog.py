import os
import sys
import shutil
import subprocess

def replace_nav(srcfile, dstfile):
    nav_before_lines = []
    with open(srcfile, 'r', encoding='utf8') as f:
        lines = f.readlines()
        for line in lines:
            if 'nav:' in line:
                break
            nav_before_lines.append(line)

    nav_after_lines = []
    with open(dstfile, 'r', encoding='utf8') as f:
        lines = f.readlines()
        is_nav = False
        for line in lines:
            if 'nav:' in line:
                is_nav = True
            if is_nav:
                nav_after_lines.append(line)

    with open(dstfile, 'w', encoding='utf8') as f:
        f.writelines(nav_before_lines)
        f.writelines(nav_after_lines)

script_dir = r'D:\Blog\scripts'

lo, hi = 0, 3
if len(sys.argv) == 2:
    lo = int(sys.argv[1])
    hi = lo + 1
if len(sys.argv) == 3:
    lo = int(sys.argv[1])
    hi = int(sys.argv[2])

'''
生成手机端
'''
if lo <= 0 < hi:
    dstdir = r'D:\BlogSite\masterAllen.github.io'
    subprocess.run(
        ["python", "main.py"],
        cwd=f'{script_dir}/web',
        check=True
    )
    # 手机端：必须要删除 partials/comments.html
    comments_pth = os.path.join(dstdir, 'overrides', 'partials', 'comments.html')
    if os.path.exists(comments_pth):
        os.remove(comments_pth)

    replace_nav(os.path.join(script_dir, 'web', 'mkdocs-phone.yml'), os.path.join(dstdir, 'mkdocs.yml'))
    subprocess.run(
        ["zensical", "build"],
        cwd=dstdir,
        check=True
    )
    # 在重命名前检测目标文件夹是否已存在，如果存在则先删除
    site_src = os.path.join(dstdir, 'site')
    site_dst = os.path.join(dstdir, 'site-phone')
    if os.path.exists(site_dst):
        # 删除内容
        for item in os.listdir(site_dst):
            item_path = os.path.join(site_dst, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

    # 复制内容
    for item in os.listdir(site_src):
        s = os.path.join(site_src, item)
        d = os.path.join(site_dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

'''
生成 Web 端
'''
if lo <= 1 < hi:
    dstdir = r'D:\BlogSite\masterAllen.github.io'
    subprocess.run(
        ["python", "main.py"],
        cwd=f'{script_dir}/web',
        check=True
    )
    replace_nav(os.path.join(script_dir, 'web', 'mkdocs-web.yml'), os.path.join(dstdir, 'mkdocs.yml'))
    subprocess.run(
        ["zensical", "build"],
        cwd=dstdir,
        check=True
    )

# '''
# 生成本地端
# '''
# if lo <= 2 < hi:
#     dstdir = r'D:\BlogSite\offline'
    # subprocess.run(
    #     ["python", "main.py"],
    #     cwd=f'{script_dir}/local',
    #     check=True
    # )
    # subprocess.run(
    #     ["mkdocs", "build"],
    #     cwd=dstdir,
    #     check=True
    # )