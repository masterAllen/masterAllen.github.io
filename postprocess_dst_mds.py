"""
生成后的 Markdown 格式后处理
列表前空行、<details>→admonition、【】高亮、安全替换箭头、块级公式空行。
"""
import os
import re

os.chdir(os.path.dirname(__file__))

import settings
import utils


DETAILS_RE = re.compile(r'^\s*<details\b(?P<attrs>[^>]*)>\s*$', re.IGNORECASE)
DETAILS_END_RE = re.compile(r'^\s*</details>\s*$', re.IGNORECASE)
SUMMARY_RE = re.compile(r'^\s*<summary>\s*(?P<title>.*?)\s*</summary>\s*$', re.IGNORECASE)
NAME_RE = re.compile(r"""\bname\s*=\s*["'](?P<name>[^"']*)["']""", re.IGNORECASE)
HEADING_RE = re.compile(r'^\s*#{1,6}\s+(?P<title>.+?)\s*$')
IMAGE_RE = re.compile(r'!\[(?P<alt>[^\]]*)\]\((?P<src>[^)]+)\)')
DEFINE_RE = re.compile(r'^\s*<!--\s*define:\s*(?P<title>.*?)\s*-->\s*$', re.IGNORECASE)
CODE_FENCE_RE = re.compile(r'^\s*(`{3,}|~{3,})')


def get_code_fence(line: str) -> str | None:
    match = CODE_FENCE_RE.match(line_text(line))
    return match.group(1) if match else None


def update_code_fence_state(line: str, active_fence: str | None) -> str | None:
    fence = get_code_fence(line)
    if fence is None:
        return active_fence
    if active_fence is None:
        return fence
    if fence[0] == active_fence[0] and len(fence) >= len(active_fence):
        return None
    return active_fence


def add_blank_before_list(text):
    """
    智能补列表空行：检测到列表衔接不规范时自动插入空行。
    支持无序/有序列表混排，包括 `1. 2. 3.` 与 `1. xx:` 后接子列表等场景。
    """
    lines = text.split('\n')
    result = []
    active_fence: str | None = None
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
        active_fence = update_code_fence_state(line, active_fence)

        if active_fence is None and i > 0 and stripped:
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


def ensure_blank_around_block_math(text):
    """
    确保 $$ ... $$ 块级公式上下都是空行；跳过代码块内部。
    支持跨行（$$ 单独成行）和单行 $$ ... $$ 两种形式。
    """
    lines = text.split('\n')
    active_fence: str | None = None
    in_math = False
    math_start = -1
    regions: list[tuple[int, int]] = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        active_fence = update_code_fence_state(line, active_fence)
        if get_code_fence(line):
            continue
        if active_fence is not None:
            continue

        # 单行块公式：整行内容形如 $$...$$
        if (
            not in_math
            and stripped.startswith('$$')
            and stripped.endswith('$$')
            and len(stripped) > 4
            and '$$' not in stripped[2:-2]
        ):
            regions.append((i, i))
            continue

        if stripped == '$$':
            if not in_math:
                in_math = True
                math_start = i
            else:
                in_math = False
                regions.append((math_start, i))

    if not regions:
        return text

    result = list(lines)
    for start, end in reversed(regions):
        if end + 1 < len(result) and result[end + 1].strip() != '':
            indent = ' ' * (len(result[end]) - len(result[end].lstrip(' ')))
            result.insert(end + 1, indent)
        if start > 0 and result[start - 1].strip() != '':
            indent = ' ' * (len(result[start]) - len(result[start].lstrip(' ')))
            result.insert(start, indent)

    return '\n'.join(result)


def line_text(line: str) -> str:
    return line.rstrip('\r\n')


def is_blank(line: str) -> bool:
    return line_text(line).strip() == ''


def trim_blank_edges(lines: list[str]) -> list[str]:
    start = 0
    end = len(lines)
    while start < end and is_blank(lines[start]):
        start += 1
    while end > start and is_blank(lines[end - 1]):
        end -= 1
    return lines[start:end]


def indent_lines(lines: list[str], spaces: int = 4) -> list[str]:
    prefix = ' ' * spaces
    return [line if is_blank(line) else prefix + line for line in lines]


def quote_title(title: str) -> str:
    return title.strip().replace('"', r'\"')


def find_comment_end(lines: list[str], start: int) -> int | None:
    active_fence: str | None = None
    for index in range(start + 1, len(lines)):
        active_fence = update_code_fence_state(lines[index], active_fence)
        if get_code_fence(lines[index]):
            continue
        if active_fence is None and line_text(lines[index]).strip().lower() == '<!-- end -->':
            return index
    return None


def find_details_end(lines: list[str], start: int) -> int | None:
    depth = 0
    active_fence: str | None = None
    for index in range(start, len(lines)):
        active_fence = update_code_fence_state(lines[index], active_fence)
        if get_code_fence(lines[index]):
            continue
        if active_fence is not None:
            continue

        stripped = line_text(lines[index]).strip()
        if DETAILS_RE.match(stripped):
            depth += 1
        elif DETAILS_END_RE.match(stripped):
            depth -= 1
            if depth == 0:
                return index
    return None


def parse_details_attrs(attrs: str) -> tuple[bool, str]:
    is_open = bool(re.search(r'\bopen\b', attrs, re.IGNORECASE))
    name_match = NAME_RE.search(attrs)
    name = name_match.group('name').strip() if name_match else 'note'
    return is_open, name or 'note'


def split_summary(inner: list[str]) -> tuple[str, list[str]] | None:
    for index, line in enumerate(inner):
        if is_blank(line):
            continue
        match = SUMMARY_RE.match(line_text(line))
        if not match:
            return None
        content = inner[:index] + inner[index + 1:]
        return match.group('title').strip(), content
    return '', []


def render_admonition(marker: str, kind: str, title: str, content: list[str]) -> list[str]:
    body = indent_lines([line_text(line) for line in trim_blank_edges(content)])
    output = [f'{marker} {kind} "{quote_title(title)}"', '']
    output.extend(body)
    return output


def render_llm_block(title: str, content: list[str]) -> list[str]:
    body = indent_lines([line_text(line) for line in trim_blank_edges(content)])
    output = ['!!! info ""', '', f'    {title.strip()}', '', '???+ abstract "answer"', '']
    output.extend(body)
    return output


def convert_details(lines: list[str], start: int) -> tuple[list[str], int] | None:
    match = DETAILS_RE.match(line_text(lines[start]).strip())
    if not match:
        return None

    end = find_details_end(lines, start)
    if end is None:
        return None

    summary = split_summary(lines[start + 1:end])
    if summary is None:
        return None

    title, content = summary
    is_open, name = parse_details_attrs(match.group('attrs'))
    if name == 'llm':
        return render_llm_block(title, content), end + 1

    kind = 'note' if name == 'code' else name
    marker = '???+' if is_open else '???'
    return render_admonition(marker, kind, title, content), end + 1


def convert_figcaption(lines: list[str], start: int) -> tuple[list[str], int] | None:
    if line_text(lines[start]).strip().lower() != '<!-- figcaption -->':
        return None

    end = find_comment_end(lines, start)
    if end is None:
        return None

    image_match = None
    for line in lines[start + 1:end]:
        image_match = IMAGE_RE.search(line_text(line))
        if image_match:
            break

    if image_match is None:
        return None

    alt = image_match.group('alt').strip()
    src = image_match.group('src').strip()
    return [
        '<figure class="img-center">',
        f'    <img src="{src}" alt="{alt}">',
        f'    <figcaption> {alt} </figcaption>',
        '</figure>',
    ], end + 1


def extract_heading_title(lines: list[str]) -> tuple[str, list[str]]:
    for index, line in enumerate(lines):
        if is_blank(line):
            continue
        match = HEADING_RE.match(line_text(line))
        if not match:
            return '', lines
        return match.group('title').strip(), lines[:index] + lines[index + 1:]
    return '', []


def convert_question_comment(lines: list[str], start: int) -> tuple[list[str], int] | None:
    if line_text(lines[start]).strip().lower() != '<!-- question -->':
        return None

    end = find_comment_end(lines, start)
    if end is None:
        return None

    title, content = extract_heading_title(lines[start + 1:end])
    return render_admonition('???', 'question', title, content), end + 1


def convert_llm_comment(lines: list[str], start: int) -> tuple[list[str], int] | None:
    if line_text(lines[start]).strip().lower() != '<!-- llm -->':
        return None

    end = find_comment_end(lines, start)
    if end is None:
        end = len(lines)

    title, content = extract_heading_title(lines[start + 1:end])
    return render_llm_block(title, content), end + (1 if end < len(lines) else 0)


def convert_define_comment(lines: list[str], start: int) -> tuple[list[str], int] | None:
    match = DEFINE_RE.match(line_text(lines[start]))
    if not match:
        return None

    end = find_comment_end(lines, start)
    if end is None:
        return None

    title = match.group('title').strip()
    content = indent_lines([line_text(line) for line in trim_blank_edges(lines[start + 1:end])])
    output = [f'!!! note "{quote_title(title)}"', '']
    output.extend(content)
    return output, end + 1


def convert_document_blocks(text: str) -> tuple[str, bool]:
    """
    按 docs/原文转换格式说明.md 处理源文档标记。
    返回值第二项表示是否生成了 LLM 问答块，用于隐藏 toc。
    """
    lines = text.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    active_fence: str | None = None
    has_llm_block = False
    converters = (
        convert_details,
        convert_figcaption,
        convert_question_comment,
        convert_llm_comment,
        convert_define_comment,
    )

    while index < len(lines):
        active_fence = update_code_fence_state(lines[index], active_fence)
        if get_code_fence(lines[index]):
            output.append(line_text(lines[index]))
            index += 1
            continue

        if active_fence is None:
            for converter in converters:
                result = converter(lines, index)
                if result is None:
                    continue
                converted, next_index = result
                if converted and converted[0] == '!!! info ""':
                    has_llm_block = True
                output.extend(converted)
                output.append('')
                index = next_index
                break
            else:
                output.append(line_text(lines[index]))
                index += 1
        else:
            output.append(line_text(lines[index]))
            index += 1

    while output and output[-1] == '':
        output.pop()
    output.append('')
    return '\n'.join(output), has_llm_block


def ensure_toc_hidden(text):
    """
    为 Markdown 文件补充/合并 front matter，确保隐藏 toc。
    """
    if re.match(r'^---\n', text) is None:
        return f'---\nhide:\n  - toc\n---\n\n{text}'

    match = re.match(r'^(---\n)(.*?)(\n---\n?)', text, re.DOTALL)
    if match is None:
        return f'---\nhide:\n  - toc\n---\n\n{text}'

    prefix, front_matter, suffix = match.groups()
    if re.search(r'^\s*-\s*toc\s*$', front_matter, re.MULTILINE):
        return text

    fm_lines = front_matter.split('\n')
    while fm_lines and fm_lines[-1] == '':
        fm_lines.pop()

    hide_index = next((i for i, line in enumerate(fm_lines) if line.startswith('hide:')), None)
    if hide_index is None:
        fm_lines.extend(['hide:', '  - toc'])
    elif fm_lines[hide_index].strip() == 'hide:':
        fm_lines.insert(hide_index + 1, '  - toc')
    else:
        fm_lines[hide_index:hide_index + 1] = ['hide:', '  - toc']

    new_front_matter = '\n'.join(fm_lines)
    return f'{prefix}{new_front_matter}{suffix}{text[match.end():]}'


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

    skip_regions: list[tuple[int, int]] = []
    for match in html_comment_pattern.finditer(content):
        skip_regions.append(match.span())
    for match in code_block_pattern.finditer(content):
        skip_regions.append(match.span())
    for match in inline_code_pattern.finditer(content):
        start, end = match.span()
        in_skip_region = False
        for cb_start, cb_end in skip_regions:
            if cb_start <= start < cb_end:
                in_skip_region = True
                break
        if not in_skip_region:
            skip_regions.append((start, end))

    skip_regions.sort(key=lambda x: x[0])
    merged_skip_regions: list[tuple[int, int]] = []
    for start, end in skip_regions:
        if not merged_skip_regions or start > merged_skip_regions[-1][1]:
            merged_skip_regions.append((start, end))
        else:
            last_start, last_end = merged_skip_regions[-1]
            merged_skip_regions[-1] = (last_start, max(last_end, end))

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
    for start, end in merged_skip_regions:
        parts.append(do_replace(content[last_end:start]))
        parts.append(content[start:end])
        last_end = end
    parts.append(do_replace(content[last_end:]))
    return ''.join(parts)


def process_markdown_file(webfile_pth: str) -> None:
    try:
        with open(webfile_pth, 'r', encoding='utf-8') as f:
            content = f.read()

        content, has_llm_block = convert_document_blocks(content)
        if has_llm_block:
            content = ensure_toc_hidden(content)
        content = ensure_blank_around_block_math(content)
        content = add_blank_before_list(content)
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
