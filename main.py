# TODO: 文件名选择
import os
os.chdir(os.path.dirname(__file__))

import re
import pickle
import transform_name
import transform_file
import parse_navbar
import collections


if __name__ == '__main__':
    srcdir = os.path.abspath('../done')
    dstdir = os.path.abspath(os.path.join('.', 'docs'))

    # 文件绝对路径：时间信息
    oldtimes = dict() 
    if os.path.exists('./oldtimes.bin'):
        oldtimes = pickle.load(open('./oldtimes.bin', 'rb'))
    newtimes = dict()
    # 文件绝对路径：产生的文件路径
    oldfiles = dict() 
    if os.path.exists('./oldfiles.bin'):
        oldfiles = pickle.load(open('./oldfiles.bin', 'rb'))
    newfiles = dict()

    assetdir = os.path.join(dstdir, 'asset')
    os.makedirs(assetdir, exist_ok=True)
    for ftype in ['html', 'pdf', 'image']:
        os.makedirs(os.path.join(assetdir, ftype), exist_ok=True)

    dirnames = collections.deque([(srcdir, dstdir)])

    while len(dirnames):
        nowsrc, nowdst = dirnames.popleft()

        # 本目录生成的新文件
        nowdir_finalfiles = dict()

        # 先获取当前文件夹的子文件夹和子文件
        now_subdirs, now_subfiles = [], []
        for nowname in os.listdir(nowsrc):
            if nowname.startswith('~'):
                continue
            if nowname == '.pages':
                continue

            nowpth = os.path.join(nowsrc, nowname)
            if os.path.isdir(nowpth):
                now_subdirs.append(nowname)
            else:
                # 是文件，根据时间，判断要不要更改
                newtime = os.stat(nowpth).st_mtime
                newtimes[nowpth] = newtime
                if nowpth in oldtimes and oldtimes[nowpth] == newtime:
                    nowdir_finalfiles[nowpth] = oldfiles[nowpth]
                else:
                    now_subfiles.append(nowname)

        # 处理文件夹的内容
        for nowname in now_subdirs:
            if nowname == '材料' or nowname == 'references':
                # TODO: 如果是材料目录，那么就单独写一个 README，把这些文件都放进去
                pass
            elif nowname in ['src', 'code', 'asset']:
                # TODO: 如果是 src 目录，同样单独写一个 README，把这些文件都放进去

                # 1. 只会把文件放进去，如果是 markdown 那么就转为 html
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
                print(nowname)
                newname = transform_name.remove_suffix(nowname)
                newname = transform_name.beautify_name(newname)
                if 'README' in newname:
                    print(newname)
                #     newname = newname.replace('_', ':')

                newfile = None
                if nowname.endswith('md'):
                    newfile = transform_file.do_md(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('html') or nowname.endswith('htm'):
                    newfile = transform_file.do_html(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('ipynb'):
                    newfile = transform_file.do_ipynb(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('PNG') or nowname.endswith('png'):
                    newfile = transform_file.do_png(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('pdf'):
                    newfile = transform_file.do_pdf(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('docx'):
                    newfile = transform_file.do_word(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('pptx'):
                    newfile = transform_file.do_ppt(nowsrc, nowdst, assetdir, nowname, newname)
                if nowname.endswith('txt'):
                    print('txt', nowname)
                    newfile = transform_file.do_txt(nowsrc, nowdst, assetdir, nowname, newname)

                nowdir_finalfiles[os.path.join(nowsrc, nowname)] = newfile
            except Exception as e:
                print('nowsrc:', nowsrc)
                print('nowdst:', nowdst)
                print('subname:', nowname)
                print(e)
                print('-----------------------------')

        # 检查文件夹里面有没有 .pages 文件，如果有则进行解析
        # 遍历 nowdir_finalfiles，即生成的新文件，看看是否可以
        if '.pages' in os.listdir(nowsrc):
            pages_pth = os.path.join(nowsrc, '.pages')
            rules = parse_navbar.parse_rules(pages_pth)

            rules_file = open(os.path.join(nowdst, '.pages'), 'w', encoding='utf8')
            rules_file.writelines('nav: \n')
            rules_file.writelines('  - ...\n')
            srcpths = sorted(nowdir_finalfiles.keys())
            for srcpth in srcpths:
                dstpth = nowdir_finalfiles[srcpth]
                src_basename = os.path.basename(srcpth)
                dst_basename = os.path.basename(dstpth)
                for rule_type, re_str in rules:
                    if re_str == '*' or re.match(re_str, src_basename) is not None:
                        src_basename = transform_name.remove_suffix(src_basename)
                        src_basename = transform_name.beautify_name(src_basename)
                        rules_file.writelines(f'  - {src_basename}: {dst_basename}\n')
            rules_file.writelines('order_by: title\n')
        
        # 本次目标目录的文件也要放在总体的记录表中
        for srcpth, dstpth in nowdir_finalfiles.items():
            newfiles[srcpth] = dstpth


    # 保存好各个文件的时间记录、对应生成的文件记录
    pickle.dump(newtimes, open('./oldtimes.bin', 'wb'))
    pickle.dump(newfiles, open('./oldfiles.bin', 'wb'))

    # 删除掉那些源文件不见的文件（也就是 oldtimes 有，但 newtimes 没有）
    print('删除文件................')
    removed_pths = set(oldtimes.keys()).difference(set(newtimes.keys()))
    for onepth in removed_pths:
        print(onepth, oldfiles[onepth])
        os.remove(oldfiles[onepth])
