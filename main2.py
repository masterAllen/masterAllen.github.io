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


# 从文件内容中提取非网页链接，检查是否失效
def process_markdown_links(content, webfile_pth, raw2web_mapping, web2raw_mapping):
    rawfile_pth = web2raw_mapping.get(webfile_pth)

    # 每个元素：(start_pos, end_pos, new_link, old_link_url)
    # start_pos 和 end_pos 是链接 URL 部分在 content 中的位置
    result = []
    
    # 使用 utils.extract_links 提取所有链接及其位置信息
    matches = utils.extract_links(content, exclude=settings.skip_types)

    if rawfile_pth is None:
        if len(matches) > 0:
            print(f'在特殊文件 {webfile_pth} 中发现了链接，但原始文件不存在')
            print(f'链接: {matches}')
            print(f'--------------------------------')
        return []

    for url_start, url_end, link_url, is_html in matches:
        link_type = utils.check_url_type(link_url)
        if link_type in settings.skip_types:
            continue

        link_url_abs = (Path(webfile_pth).parent / link_url).resolve()

        # 如果是 HTML 链接，Mkdocs 的特性，渲染 HTML 是从当前文件（而不是所在目录）开始计算的
        if is_html:
            # 如果链接指向的文件存在，在前面加个 ../
            if link_url_abs.exists() and not os.path.isabs(link_url):
                new_link_url = '../' + link_url
                result.append((url_start, url_end, new_link_url, link_url))
                continue

            # 在前面减去 ../ 看看是否能访问到，能访问到说明是对的，是直接跳过就行
            temp_link_url = os.path.join(os.path.dirname(webfile_pth), link_url[3:])
            if os.path.exists(temp_link_url):
                continue

            # 如果 HTML 中是 /xx/yy.js 这种，也是忽略
            if link_url.startswith('/') and link_type == 'code':
                continue

        # 检查链接是否失效：如果是绝对路径，或者文件不存在，那么就说明链接失效
        if os.path.isabs(link_url) or not link_url_abs.exists():
            # 链接失效 -> 寻找文件并且替换
            link_url_abs_inweb = link_url_abs
            link_url_abs = utils.abspath((Path(rawfile_pth).parent / link_url).resolve())

            # 检查 asset 路径 --> 如链接的是 xx/yy.docx，就转成真正的资源文件
            # 此时 link_url_abs = src_file/xx/yy.docx，然后计算假设要把这个资源放在资源库的路径
            asset_absdir = utils.asset_link(link_url_abs, link_type, makedir=False)
            asset_absfile = utils.abspath(os.path.join(asset_absdir, os.path.basename(link_url)))

            r'''
            下面是三种可能：
            1. asset_absfile --> D:\Blog\目标生成目录\docs\asset\yy\zz.docx
                如果存在，那么说明这个资源文件在我们的资源库中，那我们把链接替换成转到资源库的路径
                UPDATE: 取消这个，还是直接跳转到对应的文件中去比较好
            2. link_url_abs --> D:\Blog\原始文件库\xx\yy\zz.docx
                必须要存在，否则原始文件里面的相对路径就是错的
                2.1 如果在 mapping 中，也就是这个文件我们转换过，那替换成转到我们转换的文件路径
                2.2 如果不再 mapping 中，那就把这个文件放在资料库中
            '''

            # # 如果 asset 资源存在，那么我们把文件链接改成资源文件链接就行
            # if os.path.exists(asset_absfile):
            #     pth2 = asset_absfile                 # 资源文件路径
            #     pth1 = webfile_pth                   # 当前这个 MD 文件被转换后的路径

            #     link_relpth = utils.relpath(pth2, pth1)
            #     if is_html:
            #         link_relpth = '../' + link_relpth

            #     result.append((link_url, link_relpth))
            #     continue

            # 原文件的链接不存在，说明原始文件中链接有错
            if not os.path.exists(link_url_abs):
                # 原始文件中的链接有错，需要提醒用户
                print('----------链接失效----------')
                print(f'WEB 文件: {webfile_pth}')
                print(f'WEB 文件中链接内容: {link_url}')
                print(f'WEB 文件中链接指向的绝对路径: {link_url_abs_inweb}')

                print(f'没有找到这个文件，所以开始对原始文件进行解析')

                print(f'原始文件: {rawfile_pth}')
                print(f'原始文件中链接指向的绝对路径: {link_url_abs}')
                print(f'解析的资源文件路径: {asset_absfile}')

                continue

            # 如果在转换的这些文件中，这样说明这个文件可以在网页上跳转
            if link_url_abs in raw2web_mapping:
                pth2 = raw2web_mapping[link_url_abs] # 这个链接被转换后的路径
                pth1 = webfile_pth                   # 当前这个 MD 文件被转换后的路径

                link_relpth = utils.relpath(pth2, pth1)
                if is_html:
                    link_relpth = '../' + link_relpth

                result.append((url_start, url_end, link_relpth, link_url))
                continue

            # 如果到这里，就说明原始文件有没有加入到 assetdir 的资源，比如 [xx](xx.png)
            # 复制这个资源文件到 assetdir

            try:
                if link_type == 'text':
                    asset_absfile = asset_absfile + '.txt'

                # 这里要也要防止复制过大文件
                # 复制文件到 assetdir 对应位置
                os.makedirs(asset_absdir, exist_ok=True)
                copy_success = utils.copy(link_url_abs, asset_absfile)

                # 现在 webfile_pth 中的链接需要替换为 assetdir 中的相对路径
                if copy_success:
                    asset_relto_webfile = utils.relpath(asset_absfile, webfile_pth)
                    if is_html:
                        asset_relto_webfile = '../' + asset_relto_webfile
                    result.append((url_start, url_end, asset_relto_webfile, link_url))
                else:
                    # 文件过大，保留链接格式但指向 #，并在文本中添加提示
                    # 标记这个链接需要特殊处理
                    webfile_name = os.path.basename(webfile_pth)
                    result.append((url_start, url_end, f'./{webfile_name} "文件过大，未上传"', link_url))

            except Exception as e:
                print(f'复制文件失败: {str(e)}')
                print(f'WEB 文件: {webfile_pth}')
                print(f'WEB 文件中链接内容: {link_url}')
                print(f'WEB 文件中链接指向的绝对路径: {link_url_abs_inweb}')

                print(f'没有找到这个文件，所以开始对原始文件进行解析')

                print(f'原始文件: {rawfile_pth}')
                print(f'原始文件中链接指向的绝对路径: {link_url_abs}')
                print(f'解析的资源文件路径: {asset_absfile}')
                exit(0)

    return result


def replace_arrow_safely(content):
    """
    将 -->、->、<--、<- 替换为箭头符号，但避免替换：
    1. HTML 注释 <!--...--> 中的内容
    2. 代码块 ```...``` 中的内容
    3. 行内代码 `...` 中的内容
    
    参数:
        content: Markdown 文件内容
    
    返回:
        替换后的内容
    """
    # 使用正则表达式匹配需要跳过的区域
    # HTML 注释 <!-- ... -->
    html_comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    # 代码块 ```...```
    code_block_pattern = re.compile(r'```[\s\S]*?```', re.DOTALL)
    # 行内代码 `...`（注意：不能匹配代码块中的反引号）
    # 使用负向前瞻/后顾来避免匹配代码块中的反引号
    inline_code_pattern = re.compile(r'`[^`\n]+`')
    
    # 找到所有需要跳过的区域
    skip_regions = []
    
    # 收集 HTML 注释
    for match in html_comment_pattern.finditer(content):
        skip_regions.append((match.start(), match.end(), 'html_comment'))
    
    # 收集代码块
    for match in code_block_pattern.finditer(content):
        skip_regions.append((match.start(), match.end(), 'code_block'))
    
    # 收集行内代码（需要排除已经在代码块中的）
    for match in inline_code_pattern.finditer(content):
        start, end = match.span()
        # 检查是否在代码块中
        in_code_block = False
        for cb_start, cb_end, _ in skip_regions:
            if cb_start <= start < cb_end:
                in_code_block = True
                break
        if not in_code_block:
            skip_regions.append((start, end, 'inline_code'))
    
    # 按起始位置排序
    skip_regions.sort(key=lambda x: x[0])
    
    # 如果没有需要跳过的区域，直接替换
    if not skip_regions:
        content = content.replace('-->', '→')
        content = content.replace('->', '→')
        content = content.replace('<--', '←')
        content = content.replace('<-', '←')
        return content
    
    # 分段处理：在跳过区域之外替换
    parts = []
    last_end = 0
    
    for start, end, region_type in skip_regions:
        # 添加跳过区域之前的部分（需要替换）
        before_region = content[last_end:start]
        # 先替换 -->，再替换 ->（避免重复替换）
        before_region = before_region.replace('-->', '→')
        before_region = before_region.replace('->', '→')
        before_region = before_region.replace('<--', '←')
        before_region = before_region.replace('<-', '←')
        parts.append(before_region)
        
        # 添加跳过区域本身（不替换）
        parts.append(content[start:end])
        
        last_end = end
    
    # 添加最后剩余的部分（需要替换）
    after_last_region = content[last_end:]
    after_last_region = after_last_region.replace('-->', '→')
    after_last_region = after_last_region.replace('->', '→')
    after_last_region = after_last_region.replace('<--', '←')
    after_last_region = after_last_region.replace('<-', '←')
    parts.append(after_last_region)
    
    return ''.join(parts)


def process_markdown_file(webfile_pth, raw2web_mapping, web2raw_mapping, is_replace=False):
    try:
        with open(webfile_pth, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. 处理有序列表
        # content = utils.add_slash(content)

        # 2. 处理 details 标签 (<details> 转为 ???note)
        content = utils.process_details(content)

        # 3. 处理【】包起来的内容，转换为更醒目的格式
        content = utils.process_square_brackets(content)

        # 4. 把 -> 替换成右箭头 →，但要注意 <!--...--> 这种注释不应该转换
        content = replace_arrow_safely(content)

        # 5. 检查是否有失效链接
        need_replaces = process_markdown_links(content, webfile_pth, raw2web_mapping, web2raw_mapping)
        # print(f'处理文件 {webfile_pth} 时需要替换 {len(need_replaces)} 个链接')
        
        # 按位置从后往前替换，避免位置偏移
        if is_replace:
            need_replaces.sort(key=lambda x: x[0], reverse=True)
            for url_start, url_end, new_link, old_link_url in need_replaces:
                content = content[:url_start] + new_link + content[url_end:]

        # 6. 写回文件
        with open(webfile_pth, 'w', encoding='utf-8') as f:
            f.write(content)

        
    except Exception as e:
        print(f'处理文件 {webfile_pth} 时出错: {str(e)}')
        print(f'原始文件: {web2raw_mapping[webfile_pth]}')
        exit(0)

# 用于记录文件路径的转换
import pickle
import config_parser
config_parser = config_parser.ConfigParser()
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
            process_markdown_file(webfile_pth, raw2web_mapping, web2raw_mapping, is_replace=False)

# 询问是否进行替换，只有回答y才进行替换，然后就在执行上面的操作就行
do_replace_input = input("是否进行替换？输入y进行替换，其它键跳过: ").strip().lower()
do_replace = do_replace_input == 'y'
if not do_replace:
    raise Exception("跳过替换操作，主动发生异常，防止调用该任务的程序继续执行其他任务")

# 再来一遍
for root, dirs, files in os.walk(settings.docsdir):
    if 'asset' in root or 'code' in root or 'src' in root:
        continue

    for file in files:
        if file.endswith('.md'):
            webfile_pth = utils.abspath(os.path.join(root, file))
            process_markdown_file(webfile_pth, raw2web_mapping, web2raw_mapping, is_replace=True)

print('所有文件处理完成！')