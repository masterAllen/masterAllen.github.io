(function() {
  'use strict';

  var STORAGE_PREFIX = 'CUSTOM_SIDEBAR_';
  var NAV_KEY = STORAGE_PREFIX + 'NAVIGATION';
  var TOC_KEY = STORAGE_PREFIX + 'TOC';

  function loadBool(key, defaultValue) {
    try {
      var value = localStorage.getItem(key);
      if (value === null) {
        return defaultValue;
      }
      return value === '1';
    } catch (e) {
      return defaultValue;
    }
  }

  function saveBool(key, value) {
    try {
      localStorage.setItem(key, value ? '1' : '0');
    } catch (e) {}
  }

  function getNavVisible() {
    return loadBool(NAV_KEY, true);
  }

  function getTocVisible() {
    return loadBool(TOC_KEY, true);
  }

  function getHeaderInner() {
    return document.querySelector('.md-header__inner');
  }

  function getHeaderTitle() {
    return document.querySelector('.md-header__title');
  }

  function getSearchButton() {
    return document.querySelector('.md-header__button[for="__search"]');
  }

  function getPrimarySidebar() {
    return document.querySelector('.md-sidebar--primary');
  }

  function getSecondarySidebar() {
    return document.querySelector('.md-sidebar--secondary');
  }

  function hasTocSidebar() {
    return !!getSecondarySidebar();
  }

  function setVisibility(navVisible, tocVisible) {
    document.documentElement.dataset.sidebarPrimaryState = navVisible ? 'shown' : 'hidden';
    document.documentElement.dataset.sidebarSecondaryState = tocVisible ? 'shown' : 'hidden';
  }

  function createButton(kind) {
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'md-header__button md-icon custom-sidebar-toggle-button custom-sidebar-toggle-button--' + kind;

    if (kind === 'nav') {
      button.setAttribute('aria-label', '切换左侧导航栏');
      button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 5h18v14H3V5m5 2H5v10h3V7m1 0v10h10V7H9Z"/></svg>';
      button.addEventListener('click', function() {
        var nextValue = !getNavVisible();
        saveBool(NAV_KEY, nextValue);
        setVisibility(nextValue, getTocVisible());
        syncButtonStates();
      });
    } else {
      button.setAttribute('aria-label', '切换右侧目录栏');
      button.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M3 5h18v14H3V5m2 2v10h10V7H5m12 0v2h2V7h-2m0 4v2h2v-2h-2m0 4v2h2v-2h-2Z"/></svg>';
      button.addEventListener('click', function() {
        var nextValue = !getTocVisible();
        saveBool(TOC_KEY, nextValue);
        setVisibility(getNavVisible(), nextValue);
        syncButtonStates();
      });
    }

    return button;
  }

  function getButtonGroup() {
    return document.querySelector('.custom-sidebar-toggle-group');
  }

  function syncButtonStates() {
    var navButton = document.querySelector('.custom-sidebar-toggle-button--nav');
    var tocButton = document.querySelector('.custom-sidebar-toggle-button--toc');
    var navVisible = getNavVisible();
    var tocVisible = getTocVisible();
    var tocExists = hasTocSidebar();

    if (navButton) {
      navButton.setAttribute('aria-pressed', navVisible ? 'true' : 'false');
      navButton.title = navVisible ? '隐藏左侧导航栏' : '显示左侧导航栏';
    }

    if (tocButton) {
      tocButton.disabled = !tocExists;
      tocButton.setAttribute('aria-disabled', tocExists ? 'false' : 'true');
      tocButton.setAttribute('aria-pressed', tocExists && tocVisible ? 'true' : 'false');
      tocButton.title = tocExists
        ? (tocVisible ? '隐藏右侧目录栏' : '显示右侧目录栏')
        : '当前页面没有右侧目录栏';
    }
  }

  function ensureButtons() {
    var headerInner = getHeaderInner();
    var headerTitle = getHeaderTitle();
    if (!headerInner || !headerTitle) {
      return;
    }

    var group = getButtonGroup();
    if (!group) {
      group = document.createElement('div');
      group.className = 'custom-sidebar-toggle-group';
      group.appendChild(createButton('nav'));
      group.appendChild(createButton('toc'));

      var searchButton = getSearchButton();
      if (searchButton && searchButton.parentNode === headerInner) {
        headerInner.insertBefore(group, searchButton);
      } else {
        headerInner.insertBefore(group, headerTitle.nextSibling);
      }
    }

    syncButtonStates();
  }

  function applyStoredVisibility() {
    setVisibility(getNavVisible(), getTocVisible());
    syncButtonStates();
  }

  function registerKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
      if (event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) {
        return;
      }

      var tagName = event.target && event.target.tagName ? event.target.tagName : '';
      if (/^(INPUT|TEXTAREA|SELECT)$/.test(tagName) || event.target.isContentEditable) {
        return;
      }

      if (event.key === 'm') {
        saveBool(NAV_KEY, !getNavVisible());
        setVisibility(getNavVisible(), getTocVisible());
        syncButtonStates();
      } else if (event.key === 't') {
        saveBool(TOC_KEY, !getTocVisible());
        setVisibility(getNavVisible(), getTocVisible());
        syncButtonStates();
      }
    });
  }

  function initSidebarToggleButtons() {
    ensureButtons();
    applyStoredVisibility();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSidebarToggleButtons);
  } else {
    initSidebarToggleButtons();
  }

  registerKeyboardShortcuts();

  if (typeof document$ !== 'undefined') {
    document$.subscribe(function() {
      setTimeout(initSidebarToggleButtons, 100);
    });
  }
})();
