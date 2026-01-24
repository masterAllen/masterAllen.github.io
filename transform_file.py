import os
from win32com.client import Dispatch, DispatchEx
import pypdfium2 as pdfium
import numpy as np
import utils
import transform_name
from PIL import Image

def do_secret_file(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(f'**⚠️ 此文件为保密文件，不上传。**\n')
        f.writelines(f'\n')
    return dstpth

def do_file_too_large(srcdir, dstdir, nowname, newname, file_type):
    """
    处理文件过大的情况，生成一个说明文件
    
    参数:
        srcdir: 源目录
        dstdir: 目标目录
        nowname: 原始文件名
        newname: 新文件名
        file_type: 文件类型
    
    返回:
        生成的文件路径
    """
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)
    
    # 获取文件大小（MB）
    file_size_mb = os.path.getsize(srcpth) / (1024 * 1024)
    
    # 根据文件类型生成不同的提示信息
    type_messages = {
        'html': 'HTML 文件',
        'image': '图片文件',
        'pdf': 'PDF 文件',
        'word': 'Word 文档',
        'ppt': 'PPT 演示文稿',
        'video': '视频文件',
        'unknown': '文件'
    }
    file_type_name = type_messages.get(file_type, '文件')
    
    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'\n')
        f.writelines(f'**⚠️ 此 {file_type_name}过大（{file_size_mb:.2f} MB，超过 10MB 限制），未上传。**\n')
        f.writelines(f'\n')
        f.writelines(f'原始文件路径：`{srcpth}`\n')
    
    return dstpth

def do_md(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    title = transform_name.remove_suffix(newname)
    dstpth = os.path.join(dstdir, f'{title}.md')

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
                title = f'# {title}'
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
    title = transform_name.remove_suffix(newname)

    # 获取原文的地址
    srcurl = ''
    with open(srcpth, 'r', encoding='utf-8') as f:
        for oneline in f:
            if oneline.strip()[0:4] == 'url:':
                srcurl = oneline.strip()[4:].strip()
                break

    asset_absdir = utils.asset_link(srcpth, 'html')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    copy_success = utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'转载文章，文章链接：[{srcurl}]({srcurl})\n')
        if asset_reldir is not None:
            f.writelines(f'本地备份：[链接]({asset_reldir}/{nowname})\n')
    return dstpth


def do_ipynb(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    # 原文转成 markdown
    os.system(f'python -m jupyter nbconvert --to markdown {srcpth}')

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        # 把原文转的 md 内容追加到这里，然后开头部分添加一个说明
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            f.write(utils.get_topinfo(comments=True) + '\n')
            # 开头的标题
            f.writelines(f'# {title}\n')
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
    title = transform_name.remove_suffix(newname)

    # 获取 asset 的相对路径
    asset_absdir = utils.asset_link(srcpth, 'image')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'![{newname}]({asset_reldir}/{nowname})\n')
    return dstpth


def do_pdf(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    # 获取 asset 的相对路径
    asset_absdir = utils.asset_link(srcpth, 'pdf')
    asset_reldir = utils.relpath(asset_absdir, dstpth)
    utils.copy(srcpth, os.path.join(asset_absdir, nowname))

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(srcpth)
    img_absdir = utils.asset_link(srcpth, 'image')
    img_reldir = utils.relpath(img_absdir, dstpth)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True, hide=['toc']) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')

        f.writelines(f'原文为 PDF 格式：[链接]({asset_reldir}/{nowname})')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(img_absdir, f'{nowname}_out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg = np.array(nowimg)
            nowimg = Image.fromarray(nowimg)
            nowimg.save(imgpth)
            f.writelines(f'![IMG{count}]({img_reldir}/{nowname}_out{count}.jpg)\n')
        f.writelines('\n')

    return dstpth

def do_word(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    # 原文转成 pdf
    pdf_absdir = utils.asset_link(srcpth, 'pdf')
    pdf_reldir = utils.relpath(pdf_absdir, dstpth)
    pdf_absfile = os.path.join(pdf_absdir, f'{newname}.pdf')

    word = DispatchEx("Word.Application")
    word.Visible = False

    doc_path = os.path.abspath(srcpth)
    pdf_path = os.path.abspath(pdf_absfile)

    doc = word.Documents.Open(doc_path)
    doc.ExportAsFixedFormat(
        OutputFileName=pdf_path,
        ExportFormat=17  # wdExportFormatPDF
    )
    doc.Close(False)
    word.Quit()

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdf_absfile)

    img_absdir = utils.asset_link(srcpth, 'image')
    img_reldir = utils.relpath(img_absdir, dstpth)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True, hide=['toc']) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')

        info_str = f'原文也转换了 [PDF 格式]({pdf_reldir}/{newname}.pdf)'
        f.writelines(info_str)

        f.writelines('\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(img_absdir, f'{newname}_out{count}.jpg')
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
            f.writelines(f'![IMG{count}]({img_reldir}/{newname}_out{count}.jpg)\n')
    return dstpth


def do_ppt(srcdir, dstdir, nowname, newname):
    # 原文转成 pdf
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    # 转成 PDF
    pdf_absdir = utils.asset_link(srcpth, 'pdf')
    pdf_reldir = utils.relpath(pdf_absdir, dstpth)

    # PPTConvert 一定是转成了去掉后缀的 PDF
    pdf_absfile = os.path.join(pdf_absdir, f'{newname}.pdf')
    powerpoint = Dispatch("PowerPoint.Application")
    presentation = powerpoint.Presentations.Open(srcpth, WithWindow=False)
    presentation.SaveAs(pdf_absfile, 32)  # 32 = PDF
    presentation.Close()
    powerpoint.Quit()

    # PDF 再转为图片
    pdf = pdfium.PdfDocument(pdf_absfile)
    img_absdir = utils.asset_link(srcpth, 'image')
    img_reldir = utils.relpath(img_absdir, dstpth)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'**原文格式为 PPTX，本文为转换后的图片。原文也转换了 [PDF 格式]({pdf_reldir}/{newname}.pdf)（个人笔记，请勿用于商业，转载请注明来源！）**\n')
        for count, page in enumerate(pdf):
            imgpth = os.path.join(img_absdir, f'{newname}_out{count}.jpg')
            nowimg = page.render(scale=4).to_pil()
            nowimg.save(imgpth)
            f.writelines(f'![{newname}_out{count}]({img_reldir}/{newname}_out{count}.jpg)\n')
    return dstpth


def do_txt(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    with open(srcpth, 'r', encoding='utf-8') as srcf:
        content = srcf.readlines()

    if len(content) == 0:
        return None

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')

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
                return None
                # raise Exception(f"处理 TXT 文件错误，原始文件路径: {srcpth}，content 长度: {len(content)}")

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
    title = transform_name.remove_suffix(newname)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')

        f.writelines('\n')
        f.writelines(f'视频文件，暂不上传⚠️\n')
        f.writelines(f'\n')

    return dstpth

# def do_video(srcdir, dstdir, nowname, newname):
#     srcpth = os.path.join(srcdir, nowname)
#     dstpth  = os.path.join(dstdir, f'{newname}.md')
#     title = transform_name.remove_suffix(newname)

#     # 获取 asset 的相对路径
#     asset_absdir = utils.asset_link(srcpth, 'video')
#     asset_reldir = utils.relpath(asset_absdir, dstpth)
#     utils.copy(srcpth, os.path.join(asset_absdir, nowname))

#     # 写入文件
#     with open(dstpth, 'w', encoding='utf-8') as f:
#         f.write(utils.get_topinfo(comments=True) + '\n')
#         f.writelines(f'# {title}\n')
#         f.writelines(utils.get_filelink(srcpth) + '\n')

#         f.writelines('\n')
#         f.writelines('<video controls>\n')
#         f.writelines(f'<source src="{asset_reldir}/{nowname}" type="video/mp4">\n')
#         f.writelines('</video>\n')

#         # f.writelines('<!--\n') 
#         # f.writelines('    在 Mkdocs 中，HTML 和 Markdown 解析路径方式不一样，HTML 是从文件本身开始，而 Markdown 则要从当前目录开始。\n')
#         # f.writelines('    Python 的解析和 HTML 是一样的，由于这种不一致性，导致后续一些对资源的处理难度和繁琐程度大大加强。\n')
#         # f.writelines(f'    因此这里增加一个注释，便于后续处理: [WhatCanISay]({asset_reldir}/{nowname})\n')
#         # f.writelines('-->\n')


#     return dstpth


def do_code(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth  = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    suffix = os.path.splitext(nowname)[1].lower()

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'原始文件为 {suffix} 代码，本文是转换后的 Markdown 文件。\n\n')
        f.writelines(f'```{suffix}\n')
        with open(srcpth, 'r', encoding='utf-8') as srcf:
            content = srcf.readlines()
            f.writelines(content)
        f.writelines(f'```\n')

    return dstpth


def do_unknown(srcdir, dstdir, nowname, newname):
    srcpth = os.path.join(srcdir, nowname)
    dstpth = os.path.join(dstdir, f'{newname}.md')
    title = transform_name.remove_suffix(newname)

    # 写入文件
    with open(dstpth, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=True) + '\n')
        f.writelines(f'# {title}\n')
        f.writelines(utils.get_filelink(srcpth) + '\n')
        f.writelines(f'原始文件为 {srcpth}，未知文件类型。\n\n')

    return dstpth