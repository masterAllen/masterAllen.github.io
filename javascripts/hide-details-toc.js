// 隐藏 <details> 内标题对应的右侧目录项。
(function() {
  'use strict';

  function hideDetailsHeadingsFromToc() {
    const toc = document.querySelector('.md-sidebar--secondary nav.md-nav--secondary');
    if (!toc) {
      return;
    }

    toc.querySelectorAll('a[href^="#"]').forEach(link => {
      const target = document.getElementById(link.hash.slice(1));
      if (!target || !target.closest('details')) {
        return;
      }

      const item = link.closest('.md-nav__item');
      if (item) {
        item.hidden = true;
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', hideDetailsHeadingsFromToc);
  } else {
    hideDetailsHeadingsFromToc();
  }
  if (typeof document$ !== 'undefined') document$.subscribe(hideDetailsHeadingsFromToc);
})();
