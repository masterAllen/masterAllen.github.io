// 仅在本地实时预览启用；页面块 ID 对应当前版本原文的字符区间。
(function () {
  const script = document.currentScript;
  const api = script.dataset.api;
  const token = script.dataset.token;
  if (!api || !['127.0.0.1', 'localhost'].includes(location.hostname)) return;

  let enabled = false;
  let toggle;
  let dialog;
  let active;
  let busy = false;
  let heartbeat;
  const draftKey = () => 'blog-text-edit:' + location.pathname;
  const timingKey = 'blog-text-edit-timing';
  const clock = () => performance.timeOrigin + performance.now();

  function pendingTiming() {
    try { return JSON.parse(sessionStorage.getItem(timingKey) || 'null'); }
    catch (_) { return null; }
  }

  function reportTiming(pending, phase) {
    const metrics = { trace_id: pending.trace_id, phase, total_ms: clock() - pending.started,
      request_ms: pending.request_ms, loads: pending.loads };
    request('timing', metrics, true).catch(() => {});
    console.info('[编辑计时]', metrics);
  }

  function checkRenderedTiming(article) {
    const pending = pendingTiming();
    if (!pending || pending.page !== location.pathname || article.dataset.editTimingSeen === pending.trace_id) return;
    article.dataset.editTimingSeen = pending.trace_id;
    pending.loads += 1;
    try { sessionStorage.setItem(timingKey, JSON.stringify(pending)); } catch (_) {}
    const revision = article.querySelector('[data-text-edit-revision]')?.dataset.textEditRevision;
    if (revision !== pending.revision) { reportTiming(pending, 'browser_stale'); return; }
    requestAnimationFrame(() => requestAnimationFrame(() => {
      if (!article.isConnected) return;
      reportTiming(pending, 'browser_content_shown');
      try { sessionStorage.removeItem(timingKey); } catch (_) {}
    }));
  }

  async function request(action, body, keepalive = false) {
    const response = await fetch(api + '/text/' + action, {
      method: 'POST', keepalive,
      headers: { 'Content-Type': 'application/json', 'X-Blog-Edit-Token': token },
      body: JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || '本地编辑服务不可用');
    return result;
  }

  function dirty() {
    return active && dialog && dialog.querySelector('textarea').value !== active.original;
  }

  function storeDraft() {
    if (!active || !dialog) return;
    try {
      if (dirty()) sessionStorage.setItem(draftKey(), JSON.stringify({
        source: active.source, revision: active.revision, block: active.block,
        kind: active.kind, original: active.original, text: dialog.querySelector('textarea').value
      }));
      else sessionStorage.removeItem(draftKey());
    } catch (_) { /* 浏览器禁用存储时，仍由离开页面确认保护当前输入。 */ }
  }

  function close(discard = false) {
    if (busy) return;
    if (!discard && dirty() && !window.confirm('放弃这次未保存的修改？')) return;
    clearInterval(heartbeat);
    if (active?.lease) request('release', { lease: active.lease }, true).catch(() => {});
    active = null;
    if (dialog) { dialog.close(); dialog.remove(); dialog = null; }
    try { sessionStorage.removeItem(draftKey()); } catch (_) {}
    document.querySelectorAll('.text-edit-selected').forEach(node => node.classList.remove('text-edit-selected'));
    toggle?.focus();
  }

  function setMode(value) {
    enabled = value;
    document.body.classList.toggle('text-edit-mode', enabled);
    if (toggle) {
      toggle.textContent = enabled ? '退出网页修改' : '网页修改';
      toggle.setAttribute('aria-pressed', String(enabled));
    }
  }

  function markBlocks(article) {
    if (article.dataset.textEditMapped) return;
    article.dataset.textEditMapped = 'true';
    const tag = article.querySelector('[data-text-edit-marker]')?.dataset.textEditMarker;
    const walker = document.createTreeWalker(article, NodeFilter.SHOW_COMMENT);
    let node, start;
    while ((node = walker.nextNode())) {
      const match = node.data.trim().match(/^blog-edit-(start|end):([a-f0-9]{16}):(b\d+)$/);
      if (!match || match[2] !== tag) continue;
      if (match[1] === 'start') { start = { node, id: match[3] }; continue; }
      if (!start || start.id !== match[3] || start.node.parentNode !== node.parentNode) {
        start = null;
        continue;
      }
      for (let item = start.node.nextSibling; item && item !== node; item = item.nextSibling) {
        if (item.nodeType === Node.ELEMENT_NODE) item.dataset.textEditBlock = start.id;
      }
      start = null;
    }
  }

  function attachToggle() {
    if (!toggle) return;
    let toolbar = document.querySelector('.floating-file-actions:not([data-text-edit-toolbar])');
    let own = document.querySelector('[data-text-edit-toolbar]');
    if (toolbar) own?.remove();
    else {
      if (!own) {
        own = document.createElement('nav');
        own.className = 'floating-file-actions';
        own.dataset.textEditToolbar = 'true';
        own.setAttribute('aria-label', '当前文章文件操作');
        document.body.appendChild(own);
      }
      toolbar = own;
    }
    if (toggle.parentElement !== toolbar) {
      toolbar.insertBefore(toggle, toolbar.querySelector('.file-action-link--image-resize, .file-action-link--secondary'));
    }
  }

  function attachFormatting(textarea, toolbar) {
    const wrappers = {
      red: ['[', '](#r)'],
      bold: ['**', '**'],
      quote: ['`', '`']
    };
    function apply(name) {
      if (textarea.disabled || toolbar.disabled) return;
      const [before, after] = wrappers[name];
      const start = textarea.selectionStart;
      const selected = textarea.value.slice(start, textarea.selectionEnd);
      const scrollTop = textarea.scrollTop;
      textarea.focus({ preventScroll: true });
      // insertText 保留浏览器原生撤销；不支持时回退到选区替换。
      if (!document.execCommand('insertText', false, before + selected + after)) {
        textarea.setRangeText(before + selected + after, start, textarea.selectionEnd, 'end');
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      }
      textarea.setSelectionRange(start + before.length, start + before.length + selected.length);
      textarea.scrollTop = scrollTop;
    }
    toolbar.addEventListener('mousedown', event => {
      if (event.target.closest('button')) event.preventDefault();
    });
    toolbar.addEventListener('click', event => {
      const button = event.target.closest('[data-format]');
      if (button) apply(button.dataset.format);
    });
    textarea.addEventListener('keydown', event => {
      if (!event.isComposing && !event.altKey && !event.shiftKey &&
          (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'b') {
        event.preventDefault();
        apply('bold');
      }
    });
  }

  async function open(block, draft) {
    if (dialog || busy) return;
    const meta = document.querySelector('article [data-text-edit-source]');
    if (!meta) return;
    const context = draft || { source: meta.dataset.textEditSource, revision: meta.dataset.textEditRevision, block };
    dialog = document.createElement('dialog');
    dialog.className = 'text-edit-dialog';
    dialog.setAttribute('aria-labelledby', 'text-edit-title');
    dialog.innerHTML = '<h2 id="text-edit-title">修改原始 Markdown</h2><p class="text-edit-file"></p>' +
      '<fieldset class="text-edit-format" disabled aria-label="文字格式">' +
      '<button type="button" data-format="red" title="将选中文字设为红色">红色</button>' +
      '<button type="button" data-format="bold" title="加粗（Ctrl+B / ⌘B）">粗体</button>' +
      '<button type="button" data-format="quote" title="添加单反引号（Markdown 行内代码）">引号</button></fieldset>' +
      '<label>原文内容<textarea spellcheck="false" aria-label="原始 Markdown 内容"></textarea></label>' +
      '<p role="status">正在读取原文…</p><div class="text-edit-actions">' +
      '<button type="button" data-save>保存</button><button type="button" data-cancel>取消</button></div>';
    document.body.appendChild(dialog);
    const current = dialog;
    const textarea = dialog.querySelector('textarea');
    const formatting = dialog.querySelector('.text-edit-format');
    attachFormatting(textarea, formatting);
    const status = dialog.querySelector('[role="status"]');
    const save = dialog.querySelector('[data-save]');
    const cancel = dialog.querySelector('[data-cancel]');
    active = { ...context, original: draft?.original || '' };
    if (draft) textarea.value = draft.text;
    textarea.disabled = save.disabled = true;
    dialog.querySelector('.text-edit-file').textContent = context.source;
    dialog.addEventListener('cancel', event => { event.preventDefault(); close(); });
    cancel.addEventListener('click', () => close());
    textarea.addEventListener('input', storeDraft);
    dialog.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault();
        if (!save.disabled) save.click();
      }
    });
    dialog.showModal();
    try {
      const result = await request('inspect', context);
      if (dialog !== current) {
        request('release', { lease: result.lease }, true).catch(() => {});
        return;
      }
      active = { ...context, ...result, original: result.text.replace(/\r\n?/g, '\n') };
      textarea.value = draft ? draft.text : result.text;
      dialog.querySelector('h2').textContent = '修改原文 · ' + result.kind;
      formatting.disabled = textarea.disabled = save.disabled = false;
      status.textContent = '选中文字后点击格式按钮；未选中时插入格式。Ctrl+B 加粗，Ctrl+S 保存。';
      heartbeat = setInterval(() => request('hold', { lease: result.lease }).catch(() => {
        status.textContent = '本地编辑连接中断，输入已保留。';
      }), 20000);
      document.querySelectorAll('[data-text-edit-block]').forEach(node => {
        if (node.dataset.textEditBlock === context.block) node.classList.add('text-edit-selected');
      });
      textarea.focus();
      storeDraft();
    } catch (error) {
      if (dialog !== current) return;
      status.textContent = error.message;
      // 过期草稿仍可选中复制，绝不依据新版本重新定位后覆盖。
      formatting.disabled = textarea.disabled = !draft;
      if (draft) textarea.focus();
    }
    save.addEventListener('click', async () => {
      const started = clock();
      busy = true;
      formatting.disabled = save.disabled = cancel.disabled = textarea.disabled = toggle.disabled = true;
      status.textContent = '正在保存…';
      try {
        const result = await request('save', { ...active, text: textarea.value });
        if (result.trace_id && result.changed) {
          const pending = { trace_id: result.trace_id, revision: result.revision, page: location.pathname,
            started, request_ms: clock() - started, loads: 0 };
          try { sessionStorage.setItem(timingKey, JSON.stringify(pending)); } catch (_) {}
          reportTiming(pending, 'save_response');
        }
        active.original = textarea.value;
        active.lease = null;
        try { sessionStorage.removeItem(draftKey()); } catch (_) {}
        busy = false;
        close(true);
        if (result.changed) {
          const notice = document.createElement('div');
          notice.className = 'text-edit-notice';
          notice.setAttribute('role', 'status');
          notice.textContent = '已写入原文，正在等待页面更新…';
          document.body.appendChild(notice);
          setTimeout(() => { notice.textContent = '原文已保存；页面尚未更新，可刷新或检查预览终端。'; }, 12000);
        }
      } catch (error) {
        status.textContent = error.message || '保存失败，输入已保留。';
        formatting.disabled = save.disabled = textarea.disabled = false;
        storeDraft();
      } finally {
        busy = false;
        cancel.disabled = toggle.disabled = false;
      }
    });
  }

  function init() {
    if (dialog) return;
    toggle?.remove();
    toggle = null;
    document.querySelector('[data-text-edit-toolbar]')?.remove();
    document.querySelectorAll('.text-edit-notice').forEach(node => node.remove());
    const article = document.querySelector('article.md-content__inner');
    if (!article?.querySelector('[data-text-edit-source]')) { setMode(false); return; }
    markBlocks(article);
    checkRenderedTiming(article);
    toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'file-action-link';
    toggle.addEventListener('click', () => {
      if (!enabled && !document.dispatchEvent(new CustomEvent('blog-edit-mode', {
        detail: 'text', cancelable: true
      }))) return;
      setMode(!enabled);
    });
    attachToggle();
    let restoreMode = false;
    try {
      restoreMode = sessionStorage.getItem('blog-text-edit-mode') === location.pathname;
      sessionStorage.removeItem('blog-text-edit-mode');
    } catch (_) {}
    setMode(enabled || restoreMode);
    try {
      const draft = JSON.parse(sessionStorage.getItem(draftKey()) || 'null');
      if (draft && draft.source === article.querySelector('[data-text-edit-source]').dataset.textEditSource) {
        setMode(true);
        open(draft.block, draft);
      }
    } catch (_) {}
  }

  document.addEventListener('click', event => {
    if (!enabled || dialog || !(event.target instanceof Element)) return;
    const block = event.target.closest('article [data-text-edit-block]');
    if (!block) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    open(block.dataset.textEditBlock);
  }, true);
  document.addEventListener('pointerover', event => {
    if (!(event.target instanceof Element)) return;
    const block = enabled ? event.target.closest('article [data-text-edit-block]') : null;
    const id = block?.dataset.textEditBlock;
    document.querySelectorAll('[data-text-edit-block]').forEach(node => {
      node.classList.toggle('text-edit-hover', Boolean(id && node.dataset.textEditBlock === id));
    });
  });
  document.addEventListener('blog-edit-mode', event => {
    if (event.detail !== 'text') {
      if (dialog) event.preventDefault();
      else setMode(false);
    }
  });
  window.addEventListener('beforeunload', event => {
    storeDraft();
    try { if (enabled) sessionStorage.setItem('blog-text-edit-mode', location.pathname); } catch (_) {}
    if (dirty()) { event.preventDefault(); event.returnValue = ''; }
  });
  window.addEventListener('pagehide', () => {
    const pending = pendingTiming();
    if (pending?.page === location.pathname) reportTiming(pending, 'browser_leaving');
    if (active?.lease) request('release', { lease: active.lease }, true).catch(() => {});
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
  if (typeof document$ !== 'undefined') document$.subscribe(init);
  new MutationObserver(attachToggle).observe(document.body, { childList: true });
})();
