import re

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

def add_blank_before_list(text):
    """
    在非列表行后面紧跟列表时，自动插入空行，确保 MkDocs 正确渲染。
    """
    lines = text.split('\n')
    result = []
    in_code_block = False
    list_pattern = re.compile(r'^(\s*)([-*+]|\d+\.)\s')

    for i, line in enumerate(lines):
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        if not in_code_block and i > 0 and list_pattern.match(line):
            prev = lines[i - 1]
            if prev.strip() and not list_pattern.match(prev):
                result.append('')

        result.append(line)

    return '\n'.join(result)


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
