(function() {
  'use strict';

  var CACHE_KEY = 'CUSTOM_SHARED_NAVIGATION';

  function pagePath(url) {
    return decodeURIComponent(url.pathname).replace(/\/index\.html$/, '/').replace(/\/+$/, '') || '/';
  }

  function activate(container, root) {
    container.querySelectorAll('a[href], img[src]').forEach(function(element) {
      var attribute = element.tagName === 'IMG' ? 'src' : 'href';
      element.setAttribute(attribute, new URL(element.getAttribute(attribute), root).href);
    });
    container.querySelectorAll('.md-nav__link--active, .md-nav__item--active').forEach(function(element) {
      element.classList.remove('md-nav__link--active', 'md-nav__item--active');
      element.removeAttribute('aria-current');
    });
    var current = pagePath(new URL(window.location.href));
    container.querySelectorAll('a.md-nav__link[href]').forEach(function(link) {
      var url = new URL(link.href);
      if (url.origin !== window.location.origin || pagePath(url) !== current) return;
      link.classList.add('md-nav__link--active');
      link.setAttribute('aria-current', 'page');
      var item = link.closest('li.md-nav__item');
      while (item) {
        item.classList.add('md-nav__item--active');
        var toggle = item.querySelector(':scope > input.md-nav__toggle');
        if (toggle && !toggle.checked) {
          toggle.checked = true;
          toggle.dispatchEvent(new Event('change'));
        }
        item = item.parentElement.closest('li.md-nav__item');
      }
    });
    container.querySelectorAll('nav[aria-expanded]').forEach(function(nav) {
      var item = nav.closest('li');
      var toggle = item && item.querySelector(':scope > input.md-nav__toggle');
      if (!toggle || nav.dataset.expansionBound) return;
      nav.dataset.expansionBound = 'true';
      function sync() { nav.setAttribute('aria-expanded', String(toggle.checked)); }
      toggle.addEventListener('change', sync);
      sync();
    });
  }

  function init() {
    document.querySelectorAll('[data-shared-navigation]').forEach(function(container) {
      var target = document.querySelector('[data-shared-navigation-target]');
      var root = new URL(target ? target.dataset.siteRoot : container.dataset.siteRoot, window.location.href);
      var url = new URL(target ? target.dataset.sharedNavigationTarget : container.dataset.sharedNavigation, window.location.href).href;
      var sidebar = container.closest('.md-sidebar--primary');
      if (target && sidebar) sidebar.hidden = target.dataset.navigationHidden === 'true';
      if (container.dataset.navigationLoaded === url) {
        delete container.dataset.navigationLoading;
        activate(container, root);
        return;
      }
      if (container.dataset.navigationLoading === url) return;
      container.dataset.navigationLoading = url;
      function render(html) {
        // A slower request for a previous section must not replace the current tree.
        if (container.dataset.navigationLoading !== url) return;
        container.innerHTML = html;
        container.dataset.navigationLoaded = url;
        delete container.dataset.navigationLoading;
        activate(container, root);
        container.setAttribute('aria-busy', 'false');
        document.dispatchEvent(new CustomEvent('shared-navigation-ready'));
        window.dispatchEvent(new Event('resize'));
      }
      // 只保留最近一份原始目录；绝对 URL 包含内容指纹和站点根路径。
      var cached;
      try { cached = JSON.parse(sessionStorage.getItem(CACHE_KEY)); } catch (e) {}
      if (cached && cached.url === url) {
        render(cached.html);
        return;
      }
      fetch(url).then(function(response) {
        if (!response.ok) throw new Error('HTTP ' + response.status);
        return response.text();
      }).then(function(html) {
        try { sessionStorage.setItem(CACHE_KEY, JSON.stringify({url: url, html: html})); } catch (e) {}
        render(html);
      }).catch(function(error) {
        if (container.dataset.navigationLoading !== url) return;
        delete container.dataset.navigationLoading;
        container.setAttribute('aria-busy', 'false');
        if (!container.dataset.navigationLoaded) container.querySelector('a').textContent = '返回首页';
        console.error('共享导航加载失败', error);
      });
    });
  }

  init();
  // This script runs beside the sidebar, before the theme defines document$.
  document.addEventListener('DOMContentLoaded', function() {
    if (typeof document$ !== 'undefined') document$.subscribe(init);
  });
})();
