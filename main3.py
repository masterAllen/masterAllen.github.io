'''
生成侧边栏的索引
'''
import os
os.chdir(os.path.dirname(__file__))

import re
import yaml
import shutil
import utils
import parse_navbar
import transform_name
import settings

def traverse_dir(rootdir, nowdir):
    result = {}

    # 先处理文件
    md_names = {x for x in os.listdir(nowdir) if x.endswith('.md')}

    # 先找有没有 index
    result['readme'] = None
    old_md_names = md_names.copy()
    for md_name in old_md_names:
        if md_name.lower().startswith('index.md'):
            result['readme'] = os.path.relpath(os.path.join(nowdir, md_name), rootdir)
            md_names.remove(md_name)

    # 如果有 .pages 文件，按照 .pages 文件的规则排序
    rules = parse_navbar.parse_rules(os.path.join(nowdir, '.pages'))

    # 获取文件标题
    md_titles = {}
    for md_name in md_names:
        # 获取文件标题
        title1 = utils.get_md_title(os.path.join(nowdir, md_name))
        title2 = transform_name.beautify_name(transform_name.remove_suffix(md_name))

        title = title1 if title1 is not None else title2
        for re_str in rules['title']:
            if re_str == '*' or re.match(re_str, md_name) is not None:
                title = title2
                break
        md_titles[md_name] = title

    # 先把 .pages 文件中规定的顺序的文件放进去
    ordered_files = {}
    for name in rules['order']:
        if name in md_titles:
            ordered_files[md_titles[name]] = os.path.relpath(os.path.join(nowdir, name), rootdir)
            del md_titles[name]

    # 再把剩下的文件按标题排序
    md_titles = sorted(md_titles.items(), key=lambda x: x[0])
    for name, title in md_titles:
        mdpth = os.path.normpath(os.path.abspath(os.path.join(nowdir, name)))
        ordered_files[title] = os.path.relpath(os.path.join(nowdir, name), rootdir)
    result['mdfiles'] = ordered_files

    # 再处理文件夹
    subdirs = {x for x in os.listdir(nowdir) if os.path.isdir(os.path.join(nowdir, x))}

    # 还是一样，要排序
    ordered_subdirs = []
    for name in rules['order']:
        if name in subdirs:
            ordered_subdirs.append(name)
            subdirs.remove(name)
    subdirs = sorted(subdirs, key=lambda x: x.lower())
    ordered_subdirs.extend(subdirs)

    # 统计数量
    num = len(result['mdfiles']) + (result['readme'] is not None)

    # 按照顺序去处理子文件夹
    for subdir in ordered_subdirs:
        sub_result, sub_num = traverse_dir(rootdir, os.path.join(nowdir, subdir))
        num += sub_num
        if sub_num > 0:
            result[subdir] = sub_result

    return result, num

def print_one(rules, depth=1):
    result = ''
    if rules['readme'] is not None:
        result += ' ' * 4 * depth
        result += f'- {rules["readme"].replace('\\', '/')}\n'

    for key, value in rules['mdfiles'].items():
        result += ' ' * 4 * depth
        result += f'- "{key}": {value.replace('\\', '/')}\n'

    for key, value in rules.items():
        if key == 'readme' or key == 'mdfiles':
            continue
        result += ' ' * 4 * depth
        result += f'- "{key}":\n'
        result += print_one(value, depth + 1)
    return result

# 主程序
website_dir = settings.docsdir

result = {'readme': None, 'mdfiles': {}}

# 遍历程序
topdir_info = yaml.load(open(os.path.join(settings.config_dir, 'topdir.yml'), 'r', encoding='utf8'), Loader=yaml.FullLoader)
topdir_dirs = topdir_info['dirs']
for dirname in topdir_dirs:
    if os.path.exists(os.path.join(website_dir, dirname)):
        now_result, num = traverse_dir(website_dir, os.path.join(website_dir, dirname))
        result[dirname] = now_result


with open(os.path.join(settings.dstdir, 'mkdocs.yml'), 'r', encoding='utf8') as f:
    lines = f.readlines()

with open(os.path.join(settings.dstdir, 'mkdocs.yml'), 'w', encoding='utf8') as f:
    for line in lines:
        if 'nav:' in line:
            break
        f.write(line)
    f.write('nav:\n')
    f.write(print_one(result, 1))