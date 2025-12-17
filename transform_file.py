import os
import re
import time
import shutil
import docx2pdf
import pptxtopdf
import pypdfium2 as pdfium
import numpy as np
import utils
import urllib.parse
from PIL import Image

def do_md(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    with open(dstpth, 'w', encoding='utf8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')

        # 读取原文件的标题（假定第一行为标题），作为 md 文件的开头
        with open(srcpth, 'r', encoding='utf8') as srcf:
            lines = srcf.readlines()
            # 判断第一行是否为 Markdown 标题，否则用 newname
            if lines and lines[0].strip().startswith('# '):
                title = lines[0].strip()
                content_start = 1
            else:
                title = f'# {newname}'
                content_start = 0
            f.write(f'{title}\n')

            # 写入 filelink
            f.write(utils.get_filelink(srcpth) + '\n')

            # 写入内容（如果 title 已写过则跳过第一行）
            for line in lines[content_start:]:
                f.write(line)

    return dstpth


def do_html(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')

    # 获取原文的地址
    srcurl = ''
    with open(srcpth, 'r', encoding='utf-8') as f:
        for oneline in f:
            if oneline.strip()[0:4] == 'url:':
                srcurl = oneline.strip()[4:].strip()
                break

    asset_absdir = utils.asset_link(srcpth, 'html')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})\n')
        if asset_reldir is not None:
            f.writelines(f'本地备份：[链接]({asset_reldir}/{nowname})\n')
    return dstpth


def do_ipynb(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')

    # 原文转成 markdown
    os.system(f'python -m jupyter nbconvert --to markdown {srcpth}')

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        # 把原文转的 md 内容追加到这里，然后开头部分添加一个说明
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            f.write(utils.get_topinfo(comments=True) + '\n')
            # 开头的标题
            f.writelines(srcf.readline())
            f.writelines(utils.get_filelink(srcpth) + '\n')
            # 开头添加说明
            f.writelines(f'本文原始格式为 ipynb' + '\n')
            # 剩余部分补上
            f.writelines(srcf.readlines())
    os.remove(srcpth)
    return dstpth


def do_png(srcdir, dstdir, nowname, newname):
    # 获取原文的地址
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')

    # 获取 asset 的相对路径
    asset_absdir = utils.asset_link(srcpth, 'image')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'![{newname}]({asset_reldir}/{nowname})\n')
    return dstpth


def do_pdf(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')

    # 获取 asset 的相对路径
    asset_absdir = utils.asset_link(srcpth, 'pdf')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'原文为 PDF 格式：[链接]({asset_reldir}/{nowname})')
        f.writelines('\n')
    return dstpth

def do_word(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')

    # 原文转成 pdf
    pdf_absdir = utils.asset_link(srcpth, 'pdf')
    pdf_reldir = utils.relpath(pdf_absdir, dstpth)
    pdf_absfile = os.path.join(pdf_absdir, f'{newname}.pdf')
    for tidx in range(3):
        time.sleep(tidx)
        try:
            docx2pdf.convert(srcpth, pdf_absfile)
            break
        except:
            pass

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdf_absfile)

    img_absdir = utils.asset_link(srcpth, 'image')
    img_reldir = utils.relpath(img_absdir, dstpth)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True, hide=['toc']) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')

        info_str = f'原文也转换了 [PDF 格式]({pdf_reldir}/{newname}.pdf)'
        f.writelines(info_str)

        f.writelines('\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(img_absdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg = np.array(nowimg)
            rows, cols = nowimg.shape[0:2]
            nowimg = nowimg[rows//12:-rows//12, cols//12:-cols//12]

            # 去除图片后面大部分空白区
            while True:
                if np.sum(nowimg[-rows//20:] < 250) != 0:
                    break
                nowimg = nowimg[:-rows//20]

            nowimg = Image.fromarray(nowimg)
            nowimg.save(imgpth)
            f.writelines(f'![out{count}]({img_reldir}/out{count}.jpg)\n')
    return dstpth


def do_ppt(srcdir, dstdir, nowname, newname):
    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')

    # 转成 PDF
    pdf_absdir = utils.asset_link(srcpth, 'pdf')
    pdf_reldir = utils.relpath(pdf_absdir, dstpth)
    pdf_absfile = os.path.join(pdf_absdir, f'{newname}.pdf')
    if os.path.exists(pdf_absfile):
        os.remove(pdf_absfile)
    pptxtopdf.convert(srcpth, pdf_absdir) # convert 第二个参数是文件夹

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdf_absfile)
    img_absdir = utils.asset_link(srcpth, 'image')
    img_reldir = utils.relpath(img_absdir, dstpth)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'**原文格式为 PPTX，本文为转换后的图片。原文也转换了 [PDF 格式]({pdf_reldir}/{newname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(img_absdir, f'out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg.save(imgpth)
            f.writelines(f'![out{count}]({img_reldir}/out{count}.jpg)\n')
    return dstpth


def do_txt(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            content = srcf.readlines()

        # 查看是否应该是 markdown 文件
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
            try:
                if content[-1][-1] != '\n':
                    f.writelines('\n')
                f.writelines('`````')
            except:
                print(f"处理 TXT 文件错误，原始文件路径: {srcpth}，content 长度: {len(content)}")
                raise Exception(f"处理 TXT 文件错误，原始文件路径: {srcpth}，content 长度: {len(content)}")

    return dstpth

def do_special_dir(srcdir, dstpth):
    # 在 dstdir 中创建一个 README.md 文件
    os.makedirs(os.path.dirname(dstpth), exist_ok=True)
    with open(dstpth, 'w', encoding='utf-8') as f:
        # 列出 srcdir 中的所有文件
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {os.path.basename(srcdir)}\n')

        f.writelines(f'本文件为自动生成，以下列表展示了这个资源目录的文件名称，以供参考：\n\n')
        for file in os.listdir(srcdir):
            f.writelines(f'- {file}\n')

def do_video(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')

    # # 获取 asset 的相对路径
    # asset_absdir, asset_reldir = utils.asset_link(dstpth, 'video')
    # utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {newname}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'源文件为视频文件，暂不进行转换\n')

        # f.writelines('\n')
        # f.writelines('<video controls>\n')
        # # mkdocs 的一个奇怪的点，src 索引针对的是上一层目录
        # f.writelines(f'<source src="../{asset_reldir}/{nowname}" type="video/mp4">\n')
        # f.writelines('</video>\n')

    return dstpth