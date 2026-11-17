// 仅由 live_preview.py 启用；沿用原文的 #wNN 或已有 zoom 写法。
(function () {
  const script = document.currentScript;
  const api = script.dataset.api;
  const token = script.dataset.token;
  if (!api || !['127.0.0.1', 'localhost'].includes(location.hostname)) return;

  let enabled = false;
  let active = null;
  let panel;
  let toggle;
  let busy = false;
  let generation = 0;

  const stripWidth = value => value.replace(/(?:#|%23)w\d+$/i, '');

  async function request(action, body) {
    const response = await fetch(api + action, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Blog-Edit-Token': token },
      body: JSON.stringify(body)
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error);
    return result;
  }

  function close() {
    generation += 1;
    if (active) {
      active.image.setAttribute('src', active.original);
      if (active.originalStyle === null) active.image.removeAttribute('style');
      else active.image.setAttribute('style', active.originalStyle);
      active.image.classList.remove('image-resize-selected');
    }
    active = null;
    if (panel) panel.remove();
  }

  function init() {
    close();
    enabled = false;
    busy = false;
    document.body.classList.remove('image-resize-mode');
    if (toggle) toggle.remove();
    const toolbar = document.querySelector('.floating-file-actions');
    if (!document.querySelector('.md-content__inner [data-copy]')) return;
    toggle = document.createElement('button');
    toggle.type = 'button';
    toggle.className = 'file-action-link file-action-link--image-resize';
    toggle.textContent = '图片缩放';
    toggle.setAttribute('aria-pressed', 'false');
    toggle.addEventListener('click', function () {
      if (busy) return;
      if (!enabled && !document.dispatchEvent(new CustomEvent('blog-edit-mode', {
        detail: 'image', cancelable: true
      }))) return;
      close();
      enabled = !enabled;
      document.body.classList.toggle('image-resize-mode', enabled);
      toggle.textContent = enabled ? '退出图片缩放' : '图片缩放';
      toggle.setAttribute('aria-pressed', String(enabled));
    });
    if (toolbar) toolbar.insertBefore(toggle, toolbar.querySelector('.file-action-link--secondary'));
  }

  document.addEventListener('click', async function (event) {
    const image = event.target.closest('article.md-content__inner img');
    if (!enabled || !image) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (busy) return;
    close();
    const currentGeneration = generation;
    const source = document.querySelector('.md-content__inner [data-copy]').dataset.copy;
    const pageRevision = document.querySelector('.md-content__inner [data-image-edit-revision]')?.dataset.imageEditRevision;
    const peers = Array.from(document.querySelectorAll('article.md-content__inner img'))
      .filter(item => stripWidth(item.src) === stripWidth(image.src));
    panel = document.createElement('div');
    panel.className = 'image-resize-panel';
    panel.setAttribute('role', 'dialog');
    panel.setAttribute('aria-label', '调整图片宽度');
    panel.innerHTML = '<label><span data-size-label>正文宽度</span> <output></output><input type="range" min="5" max="200" step="5" aria-label="图片占正文宽度百分比"></label>' +
      '<div><button type="button" data-save>保存</button><button type="button" data-cancel>取消</button></div>' +
      '<p role="status">正在定位原始图片…</p>';
    document.body.appendChild(panel);
    const currentPanel = panel;
    const range = panel.querySelector('input');
    const output = panel.querySelector('output');
    const status = panel.querySelector('[role="status"]');
    const save = panel.querySelector('[data-save]');
    const cancel = panel.querySelector('[data-cancel]');
    range.disabled = save.disabled = true;
    cancel.addEventListener('click', () => { if (!busy) close(); });

    try {
      const context = await request('/inspect', {
        source, page_revision: pageRevision, images: peers.map(item => item.src), occurrence: peers.indexOf(image)
      });
      if (generation !== currentGeneration) return;
      active = { image, original: image.getAttribute('src'), originalStyle: image.getAttribute('style') };
      image.classList.add('image-resize-selected');
      if (context.mode === 'zoom') {
        panel.querySelector('[data-size-label]').textContent = '显示缩放比例';
        range.setAttribute('aria-label', '图片显示缩放百分比');
      }
      const initialWidth = context.width || image.getBoundingClientRect().width / image.parentElement.clientWidth * 100;
      range.value = Math.max(5, Math.min(200, Math.round(initialWidth / 5) * 5));
      output.value = range.value + '%';
      range.disabled = save.disabled = false;
      status.textContent = context.storage === 'metadata'
        ? '拖动预览，保存后记录这张照片的显示比例。' : '拖动预览，保存后写回原始 MD。';
      range.addEventListener('input', function () {
        output.value = range.value + '%';
        if (context.mode === 'zoom') {
          image.style.setProperty('zoom', range.value + '%', image.style.getPropertyPriority('zoom'));
        } else {
          image.setAttribute('src', stripWidth(active.original) + '#w' + range.value);
        }
      });
      range.dispatchEvent(new Event('input'));
      save.addEventListener('click', async function () {
        busy = true;
        range.disabled = save.disabled = cancel.disabled = toggle.disabled = true;
        status.textContent = '正在保存…';
        try {
          await request('/save', { source, index: context.index, revision: context.revision, width: Number(range.value) });
          if (generation !== currentGeneration) return;
          if (context.mode === 'zoom') {
            image.style.setProperty('zoom', range.value + '%', image.style.getPropertyPriority('zoom'));
            active.originalStyle = image.getAttribute('style');
          } else {
            active.original = stripWidth(active.original) + '#w' + range.value;
            image.setAttribute('src', active.original);
          }
          save.disabled = range.disabled = true;
          status.textContent = context.storage === 'metadata'
            ? '已保存图片显示比例，预览将自动刷新。' : '已保存到原始 MD，预览将自动刷新。';
        } catch (error) {
          if (generation !== currentGeneration) return;
          status.textContent = error.message || '保存失败，请取消后重试。';
          range.disabled = save.disabled = false;
        } finally {
          busy = false;
          cancel.disabled = toggle.disabled = false;
        }
      });
      range.focus();
    } catch (error) {
      if (generation === currentGeneration && panel === currentPanel) {
        status.textContent = error.message || '无法连接本地编辑服务，请重启实时预览。';
      }
    }
  }, true);

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !busy) close();
  });
  document.addEventListener('blog-edit-mode', event => {
    if (event.detail === 'image') return;
    if (busy) { event.preventDefault(); return; }
    close();
    enabled = false;
    document.body.classList.remove('image-resize-mode');
    if (toggle) {
      toggle.textContent = '图片缩放';
      toggle.setAttribute('aria-pressed', 'false');
    }
  });
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
  if (typeof document$ !== 'undefined') document$.subscribe(init);
  // copy.js 在导航及初始化时重建工具栏，把已有按钮挂回新容器。
  new MutationObserver(() => {
    const toolbar = document.querySelector('.floating-file-actions');
    if (toggle && toolbar && toggle.parentElement !== toolbar) toolbar.insertBefore(toggle, toolbar.querySelector('.file-action-link--secondary'));
  }).observe(document.body, { childList: true });
})();
