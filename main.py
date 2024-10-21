import os
os.chdir(os.path.dirname(__file__))

import shutil
import collections

def do_md(srcdir, dstdir, subdir, onename):
    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir, onename)
    shutil.copyfile(srcpth, dstpth)

def do_html(srcdir, dstdir, subdir, onename):
    # 先截断名称，按照  - 分割，第一个就是最终的名字
    dstname = onename.split(' - ')[0].strip()
    dstname = dstname.split('.')[0]

    # 获取原文的地址
    srcpth = os.path.join(srcdir, subdir, onename)
    srcurl = ''
    with open(srcpth, 'r', encoding='utf-8') as f:
        for oneline in f:
            if oneline.strip()[0:4] == 'url:':
                srcurl = oneline.strip()[4:].strip()
                break

    dstpth = os.path.join(dstdir, subdir)

    bakpth = os.path.join(dstdir, 'asset', 'html', onename)
    shutil.copyfile(srcpth, bakpth)
    # 相对现在文件的路径，这样才能正确导入
    bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth))
    # Windows 下的处理
    bakpth = bakpth.replace('\\', '/')
    bakpth = bakpth.replace(' ', '%20')

    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})，本地备份：[链接]({bakpth})\n')


def do_ipynb(srcdir, dstdir, subdir, onename):
    dstname = onename.strip()
    dstname = dstname[:dstname.find('.')]

    # 原文转成 markdown
    srcpth = os.path.join(srcdir, subdir, onename)
    os.system(f'python -m jupyter nbconvert --to markdown {srcpth}')
    srcpth = os.path.join(srcdir, subdir, f'{dstname}.md')

    dstpth = os.path.join(dstdir, subdir)
    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        # 把原文转的 md 内容追加到这里，然后开头部分添加一个说明
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            # 开头的标题
            f.writelines(srcf.readline() + '\n')
            # 开头添加说明
            f.writelines(f'本文原始格式为 ipynb，原文链接：[TODO](TODO)\n')
            # 剩余部分补上
            f.writelines(srcf.readlines())
    os.remove(srcpth)


def do_png(srcdir, dstdir, subdir, onename):
    dstname = onename[:onename.rfind('.')]

    # 获取原文的地址
    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir)
    bakpth = os.path.join(dstdir, 'asset', 'image', onename)

    shutil.copyfile(srcpth, bakpth)
    # 相对现在文件的路径，这样才能正确导入
    bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth))
    # Windows 下的处理
    bakpth = bakpth.replace('\\', '/')
    bakpth = bakpth.replace(' ', '%20')

    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'原始文件格式为 PNG，以下是该图片：\n\n')
        f.writelines(f'![{dstname}]({bakpth})\n')

def do_pdf(srcdir, dstdir, subdir, onename):
    # dstname = onename.strip()
    # dstname = dstname[:dstname.find('.')]

    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, subdir, onename)
    # dstpth = os.path.join(dstdir, subdir, f'{dstname}.md')
    # os.system(f'pandoc -f docx -t markdown {srcpth} -o {dstpth}')

    pass

def do_word(srcdir, dstdir, subdir, onename):
    dstname = onename.strip()
    dstname = dstname[:dstname.find('.')]

    # 原文转成 markdown
    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir, f'{dstname}.md')
    # pandoc_pth = f'C:\\Program Files\\Pandoc\\pandoc.exe'
    # os.system(f'"{pandoc_pth}" -f docx -t markdown {srcpth} -o {dstpth}')

    # 原文转成 pdf
    bakpth = os.path.join(dstdir, 'asset', 'pdf', f'{dstname}.pdf')
    os.system(f'docx2pdf {srcpth} {bakpth}')

    # 相对现在文件的路径，这样才能正确导入
    bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth))
    # Windows 下的处理
    bakpth = bakpth.replace('\\', '/')
    bakpth = bakpth.replace(' ', '%20')

    with open(dstpth, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines.insert(1, f'\n**原文格式为 word，本文通过 pandoc 转换而来。原文转换的 [PDF 文件]({bakpth})（个人笔记，请勿用于商业，转载请注明来源！）**\n')
    with open(dstpth, 'w', encoding='utf-8') as f:
        for oneline in lines:
            if '.我的标题' in oneline:
                oneline = oneline[:oneline.find('{')]
                print(oneline)
                oneline = oneline[oneline.rfind('#'):]
                print(oneline)
            f.writelines(oneline)

def do_txt(srcdir, dstdir, subdir, onename):
    dstname = onename[:onename.rfind('.')]

    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir)
    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            f.writelines(f'# {dstname}\n')
            f.writelines(srcf.readlines())


if __name__ == '__main__':
    srcdir = '..\\sources'
    dstdir = os.path.join('.', 'docs')

    # 先创建资源目录
    asset_dir = os.path.join(dstdir, 'asset')
    if not os.path.exists(asset_dir):
        os.mkdir(asset_dir)
    for asset_type in ['html', 'pdf', 'image']:
        if not os.path.exists(os.path.join(asset_dir, asset_type)):
            os.mkdir(os.path.join(asset_dir, asset_type))


    dirnames = collections.deque([''])
    while len(dirnames):
        subdir = dirnames.popleft()
        nowdir = os.path.join(srcdir, subdir)

        # 遍历当前文件夹内容
        for onename in os.listdir(nowdir):
            now_sub = os.path.join(subdir, onename)
            now_pth = os.path.join(srcdir, now_sub)

            # 如果是子文件夹，那么就继续加入到队列中，加入的是 subdir，这样才好创建 dstdir/subdir
            if os.path.isdir(now_pth):
                now_dst = os.path.join(dstdir, now_sub)
                if not os.path.exists(now_dst):
                    os.system(f'mkdir {now_dst}')
                
                if onename == '材料':
                    # TODO: 如果是材料目录，那么就单独写一个 README，把这些文件都放进去
                    pass
                else:
                    dirnames.append(now_sub)
            else:
                if now_pth.endswith('md'):
                    do_md(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('html') or now_pth.endswith('htm'):
                    do_html(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('ipynb'):
                    do_ipynb(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('PNG') or now_pth.endswith('png'):
                    do_png(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('pdf'):
                    do_pdf(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('docx'):
                    do_word(srcdir, dstdir, subdir, onename)
                elif now_pth.endswith('txt'):
                    do_txt(srcdir, dstdir, subdir, onename)
                else:
                    print(now_pth, now_pth.endswith('md'))