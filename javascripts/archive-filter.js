// 归档页按原始文件类型筛选，兼容 instant 导航。
(function() {
  'use strict';

  function initArchiveFilters() {
    const filters = document.querySelector('.archive-filters');
    if (!filters || filters.dataset.initialized) return;
    filters.dataset.initialized = 'true';

    const article = filters.closest('article');
    const entries = Array.from(article.querySelectorAll('.archive-entry'));
    const groups = Array.from(article.querySelectorAll('.archive-month-count')).map(count => {
      const heading = count.closest('h2');
      const items = Array.from(heading.nextElementSibling.querySelectorAll('.archive-entry'));
      return { count, heading, items };
    });
    const cells = Array.from(article.querySelectorAll('.archive-heatmap__cell[data-date]'));
    const buttons = Array.from(filters.querySelectorAll('button'));

    function applyFilter(type) {
      const dates = new Map();
      let total = 0;
      entries.forEach(entry => {
        const visible = type === 'all' || entry.dataset.type === type;
        entry.closest('li').hidden = !visible;
        if (visible) {
          total++;
          dates.set(entry.dataset.date, (dates.get(entry.dataset.date) || 0) + 1);
        }
      });
      groups.forEach(group => {
        const count = group.items.filter(entry => !entry.closest('li').hidden).length;
        group.count.textContent = count;
        group.heading.hidden = count === 0;
        group.items[0].closest('ul').hidden = count === 0;
      });
      document.querySelectorAll('.md-nav--secondary a[href*="#"]').forEach(link => {
        const heading = document.getElementById(decodeURIComponent(link.hash.slice(1)));
        const group = groups.find(group => group.heading === heading);
        if (group) {
          link.closest('li').hidden = heading.hidden;
          const count = link.querySelector('.archive-month-count');
          if (count) count.textContent = group.count.textContent;
        }
      });
      article.querySelector('.archive-result strong').textContent = total;
      article.querySelector('.archive-empty').hidden = total !== 0;
      buttons.forEach(button => {
        button.setAttribute('aria-pressed', String(button.dataset.archiveFilter === type));
      });

      const nonzero = cells.map(cell => dates.get(cell.dataset.date) || 0)
        .filter(count => count > 0).sort((a, b) => a - b);
      const thresholds = [0.25, 0.50, 0.75].map(q => nonzero[Math.floor((nonzero.length - 1) * q)] || 0);
      cells.forEach(cell => {
        const count = dates.get(cell.dataset.date) || 0;
        const level = count === 0 ? 0 : count <= thresholds[0] ? 1 : count <= thresholds[1] ? 2 : count <= thresholds[2] ? 3 : 4;
        cell.className = 'archive-heatmap__cell archive-heatmap__cell--level-' + level;
        cell.title = cell.dataset.date + '：' + count + ' 篇文章';
        cell.setAttribute('aria-label', cell.title);
      });
    }

    filters.addEventListener('click', event => {
      const button = event.target.closest('button[data-archive-filter]');
      if (button && filters.contains(button)) applyFilter(button.dataset.archiveFilter);
    });
    filters.hidden = false;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initArchiveFilters);
  } else {
    initArchiveFilters();
  }
  if (typeof document$ !== 'undefined') document$.subscribe(initArchiveFilters);
})();
