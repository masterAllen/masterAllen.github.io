import os
os.chdir(os.path.dirname(__file__))

import re
import time
import shutil
import collections
import pathlib
import docx2pdf
import pptxtopdf
import pypdfium2 as pdfium
import cv2
import numpy as np
from PIL import Image

def mkdir(pth):
    if not os.path.exists(pth):
        os.system(f'mkdir {pth}')


def do_md(srcdir, dstdir, subdir, onename):
    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir, onename)
    shutil.copyfile(srcpth, dstpth)

    # 找到 md 文档中的图片链接，即 ![]()
    pattern = r'!\[(.*?)\]\((.*?)\)'
    text = open(dstpth, 'r', encoding='utf-8').read()
    matches = re.findall(pattern, text)
    for match in matches:
        # 如果里面的链接是 base64 编码，那么可以不处理
        if match[1].startswith('data:image'):
            continue

        # 把图片放到资料库中，然后把源文件修改
        srcimg = match[1]
        # 如果一开始就发现存在文件，则是绝对路径；否则就根据当前文件路径加上这个相对链接，就得出图片绝对路径
        if not os.path.exists(srcimg):
            srcimg = os.path.join(srcdir, subdir, match[1])
        
        if os.path.exists(srcimg):
            imgname = os.path.basename(srcimg)
            dstimg = os.path.join(dstdir, 'asset', 'images', imgname)

            shutil.copyfile(srcimg, dstimg)
            text = text.replace(match[1], f'/asset/images/{imgname}')
        else:
            print('没见过的链接', '链接：', match[1], '原文', srcdir, subdir, onename)

    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(text)


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

    # bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth)) # 相对现在文件的路径，这样才能正确导入
    # bakpth = bakpth.replace('\\', '/') # Windows 下的处理
    # bakpth = bakpth.replace(' ', '%20')

    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})，本地备份：[链接](/asset/html/{onename})\n')


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
    bakpth = os.path.join(dstdir, 'asset', 'images', onename)

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

    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, subdir, onename)
    # dstpth = os.path.join(dstdir, subdir, f'{dstname}.md')
    # pandoc_pth = f'C:\\Program Files\\Pandoc\\pandoc.exe'
    # os.system(f'"{pandoc_pth}" -f docx -t markdown {srcpth} -o {dstpth}')

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, subdir, onename)
    pdfpth = os.path.join(dstdir, 'asset', 'pdf', f'{dstname}.pdf')
    for tidx in range(3):
        time.sleep(tidx)
        try:
            docx2pdf.convert(srcpth, pdfpth)
            break
        except:
            pass
    # pandoc_pth = f'C:\\Program Files\\Pandoc\\pandoc.exe'
    # os.system(f'"{pandoc_pth}" -f docx -t pdf {srcpth} -o {bakpth}')
    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(dstdir, 'asset', 'images', dstname)
    mkdir(imgdir)

    mdpth = os.path.join(dstdir, subdir, f'{dstname}.md')
    with open(mdpth, 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'**原文格式为 word，本文为转换后的图片。原文也转换了 [PDF 格式](/asset/pdf/{dstname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(imgdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg = np.array(nowimg)
            rows, cols = nowimg.shape[0:2]
            nowimg = nowimg[rows//12:-rows//12, cols//15:-cols//15]

            nowimg = Image.fromarray(nowimg)
            nowimg.save(imgpth)
            f.writelines(f'![out{count}](/asset/images/{dstname}/out{count}.jpg)\n')

        # for oneline in lines:
        #     if '.我的标题' in oneline:
        #         nowline = oneline[:oneline.find('{')]
        #         nowline = nowline[nowline.rfind('#')+1:].strip()
        #         if '.我的标题一' in oneline:
        #             oneline = f'# {nowline}\n'

def do_ppt(srcdir, dstdir, subdir, onename):
    dstname = onename.strip()
    dstname = dstname[:dstname.find('.')]

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, subdir, onename)
    pdfpth = os.path.join(dstdir, 'asset', 'pdf', f'{dstname}.pdf')
    if os.path.exists(pdfpth):
        os.remove(pdfpth)
    pptxtopdf.convert(srcpth, os.path.join(dstdir, 'asset', 'pdf'))
    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(dstdir, 'asset', 'images', dstname)
    mkdir(imgdir)

    mdpth = os.path.join(dstdir, subdir, f'{dstname}.md')
    with open(mdpth, 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'**原文格式为 PPTX，本文为转换后的图片。原文也转换了 [PDF 格式](/asset/pdf/{dstname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(imgdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg.save(imgpth)
            f.writelines(f'![out{count}](/asset/images/{dstname}/out{count}.jpg)\n')

def do_txt(srcdir, dstdir, subdir, onename):
    dstname = onename[:onename.rfind('.')]

    srcpth = os.path.join(srcdir, subdir, onename)
    dstpth = os.path.join(dstdir, subdir)
    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            for oneline in srcf:
                f.writelines(oneline + '\n')

if __name__ == '__main__':
    srcdir = '../sources'
    dstdir = os.path.join('.', 'docs')

    dirnames = collections.deque([''])

    mkdir(os.path.join(dstdir, 'asset'))
    for ftype in ['html', 'pdf', 'images']:
        mkdir(os.path.join(dstdir, 'asset', ftype))

    while len(dirnames):
        subdir = dirnames.popleft()
        nowdir = os.path.join(srcdir, subdir)

        # 遍历当前文件夹内容
        for onename in os.listdir(nowdir):
            now_sub = os.path.join(subdir, onename)
            now_pth = os.path.join(srcdir, now_sub)

            if onename.startswith('~'):
                continue

            # 如果是子文件夹，那么就继续加入到队列中，加入的是 subdir，这样才好创建 dstdir/subdir
            if os.path.isdir(now_pth):
                now_dst = os.path.join(dstdir, now_sub)
                if onename == '材料' or onename == 'references':
                    # TODO: 如果是材料目录，那么就单独写一个 README，把这些文件都放进去
                    pass
                elif onename == 'src' or onename == 'code':
                    # TODO: 如果是 src 目录，同样单独写一个 README，把这些文件都放进去
                    pass
                elif onename.startswith('image'):
                    continue
                else:
                    mkdir(now_dst)
                    dirnames.append(now_sub)
            else:
                try:
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
                    elif now_pth.endswith('pptx'):
                        do_ppt(srcdir, dstdir, subdir, onename)
                    elif now_pth.endswith('txt'):
                        do_txt(srcdir, dstdir, subdir, onename)
                    else:
                        assert(False)
                except Exception as e:
                    print(now_pth, e)
                    pass