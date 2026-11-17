// 代码块标题栏、完整复制与长代码预览；语法高亮使用主题原生功能。
(function() {
  'use strict';

  function setupCodeBlocks() {
    document.querySelectorAll('.md-content__inner div.highlight').forEach(function(block, index) {
      const code = block.querySelector(':scope > pre > code');
      if (!code || block.classList.contains('code-block')) return;

      const languageClass = Array.from(block.classList).find(function(name) {
        return name.startsWith('language-');
      });
      const language = languageClass ? languageClass.slice(9) : 'text';
      const lines = code.textContent.replace(/\n$/, '').split('\n').length;
      block.classList.add('code-block');
      if (language === 'text' || (lines === 1 && /^(bash|sh|shell|console|powershell|ps1|batch)$/.test(language))) {
        block.classList.add('code-block--no-linenos');
      }

      const toolbar = document.createElement('div');
      toolbar.className = 'code-block__toolbar';
      const title = document.createElement('span');
      title.className = 'code-block__title';
      const filename = block.querySelector(':scope > .filename');
      title.textContent = filename ? filename.textContent : (language === 'text' ? '纯文本' : language);
      if (filename) filename.remove();
      toolbar.appendChild(title);
      if (!block.classList.contains('no-copy')) {
        const copy = document.createElement('button');
        copy.type = 'button';
        copy.className = 'code-block__copy';
        copy.textContent = '复制';
        copy.setAttribute('aria-label', '复制完整代码');
        copy.addEventListener('click', async function() {
          try {
            await navigator.clipboard.writeText(code.textContent);
            copy.textContent = '已复制';
          } catch (error) {
            copy.textContent = '复制失败';
          }
          setTimeout(function() { copy.textContent = '复制'; }, 2000);
        });
        toolbar.appendChild(copy);
      }
      block.insertBefore(toolbar, block.firstChild);

      if (lines <= 30) return;
      const toggle = document.createElement('button');
      toggle.type = 'button';
      toggle.className = 'code-block__toggle';
      if (!code.id) code.id = 'code-preview-' + index;
      toggle.setAttribute('aria-controls', code.id);
      function setExpanded(expanded) {
        block.classList.toggle('code-block--collapsed', !expanded);
        toggle.setAttribute('aria-expanded', String(expanded));
        toggle.textContent = expanded ? '收起（预览 15 行）' : '展开全部（' + lines + ' 行）';
      }
      setExpanded(false);
      toggle.addEventListener('click', function() {
        setExpanded(toggle.getAttribute('aria-expanded') !== 'true');
      });
      block.appendChild(toggle);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setupCodeBlocks);
  } else {
    setupCodeBlocks();
  }
  if (typeof document$ !== 'undefined') document$.subscribe(setupCodeBlocks);
})();
