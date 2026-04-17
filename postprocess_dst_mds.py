"""
生成后的 Markdown 格式后处理
列表前空行、<details>→admonition、【】高亮、安全替换箭头。
"""
import os
import re

os.chdir(os.path.dirname(__file__))

import settings
import utils


def add_blank_before_list(text):
    """
    智能补列表空行：检测到列表衔接不规范时自动插入空行。
    支持无序/有序列表混排，包括 `1. 2. 3.` 与 `1. xx:` 后接子列表等场景。
    """
    lines = text.split('\n')
    result = []
    in_code_block = False
    list_pattern = re.compile(r'^(\s*)([-*+]|\d+[.)])(?:\s+.*)?$')

    def parse_list_info(line):
        match = list_pattern.match(line)
        if not match:
            return None
        indent = len(match.group(1))
        marker = match.group(2)
        list_type = 'ordered' if re.match(r'^\d+[.)]$', marker) else 'unordered'
        return indent, list_type

    def get_last_nonempty_line(out_lines):
        for now_line in reversed(out_lines):
            if now_line.strip():
                return now_line
        return ''

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block

        if not in_code_block and i > 0 and stripped:
            current_info = parse_list_info(line)
            prev_line = get_last_nonempty_line(result)
            prev_stripped = prev_line.strip()
            prev_info = parse_list_info(prev_line) if prev_stripped else None

            # 规范嵌套列表缩进：子列表统一为父级 +4 空格
            if current_info is not None and prev_info is not None:
                cur_indent, cur_type = current_info
                prev_indent, prev_type = prev_info

                fixed_to = None
                if cur_type == prev_type and cur_indent != prev_indent:
                    # 同类型连续列表项：对齐到上一项缩进（修复 1/2/3 或 */* 的错位）
                    fixed_to = prev_indent
                elif prev_indent < cur_indent < prev_indent + 4:
                    # 新子列表：统一提升到父级 +4
                    fixed_to = prev_indent + 4

                if fixed_to is not None:
                    fixed_indent = ' ' * fixed_to
                    line = fixed_indent + line.lstrip(' ')
                    current_info = parse_list_info(line)

            should_insert = False
            if current_info is not None and prev_stripped:
                if prev_info is None:
                    # 普通段落/标题后直接进入列表
                    should_insert = True
                else:
                    # 列表与列表之间：层级变化或类型变化时补空行
                    cur_indent, cur_type = current_info
                    prev_indent, prev_type = prev_info
                    if cur_indent != prev_indent or cur_type != prev_type:
                        should_insert = True

            if should_insert:
                # 使用当前行的缩进补空行，避免在 admonition/note 内掉级
                if not result or result[-1].strip() != '':
                    current_indent = len(line) - len(line.lstrip(' '))
                    result.append(' ' * current_indent)

        result.append(line)

    return '\n'.join(result)


def process_question_sections(text):
    """
    将二级标题 `## <!--question--> xxx` 转为 question + note 的 admonition 结构。
    仅处理普通文本区域，跳过代码块中的内容。
    """
    lines = text.split('\n')
    result = []
    i = 0
    in_code_block = False
    has_question_section = False

    question_heading_pattern = re.compile(r'^##\s*<!--question-->\s*(.*?)\s*$')
    generic_heading_pattern = re.compile(r'^(#{1,6})\s+')

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            in_code_block = not in_code_block

        heading_match = question_heading_pattern.match(line)
        if in_code_block or heading_match is None:
            result.append(line)
            i += 1
            continue

        has_question_section = True

        question_title = heading_match.group(1).strip()

        # 收集当前二级标题的章节内容：直到下一个 <= 二级标题
        body_lines = []
        j = i + 1
        body_in_code_block = False
        while j < len(lines):
            now_line = lines[j]
            if now_line.strip().startswith('```'):
                body_in_code_block = not body_in_code_block

            next_heading = generic_heading_pattern.match(now_line)
            if (not body_in_code_block) and next_heading and len(next_heading.group(1)) <= 2:
                break

            body_lines.append(now_line)
            j += 1

        # 去掉章节首尾空行，避免生成块过于松散
        while body_lines and body_lines[0].strip() == '':
            body_lines.pop(0)
        while body_lines and body_lines[-1].strip() == '':
            body_lines.pop()

        result.append('!!! question ""')
        result.append('')
        result.append(f'    {question_title}')
        result.append('')
        result.append('???+ abstract "answer"')
        result.append('')
        if body_lines:
            for body_line in body_lines:
                result.append(f'    {body_line}')

        # result.append('')
        # result.append(f'## answer')
        # result.append('')
        # if body_lines:
        #     for body_line in body_lines:
        #         result.append(f'{body_line}')

        # 块结束后补一个空行，避免与后续标题/段落粘连
        result.append('')

        i = j

    return '\n'.join(result), has_question_section


def ensure_toc_hidden(text):
    """
    为 Markdown 文件补充/合并 front matter，确保隐藏 toc。
    """
    if re.match(r'^---\n', text) is None:
        return f'---\nhide: true\n  - toc\n---\n\n{text}'

    match = re.match(r'^(---\n)(.*?)(\n---\n?)', text, re.DOTALL)
    if match is None:
        return f'---\nhide: true\n  - toc\n---\n\n{text}'

    prefix, front_matter, suffix = match.groups()
    if re.search(r'^\s*-\s*toc\s*$', front_matter, re.MULTILINE):
        return text

    fm_lines = front_matter.split('\n')
    while fm_lines and fm_lines[-1] == '':
        fm_lines.pop()

    has_hide = any(line.startswith('hide:') for line in fm_lines)
    if not has_hide:
        fm_lines.append('hide: true')
    fm_lines.append('  - toc')

    new_front_matter = '\n'.join(fm_lines)
    return f'{prefix}{new_front_matter}{suffix}{text[match.end():]}'


def process_details(text):
    pattern = r'<details>\s*<summary>(.*?)</summary>\s*(.*?)</details>'
    matches = re.finditer(pattern, text, re.DOTALL)

    offset = 0
    result = str(text)
    for match in matches:
        lo, hi = match.span()
        if text[lo - 1] == '`':
            continue

        title = match.group(1).strip()
        details_content = match.group(2).strip()
        indented_content = '\n'.join('    ' + line for line in details_content.split('\n'))
        new_format = f'??? note "{title}"\n\n{indented_content}\n'

        lo, hi = lo + offset, hi + offset
        result = result[:lo] + new_format + result[hi:]
        offset += len(new_format) - (hi - lo)

    return result


def process_square_brackets(text):
    """
    将【】包起来的内容转换为更醒目的 HTML 格式。
    注意：不会替换代码块中的【】
    """
    pattern = r'【([^】]+)】'

    def replace_func(match):
        content = match.group(1)
        return f'<mark class="term-highlight">{content}</mark>'

    parts = []
    last_end = 0
    code_block_pattern = r'```[\s\S]*?```|`[^`\n]+`'

    for code_match in re.finditer(code_block_pattern, text):
        code_start, code_end = code_match.span()
        before_code = text[last_end:code_start]
        before_code = re.sub(pattern, replace_func, before_code)
        parts.append(before_code)
        parts.append(text[code_start:code_end])
        last_end = code_end

    remaining = text[last_end:]
    remaining = re.sub(pattern, replace_func, remaining)
    parts.append(remaining)

    return ''.join(parts)


def replace_arrow_safely(content):
    """
    将 -->、->、<--、<- 替换为箭头符号，但避免替换注释、代码块、行内代码。
    """
    html_comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
    code_block_pattern = re.compile(r'```[\s\S]*?```', re.DOTALL)
    inline_code_pattern = re.compile(r'`[^`\n]+`')

    skip_regions = []
    for match in html_comment_pattern.finditer(content):
        skip_regions.append((match.start(), match.end(), 'html_comment'))
    for match in code_block_pattern.finditer(content):
        skip_regions.append((match.start(), match.end(), 'code_block'))
    for match in inline_code_pattern.finditer(content):
        start, end = match.span()
        in_code_block = False
        for cb_start, cb_end, _ in skip_regions:
            if cb_start <= start < cb_end:
                in_code_block = True
                break
        if not in_code_block:
            skip_regions.append((start, end, 'inline_code'))

    skip_regions.sort(key=lambda x: x[0])

    def do_replace(s):
        s = s.replace('-->', '→')
        s = s.replace('->', '→')
        s = s.replace('<--', '←')
        s = s.replace('<-', '←')
        return s

    if not skip_regions:
        return do_replace(content)

    parts = []
    last_end = 0
    for start, end, _ in skip_regions:
        parts.append(do_replace(content[last_end:start]))
        parts.append(content[start:end])
        last_end = end
    parts.append(do_replace(content[last_end:]))
    return ''.join(parts)


def process_markdown_file(webfile_pth: str) -> None:
    try:
        with open(webfile_pth, 'r', encoding='utf-8') as f:
            content = f.read()

        content, has_question_section = process_question_sections(content)
        if has_question_section:
            content = ensure_toc_hidden(content)
        content = add_blank_before_list(content)
        content = process_details(content)
        content = process_square_brackets(content)
        content = replace_arrow_safely(content)

        with open(webfile_pth, 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print(f'处理文件 {webfile_pth} 时出错: {str(e)}')
        exit(0)


def run() -> None:
    for root, dirs, files in os.walk(settings.docsdir):
        if 'asset' in root or 'code' in root or 'src' in root:
            continue

        for file in files:
            if file.endswith('.md'):
                webfile_pth = utils.abspath(os.path.join(root, file))
                process_markdown_file(webfile_pth)

    print('Markdown 格式后处理完成！')


if __name__ == '__main__':
    run()
