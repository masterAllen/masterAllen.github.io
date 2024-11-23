# TODO: 文件名选择
import os
os.chdir(os.path.dirname(__file__))

import re
import pickle
import transform_name
import transform_file
import parse_navbar
import collections
import shutil
import json
import yaml

if __name__ == '__main__':
    srcdir = os.path.abspath('../done')
    dstdir = os.path.abspath(os.path.join('.', 'docs'))

    # dirnames 表示待处理的文件夹
    dirnames = collections.deque([])

    # 设置导航栏
    # 加载 topdir.yml 文件
    topdir_info = yaml.load(open('./topdir.yml', 'r', encoding='utf8'), Loader=yaml.FullLoader)
    topdir_main = topdir_info['main_dir']
    topdir_tabnames = {}
    for k, vs in topdir_info['other_dir'].items():
        # 这里是因为：如果发现某个文件夹专享一个标签栏，那标签栏里面就是其中子文件夹，而不是这个文件夹本身（否则要多点一步）
        if len(vs) == 1:
            topdir_tabnames[vs[0]] = '.'
        else:
            for v in vs:
                topdir_tabnames[v] = k

    # 遍历 src，通过 topdir 将里面的文件夹转换为 dst 中新的名字
    for nowsrc in os.listdir(srcdir):
        if not os.path.isdir(os.path.join(srcdir, nowsrc)):
            continue

        if nowsrc in topdir_tabnames:
            nowdst = os.path.join(dstdir, topdir_tabnames[nowsrc], nowsrc)
            os.makedirs(nowdst, exist_ok=True)
            dirnames.append((os.path.join(srcdir, nowsrc), nowdst))
        else:
            # 如果不在 topdir_tabnames 中，说明是主标签
            nowdst = os.path.join(dstdir, topdir_main, nowsrc)
            os.makedirs(nowdst, exist_ok=True)
            dirnames.append((os.path.join(srcdir, nowsrc), nowdst))

    # 再次遍历 src，只对里面的文件处理，把文件统一放在主导航栏所在的目录
    for nowsrc in os.listdir(srcdir):
        if not os.path.isdir(os.path.join(srcdir, nowsrc)):
            shutil.copy(os.path.join(srcdir, nowsrc), os.path.join(dstdir, topdir_main))
            continue


    # 最后还要在里面写一个 .pages 文件，用于指定导航栏顺序
    with open(os.path.join(dstdir, '.pages'), 'w', encoding='utf8') as f:
        f.writelines('nav: \n')
        f.writelines(f'  - {topdir_main}\n')
        for k in topdir_info['other_dir']:
            f.writelines(f'  - {k}\n')


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

    # 用于解析 windows 的文件
    import win32com.client 
    shell = win32com.client.Dispatch("WScript.Shell")

    # 专门为了 link 文件去解决
    link_files = []

    while len(dirnames):
        nowsrc, nowdst = dirnames.popleft()

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
            # print(nowname)

            newname = transform_name.remove_suffix(nowname)
            newname = transform_name.beautify_name(newname)
            if 'README' in newname:
                print(newname)

            # 如果是链接文件，那就什么都不做，直接返回一个文件名字，最后统一处理链接文件
            if nowname.endswith('.link') or nowname.endswith('.lnk'):
                link_files.append((nowsrc, nowdst, nowname))

            # 先根据时间，判断要不要更改
            nowpth = os.path.join(nowsrc, nowname)
            newtime = os.stat(nowpth).st_mtime
            newtimes[nowpth] = newtime

            # 如果没修改，那么就按照原来的搞；否则就继续处理
            if (nowpth in oldtimes and oldtimes[nowpth] == newtime):
                newfiles[nowpth] = oldfiles[nowpth]
                continue

            newfile = None
            if nowname.endswith('md'):
                newfile = transform_file.do_md(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('html') or nowname.endswith('htm'):
                newfile = transform_file.do_html(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('ipynb'):
                newfile = transform_file.do_ipynb(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('PNG') or nowname.endswith('png') or nowname.endswith('jpg'):
                newfile = transform_file.do_png(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('pdf'):
                newfile = transform_file.do_pdf(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('docx'):
                newfile = transform_file.do_word(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('pptx'):
                newfile = transform_file.do_ppt(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('txt'):
                newfile = transform_file.do_txt(nowsrc, nowdst, assetdir, nowname, newname)
            if nowname.endswith('.link') or nowname.endswith('.lnk'):
                newfile = os.path.join(dstdir, f'{newname}.md')

            newfiles[os.path.join(nowsrc, nowname)] = newfile


        # 检查文件夹里面有没有 .pages 文件，如果有则进行解析
        if '.pages' in os.listdir(nowsrc):
            pages_pth = os.path.join(nowsrc, '.pages')
            rules = parse_navbar.parse_rules(pages_pth)

            rules_file = open(os.path.join(nowdst, '.pages'), 'w', encoding='utf8')
            rules_file.writelines('nav: \n')
            rules_file.writelines('  - ...\n')

            # 遍历原始文件夹，如果该文件在目标文件夹有生成的文件，那么就处理一下
            srcpths = sorted(os.listdir(nowsrc))
            for srcpth in srcpths:
                srcpth = os.path.join(nowsrc, srcpth)
                if srcpth in newfiles:
                    dstpth = newfiles[srcpth]
                    src_basename = os.path.basename(srcpth)
                    dst_basename = os.path.basename(dstpth)
                    for rule_type, re_str in rules:
                        if re_str == '*' or re.match(re_str, src_basename) is not None:
                            src_basename = transform_name.remove_suffix(src_basename)
                            src_basename = transform_name.beautify_name(src_basename)
                            rules_file.writelines(f'  - {src_basename}: {dst_basename}\n')
            rules_file.writelines('order_by: title\n')

    # 处理 link 文件
    for nowsrc, nowdst, srcname in link_files:
        srcpth = os.path.join(nowsrc, srcname)
        linkpth = None

        # Windows 快捷方式
        if srcname.endswith('lnk'):
            shortcut = shell.CreateShortCut(srcpth)
            linkpth = shortcut.Targetpath
        # 个人的 link 文件
        elif srcname.endswith('link'):
            linkpth = open(srcpth, 'r', encoding='utf8').read().strip()
            linkpth = os.path.join(nowsrc, linkpth)
            linkpth = os.path.abspath(linkpth)
        # TODO Linux 软连接
        else:
            continue

        print('link file:', nowsrc, nowdst, srcname)

        # 查看源文件是否还存在 ...
        if linkpth not in newfiles:
            print('重大问题，请检查。链接文件不存在：', linkpth, srcpth)
            continue

        # 三种情况会处理：链接文件第一次出现、源文件第一次出现、源文件有改变
        if srcpth not in oldtimes or \
            linkpth not in oldtimes or \
             newtimes[linkpth] != oldtimes[linkpth]:

            # 如果源文件发生修改，那么复制粘贴
            newname = transform_name.beautify_name(transform_name.remove_suffix(srcname))
            shutil.copy(newfiles[linkpth], os.path.join(nowdst, f'{newname}.md'))

            print('link copy done')
            continue

    # 保存好各个文件的时间记录、对应生成的文件记录
    pickle.dump(newtimes, open('./oldtimes.bin', 'wb'))
    pickle.dump(newfiles, open('./oldfiles.bin', 'wb'))

    # 删除掉那些源文件不见的文件（也就是 oldtimes 有，但 newtimes 没有）
    print('删除文件................')
    removed_pths = set(oldtimes.keys()).difference(set(newtimes.keys()))
    for onepth in removed_pths:
        print(onepth, oldfiles[onepth])
        os.remove(oldfiles[onepth])

    # 遍历目标目录，删除空目录
    for root, dirs, files in os.walk(dstdir):
        for dir in dirs:
            if len(os.listdir(os.path.join(root, dir))) == 0:
                os.rmdir(os.path.join(root, dir))