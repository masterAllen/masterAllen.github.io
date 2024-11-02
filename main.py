# TODO: 文件名选择
import os
os.chdir(os.path.dirname(__file__))

import transform_file
import collections


if __name__ == '__main__':
    srcdir = os.path.abspath('../done')
    dstdir = os.path.abspath(os.path.join('.', 'docs'))

    assetdir = os.path.join(dstdir, 'asset')
    os.makedirs(assetdir, exist_ok=True)
    for ftype in ['html', 'pdf', 'image']:
        os.makedirs(os.path.join(assetdir, ftype), exist_ok=True)

    dirnames = collections.deque([(srcdir, dstdir)])

    while len(dirnames):
        nowsrc, nowdst = dirnames.popleft()

        # 先获取当前文件夹的子文件夹和子文件
        now_subdirs, now_subfiles = [], []
        for nowname in os.listdir(nowsrc):
            if nowname.startswith('~'):
                continue

            nowpth = os.path.join(nowsrc, nowname)
            if os.path.isdir(nowpth):
                now_subdirs.append(nowname)
            else:
                now_subfiles.append(nowname)

        # 处理文件夹的内容
        for nowname in now_subdirs:
            if nowname == '材料' or nowname == 'references':
                # TODO: 如果是材料目录，那么就单独写一个 README，把这些文件都放进去
                pass
            elif nowname == 'src' or nowname == 'code':
                # TODO: 如果是 src 目录，同样单独写一个 README，把这些文件都放进去
                pass
            elif nowname.startswith('image'):
                continue
            else:
                newsrc = os.path.join(nowsrc, nowname)
                newdst = os.path.join(nowdst, nowname)
                os.makedirs(newdst, exist_ok=True)
                dirnames.append((newsrc, newdst))

        # 处理文件的内容
        for nowname in now_subfiles:
            try:
                # TODO: 如果是 .pages，那么就要解析
                if nowname[0:5] == '.page':
                    continue
                if nowname.endswith('md'):
                    transform_file.do_md(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('html') or nowname.endswith('htm'):
                    transform_file.do_html(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('ipynb'):
                    transform_file.do_ipynb(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('PNG') or nowname.endswith('png'):
                    transform_file.do_png(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('pdf'):
                    transform_file.do_pdf(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('docx'):
                    transform_file.do_word(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('pptx'):
                    transform_file.do_ppt(nowsrc, nowdst, assetdir, nowname)
                if nowname.endswith('txt'):
                    transform_file.do_txt(nowsrc, nowdst, assetdir, nowname)
            except Exception as e:
                print('nowsrc:', nowsrc)
                print('nowdst:', nowdst)
                print('subname:', nowname)
                print(e)
                print('-----------------------------')
                pass