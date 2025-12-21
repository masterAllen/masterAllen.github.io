# TODO: 文件名选择
import os
os.chdir(os.path.dirname(__file__))

import pathlib
import winshell

import re
import pickle
import transform_name
import transform_file
import collections
import shutil
import json
import yaml

import utils
import settings
from configParser import ConfigParser

if __name__ == '__main__':
    srcdir = utils.abspath(settings.srcdir)
    dstdir = utils.abspath(settings.docsdir)

    # 记录所有 mp4 文件
    mp4_files = open(os.path.join(settings.config_dir, 'mp4.txt'), 'w', encoding='utf8')
    big_files = open(os.path.join(settings.config_dir, 'big_files.txt'), 'w', encoding='utf8')

    # 加载 Special 文件，这些文件不在 main 中处理，使用对应的文件进行处理
    raw_specials = yaml.load(open(os.path.join(settings.config_dir, 'special.yml'), 'r', encoding='utf8'), Loader=yaml.FullLoader)
    specials = {}
    if raw_specials:  # 处理 YAML 文件为空或只有注释的情况
        for rel_src, rel_py in raw_specials.items():
            abs_src = utils.abspath(os.path.join(srcdir, rel_src))
            abs_py = utils.abspath(os.path.join('.', rel_py))
            specials[abs_src] = {'py': abs_py, 'dsts': None}

    assert all([os.path.exists(k) for k in specials.keys()])
    assert all([os.path.exists(v['py']) for v in specials.values()])

    configs = ConfigParser()

    # dirnames 表示待处理的文件/文件夹
    todos = collections.deque([])

    # 设置导航栏
    # 加载 topdir.yml 文件 --> 读取哪些文件夹要处理
    topdir_info = yaml.load(open(os.path.join(settings.config_dir, 'topdir.yml'), 'r', encoding='utf8'), Loader=yaml.FullLoader)
    topdir_dirs = topdir_info['dirs']
    for dirname in topdir_dirs:
        todos.append((os.path.join(srcdir, dirname), os.path.join(dstdir, dirname)))

    # 首页单独更新
    srcpth = os.path.join(srcdir, 'index.md')
    dstpth = os.path.join(dstdir, 'index.md')
    with open(dstpth, 'w', encoding='utf8') as f:
        f.write(utils.get_topinfo(comments=True, hide=['navigation']) + '\n')
        with open(srcpth, 'r', encoding='utf8') as srcf:
            f.write(srcf.read())
    configs.update_cache(srcpth, dstpth, os.stat(srcpth).st_mtime)

    # 需要处理的链接文件
    link_files = []

    # 接下来会处理的文件
    changed_files = []

    while len(todos):
        nowsrc, nowdst = todos.popleft()

        if os.path.isdir(nowsrc):
            is_special_dir = False
            
            # 如果是文件夹，那么先处理一些特殊的文件夹
            nowname = os.path.basename(nowsrc)
            for special_dirname in settings.special_dirs:
                if nowname.startswith(special_dirname):
                    # TODO: 如果目录名称是材料、papers 等，那么就单独写一个 README，把这些文件列出来，是否要展示：先不进行展示

                    # 结构: Reference/xxx.md
                    nowdst = utils.abspath(os.path.join(nowdst, '..', 'Reference', f'{nowname}.md'))
                    configs.process_if_needed(nowsrc, nowdst, lambda src, dst: transform_file.do_special_dir(src, dst))
                    is_special_dir = True
                    break

            if nowname.startswith('image'):
                # print(nowsrc)
                is_special_dir = True

            if is_special_dir:
                continue

            os.makedirs(nowdst, exist_ok=True)

            # 如果是文件夹，那么先获取当前文件夹的子文件夹或者子文件，根据情况添加到 todos 中
            now_subdirs, now_subfiles = [], []
            for nowname in os.listdir(nowsrc):
                # 如果里面有 '#不上传'，那么就跳过
                if '#不上传' in nowname:
                    srcfpath = utils.abspath(os.path.join(nowsrc, nowname))
                    nowname = nowname[0:nowname.find('#不上传')]
                    dstfpath = utils.abspath(os.path.join(nowdst, f'{nowname}.md'))
                    with open(dstfpath, 'w', encoding='utf8') as f:
                        f.writelines(f'# {nowname}\n')
                        f.writelines('本文件涉及隐私，不上传，谢谢\n')
                    configs.update_cache(srcfpath, dstfpath, os.stat(srcfpath).st_mtime)
                    continue

                # 如果是 zip 文件，就说明这是 zip 文件
                if nowname.endswith('zip'):
                    srcfpath = utils.abspath(os.path.join(nowsrc, nowname))
                    nowname = nowname[0:nowname.find('.zip')]
                    dstfpath = utils.abspath(os.path.join(nowdst, f'{nowname}.md'))
                    with open(dstfpath, 'w', encoding='utf8') as f:
                        f.writelines(f'# {nowname}\n')
                        f.writelines('源文件为 ZIP 文件，不上传\n')
                    configs.update_cache(srcfpath, dstfpath, os.stat(srcfpath).st_mtime)
                    continue

                # 如果是单独处理的文件夹，跳过去
                newdst = utils.abspath(os.path.join(nowdst, nowname))
                newsrc = utils.abspath(os.path.join(nowsrc, nowname))
                if newsrc in specials:
                    print(f'special: {newsrc} -> {newdst}')
                    specials[newsrc]['dsts'] = utils.abspath(newdst)
                    continue

                todos.append((newsrc, newdst))
                continue

        if os.path.isfile(nowsrc):
            nowname = os.path.basename(nowsrc)

            if nowname.startswith('~'):
                continue

            file_type = utils.check_url_type(nowname)

            '''
            特殊文件
            1. link 文件实现存储，到最后统一处理
            '''
            if nowname.endswith('link') or nowname.endswith('lnk'):
                link_files.append((nowsrc, os.path.dirname(nowdst)))

            '''
            临时 Debug 区域
            '''
            # 先根据时间，判断要不要更改；如果没修改，那么就按照原来的搞；否则就继续处理
            # if (not nowname.endswith('md')) and (not nowname.endswith('mp4')):
            # if True:
            # if (file_type == 'html') or (file_type == 'word') or (file_type == 'ppt') or (file_type == 'image'):
            # if (file_type == 'word') or (file_type == 'ppt') or (file_type == 'image'):
            if (file_type == 'word') or (file_type == 'image'):
                if not configs.is_need_update(nowsrc):
                    configs.update_cache_byold(nowsrc)
                    continue

            # TODO: 这里需要修改地更好
            nowsrc_dir, nowdst_dir = os.path.dirname(nowsrc), os.path.dirname(nowdst)

            newname = nowname
            # 统一不去后缀了，避免重名
            # newname = transform_name.remove_suffix(nowname) 
            newname = transform_name.beautify_name(newname)

            # 检查文件是否超过大小，如果超过，则直接转成说明的文件
            file_size = os.path.getsize(nowsrc)
            if file_size > settings.MAX_FILE_SIZE:
                web_file_abs = transform_file.do_file_too_large(nowsrc_dir, nowdst_dir, nowname, newname, file_type)
                big_files.write(f'{nowsrc}\n')
            else:
                web_file_abs = None
                
            if web_file_abs is None:
                # 正常处理文件
                if nowname.endswith('md'):
                    web_file_abs = transform_file.do_md(nowsrc_dir, nowdst_dir, nowname, newname)
                if nowname.endswith('txt'):
                    web_file_abs = transform_file.do_txt(nowsrc_dir, nowdst_dir, nowname, newname)
                if nowname.endswith('ipynb'):
                    web_file_abs = transform_file.do_ipynb(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'html':
                    web_file_abs = transform_file.do_html(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'image':
                    web_file_abs = transform_file.do_png(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'pdf':
                    web_file_abs = transform_file.do_pdf(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'word':
                    web_file_abs = transform_file.do_word(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'ppt':
                    web_file_abs = transform_file.do_ppt(nowsrc_dir, nowdst_dir, nowname, newname)
                if file_type == 'video':
                    web_file_abs = transform_file.do_video(nowsrc_dir, nowdst_dir, nowname, newname)
                if nowname == '.pages':
                    # 如果是 .pages 文件，如果有以后会用到，需要复制过去
                    utils.copy(nowsrc, nowdst)
                    web_file_abs = nowdst

            # 生成结果后，保存到 cache 中
            if web_file_abs is not None:
                # 检查是否是 README，如果是的话，替换成 index.md
                if os.path.basename(web_file_abs).lower() == 'readme.md':
                    new_web_file_abs = os.path.join(os.path.dirname(web_file_abs), 'index.md')
                    shutil.move(web_file_abs, new_web_file_abs)
                    web_file_abs = new_web_file_abs

                changed_files.append((nowsrc, web_file_abs))

    # 更新 cache
    for raw_file_abs, web_file_abs in changed_files:
        # print(f'Raw: {raw_file_abs}; Web: {web_file_abs}')
        configs.update_cache(raw_file_abs, web_file_abs, os.stat(raw_file_abs).st_mtime)

    # 处理 link 文件，格式: [链接文件原始路径，应该生成的文件所在目录]
    for link_src_path, link_dst_dir in link_files:
        # link 文件特殊点：既要看 **当前链接文件** 是否有更新，也要看 **原始文件** 是否更新
        source_raw_path = utils.abspath(winshell.shortcut(link_src_path).path)

        if configs.is_need_update(source_raw_path) or configs.is_need_update(link_src_path):
            # 需要更新：把 **原始文件对应的 WEB 文件** 直接复制到想要的位置去
            source_web_path = configs.get_web_path(source_raw_path)
            link_web_path = os.path.join(link_dst_dir, os.path.basename(source_web_path))
            utils.copy(source_web_path, link_web_path)

            # 把这个链接文件复制到目标目录即可
            print('----------更新链接文件----------')
            print(f'原始链接文件: {link_src_path}, 原始文件: {source_raw_path}')
            print(f'复制链接文件: {source_web_path} -> {link_web_path}')
            configs.update_cache(link_src_path, link_web_path, os.stat(link_src_path).st_mtime)
        else:
            configs.update_cache_byold(link_src_path)


    # 处理 Special 文件
    import importlib.util
    for nowsrc, info in specials.items():
        pyfile = info['py']
        dst = info['dsts']
        if not dst:
            print(f'warning: special {nowsrc} 未匹配到目标目录，跳过')
            continue

        name = os.path.basename(pyfile)[:-3]
        module = importlib.import_module(f"{name}")
        if not hasattr(module, "run"):
            raise AttributeError(f"{name}.py does not have a 'run' function")

        # print(f'RUN {pyfile}, nowsrc={nowsrc}, nowdst={dst}')
        module.run(nowsrc, dst, configs)

    '''
    处理缓存文件
    '''
    configs.save_cache() # 保存 cache
