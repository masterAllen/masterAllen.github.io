'''
生成所有文件后进行的处理，比如：
1. 看看链接是否失效了
2. 处理一些格式问题，以此来让 mkdocs material 正确渲染
'''
import os
os.chdir(os.path.dirname(__file__))

import re
import urllib.parse
import shutil
import utils
import settings
from pathlib import Path

# 分析链接文件的类型
def check_url_type(url):
    # 解析 URL
    parsed_url = urllib.parse.urlparse(url)

    # 如果是网页链接，跳过
    if parsed_url.scheme and parsed_url.scheme in ['http', 'https']:
        return 'web'
        
    # 如果是base64或data:image链接，跳过
    if 'base64' in url or url.startswith('data:image'):
        return 'base64'

    # 是否是图片
    suffix = os.path.splitext(url)[1].lower()
    image_extensions = {
        '.jpg', '.jpeg', '.png', '.gif', 
        '.bmp', '.webp', '.svg', '.webp'
    }
    if suffix in image_extensions:
        return 'image'

    # 是否是 HTML 文件
    if suffix in {'.html', '.htm'}:
        return 'html'

    # 是否是 PDF 文件
    if suffix in {'.pdf'}:
        return 'pdf'

    if suffix in {'.md', '.txt'}:
        return 'text'
    
    return 'unknown'


# 从文件内容中提取非网页链接，检查是否失效
def extract_links(content, webfile_pth, assetdir, raw2web_mapping, web2raw_mapping):
    rawfile_pth = web2raw_mapping.get(webfile_pth)

    text = open(webfile_pth, 'r', encoding='utf-8').read()

    # 匹配 Markdown 链接格式 [text](url)
    link_pattern = r'\[(.*?)\]\((.+?)\)'
    matches = re.finditer(link_pattern, text)

    # 每个元素：(old_link, new_link)
    result = []
    
    for match in matches:
        link_text = match.group(1)
        link_url = match.group(2)

        link_type = check_url_type(link_url)
        if link_type == 'web' or link_type == 'base64' or link_type == 'unknown':
            continue

        # 检查链接是否失效 --> 必须是相对路径
        link_url_abs = (Path(webfile_pth).parent / link_url).resolve()
        if os.path.isabs(link_url) or not link_url_abs.exists():
            # 链接失效 -> 寻找文件并且替换
            link_url_abs_inweb = link_url_abs
            link_url_abs = (Path(rawfile_pth).parent / link_url).resolve()

            if not link_url_abs.exists():
                # 原始文件中的链接有错，需要提醒用户
                print('----------链接失效----------')
                print(f'WEB 文件: {webfile_pth}')
                print(f'WEB 文件中链接内容: {link_url}')
                print(f'WEB 文件中链接指向的绝对路径: {link_url_abs_inweb}')

                print(f'没有找到这个文件，所以开始对原始文件进行解析')

                print(f'原始文件: {rawfile_pth}')
                print(f'原始文件中链接指向的绝对路径: {link_url_abs}')

                continue

            # 先查看是否在转换的这些文件中，这样说明这个文件可以在网页上跳转
            if link_url_abs in raw2web_mapping:
                pth2 = raw2web_mapping[link_url_abs] # 这个链接被转换后的路径
                pth1 = webfile_pth                   # 当前这个 MD 文件被转换后的路径

                link_relpth = os.path.relpath(pth2, os.path.dirname(pth1))
                link_relpth = link_relpth.replace('\\', '/')

                result.append((link_url, link_relpth))
                continue

            # 复制文件到 assetdir，首先需要先计算把这个文件复制到 assetdir 的哪个路径下
            asset_reldir = utils.asset_link(link_url_abs, assetdir, link_type)
            asset_absdir = (Path(link_url_abs).parent / asset_reldir).resolve()

            try:
                link_basename = os.path.basename(link_url)

                if link_type == 'text':
                    link_basename = f'{link_basename}.txt'

                # 复制文件到 assetdir 对应位置
                asset_absfile = asset_absdir / link_basename
                shutil.copy2(link_url_abs, asset_absfile)

                # 现在 webfile_pth 中的链接需要替换为 assetdir 中的相对路径
                asset_relto_webfile = os.path.relpath(asset_absfile, os.path.dirname(webfile_pth))
                asset_relto_webfile = asset_relto_webfile.replace('\\', '/')

                result.append((link_url, asset_relto_webfile))

            except Exception as e:
                print(f'复制文件失败 {link_url}: {str(e)}，源文件: {rawfile_pth}')
                exit(0)

    return result


def process_markdown_file(webfile_pth, assetdir, raw2web_mapping, web2raw_mapping):
    try:
        with open(webfile_pth, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 处理有序列表
        # content = utils.add_slash(content)

        # 2. 处理 details 标签 (<details> 转为 ???note)
        content = utils.process_details(content)

        # 3. 处理【】包起来的内容，转换为更醒目的格式
        content = utils.process_square_brackets(content)

        # 4. 检查是否有失效链接
        need_replaces = extract_links(content, webfile_pth, assetdir, raw2web_mapping, web2raw_mapping)
        # print(f'处理文件 {webfile_pth} 时需要替换 {len(need_replaces)} 个链接')
        for old_link, new_link in need_replaces:
            content = content.replace(old_link, new_link)

        # 5. 写回文件
        with open(webfile_pth, 'w', encoding='utf-8') as f:
            f.write(content)

        
    except Exception as e:
        print(f'处理文件 {webfile_pth} 时出错: {str(e)}')
        print(f'原始文件: {web2raw_mapping[webfile_pth]}')
        exit(0)

# 主程序
assetdir = settings.assetdir

# 用于记录文件路径的转换
import pickle
import configParser
config_parser = configParser.ConfigParser()
file_cache = config_parser.file_cache

raw2web_mapping = {k: v[1] for k, v in file_cache.items()}
web2raw_mapping = {v[1]: k for k, v in file_cache.items()}

# 遍历处理所有 Markdown 文件，检查链接是否有损伤
for root, dirs, files in os.walk(settings.docsdir):
    if 'asset' in root or 'code' in root or 'src' in root:
        continue

    for file in files:
        if file.endswith('.md'):
            webfile_pth = utils.abspath(os.path.join(root, file))
            process_markdown_file(webfile_pth, assetdir, raw2web_mapping, web2raw_mapping)

print('所有文件处理完成！')