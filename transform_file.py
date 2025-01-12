import os
import re
import time
import shutil
import docx2pdf
import pptxtopdf
import pypdfium2 as pdfium
import numpy as np
import utils
from PIL import Image

def do_md(srcdir, dstdir, assetdir, nowname, newname):
    # 添加反斜杠，用于有序列表，即 1. 变为 1\.
    def add_slash(m):
        matched_txt = m.group()
        return matched_txt[:-2] + '\\' + matched_txt[-2:]

    # 存储图片链接，并且把文档中的图片链接转为存储路径
    def change_pth(m):
        link_name, link_pth = m.group(1), m.group(2)
        # 如果里面的链接是 base64 编码，那么可以不处理
        if link_pth.startswith('data:image'):
            return link_pth

        # 把图片放到资料库中，然后把源文件修改

        # 如果一开始就发现存在文件，则是绝对路径；否则就根据当前文件路径加上这个相对链接，就得出图片绝对路径
        if not os.path.exists(link_pth):
            link_pth = os.path.join(srcdir, link_pth)
        
        if os.path.exists(link_pth):
            if link_pth.endswith('html'):
                pass
            else:
                imgname = os.path.basename(link_pth)
                dstimg = os.path.join(assetdir, 'image', imgname)
                shutil.copyfile(link_pth, dstimg)

                return f'![{link_name}](/asset/image/{imgname})'
        else:
            print('没见过的链接', '链接：', link_pth, '原文', srcdir, nowname)
            return ''


    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    shutil.copyfile(srcpth, dstpth)

    text = open(dstpth, 'r', encoding='utf-8').read()

    # 找到 md 文档中的图片链接，即 ![]()
    pattern = r'!\[(.*?)\]\((.*?)\)'
    text = re.sub(pattern, change_pth, text)

    # 找到 md 文档中的有序列表，即 1.
    pattern = r'( *[\d+]\. )'

    # 如果有序列表下一行是 - 开头，那么要加个换行
    newlines = []
    for idx, m in enumerate(re.finditer(pattern, text)):
        lo, hi = m.span()
        pos1 = text.find('\n', hi)
        pos2 = text.find('\n', pos1+1)
        if text[pos1+1:pos2].strip().startswith('-'):
            newlines.append(pos1)
    for idx, pos in enumerate(newlines):
        text = text[:pos+idx] + '\n' + text[pos+idx:]

    # 把有序列表替换为 1\.
    text = re.sub(pattern, add_slash, text)

    with open(dstpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f)
        f.write(text)
    return dstpth


def do_html(srcdir, dstdir, assetdir, nowname, newname):
    # 获取原文的地址
    srcpth = os.path.join(srcdir, nowname)
    srcurl = ''
    with open(srcpth, 'r', encoding='utf-8') as f:
        for oneline in f:
            if oneline.strip()[0:4] == 'url:':
                srcurl = oneline.strip()[4:].strip()
                break

    fsize = os.path.getsize(srcpth)
    # 如果小于 10M 才会保存
    if fsize < 10 * 1024 * 1024:
        bakpth = os.path.join(assetdir, 'html', nowname)
        shutil.copyfile(srcpth, bakpth)

    dstpth = os.path.join(dstdir, f'{newname}.md')

    # bakpth = os.path.join('..', os.path.relpath(bakpth, dstpth)) # 相对现在文件的路径，这样才能正确导入
    # bakpth = bakpth.replace('\\', '/') # Windows 下的处理
    # bakpth = bakpth.replace(' ', '%20')

    with open(dstpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f)
        f.writelines(f'# {newname}\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})\n')
        if fsize < 10 * 1024 * 1024:
            f.writelines(f'本地备份：[链接](/asset/html/{nowname})\n')
    return dstpth


def do_ipynb(srcdir, dstdir, assetdir, nowname, newname):
    # 原文转成 markdown
    srcpth = os.path.join(srcdir, nowname)
    os.system(f'python -m jupyter nbconvert --to markdown {srcpth}')

    dstpth  = os.path.join(dstdir, f'{newname}.md')
    with open(dstpth, 'w', encoding='utf-8') as f:
        # 把原文转的 md 内容追加到这里，然后开头部分添加一个说明
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            utils.add_topinfo(f)
            # 开头的标题
            f.writelines(srcf.readline())
            # 开头添加说明
            f.writelines(f'本文原始格式为 ipynb' + '\n')
            # 剩余部分补上
            f.writelines(srcf.readlines())
    os.remove(srcpth)
    return dstpth


def do_png(srcdir, dstdir, assetdir, nowname, newname):
    # 获取原文的地址
    srcpth = os.path.join(srcdir, nowname)
    bakpth = os.path.join(assetdir, 'image', nowname)

    shutil.copyfile(srcpth, bakpth)

    dstpth  = os.path.join(dstdir, f'{newname}.md')

    with open(dstpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f)
        f.writelines(f'# {newname}\n')
        # f.writelines(f'原始文件格式为 PNG，以下是该图片：\n\n')
        f.writelines(f'![{newname}](/asset/image/{nowname})\n')
    return dstpth


def do_pdf(srcdir, dstdir, assetdir, nowname, newname):
    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    # os.system(f'pandoc -f docx -t markdown {srcpth} -o {dstpth}')
    return dstpth

def do_word(srcdir, dstdir, assetdir, nowname, newname):
    # # 原文转成 markdown
    # srcpth = os.path.join(srcdir, nowname)
    # dstpth = os.path.join(dstdir, f'{dstname}.md')
    # pandoc_pth = f'C:\\Program Files\\Pandoc\\pandoc.exe'
    # os.system(f'"{pandoc_pth}" -f docx -t markdown {srcpth} -o {dstpth}')

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    pdfpth = os.path.join(assetdir, 'pdf', f'{newname}.pdf')
    for tidx in range(3):
        time.sleep(tidx)
        try:
            docx2pdf.convert(srcpth, pdfpth)
            break
        except:
            pass

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(assetdir, 'image', newname)
    os.makedirs(imgdir, exist_ok=True)

    mdpth = os.path.join(dstdir, f'{newname}.md')
    with open(mdpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f, hide=['toc'])
        f.writelines(f'# {newname}\n')
        f.writelines(f'**原文格式为 word，本文为转换后的图片。原文也转换了 [PDF 格式](/asset/pdf/{newname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        f.writelines('\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(imgdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg = np.array(nowimg)
            rows, cols = nowimg.shape[0:2]
            nowimg = nowimg[rows//12:-rows//12, cols//12:-cols//12]

            nowimg = Image.fromarray(nowimg)
            nowimg.save(imgpth)
            f.writelines(f'![out{count}](/asset/image/{newname}/out{count}.jpg)\n')
    return mdpth


def do_ppt(srcdir, dstdir, assetdir, nowname, newname):

    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    pdfpth = os.path.join(assetdir, 'pdf', f'{newname}.pdf')
    if os.path.exists(pdfpth):
        os.remove(pdfpth)
    pptxtopdf.convert(srcpth, os.path.join(assetdir, 'pdf'))
    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdfpth)
    imgdir = os.path.join(assetdir, 'image', newname)
    os.makedirs(imgdir, exist_ok=True)

    mdpth = os.path.join(dstdir, f'{newname}.md')
    with open(mdpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f)
        f.writelines(f'# {newname}\n')
        f.writelines(f'**原文格式为 PPTX，本文为转换后的图片。原文也转换了 [PDF 格式](/asset/pdf/{newname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(imgdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg.save(imgpth)
            f.writelines(f'![out{count}](/asset/image/{newname}/out{count}.jpg)\n')
    return mdpth


def do_txt(srcdir, dstdir, assetdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)

    dstpth  = os.path.join(dstdir, f'{newname}.md')
    with open(dstpth, 'w', encoding='utf-8') as f:
        utils.add_topinfo(f)
        f.writelines(f'# {newname}\n')
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            content = srcf.readlines()

        flag = False
        for idx in range(len(content)):
            if content[idx][0] == '#':
                flag = True
                break

        if flag:
            for idx in range(len(content)):
                if content[idx].startswith('# '):
                    content[idx] = '## ' + content[idx][2:]
            f.writelines(content)
        else:
            f.writelines('`````\n')
            f.writelines(content)
            if content[-1][-1] != '\n':
                f.writelines('\n')
            f.writelines('`````')
    return dstpth