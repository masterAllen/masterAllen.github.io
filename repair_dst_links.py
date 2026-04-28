"""
修复生成后的 Markdown 里的链接，并复制资源到 asset 并改写为相对路径。
"""
import os
os.chdir(os.path.dirname(__file__))

from pathlib import Path

import settings
import utils


def process_markdown_links(content, webfile_pth, raw2web_mapping, web2raw_mapping, local_raw2web_mapping=None):
    rawfile_pth = web2raw_mapping.get(webfile_pth)

    # 每个元素：(start_pos, end_pos, new_link, old_link_url)
    result = []

    matches = utils.extract_links(content, exclude=settings.skip_types)

    if rawfile_pth is None:
        return []

    for url_start, url_end, link_url, is_html in matches:
        link_type = utils.check_url_type(link_url)
        if link_type in settings.skip_types:
            continue

        link_url_abs = (Path(webfile_pth).parent / link_url).resolve()

        if is_html:
            if link_url_abs.exists() and not os.path.isabs(link_url):
                new_link_url = '../' + link_url
                result.append((url_start, url_end, new_link_url, link_url))
                continue

            temp_link_url = os.path.join(os.path.dirname(webfile_pth), link_url[3:])
            if os.path.exists(temp_link_url):
                continue

            if link_url.startswith('/') and link_type == 'code':
                continue

        if os.path.isabs(link_url) or not link_url_abs.exists():
            link_url_abs_inweb = link_url_abs
            link_url_abs = utils.abspath((Path(rawfile_pth).parent / link_url).resolve())

            asset_absdir = utils.asset_link(link_url_abs, link_type, makedir=False)
            asset_absfile = utils.abspath(os.path.join(asset_absdir, os.path.basename(link_url)))

            if not os.path.exists(link_url_abs):
                print('----------链接失效----------')
                print(f'WEB 文件: {webfile_pth}')
                print(f'WEB 文件中链接内容: {link_url}')
                print(f'WEB 文件中链接指向的绝对路径: {link_url_abs_inweb}')

                print(f'没有找到这个文件，所以开始对原始文件进行解析')

                print(f'原始文件: {rawfile_pth}')
                print(f'原始文件中链接指向的绝对路径: {link_url_abs}')
                print(f'解析的资源文件路径: {asset_absfile}')

                continue

            target_web_path = None
            if local_raw2web_mapping and link_url_abs in local_raw2web_mapping:
                target_web_path = local_raw2web_mapping[link_url_abs]
            elif link_url_abs in raw2web_mapping:
                target_web_path = raw2web_mapping[link_url_abs]

            if target_web_path is not None and link_type != 'image':
                pth2 = target_web_path
                pth1 = webfile_pth

                link_relpth = utils.relpath(pth2, pth1)
                if is_html:
                    link_relpth = '../' + link_relpth

                result.append((url_start, url_end, link_relpth, link_url))
                continue

            try:
                if link_type == 'text':
                    asset_absfile = asset_absfile + '.txt'

                os.makedirs(asset_absdir, exist_ok=True)
                copy_success = utils.copy(link_url_abs, asset_absfile)

                if copy_success:
                    asset_relto_webfile = utils.relpath(asset_absfile, webfile_pth)
                    if is_html:
                        asset_relto_webfile = '../' + asset_relto_webfile
                    result.append((url_start, url_end, asset_relto_webfile, link_url))
                else:
                    webfile_name = os.path.basename(webfile_pth)
                    result.append((
                        url_start,
                        url_end,
                        f'./{webfile_name} "文件过大，未上传"',
                        link_url,
                    ))

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


def process_markdown_file(webfile_pth, raw2web_mapping, web2raw_mapping, local_raw2web_mapping=None, is_replace=False):
    try:
        with open(webfile_pth, 'r', encoding='utf-8') as f:
            content = f.read()

        need_replaces = process_markdown_links(
            content,
            webfile_pth,
            raw2web_mapping,
            web2raw_mapping,
            local_raw2web_mapping=local_raw2web_mapping,
        )

        if not is_replace:
            return

        if not need_replaces:
            return

        need_replaces.sort(key=lambda x: x[0], reverse=True)
        for url_start, url_end, new_link, old_link_url in need_replaces:
            print(f'修复链接: {old_link_url} -> {new_link}')
            content = content[:url_start] + new_link + content[url_end:]

        with open(webfile_pth, 'w', encoding='utf-8') as f:
            f.write(content)

    except Exception as e:
        print(f'处理文件 {webfile_pth} 时出错: {str(e)}')
        raw = web2raw_mapping.get(webfile_pth)
        if raw is not None:
            print(f'原始文件: {raw}')
        exit(0)


def run(is_replace=False):
    from utils.config_parser import ConfigParser

    config_parser = ConfigParser()
    file_cache = config_parser.file_cache

    raw2web_mapping = {}
    web2raw_mapping = {}
    for raw_key, value in file_cache.items():
        web_path = value[1]
        web_path = utils.abspath(web_path)
        raw_key = utils.abspath(raw_key)
        web2raw_mapping[web_path] = raw_key
        raw2web_mapping[raw_key] = web_path

    main_markdown_files = sorted(
        web_path for web_path in web2raw_mapping
        if web_path.lower().endswith('.md') and os.path.exists(web_path)
    )

    if not is_replace:
        for webfile_pth in main_markdown_files:
            process_markdown_file(
                webfile_pth,
                raw2web_mapping,
                web2raw_mapping,
                is_replace=False,
            )

        do_replace_input = input("是否进行替换？输入y进行替换，其它键跳过: ").strip().lower()
        is_replace = do_replace_input == 'y'
        if not is_replace:
            raise Exception("跳过替换操作，主动发生异常，防止调用该任务的程序继续执行其他任务")

    for webfile_pth in main_markdown_files:
        process_markdown_file(
            webfile_pth,
            raw2web_mapping,
            web2raw_mapping,
            is_replace=True,
        )

    print('链接修复完成！')


if __name__ == '__main__':
    run(is_replace=True)
