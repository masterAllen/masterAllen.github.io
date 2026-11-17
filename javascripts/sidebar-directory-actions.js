(function() {
  'use strict';

  function init() {
    document.querySelectorAll('.md-sidebar--primary .md-nav__container').forEach(function(row) {
      if (row.classList.contains('sidebar-directory-row')) return;
      var link = row.querySelector(':scope > a.md-nav__link');
      var toggle = row.querySelector(':scope > label.md-nav__link');
      if (!link || !toggle) return;
      var checkbox = document.getElementById(toggle.htmlFor);
      if (!checkbox) return;

      var title = link.textContent.trim();
      var name = document.createElement('span');
      name.className = 'sidebar-directory-name';
      while (link.firstChild) name.appendChild(link.firstChild);
      toggle.appendChild(name);
      toggle.classList.remove('md-nav__link--active');
      toggle.setAttribute('role', 'button');
      toggle.setAttribute('tabindex', '0');
      toggle.setAttribute('aria-controls', checkbox.id + '_nav');
      var nav = row.parentElement.querySelector(':scope > nav.md-nav');
      if (nav) nav.id = checkbox.id + '_nav';

      function sync() {
        toggle.setAttribute('aria-expanded', String(checkbox.checked));
        toggle.setAttribute('aria-label', (checkbox.checked ? '收起目录：' : '展开目录：') + title);
      }
      checkbox.addEventListener('change', sync);
      sync();
      toggle.addEventListener('keydown', function(event) {
        if (event.key === ' ') {
          event.preventDefault();
          event.stopPropagation();
          checkbox.click();
        }
      });

      link.classList.add('sidebar-directory-overview');
      link.setAttribute('title', '打开目录概览：' + title);
      link.setAttribute('aria-label', '打开目录概览：' + title);
      if (link.classList.contains('md-nav__link--active')) link.setAttribute('aria-current', 'page');
      var icon = document.createElement('span');
      icon.className = 'sidebar-directory-overview-icon';
      icon.setAttribute('aria-hidden', 'true');
      link.appendChild(icon);
      row.appendChild(link);
      row.classList.add('sidebar-directory-row');
      row.addEventListener('click', function(event) {
        if (event.target === row) checkbox.click();
      });
    });
  }

  init();
  if (typeof document$ !== 'undefined') document$.subscribe(init);
  document.addEventListener('shared-navigation-ready', init);
})();
