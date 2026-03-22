/**
 * 侧边栏可拖拽调整宽度（类似 VS Code / Obsidian）
 */
(function() {
  'use strict';

  var STORAGE_KEY = 'sidebar-primary-width';
  var DEFAULT_WIDTH = 12.1; // rem, Material 默认约 12.1rem
  var MIN_WIDTH = 10;
  var MAX_WIDTH = 32;

  function getStoredWidth() {
    try {
      var stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        var num = parseFloat(stored);
        if (!isNaN(num) && num >= MIN_WIDTH && num <= MAX_WIDTH) {
          return num;
        }
      }
    } catch (e) {}
    return DEFAULT_WIDTH;
  }

  function setWidth(rem) {
    rem = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, rem));
    document.documentElement.style.setProperty('--sidebar-primary-width', rem + 'rem');
    try {
      localStorage.setItem(STORAGE_KEY, String(rem));
    } catch (e) {}
  }

  function init() {
    var sidebar = document.querySelector('.md-sidebar--primary');
    if (!sidebar) return;

    // 应用初始宽度
    setWidth(getStoredWidth());

    // 创建拖拽条（fixed 定位，挂到 body，避免被侧边栏内部滚动区遮挡）
    var handle = document.createElement('div');
    handle.className = 'sidebar-resize-handle';
    handle.setAttribute('title', '拖拽调整侧边栏宽度');
    handle.setAttribute('aria-label', '调整侧边栏宽度');
    document.body.appendChild(handle);

    function updateHandlePosition() {
      var rect = sidebar.getBoundingClientRect();
      handle.style.left = (rect.right - 6) + 'px'; // 12px 宽，居中于边缘
    }
    updateHandlePosition();
    window.addEventListener('resize', updateHandlePosition);
    window.addEventListener('scroll', updateHandlePosition, true);

    var isDragging = false;
    var startX;
    var startWidth;

    function onMouseDown(e) {
      if (e.button !== 0) return;
      isDragging = true;
      startX = e.clientX;
      startWidth = getStoredWidth();
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      handle.classList.add('sidebar-resize-handle--active');
      e.preventDefault();
    }

    function onMouseMove(e) {
      if (!isDragging) return;
      var deltaRem = (e.clientX - startX) / 16; // 16px ≈ 1rem
      setWidth(startWidth + deltaRem);
      updateHandlePosition();
    }

    function onMouseUp() {
      if (!isDragging) return;
      isDragging = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      handle.classList.remove('sidebar-resize-handle--active');
    }

    handle.addEventListener('mousedown', onMouseDown);
    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseleave', onMouseUp);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
