(function() {
  'use strict';

  var STORAGE_KEY = 'CUSTOM_SIDEBAR_SCROLL_TOP';

  function getScrollwrap() {
    return document.querySelector('.md-sidebar--primary .md-sidebar__scrollwrap');
  }

  function savePosition() {
    var scrollwrap = getScrollwrap();
    if (!scrollwrap) return;

    try {
      sessionStorage.setItem(STORAGE_KEY, String(scrollwrap.scrollTop));
    } catch (e) {}
  }

  function restorePosition() {
    var scrollwrap = getScrollwrap();
    if (!scrollwrap) return;

    try {
      var stored = sessionStorage.getItem(STORAGE_KEY);
      if (stored !== null) {
        scrollwrap.scrollTop = Number(stored) || 0;
      }
    } catch (e) {}
  }

  window.addEventListener('pagehide', savePosition);
  document.addEventListener('shared-navigation-ready', restorePosition);

  restorePosition();
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      requestAnimationFrame(function() {
        requestAnimationFrame(restorePosition);
      });
    });
  }
})();
