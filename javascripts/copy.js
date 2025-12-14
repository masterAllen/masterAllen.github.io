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
document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-copy]').forEach(function(element) {
    element.addEventListener('click', function(e) {
      e.preventDefault();
      const textToCopy = this.getAttribute('data-copy') || this.textContent;
      copyToClipboard(textToCopy);
    });
  });

  // 将文件操作链接移动到标题右侧
  document.querySelectorAll('.file-actions[data-title-link="true"]').forEach(function(fileActions) {
    const h1 = fileActions.previousElementSibling;
    if (h1 && h1.tagName === 'H1') {
      // 将 h1 设置为 flex 容器
      h1.style.display = 'flex';
      h1.style.alignItems = 'baseline';
      h1.style.justifyContent = 'space-between';
      h1.style.flexWrap = 'wrap';
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
      fileActions.style.marginLeft = 'auto';
      h1.appendChild(fileActions);
    }
  });
});
