# 处理 README.md
import os
from pathlib import Path

def run(srcfile, dstpth, configs):
    dstpth = os.path.dirname(dstpth)
    readme_dst = f'{dstpth}/README.md'
    
    # 检查 README.md 是否需要更新
    need_update_readme = configs.is_need_update(srcfile)
    
    # TODO: 应该是 Mkdocs 的 bug，如果目录名字中有 code，他会不进行处理
    codename = 'forcheck'
    codepth = f'{dstpth}/{codename}'
    os.makedirs(codepth, exist_ok=True)

    idx = 0
    readme_lines = []
    any_python_updated = False
    
    with open(f'{srcfile}', 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith('##'):
                relpth = line.split(' ')[1].strip()

                # 检查是否存在
                abspth = Path(os.path.dirname(srcfile), relpth)
                if abspth.exists():
                    # 把 python 文件变换到 md 文件，名字是父目录的名字
                    title = f'{idx:03d}'
                    newname = Path(codepth, f'{title}.md')
                    
                    # 检查每个 Python 文件是否需要更新
                    def process_python(src, dst):
                        content = open(src, 'r', encoding='utf-8').read()
                        with open(dst, 'w', encoding='utf-8') as out_f:
                            out_f.write(f'# {title}\n')
                            out_f.write(f'原始文件为 Python 代码，本文是转换后的 Markdown 文件。\n\n')
                            out_f.write('```python\n')
                            out_f.write(content)
                            out_f.write('```\n')
                    
                    if configs.process_if_needed(str(abspth), str(newname), process_python):
                        any_python_updated = True
                    
                    idx += 1
                    line = f'## [{title}](./{codename}/{title}.md)\n'
            
            readme_lines.append(line)
    
    # 如果 README.md 本身需要更新，或者任何 Python 文件更新了，则重新生成 README.md
    if need_update_readme or any_python_updated:
        with open(readme_dst, 'w', encoding='utf-8') as dstf:
            dstf.writelines(readme_lines)
        configs.update_cache(srcfile, readme_dst, os.stat(srcfile).st_mtime)
    else:
        configs.update_cache_byold(srcfile)

    return True

# import sys
# srcpth = sys.argv[1]
# dstpth = sys.argv[2]
# run(srcpth, dstpth)

if __name__ == '__main__':
    srcpth = '../done/Language/Python/README.md'
    dstpth = './docs/Language/Python'
    os.makedirs(dstpth, exist_ok=True)

    run(srcpth, dstpth)

