(function() {
  'use strict';

  // Shared navigation is replaced on page changes; bind once to the document.
  if (document.getElementById('sidebar-title-tooltip')) return;
  var tooltip = document.createElement('div');
  tooltip.id = 'sidebar-title-tooltip';
  tooltip.className = 'sidebar-title-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  tooltip.hidden = true;
  document.body.appendChild(tooltip);

  function hide() { tooltip.hidden = true; }

  function linkFrom(target) {
    var link = target instanceof Element && target.closest('.md-nav__link');
    return link && !link.classList.contains('md-nav__container') &&
      link.closest('.md-sidebar--primary') ? link : null;
  }

  function show(link) {
    hide();
    if (!link) return;
    var title = link.querySelector('.sidebar-directory-name, .md-ellipsis') || link;
    var text = title.textContent.replace(/\s+/g, ' ').trim();
    if (!text) return;
    tooltip.textContent = text;
    tooltip.hidden = false;
    var row = link.getBoundingClientRect();
    var sidebar = link.closest('.md-sidebar--primary').getBoundingClientRect();
    tooltip.style.left = Math.max(8, Math.min(sidebar.right + 8,
      window.innerWidth - tooltip.offsetWidth - 8)) + 'px';
    tooltip.style.top = Math.max(8, Math.min(row.top + (row.height - tooltip.offsetHeight) / 2,
      window.innerHeight - tooltip.offsetHeight - 8)) + 'px';
  }

  document.addEventListener('pointerover', function(event) {
    if (event.pointerType === 'touch') return;
    var link = linkFrom(event.target);
    if (link && !link.contains(event.relatedTarget)) show(link);
  });
  document.addEventListener('pointerout', function(event) {
    var link = linkFrom(event.target);
    if (link && !link.contains(event.relatedTarget)) hide();
  });
  document.addEventListener('focusin', function(event) { show(linkFrom(event.target)); });
  document.addEventListener('focusout', hide);
  document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') hide();
  });
  document.addEventListener('scroll', hide, true);
  document.addEventListener('shared-navigation-ready', hide);
  window.addEventListener('resize', hide);
  window.addEventListener('blur', hide);
})();
