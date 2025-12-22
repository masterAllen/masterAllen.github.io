# 处理 CCF-CSP
import os
from pathlib import Path
import shutil

def run(srcdir, dstdir, configs):
    os.makedirs(dstdir, exist_ok=True)

    # 1. 复制 README.md
    readme_src_path = f'{srcdir}/README.md'
    readme_dst_path = f'{dstdir}/README.md'
    configs.process_if_needed(readme_src_path, readme_dst_path, shutil.copy2)

    # 2. 遍历子目录
    # subdirs = [x for x in os.listdir(srcdir) if x.isdigit()]
    # subdirs = sorted(subdirs, key=lambda x:int(x))
    subdirs = [x for x in os.listdir(srcdir) if os.path.isdir(os.path.join(srcdir, x))]
    subdirs = sorted(subdirs)

    for subdir in subdirs:
        nowsrc = os.path.join(srcdir, subdir)
        nowdst = os.path.join(dstdir, subdir)
        os.makedirs(nowdst, exist_ok=True)

        # 1. 找到 md 文件，把他复制为 index.md
        mdfiles = [x for x in os.listdir(nowsrc) if x.endswith('md')]
        assert(len(mdfiles) < 2)

        if len(mdfiles) == 1:
            new_src = f'{nowsrc}/{mdfiles[0]}'
            new_dst = f'{nowdst}/index.md'
            configs.process_if_needed(new_src, new_dst, shutil.copy2)

        # 2. 找到 cpp 文件，然后转成 md 文件
        for suffix in ['cpp', 'h', 'py']:
            cppfiles = [x for x in os.listdir(nowsrc) if x.endswith(suffix)]
            cppfiles = sorted(cppfiles)

            for cppfile in cppfiles:
                title = cppfile[:-4]
                new_src = f'{nowsrc}/{cppfile}'
                new_dst = f'{nowdst}/{title}.md'
                
                def process_code_file(src, dst):
                    content = open(src, 'r', encoding='utf-8').read()
                    with open(dst, 'w', encoding='utf-8') as f:
                        f.write(f'# {title}\n')
                        f.write(f'原始文件为 {suffix} 代码，本文是转换后的 Markdown 文件。\n\n')
                        f.write(f'```{suffix}\n')
                        f.write(content)
                        f.write('```\n')
                configs.process_if_needed(new_src, new_dst, process_code_file)

    return True

# import sys
# srcpth = sys.argv[1]
# dstpth = sys.argv[2]
# run(srcpth, dstpth)

if __name__ == '__main__':
    srcpth = r'D:\Blog\done\算法记录\做题记录\CCF-CSP'
    dstpth = './docs/算法记录/做题记录/CCF-CSP'
    os.makedirs(dstpth, exist_ok=True)
    run(srcpth, dstpth)

    # srcpth = r'D:\Blog\done\算法记录\做题记录\刘汝佳算法竞赛'
    # dstpth = './docs/算法记录/做题记录/刘汝佳算法竞赛'
    # os.makedirs(dstpth, exist_ok=True)
    # run(srcpth, dstpth)

