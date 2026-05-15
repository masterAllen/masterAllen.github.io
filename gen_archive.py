"""
归档页面生成：读取 file_cache，分别按「修改时间」和「创建时间」生成两个归档页面
"""
import os
os.chdir(os.path.dirname(__file__))

from datetime import date, datetime, timedelta
from collections import defaultdict
from html import escape

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


def build_heatmap_thresholds(counts):
    """按非零日期的分布生成颜色阈值，避免极端值压扁整体颜色。"""
    nonzero_counts = sorted(count for count in counts if count > 0)
    if not nonzero_counts:
        return [0, 0, 0]

    last_index = len(nonzero_counts) - 1
    return [
        nonzero_counts[int(last_index * 0.25)],
        nonzero_counts[int(last_index * 0.50)],
        nonzero_counts[int(last_index * 0.75)],
    ]


def heatmap_level(count, thresholds):
    """将每日文章数映射到 GitHub 风格的 0-4 级颜色。"""
    if count <= 0:
        return 0
    if count <= thresholds[0]:
        return 1
    if count <= thresholds[1]:
        return 2
    if count <= thresholds[2]:
        return 3
    return 4


def render_archive_heatmap(articles, time_key):
    """生成最近一年的文章日期热力图 HTML。"""
    date_counts = defaultdict(int)
    for art in articles:
        date_counts[art[time_key].date()] += 1

    if not date_counts:
        return ''

    end_day = date.today()
    start_day = end_day - timedelta(days=364)
    visible_days = [start_day + timedelta(days=offset) for offset in range(365)]
    visible_counts = [date_counts.get(day, 0) for day in visible_days]
    thresholds = build_heatmap_thresholds(visible_counts)
    weekday_labels = ['日', '一', '二', '三', '四', '五', '六']
    leading_blanks = (start_day.weekday() + 1) % 7
    week_count = (leading_blanks + len(visible_days) + 6) // 7
    month_positions = []
    previous_month = None
    for offset, current_day in enumerate(visible_days):
        if current_day.month == previous_month:
            continue
        previous_month = current_day.month
        week_index = (leading_blanks + offset) // 7 + 1
        if len(month_positions) % 2 == 0:
            month_positions.append((f'{current_day.month}月', week_index))
        else:
            month_positions.append((None, week_index))

    lines = [
        '<div class="archive-heatmap" aria-label="文章活动热力图">',
        '  <div class="archive-heatmap__header">',
        '    <span class="archive-heatmap__title">最近一年文章活动</span>',
        f'    <span class="archive-heatmap__summary">{start_day:%Y-%m-%d} 至 {end_day:%Y-%m-%d}</span>',
        '  </div>',
        f'  <div class="archive-heatmap__scroller" style="--archive-heatmap-week-count: {week_count};">',
        '    <div class="archive-heatmap__months" aria-hidden="true">',
    ]
    for month, week_index in month_positions:
        if month is None:
            continue
        lines.append(f'      <span style="grid-column: {week_index};">{month}</span>')
    lines.extend([
        '    </div>',
        '    <div class="archive-heatmap__body">',
        '      <div class="archive-heatmap__weekdays" aria-hidden="true">',
    ])
    for weekday in weekday_labels:
        lines.append(f'        <span>{weekday}</span>')
    lines.extend([
        '      </div>',
        '      <div class="archive-heatmap__grid">',
    ])

    for _ in range(leading_blanks):
        lines.append('        <span class="archive-heatmap__cell archive-heatmap__cell--empty" aria-hidden="true"></span>')

    for current_day in visible_days:
        count = date_counts.get(current_day, 0)
        level = heatmap_level(count, thresholds)
        label = f'{current_day:%Y-%m-%d}：{count} 篇文章'
        lines.append(
            '        '
            f'<span class="archive-heatmap__cell archive-heatmap__cell--level-{level}" '
            f'title="{escape(label)}" aria-label="{escape(label)}"></span>'
        )

    lines.extend([
        '      </div>',
        '    </div>',
        '  </div>',
        '</div>',
        '',
    ])
    return '\n'.join(lines)


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
        f.write(render_archive_heatmap(articles, time_key) + '\n')

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
