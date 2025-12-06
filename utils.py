import hashlib
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
# 返回：生成 asset 的相对路径
def asset_link(filepth, assetdir, asset_type):
    assert(not os.path.isdir(filepth))

    filepth = os.path.normpath(os.path.abspath(filepth))

    # 根据生成的文件，生成 MD5，作为文件夹名
    file_md5 = hashlib.md5(filepth.encode()).hexdigest()
    now_assetdir = os.path.join(assetdir, asset_type, file_md5)
    os.makedirs(now_assetdir, exist_ok=True)

    # 生成相对路径
    relpth = os.path.relpath(now_assetdir, os.path.dirname(filepth))
    relpth = os.path.normpath(relpth).replace('\\', '/')

    return relpth


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