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
            result['readme'] = utils.relpath(os.path.join(nowdir, md_name), rootdir)
            md_names.remove(md_name)

    # 如果有 .pages 文件，按照 .pages 文件的规则排序
    rules = parse_navbar.parse_rules(os.path.join(nowdir, '.pages'))

    # 获取文件标题
    md_titles = {}
    for md_name in md_names:
        # 获取文件标题
        title1 = utils.get_md_title(os.path.join(nowdir, md_name))

        # 获取文件名，转换后的都是 xx.png.md 这种格式，需要去掉两次后缀
        title2 = md_name
        title2 = transform_name.remove_suffix(title2)
        if utils.check_url_type(title2) == 'unknown':
            title2 = title2 + '.md'
        title2 = transform_name.beautify_name(title2)

        title = title1 if title1 is not None else title2
        for re_str in rules['title']:
            if re_str == '*' or re.match(re_str, md_name) is not None:
                title = title2
                break
        md_titles[md_name] = title

    # 检测标题冲突：统计每个标题出现的次数
    from collections import Counter
    title_counts = Counter(md_titles.values())
    
    # 对于出现多次的标题，给所有相关文件添加扩展名后缀
    duplicate_titles = {title for title, count in title_counts.items() if count > 1}
    if duplicate_titles:
        for md_name in list(md_titles.keys()):
            if md_titles[md_name] in duplicate_titles:
                # 提取原始文件的扩展名（去掉 .md 后的扩展名）
                base_name = transform_name.remove_suffix(md_name)
                ext = os.path.splitext(base_name)[1]
                md_titles[md_name] = f"{md_titles[md_name]}{ext}"

    # 先把 .pages 文件中规定的顺序的文件放进去
    ordered_files = {}
    for name in rules['order']:
        if name in md_titles:
            ordered_files[md_titles[name]] = utils.relpath(os.path.join(nowdir, name), rootdir)
            del md_titles[name]

    # 再把剩下的文件按标题排序
    md_titles = sorted(md_titles.items(), key=lambda x: x[0])
    for name, title in md_titles:
        ordered_files[title] = utils.relpath(os.path.join(nowdir, name), rootdir)
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

    # 如果 references 在 ordered_subdirs 中，那么把他放在最后
    for name in ordered_subdirs:
        if name.lower() == 'reference':
            ordered_subdirs.remove(name)
            ordered_subdirs.append(name)
            break

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