"""
归档页面生成：读取 file_cache，分别按「修改时间」和「创建时间」生成两个归档页面
"""
import os
os.chdir(os.path.dirname(__file__))

from datetime import datetime
from collections import defaultdict

import utils
import settings
from utils.config_parser import ConfigParser


def _is_under_reference_dir(webpath):
    """Reference/ 下为 main1 自动生成的汇总页，不参与归档统计。"""
    try:
        rel = os.path.relpath(os.path.normpath(webpath), os.path.normpath(settings.docsdir))
    except ValueError:
        return False
    parts = [p for p in rel.replace('\\', '/').split('/') if p and p != '.']
    return len(parts) >= 2 and parts[-2].lower() == 'reference'


def collect_articles(file_cache):
    """从 file_cache 收集所有文章的信息（标题、web路径、修改时间、创建时间）"""
    articles = []
    for srcpath, (mtime, webpath) in file_cache.items():
        if not webpath.endswith('.md'):
            continue
        if os.path.basename(webpath).lower() == 'index.md':
            continue
        if _is_under_reference_dir(webpath):
            continue
        if not os.path.exists(webpath):
            continue

        title = utils.get_md_title(webpath)
        if not title:
            title = os.path.splitext(os.path.basename(webpath))[0]

        ctime = os.stat(srcpath).st_ctime
        mtime = os.stat(srcpath).st_mtime

        articles.append({
            'title': title,
            'webpath': webpath,
            'mtime': datetime.fromtimestamp(mtime),
            'ctime': datetime.fromtimestamp(ctime)
        })
    return articles


def escape_md_link_title(text):
    """转义标题中会破坏 Markdown [text](url) 的字符"""
    return text.replace('[', '\\[').replace(']', '\\]')


def escape_md_link_url(url):
    """转义 URL 中会破坏 Markdown [text](url) 的字符"""
    return url.replace('(', '%28').replace(')', '%29').replace('[', '%5B').replace(']', '%5D')


def write_archive_page(filepath, articles, time_key, page_title):
    """按指定时间字段分组写入归档页面"""
    archive = defaultdict(list)
    for art in articles:
        dt = art[time_key]
        archive[(dt.year, dt.month)].append({**art, 'date': dt})

    total = len(articles)
    sorted_keys = sorted(archive.keys(), reverse=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(utils.get_topinfo(comments=False) + '\n')
        f.write(f'# {page_title}\n\n')
        f.write(f'共 **{total}** 篇文章\n\n')

        f.write(f'> 为什么创建时间可能比修改时间晚，因为文件复制后，创建时间此时会更新为当前时间，而修改时间不变。\n\n')

        for year, month in sorted_keys:
            items = sorted(archive[(year, month)], key=lambda x: x['date'], reverse=True)
            f.write(f'## {year} 年 {month} 月（{len(items)} 篇）\n\n')

            for item in items:
                relpath = escape_md_link_url(utils.relpath(item['webpath'], filepath))
                title = escape_md_link_title(item['title'])
                date_str = item['date'].strftime('%m-%d')
                f.write(f'- {date_str}　[{title}]({relpath})\n')

            f.write('\n')

    print(f'归档页面已生成: {filepath}（共 {total} 篇）')


def run():
    configs = ConfigParser()
    articles = collect_articles(configs.file_cache)

    archive_dir = os.path.join(settings.docsdir, '归档')
    os.makedirs(archive_dir, exist_ok=True)

    write_archive_page(
        os.path.join(archive_dir, '修改时间.md'),
        articles, 'mtime', '归档（按修改时间）',
    )
    write_archive_page(
        os.path.join(archive_dir, '创建时间.md'),
        articles, 'ctime', '归档（按创建时间）',
    )


if __name__ == '__main__':
    run()
