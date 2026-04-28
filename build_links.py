import os
from pathlib import Path

import settings
import utils
from utils.config_parser import ConfigParser


def _build_main_mappings(configs: ConfigParser):
    web2raw_mapping = {}
    for raw_key, value in configs.file_cache.items():
        raw_path = utils.abspath(raw_key)
        web_path = utils.abspath(value[1])
        web2raw_mapping[web_path] = raw_path
    return web2raw_mapping


def _plan_file_output(configs: ConfigParser, raw_file_path: str, link_src_path: str) -> dict | None:
    raw_file_path = utils.abspath(raw_file_path)
    try:
        source_web_path = utils.abspath(configs.get_web_path(raw_file_path))
    except KeyError:
        return None

    link_web_path = configs.get_link_output_file(link_src_path, raw_file_path)
    if link_web_path is None:
        return None

    return {
        'raw': raw_file_path,
        'source_web': source_web_path,
        'web': utils.abspath(link_web_path),
    }


def _rewrite_copied_markdown_links(copied_web_path: str, source_web_path: str, main_web2raw_mapping: dict[str, str]) -> None:
    with open(copied_web_path, 'r', encoding='utf-8') as f:
        content = f.read()

    replacements = []
    for start, end, link_url, _is_html in utils.extract_links(content, exclude=settings.skip_types):
        if os.path.isabs(link_url):
            continue

        source_target_abs = utils.abspath((Path(source_web_path).parent / link_url).resolve())
        if not os.path.exists(source_target_abs):
            continue

        target_abs = source_target_abs
        if source_target_abs in main_web2raw_mapping:
            target_abs = source_target_abs

        new_rel = utils.relpath(target_abs, copied_web_path)
        if new_rel != link_url:
            replacements.append((start, end, new_rel))

    if not replacements:
        return

    replacements.sort(key=lambda item: item[0], reverse=True)
    for start, end, new_rel in replacements:
        content = content[:start] + new_rel + content[end:]

    with open(copied_web_path, 'w', encoding='utf-8') as f:
        f.write(content)
def main() -> None:
    configs = ConfigParser()
    web2raw_mapping = _build_main_mappings(configs)

    for link_src_path, info in configs.link_cache.items():
        target_raw = utils.abspath(info['target_raw'])
        planned_output = _plan_file_output(configs, target_raw, link_src_path)
        if planned_output is None:
            print(f'链接副本跳过无效目标: {link_src_path} -> {target_raw}')
            continue

        source_web_path = utils.abspath(planned_output['source_web'])
        link_web_path = utils.abspath(planned_output['web'])
        if not os.path.exists(source_web_path):
            print(f'链接副本跳过缺失主产物: {link_src_path} -> {source_web_path}')
            continue

        utils.copy(source_web_path, link_web_path)
        if link_web_path.lower().endswith('.md'):
            _rewrite_copied_markdown_links(link_web_path, source_web_path, web2raw_mapping)

        # print('----------更新链接文件----------')
        # print(f'原始链接文件: {link_src_path}, 指向原始目标: {target_raw}')
        # print(f'复制结果: {source_web_path} -> {link_web_path}')


if __name__ == '__main__':
    main()
