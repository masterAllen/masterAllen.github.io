(function () {
  'use strict';

  var STORAGE_KEY = 'BLOG_REVIEW_TRACKER_V1';
  var INTERVALS = [1, 3, 7, 14, 30, 60, 120, 180];
  var LABELS = {
    again: '忘记了',
    hard: '有些模糊',
    good: '记得',
    easy: '很熟练'
  };

  function today() {
    var date = new Date();
    return date.toISOString().slice(0, 10);
  }

  function addDays(dateText, days) {
    var date = new Date(dateText + 'T00:00:00');
    date.setDate(date.getDate() + days);
    return date.toISOString().slice(0, 10);
  }

  function loadState() {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
    } catch (error) {
      return {};
    }
  }

  function saveState(state) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      // 隐私模式或浏览器禁用存储时，页面仍应可以正常阅读。
    }
  }

  function currentKey() {
    return window.location.pathname.replace(/\/+$/, '') || '/';
  }

  function isDue(record) {
    return !record || !record.nextReview || record.nextReview <= today();
  }

  function formatDate(dateText) {
    return dateText === today() ? '今天' : dateText;
  }

  function schedule(key, result) {
    var state = loadState();
    var old = state[key] || { interval: 0, repetitions: 0 };
    var interval;

    if (result === 'again') {
      interval = 1;
    } else if (result === 'hard') {
      interval = Math.max(1, Math.round((old.interval || 1) * 1.3));
    } else {
      var multiplier = result === 'easy' ? 3 : 2;
      var index = INTERVALS.indexOf(old.interval);
      if (index >= 0) {
        interval = INTERVALS[Math.min(INTERVALS.length - 1, index + (result === 'easy' ? 2 : 1))];
      } else {
        interval = Math.max(1, Math.round((old.interval || 1) * multiplier));
      }
    }

    state[key] = {
      lastReview: today(),
      nextReview: addDays(today(), interval),
      interval: interval,
      repetitions: (old.repetitions || 0) + 1,
      result: result,
      title: document.title.replace(/\s+-\s+Allen Hong's Notes\s*$/, '')
    };
    saveState(state);
    var oldPanel = document.querySelector('.review-tracker');
    if (oldPanel) oldPanel.remove();
    renderWidget();
  }

  function button(text, className, handler) {
    var element = document.createElement('button');
    element.type = 'button';
    element.className = 'review-tracker__button ' + className;
    element.textContent = text;
    element.addEventListener('click', handler);
    return element;
  }

  function renderWidget() {
    var article = document.querySelector('article.md-content__inner');
    var heading = article && article.querySelector('h1');
    if (!article || !heading || document.querySelector('.review-tracker')) return;

    var key = currentKey();
    var record = loadState()[key];
    var panel = document.createElement('section');
    panel.className = 'review-tracker';
    panel.setAttribute('aria-label', '知识复习');

    var title = document.createElement('div');
    title.className = 'review-tracker__title';
    title.textContent = record && record.nextReview && !isDue(record)
      ? '复习安排：下次 ' + formatDate(record.nextReview)
      : '复习提醒：这篇文章今天需要复习';
    panel.appendChild(title);

    var hint = document.createElement('div');
    hint.className = 'review-tracker__hint';
    hint.textContent = record ? '上次复习：' + formatDate(record.lastReview) + ' · 间隔 ' + record.interval + ' 天' : '还没有记录复习时间';
    panel.appendChild(hint);

    var actions = document.createElement('div');
    actions.className = 'review-tracker__actions';
    Object.keys(LABELS).forEach(function (result) {
      actions.appendChild(button(LABELS[result], 'review-tracker__button--' + result, function () {
        schedule(key, result);
      }));
    });
    actions.appendChild(button('查看复习记录', 'review-tracker__button--secondary', showSummary));
    panel.appendChild(actions);
    article.appendChild(panel);
  }

  function showSummary() {
    var state = loadState();
    var keys = Object.keys(state).sort(function (a, b) {
      return (state[a].nextReview || '').localeCompare(state[b].nextReview || '');
    });
    var overlay = document.createElement('div');
    overlay.className = 'review-tracker__overlay';
    var dialog = document.createElement('section');
    dialog.className = 'review-tracker__dialog';
    dialog.setAttribute('role', 'dialog');
    dialog.setAttribute('aria-modal', 'true');
    dialog.innerHTML = '<div class="review-tracker__dialog-header"><strong>复习记录</strong><button type="button" class="review-tracker__close" aria-label="关闭">×</button></div>';
    var body = document.createElement('div');
    body.className = 'review-tracker__dialog-body';

    if (!keys.length) {
      body.textContent = '还没有复习记录。在文章顶部选择一次复习结果即可开始。';
    } else {
      var dueCount = keys.filter(function (key) { return isDue(state[key]); }).length;
      var summary = document.createElement('p');
      summary.textContent = '已记录 ' + keys.length + ' 篇，今日到期 ' + dueCount + ' 篇。';
      body.appendChild(summary);
      keys.forEach(function (key) {
        var item = document.createElement('a');
        item.className = 'review-tracker__item';
        item.href = key + '/';
        item.innerHTML = '<span>' + escapeHtml(state[key].title || key) + '</span><small>' + (isDue(state[key]) ? '今天复习' : '下次 ' + state[key].nextReview) + '</small>';
        body.appendChild(item);
      });
    }
    dialog.appendChild(body);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    dialog.querySelector('.review-tracker__close').addEventListener('click', function () { overlay.remove(); });
    overlay.addEventListener('click', function (event) { if (event.target === overlay) overlay.remove(); });
  }

  function escapeHtml(value) {
    return String(value).replace(/[&<>"']/g, function (character) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[character];
    });
  }

  function init() {
    renderWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  if (typeof document$ !== 'undefined') {
    document$.subscribe(function () {
      setTimeout(init, 100);
    });
  }
})();
