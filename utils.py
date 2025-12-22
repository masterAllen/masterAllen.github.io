import hashlib
import shutil
import os
import re
from pathlib import Path
import settings

'''
文件一开始添加相关信息，比如是否注释等，是否隐藏 toc 等
'''
def get_topinfo(comments=True, hide=[]):
    result = ''
    if not comments and len(hide) == 0:
        return result

    result += '---\n'
    if comments:
        result += 'comments: true\n'
    if len(hide) > 0:
        result += 'hide: true\n'
        for h in hide:
            result += f'  - {h}\n'
    result += '---\n'
    return result

'''
添加可以用于修改的链接，最终效果如下：
复制本地路径 | 在线编辑
'''
def get_filelink(filepth):
    abs_filepth = Path(filepth).resolve()
    link1 = f'<span class="file-action-link" style="cursor: pointer;" data-copy="{abs_filepth}">复制本地路径</span>'

    rel_filepth = Path(filepth).relative_to(settings.srcdir)
    rel_filepth = str(rel_filepth).replace('\\', '/')
    link2 = f'<a href="https://github.com/masterAllen/BlogRawData/edit/main/{rel_filepth}" class="file-action-link">在线编辑</a>'
    return f'<div class="file-actions" data-title-link="true">{link1} | {link2}</div>\n'

# filepth: 生成的文件路径；asset_type: 文件类型
# 返回：生成 asset 的绝对路径、相对 dir(filepth) 的路径
def asset_link(asset_src, asset_type, makedir=True):
    assert(not os.path.isdir(asset_src))

    asset_src_dir = abspath(os.path.dirname(asset_src))

    # 根据生成的文件，生成 MD5，作为文件夹名
    file_md5 = hashlib.md5(asset_src_dir.encode()).hexdigest()
    now_assetdir = abspath(os.path.join(settings.assetdir, asset_type, file_md5))

    if makedir:
        # print(f'创建 asset 目录: {now_assetdir}')
        os.makedirs(now_assetdir, exist_ok=True)

    return now_assetdir


def make_filetree(path):
    result = ''
    result += '原文是文件夹，下面是文件夹结构。\n\n'
    result += '```markup \n'

    stack = [(path, 0)]  # 初始化栈，存储的是 (目录路径, 当前缩进级别)
    while stack:
        current_path, indent = stack.pop()  # 获取当前目录路径和缩进级别
        result += (" " * indent + "- " + os.path.basename(current_path) + "\n")  # 打印当前目录
        
        # 获取当前目录中的文件和子目录
        items = os.listdir(current_path)
        
        # 先将子目录加入栈，以便后续遍历
        for item in items:
            full_path = os.path.join(current_path, item)
            if os.path.isdir(full_path):
                stack.append((full_path, indent + 2))  # 子目录缩进 +1
            else:
                # 打印文件名，缩进 +1（因为文件在当前目录下）
                result += (" " * (indent + 2) + "- " + item + '\n')

    result += '``` \n'
    return result

def get_md_title(pth):
    with open(pth, 'r', encoding='utf8') as f:
        for line in f:
            if line.startswith('# '):
                return line[2:].strip()
    return None

# 改变有序列表
def add_slash(text):
    # 匹配有序列表模式，如 "1. " 或 "  1. "
    pattern = r'( *[\d+]\. )'
    
    # 存储需要添加换行符的位置
    newlines = []
    
    # 在有序列表后如果是无序列表（以 "-" 开头）时添加换行符
    for m in re.finditer(pattern, text):
        lo, hi = m.span()
        pos1 = text.find('\n', hi)
        pos2 = text.find('\n', pos1+1)
        if pos1 != -1 and pos2 != -1 and text[pos1+1:pos2].strip().startswith('-'):
            newlines.append(pos1)
    
    for idx, pos in enumerate(newlines):
        text = text[:pos+idx] + '\n' + text[pos+idx:]
    
    # 替换有序列表为带反斜杠的格式
    text = re.sub(pattern, lambda m: m.group(1).replace('.', '\\.'), text)
    
    return text

# 将原始文件中的 <details> 改为 ??? note
def process_details(text):
    # 使用正则表达式匹配 <details> 标签及其内容
    pattern = r'<details>\s*<summary>(.*?)</summary>\s*(.*?)</details>'
    
    # 查找所有匹配项
    matches = re.finditer(pattern, text, re.DOTALL)

    offset = 0
    result = str(text)
    for match in matches:
        lo, hi = match.span()
        if text[lo-1] == '`':
            continue
        
        title = match.group(1).strip()
        details_content = match.group(2).strip()
        
        # 为内容每行添加四个空格
        indented_content = '\n'.join('    ' + line for line in details_content.split('\n'))
        
        # 构建新的格式
        new_format = f'??? note "{title}"\n\n{indented_content}\n'
        
        # 替换原内容
        lo, hi = lo+offset, hi+offset
        result = result[:lo] + new_format + result[hi:]

        # 更新偏移量
        offset += len(new_format) - (hi - lo)
    
    return result

def process_square_brackets(text):
    """
    将【】包起来的内容转换为更醒目的 HTML 格式
    例如：【重定位】 -> <mark class="term-highlight">重定位</mark>
    注意：不会替换代码块中的【】
    """
    # 匹配【】中的内容
    pattern = r'【([^】]+)】'
    
    def replace_func(match):
        content = match.group(1)
        # 转换为 HTML mark 标签，并添加自定义 class
        return f'<mark class="term-highlight">{content}</mark>'
    
    # 分割文本为代码块和非代码块部分
    parts = []
    last_end = 0
    
    # 匹配代码块（```代码块```和`行内代码`）
    code_block_pattern = r'```[\s\S]*?```|`[^`\n]+`'
    
    for code_match in re.finditer(code_block_pattern, text):
        code_start, code_end = code_match.span()
        
        # 添加代码块之前的内容（需要处理【】）
        before_code = text[last_end:code_start]
        before_code = re.sub(pattern, replace_func, before_code)
        parts.append(before_code)
        
        # 添加代码块本身（不处理）
        parts.append(text[code_start:code_end])
        last_end = code_end
    
    # 处理最后剩余的内容
    remaining = text[last_end:]
    remaining = re.sub(pattern, replace_func, remaining)
    parts.append(remaining)
    
    return ''.join(parts)

def abspath(pth):
    result = os.path.abspath(pth)
    result = result[0].upper() + result[1:]
    return result

def relpath(pth1, pth2):
    if os.path.isfile(pth2):
        pth2 = os.path.dirname(pth2)
    result = os.path.relpath(pth1, pth2)
    result = result.replace('\\', '/')
    return result

# 匹配 Markdown 链接格式 [text](url)
def extract_links(content, exclude={}):
    """
    提取内容中的所有链接
    参数:
        content: 要提取链接的内容
    返回: [(url_start, url_end, link_url, is_html), ...]
        - url_start: URL 开始位置（`(` 之后）
        - url_end: URL 结束位置（`)` 之前）
        - link_url: 链接 URL
        - is_html: 是否是 HTML 链接
    """
    # 原来的实现：使用 markdown 和 lxml 解析，但无法处理 ??? 等扩展语法
    # import markdown
    # from lxml import etree
    # html_content = markdown.markdown(content)
    # # 使用 etree.HTML() 而不是 etree.fromstring()，因为 HTML 可能不是有效的 XML
    # doc = etree.HTML(html_content)
    # matches = []
    # if doc is not None:
    #     for link in doc.xpath('//a'):
    #         link_url = link.get('href')
    #         matches.append(link_url)
    # return matches
    
    # 新实现：使用正则表达式提取 markdown 链接，这样不受 ??? 等扩展语法影响
    # link_pattern = r'\[(.*?)\]\((.+?)\)'  # 简单版本，不支持嵌套括号
    # link_pattern = r'\[(.*?)\]\(([^()\s]+(?:\([^()]*\)[^()\s]*)*)\)'  # 支持嵌套括号的版本
    
    # matches = []
    # for match in re.finditer(link_pattern, content):
    #     link_url = match.group(2)  # 获取链接 URL（第二个捕获组）
    #     matches.append(link_url)

    # 最终：支持包含空格和括号的链接，使用栈算法处理嵌套括号
    matches = []
    
    # 找到所有 [text]( 的位置（Markdown 链接）
    pattern = r'\[([^\]]*)\]\('
    for match in re.finditer(pattern, content):
        url_start = match.end()  # `(` 的位置
        
        # 从 `(` 开始，使用栈来找到匹配的 `)`
        depth = 1
        pos = url_start
        url_end = -1
        
        while pos < len(content) and depth > 0:
            if content[pos] == '(':
                depth += 1
            elif content[pos] == ')':
                depth -= 1
                if depth == 0:
                    url_end = pos
                    break
            pos += 1
        
        if url_end < 0:
            continue
        
        # 提取链接 URL
        link_url = content[url_start:url_end].strip()
        # 如果链接被引号包裹，去除引号
        if (len(link_url) >= 2 and link_url.startswith('"') and link_url.endswith('"')) or \
           (len(link_url) >= 2 and link_url.startswith("'") and link_url.endswith("'")):
            link_url = link_url[1:-1]
        
        matches.append((url_start, url_end, link_url, False))

    # 找到所有 HTML 属性中的链接（src= 或 href=）
    html_pattern = re.compile(
        r'''(?i)(?:src|href)=(".*?"|'.*?')'''
    )
    for match in html_pattern.finditer(content):
        url_start = match.start(1)  # 引号开始位置
        url_end = match.end(1)  # 引号结束位置
        url = match.group(1)
        # 去掉首尾的引号
        if (url.startswith('"') and url.endswith('"')) or (url.startswith("'") and url.endswith("'")):
            url = url[1:-1]
            url_start += 1  # 调整位置，排除引号
            url_end -= 1
        
        matches.append((url_start, url_end, url, True))

    new_matches = []
    for match in matches:
        link_type = check_url_type(match[2])
        if link_type not in exclude:
            new_matches.append(match)

    return new_matches

# 分析链接文件的类型
def check_url_type(url):
    import urllib.parse
    # 解析 URL
    parsed_url = urllib.parse.urlparse(url)

    # 如果是网页链接，跳过
    if parsed_url.scheme and parsed_url.scheme in ['http', 'https']:
        return 'web'
        
    # 如果是base64或data:image链接，跳过
    if 'base64' in url or url.startswith('data:image'):
        return 'base64'

    if url.endswith('doc') or url.endswith('docx'):
        return 'word'
    if url.endswith('ppt') or url.endswith('pptx'):
        return 'ppt'

    # 是否是图片
    suffix = os.path.splitext(url)[1].lower()

    code_extensions = {
        '.py', '.cpp', '.h', '.hpp', '.c', '.js'
    }
    if suffix in code_extensions:
        return 'code'

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

    # 是否是视频文件
    video_extensions = {'.mp4', '.flv', '.avi', '.mkv'}
    if suffix in video_extensions:
        return 'video'
    
    return 'unknown'

# 复制文件，可以在这里检查文件大小，防止复制大文件
def copy(src, dst):
    maxsize = settings.MAX_FILE_SIZE

    if os.path.isdir(src):
        os.makedirs(dst, exist_ok=True)
        # 遍历源目录
        for root, dirs, files in os.walk(src):
            # 计算相对路径
            rel_path = os.path.relpath(root, src)
            if rel_path == '.':
                dst_root = dst
            else:
                dst_root = os.path.join(dst, rel_path)
            
            # 创建子目录
            for dir_name in dirs:
                os.makedirs(os.path.join(dst_root, dir_name), exist_ok=True)
            
            # 复制文件
            for file_name in files:
                src_file = os.path.join(root, file_name)
                dst_file = os.path.join(dst_root, file_name)
                
                if os.path.getsize(src_file) < maxsize:
                    shutil.copy2(src_file, dst_file)
        return True

    if os.path.getsize(src) > maxsize:
        print(f'文件大小超过 10MB，跳过复制: {src}')
        return False
    
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True