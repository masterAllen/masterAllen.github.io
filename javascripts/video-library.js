(function() {
  'use strict';
  if (window.blogVideoLibraryInit) { window.blogVideoLibraryInit(); return; }
  function init() {
    const root = document.getElementById('video-library');
    if (!root || root.dataset.initialized) return;
    root.dataset.initialized = 'true';
    const $ = selector => root.querySelector(selector);
    const api = root.dataset.api + '/local-video-library/';
    const dialog = $('.vl-dialog'), form = dialog.querySelector('form');
    let data, page = 0, editing, baseline = '', busy = false, visible = [];
    const labels = {title: '显示标题', lecturer: '讲师 / 原创作者', uploader: '上传者 / UP 主', platform: '平台', source_url: '单集来源链接', rating: '推荐度', notes: '备注', status: '确认状态', name: '课程 / 系列名称', collection_url: '课程 / 合集链接', group: '所属课程 / 系列'};
    const node = (tag, text, className) => {
      const element = document.createElement(tag);
      if (text !== undefined) element.textContent = text;
      if (className) element.className = className;
      return element;
    };
    function status(video) {
      if (video.missing) return 'missing';
      if (video.manual.status) return video.manual.status;
      return Object.keys(video.manual).length || video.effective.lecturer || video.effective.uploader || video.effective.platform || Object.keys(video.detected.tags || {}).some(k => /^(artist|title|description)$/i.test(k)) ? 'candidate' : 'unfilled';
    }
    const statusLabels = {missing: '文件缺失', confirmed: '已确认', candidate: '待确认', unfilled: '待整理'};
    function option(select, value, text) { const o = node('option', text); o.value = value; select.append(o); }
    async function request(action, payload) {
      const response = await fetch(api + action, payload === undefined ? {} : {
        method: 'POST', headers: {'Content-Type': 'application/json', 'X-Blog-Video-Token': data.token}, body: JSON.stringify(payload)
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(result.message || (response.status === 409 ? '登记已更新。请保留输入，取消后重新载入再编辑。' : '操作失败（' + response.status + '）'));
      return result;
    }
    function populate() {
      for (const [name, values] of [
        ['group', Object.entries(data.groups).sort((a, b) => a[1].name.localeCompare(b[1].name, 'zh')).map(([id, g]) => [id, g.name])],
        ['platform', [...new Set(data.videos.map(v => v.effective.platform).filter(Boolean))].sort().map(p => [p, p])]
      ]) {
        const select = $('[name=' + name + ']'), previous = select.value;
        while (select.options.length > 1) select.remove(1);
        values.forEach(([value, text]) => option(select, value, text));
        select.value = previous;
      }
      const stats = $('.vl-stats'); stats.replaceChildren();
      for (const [label, count] of [['视频文件', data.videos.length], ['课程 / 系列', Object.keys(data.groups).length], ['已确认', data.videos.filter(v => status(v) === 'confirmed').length], ['文件缺失', data.videos.filter(v => v.missing).length]]) {
        const box = node('div'); box.append(node('strong', count), node('span', label)); stats.append(box);
      }
      render();
    }
    function render() {
      const query = $('[name=search]').value.trim().toLowerCase(), group = $('[name=group]').value, state = $('[name=status]').value, platform = $('[name=platform]').value;
      visible = data.videos.filter(v => (!group || v.group === group) && (!state || status(v) === state) && (!platform || v.effective.platform === platform) &&
        (!query || [v.path, ...Object.values(v.effective), data.groups[v.group]?.name].join(' ').toLowerCase().includes(query)));
      const sort = $('[name=sort]').value;
      visible.sort((a, b) => sort === 'rating' ? (Number(b.effective.rating) - Number(a.effective.rating) || a.path.localeCompare(b.path, 'zh')) : (sort === 'title' ? a.effective.title.localeCompare(b.effective.title, 'zh') : a.path.localeCompare(b.path, 'zh', {numeric: true})));
      const pages = Math.max(1, Math.ceil(visible.length / 40)); page = Math.min(page, pages - 1);
      const body = $('tbody'); body.replaceChildren();
      visible.slice(page * 40, (page + 1) * 40).forEach(v => {
        const row = node('tr'), title = node('td');
        title.append(node('strong', v.effective.title), node('small', data.groups[v.group]?.name || ''), node('small', v.path));
        const author = node('td', v.effective.lecturer || '—'); author.append(node('small', '上传者：' + (v.effective.uploader || '—')));
        const stateCell = node('td'); stateCell.append(node('span', statusLabels[status(v)], 'vl-badge'));
        const actions = node('td');
        for (const [action, text] of [['edit', '编辑'], ['play', '播放']]) {
          const button = node('button', text); button.type = 'button'; button.dataset.action = action; button.dataset.id = v.id;
          button.disabled = action === 'play' && v.missing; actions.append(button);
        }
        if (v.effective.source_url) {
          const link = node('a', '来源'); link.href = v.effective.source_url; link.target = '_blank'; link.rel = 'noopener'; actions.append(link);
        }
        row.append(title, author, node('td', v.effective.platform || '—'), node('td', v.effective.rating ? '★'.repeat(Number(v.effective.rating)) : '—'), stateCell, actions); body.append(row);
      });
      if (!visible.length) { const row = node('tr'), cell = node('td', '没有符合条件的视频。'); cell.colSpan = 6; row.append(cell); body.append(row); }
      $('.vl-message').textContent = '共 ' + data.videos.length + ' 个视频，当前显示 ' + visible.length + ' 个。';
      $('.vl-pagination span').textContent = (page + 1) + ' / ' + pages;
      $('[data-action=prev]').disabled = page === 0; $('[data-action=next]').disabled = page + 1 >= pages;
      $('[data-action=group]').disabled = !group;
    }
    function values() { return JSON.stringify(Object.fromEntries(new FormData(form))); }
    function dirty() { return dialog.open && values() !== baseline; }
    function openEditor(kind, id) {
      editing = {kind, id, revision: data.revision};
      const v = kind === 'video' ? data.videos.find(v => v.id === id) : null;
      const group = data.groups[v ? v.group : id], existing = v ? v.manual : group;
      const fields = v ? ['group', 'title', 'lecturer', 'uploader', 'platform', 'source_url', 'rating', 'status', 'notes'] : ['name', 'lecturer', 'uploader', 'platform', 'collection_url'];
      dialog.querySelector('h2').textContent = v ? '编辑视频' : '维护课程 · 批量应用';
      const tags = v?.detected.tags || {};
      const evidence = v ? [v.path, '扫描线索（未确认）：', ...Object.entries(tags).filter(([k]) => /^(title|artist|description|date)$/i.test(k)).map(([k, val]) => k + ': ' + val), '空白字段恢复继承课程信息。'] : ['当前课程包含 ' + data.videos.filter(v => v.group === id).length + ' 个视频。', '修改会应用于没有单独填写相应字段的视频。合集链接与单集链接分别保存。'];
      $('.vl-evidence').textContent = evidence.join('\n'); $('.vl-error').textContent = '';
      const container = $('.vl-fields'); container.replaceChildren();
      fields.forEach(name => {
        const label = node('label', labels[name]); if (['title', 'source_url', 'collection_url', 'notes', 'group', 'name'].includes(name)) label.className = 'vl-wide';
        let input;
        if (['group', 'rating', 'status'].includes(name)) {
          input = node('select');
          if (name === 'group') Object.entries(data.groups).forEach(([key, g]) => option(input, key, g.name));
          else if (name === 'rating') { option(input, '', '未评分'); for (let i = 1; i <= 5; i++) option(input, String(i), '★'.repeat(i)); }
          else { option(input, '', '尚未确认'); option(input, 'candidate', '待确认'); option(input, 'confirmed', '已确认'); }
        } else {
          input = node(name === 'notes' ? 'textarea' : 'input');
          if (name.endsWith('_url')) input.type = 'url';
          input.maxLength = name === 'notes' ? 10000 : 1000;
          input.placeholder = v && group[name] ? '沿用课程：' + group[name] : name === 'title' && v ? v.effective.title : '留空';
        }
        input.name = name; input.value = name === 'group' ? v.group : existing[name] || '';
        if (name === 'name') input.required = true;
        label.append(input); container.append(label);
      });
      baseline = values(); dialog.showModal();
    }
    function closeEditor() { if (!dirty() || window.confirm('有未保存的修改，确定放弃吗？')) dialog.close(); }
    dialog.addEventListener('cancel', e => { e.preventDefault(); if (!busy) closeEditor(); });
    form.addEventListener('submit', async event => {
      event.preventDefault(); if (busy) return;
      busy = true; form.querySelector('[type=submit]').disabled = true;
      try {
        data = await request('save', {...editing, fields: Object.fromEntries(new FormData(form))});
        baseline = values(); dialog.close(); populate(); $('.vl-message').textContent += ' 已保存。';
      } catch (error) { $('.vl-error').textContent = error.message; }
      finally { busy = false; form.querySelector('[type=submit]').disabled = false; }
    });
    root.addEventListener('input', e => { if (e.target.closest('.vl-toolbar') && data) { page = 0; render(); } });
    root.addEventListener('click', async event => {
      const button = event.target.closest('[data-action]'); if (!button || busy) return;
      const action = button.dataset.action;
      if (action === 'cancel') return closeEditor();
      if (action === 'close-player') return $('.vl-player').close();
      if (!data && action !== 'reload') return;
      if (action === 'edit') return openEditor('video', button.dataset.id);
      if (action === 'group') return openEditor('group', $('[name=group]').value);
      if (action === 'prev' || action === 'next') { page += action === 'prev' ? -1 : 1; return render(); }
      if (action === 'play') {
        const v = data.videos.find(v => v.id === button.dataset.id);
        $('.vl-player h2').textContent = v.effective.title; $('.vl-player video').src = api + 'media/' + v.id; return $('.vl-player').showModal();
      }
      if (action === 'scan' || action === 'reload') {
        busy = true; button.disabled = true; $('.vl-message').textContent = action === 'scan' ? '正在扫描；首次需要读取视频内容生成指纹，请稍候…' : '正在载入…';
        try { data = await request(action === 'scan' ? 'scan' : 'catalog', action === 'scan' ? {} : undefined); populate(); }
        catch (error) { $('.vl-message').textContent = error.message; }
        finally { busy = false; button.disabled = false; }
      }
    });
    $('.vl-player').addEventListener('close', () => { const video = $('.vl-player video'); video.pause(); video.removeAttribute('src'); video.load(); });
    window.addEventListener('beforeunload', e => { if (dirty()) { e.preventDefault(); e.returnValue = ''; } });
    request('catalog').then(result => { data = result; populate(); }).catch(error => { $('.vl-message').textContent = '无法载入：' + error.message; });
  }
  window.blogVideoLibraryInit = init;
  init();
  if (typeof document$ !== 'undefined') document$.subscribe(init);
})();
