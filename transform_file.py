import os
import re
import time
import shutil
import docx2pdf
import pptxtopdf
import pypdfium2 as pdfium
import numpy as np
from PIL import Image

def do_md(srcdir, dstdir, assetdir, nowname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, nowname)
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
            srcimg = os.path.join(srcdir, match[1])
        
        if os.path.exists(srcimg):
            imgname = os.path.basename(srcimg)
            dstimg = os.path.join(assetdir, 'image', imgname)

            shutil.copyfile(srcimg, dstimg)
            text = text.replace(match[1], f'/asset/image/{imgname}')
        else:
            print('没见过的链接', '链接：', match[1], '原文', srcdir, nowname)

    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(text)


def do_html(srcdir, dstdir, assetdir, nowname):
    # 先截断名称，按照  - 分割，第一个就是最终的名字
    dstname = nowname.split(' - ')[0].strip()
    dstname = dstname.split('.')[0]

    # 获取原文的地址
    srcpth = os.path.join(srcdir, nowname)
    srcurl = ''
    with open(srcpth, 'r', encoding='utf-8') as f:
        for oneline in f:
            if oneline.strip()[0:4] == 'url:':
                srcurl = oneline.strip()[4:].strip()
                break

    dstpth = dstdir

    bakpth = os.path.join(assetdir, 'html', nowname)
    shutil.copyfile(srcpth, bakpth)

    # bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth)) # 相对现在文件的路径，这样才能正确导入
    # bakpth = bakpth.replace('\\', '/') # Windows 下的处理
    # bakpth = bakpth.replace(' ', '%20')

    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})，本地备份：[链接](/asset/html/{nowname})\n')


def do_ipynb(srcdir, dstdir, assetdir, nowname):
    dstname = nowname.strip()
    dstname = dstname[:dstname.find('.')]

    # 原文转成 markdown
    srcpth = os.path.join(srcdir, nowname)
    os.system(f'python -m jupyter nbconvert --to markdown {srcpth}')

    dstpth = dstdir
    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        # 把原文转的 md 内容追加到这里，然后开头部分添加一个说明
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            # 开头的标题
            f.writelines(srcf.readline())
            # 开头添加说明
            f.writelines(f'本文原始格式为 ipynb' + '\n')
            # 剩余部分补上
            f.writelines(srcf.readlines())
    os.remove(srcpth)


def do_png(srcdir, dstdir, assetdir, nowname):
    dstname = nowname[:nowname.rfind('.')]

    # 获取原文的地址
    srcpth = os.path.join(srcdir, nowname)
    dstpth = dstdir
    bakpth = os.path.join(assetdir, 'image', nowname)

    shutil.copyfile(srcpth, bakpth)
    # # 相对现在文件的路径，这样才能正确导入
    # bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth))
    # # Windows 下的处理
    # bakpth = bakpth.replace('\\', '/')
    # bakpth = bakpth.replace(' ', '%20')

    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'原始文件格式为 PNG，以下是该图片：\n\n')
        f.writelines(f'![{dstname}](/asset/image/{nowname})\n')


def do_pdf(srcdir, dstdir, assetdir, nowname):
    # dstname = nowname.strip()
    # dstname = dstname[:dstname.find('.')]

    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, nowname)
    # dstpth = os.path.join(dstdir, f'{dstname}.md')
    # os.system(f'pandoc -f docx -t markdown {srcpth} -o {dstpth}')

    pass

def do_word(srcdir, dstdir, assetdir, nowname):
    dstname = nowname.strip()
    dstname = dstname[:dstname.find('.')]

    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, nowname)
    # dstpth = os.path.join(dstdir, f'{dstname}.md')
    # pandoc_pth = f'C:\\Program Files\\Pandoc\\pandoc.exe'
    # os.system(f'"{pandoc_pth}" -f docx -t markdown {srcpth} -o {dstpth}')

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    pdfpth = os.path.join(assetdir, 'pdf', f'{dstname}.pdf')
    for tidx in range(3):
        time.sleep(tidx)
        try:
            docx2pdf.convert(srcpth, pdfpth)
            break
        except:
            pass

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(assetdir, 'image', dstname)
    os.makedirs(imgdir, exist_ok=True)

    mdpth = os.path.join(dstdir, f'{dstname}.md')
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
            f.writelines(f'![out{count}](/asset/image/{dstname}/out{count}.jpg)\n')


def do_ppt(srcdir, dstdir, assetdir, nowname):
    dstname = nowname.strip()
    dstname = dstname[:dstname.find('.')]

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    pdfpth = os.path.join(assetdir, 'pdf', f'{dstname}.pdf')
    if os.path.exists(pdfpth):
        os.remove(pdfpth)
    pptxtopdf.convert(srcpth, os.path.join(assetdir, 'pdf'))
    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(assetdir, 'image', dstname)
    os.makedirs(imgdir, exist_ok=True)

    mdpth = os.path.join(dstdir, f'{dstname}.md')
    with open(mdpth, 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines(f'**原文格式为 PPTX，本文为转换后的图片。原文也转换了 [PDF 格式](/asset/pdf/{dstname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(imgdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg.save(imgpth)
            f.writelines(f'![out{count}](/asset/image/{dstname}/out{count}.jpg)\n')


def do_txt(srcdir, dstdir, assetdir, nowname):
    dstname = nowname[:nowname.rfind('.')]

    srcpth = os.path.join(srcdir, nowname)
    dstpth = dstdir
    with open(os.path.join(dstpth, f'{dstname}.md'), 'w', encoding='utf-8') as f:
        f.writelines(f'# {dstname}\n')
        f.writelines('```\n')
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            for oneline in srcf:
                f.writelines(oneline)
        f.writelines('```\n')
