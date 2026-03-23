// 标题折叠功能
(function() {
  'use strict';

  // 获取标题对应的内容区域
  function getSectionContent(heading) {
    const content = [];
    let current = heading.nextElementSibling;
    
    while (current) {
      // 如果遇到同级或更高级别的标题，停止
      if (current.tagName && /^H[1-6]$/.test(current.tagName)) {
        const currentLevel = parseInt(current.tagName.substring(1));
        const headingLevel = parseInt(heading.tagName.substring(1));
        if (currentLevel <= headingLevel) {
          break;
        }
      }
      content.push(current);
      current = current.nextElementSibling;
    }
    
    return content;
  }

  // 创建折叠容器
  function createCollapsibleWrapper(heading, content) {
    const wrapper = document.createElement('div');
    wrapper.className = 'collapsible-section';
    wrapper.style.display = 'block';
    
    // 将内容移动到 wrapper 中
    content.forEach(element => {
      wrapper.appendChild(element);
    });
    
    // 在标题后插入 wrapper
    heading.parentNode.insertBefore(wrapper, heading.nextSibling);
    
    return wrapper;
  }

  // 添加折叠图标（放在标题右侧，悬停时显示）
  function addToggleIcon(heading) {
    if (heading.querySelector('.collapsible-icon')) {
      return; // 已经添加过图标
    }
    
    const icon = document.createElement('span');
    icon.className = 'collapsible-icon';
    // 使用 SVG chevron 图标，更现代美观
    icon.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg>';
    
    // 追加到标题末尾（而不是开头）
    heading.appendChild(icon);
  }

  // 初始化标题折叠功能
  function initCollapsibleHeadings() {
    const contentArea = document.querySelector('.md-content__inner') || document.querySelector('article');
    if (!contentArea) {
      return;
    }

    // 获取所有标题（h2-h6），排除 h1（通常是页面标题）
    const headings = contentArea.querySelectorAll('h2, h3, h4, h5, h6');
    
    headings.forEach(heading => {
      // 跳过已经有折叠功能的标题（避免重复处理）
      if (heading.dataset.collapsibleInitialized) {
        return;
      }
      heading.dataset.collapsibleInitialized = 'true';
      
      const content = getSectionContent(heading);
      
      if (content.length === 0) {
        return; // 没有内容，不需要折叠
      }
      
      // 创建折叠容器并移动内容
      const wrapper = createCollapsibleWrapper(heading, content);
      
      // 添加折叠图标
      addToggleIcon(heading);
      
      // 设置标题可点击
      heading.style.cursor = 'pointer';
      heading.classList.add('collapsible-heading');
      
      // 默认展开状态
      let isExpanded = true;
      
      // 初始化样式 - 展开状态下不使用 max-height 限制
      wrapper.style.display = 'block';
      wrapper.style.overflow = 'visible'; // 展开时使用 visible，避免裁剪内容
      
      // 等待内容加载完成后再设置初始状态
      const initHeight = function() {
        // 使用 requestAnimationFrame 确保 DOM 已渲染
        requestAnimationFrame(function() {
          // 如果内容包含图片，等待图片加载
          const images = wrapper.querySelectorAll('img');
          if (images.length > 0) {
            let loadedCount = 0;
            images.forEach(function(img) {
              if (img.complete) {
                loadedCount++;
              } else {
                img.addEventListener('load', function() {
                  loadedCount++;
                  if (loadedCount === images.length) {
                    updateExpandedState();
                  }
                });
                img.addEventListener('error', function() {
                  loadedCount++;
                  if (loadedCount === images.length) {
                    updateExpandedState();
                  }
                });
              }
            });
            if (loadedCount === images.length) {
              updateExpandedState();
            }
          } else {
            updateExpandedState();
          }
        });
      };
      
      // 更新展开状态的样式
      const updateExpandedState = function() {
        if (isExpanded) {
          wrapper.style.overflow = 'visible';
          wrapper.style.maxHeight = 'none'; // 展开时移除高度限制
        }
      };
      
      // 切换函数
      const toggle = function(e) {
        // 如果点击的是链接，不处理
        if (e.target.tagName === 'A' || e.target.closest('a')) {
          return;
        }
        
        isExpanded = !isExpanded;
        const icon = heading.querySelector('.collapsible-icon');
        
        if (isExpanded) {
          // 展开
          wrapper.style.display = 'block';
          // 先设置一个较大的 max-height 用于动画
          const currentHeight = wrapper.scrollHeight;
          wrapper.style.maxHeight = currentHeight + 'px';
          wrapper.style.overflow = 'hidden';
          
          // 强制重排，确保能正确获取高度
          wrapper.offsetHeight;
          
          // 等待动画完成后移除限制
          setTimeout(function() {
            wrapper.style.maxHeight = 'none';
            wrapper.style.overflow = 'visible';
          }, 300); // 与 transition 时间一致
          
          // if (icon) {
          //   icon.style.transform = 'rotate(0deg)';
          //   icon.innerHTML = '▼';
          // }
          heading.classList.remove('collapsed');
        } else {
          // 折叠
          wrapper.style.overflow = 'hidden';
          wrapper.style.maxHeight = wrapper.scrollHeight + 'px';
          // 强制重排
          wrapper.offsetHeight;
          wrapper.style.maxHeight = '0';
          // if (icon) {
          //   icon.style.transform = 'rotate(-90deg)';
          //   icon.innerHTML = '▼';
          // }
          heading.classList.add('collapsed');
        }
      };
      
      // 绑定点击事件
      heading.addEventListener('click', toggle);
      
      // 初始化动画样式
      wrapper.style.transition = 'max-height 0.3s ease, opacity 0.3s ease';
      
      // 初始化高度
      initHeight();
    });
  }

  // 页面加载完成后初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCollapsibleHeadings);
  } else {
    initCollapsibleHeadings();
  }

  // 支持 MkDocs Material 的 instant 导航（如果启用）
  if (typeof document$ !== 'undefined') {
    document$.subscribe(function() {
      setTimeout(initCollapsibleHeadings, 100);
    });
  }

  // 监听页面变化（支持 SPA 导航）
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver(function(mutations) {
      let shouldInit = false;
      mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length > 0) {
          shouldInit = true;
        }
      });
      if (shouldInit) {
        setTimeout(initCollapsibleHeadings, 100);
      }
    });

    const contentContainer = document.querySelector('.md-content__inner') || 
                           document.querySelector('article') || 
                           document.body;
    if (contentContainer) {
      observer.observe(contentContainer, {
        childList: true,
        subtree: true
      });
    }
  }
})();

