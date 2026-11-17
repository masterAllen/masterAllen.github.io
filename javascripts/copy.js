// docs/javascripts/copy.js
function copyToClipboard(text) {
  navigator.clipboard.writeText(text).then(function() {
    // 可选：显示复制成功的提示
    const notification = document.createElement('div');
    notification.textContent = '已复制到剪贴板！';
    notification.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      background: #333;
      color: white;
      padding: 10px;
      border-radius: 4px;
      z-index: 1000;
    `;
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
  }).catch(function(err) {
    console.error('复制失败: ', err);
  });
}

// 为所有带有 data-copy 属性的元素添加点击事件
function initArticleActions() {
  document.querySelectorAll('[data-copy]').forEach(function(element) {
    if (element.dataset.copyBound) return;
    element.dataset.copyBound = 'true';
    element.addEventListener('click', function(e) {
      e.preventDefault();
      const textToCopy = this.getAttribute('data-copy') || this.textContent;
      copyToClipboard(textToCopy);
    });
  });

  // 将文件操作链接放在标题下一行，并居中显示
  document.querySelectorAll('.file-actions[data-title-link="true"]').forEach(function(fileActions) {
    const h1 = fileActions.previousElementSibling;
    if (h1 && h1.tagName === 'H1') {
      // 将 h1 设置为 flex 容器
      h1.style.display = 'flex';
      h1.style.flexDirection = 'column';
      h1.style.alignItems = 'center';
      h1.style.gap = '0.5rem';
      
      // 将 h1 的现有内容包装在一个 span 中（保留所有子元素）
      const wrapper = document.createElement('span');
      wrapper.className = 'h1-content';
      wrapper.style.flex = '1';
      
      // 将 h1 的所有子节点移动到 wrapper 中
      while (h1.firstChild) {
        wrapper.appendChild(h1.firstChild);
      }
      
      // 将 wrapper 和 file-actions 添加到 h1
      h1.appendChild(wrapper);
      
      // 将 file-actions 移动到 h1 内部
      fileActions.style.margin = '0';
      h1.appendChild(fileActions);
    }
  });

  openContentLinksInNewTab();
}
document.addEventListener('DOMContentLoaded', initArticleActions);
if (typeof document$ !== 'undefined') document$.subscribe(initArticleActions);

// 正文链接新开标签页（侧栏 / 顶栏 / 底栏导航仍在当前页跳转）
function openContentLinksInNewTab() {
  const root = document.querySelector('article.md-content__inner') ||
               document.querySelector('.md-content__inner');
  if (!root) return;

  root.querySelectorAll('a[href]').forEach(function(anchor) {
    const href = anchor.getAttribute('href');
    if (!href || href.startsWith('javascript:')) return;
    if (anchor.classList.contains('file-action-link') && !/^https?:/i.test(href)) return;
    if (isSamePageHashLink(href)) return;

    anchor.setAttribute('target', '_blank');
    const rel = (anchor.getAttribute('rel') || '').split(/\s+/).filter(Boolean);
    ['noopener', 'noreferrer'].forEach(function(token) {
      if (rel.indexOf(token) === -1) rel.push(token);
    });
    anchor.setAttribute('rel', rel.join(' '));
  });
}

function isSamePageHashLink(href) {
  if (href.charAt(0) === '#') return true;
  try {
    const url = new URL(href, window.location.href);
    return url.origin === window.location.origin &&
           url.pathname === window.location.pathname &&
           !!url.hash;
  } catch (e) {
    return false;
  }
}

// 当前文章的文件操作始终显示在右下角。
(function() {
  let toolbar;

  function initFloatingFileActions() {
    if (toolbar) toolbar.remove();

    const source = document.querySelector('.md-content__inner .file-actions[data-title-link="true"]');
    if (!source) return;

    toolbar = document.createElement('nav');
    toolbar.className = 'floating-file-actions';
    toolbar.setAttribute('aria-label', '当前文章文件操作');

    source.querySelectorAll('.file-action-link').forEach(function(element) {
      let action;
      if (element.hasAttribute('data-copy')) {
        action = document.createElement('button');
        action.type = 'button';
        action.className = 'file-action-link';
        action.textContent = element.textContent;
        action.addEventListener('click', function() {
          copyToClipboard(element.getAttribute('data-copy'));
        });
      } else {
        action = element.cloneNode(true);
      }
      if (element.hasAttribute('data-copy') || (element.getAttribute('href') || '').startsWith('blog-folder:')) {
        action.classList.add('file-action-link--secondary');
      }
      toolbar.appendChild(action);
    });
    document.body.appendChild(toolbar);

    source.hidden = true;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initFloatingFileActions);
  } else {
    initFloatingFileActions();
  }
  if (typeof document$ !== 'undefined') {
    document$.subscribe(initFloatingFileActions);
  }
})();
