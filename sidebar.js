(() => {
  'use strict';
  const sidebar = document.querySelector('aside');
  if (!sidebar) return;

  // Pass position in local links as well: file:// storage is browser-dependent.
  const positionParam = 'sidebarScroll';
  const current = new URL(window.location.href);
  const root = new URL(current.pathname.endsWith('/index.html') ? './' : '../', current);
  const storageKey = 'deepagents-sidebar:' + root.href;
  let saved = current.searchParams.get(positionParam);
  if (saved === null) {
    try { saved = sessionStorage.getItem(storageKey); } catch (_) {}
  }
  const position = saved === null ? NaN : Number(saved);
  const validPosition = Number.isFinite(position) && position >= 0;
  const links = Array.from(sidebar.querySelectorAll('a[href]'));
  const active = links.find(link => new URL(link.href).pathname === current.pathname);
  if (active) active.setAttribute('aria-current', 'page');

  function remember() {
    try { sessionStorage.setItem(storageKey, String(sidebar.scrollTop)); } catch (_) {}
  }
  function restore() {
    if (validPosition) {
      sidebar.scrollTop = position;
    } else if (active) {
      // Scroll only the sidebar; never move the article itself.
      const box = sidebar.getBoundingClientRect();
      const item = active.getBoundingClientRect();
      if (item.top < box.top || item.bottom > box.bottom) {
        sidebar.scrollTop += item.top - box.top - sidebar.clientHeight / 2;
      }
    }
    remember();
  }
  function carryPosition(event) {
    const link = event.target.closest('a[href]');
    if (!link || !sidebar.contains(link)) return;
    const target = new URL(link.href);
    if (!target.href.startsWith(root.href) || !target.pathname.endsWith('.html')) return;
    target.searchParams.set(positionParam, String(sidebar.scrollTop));
    link.href = target.href;
    remember();
  }

  restore();
  sidebar.addEventListener('scroll', remember, { passive: true });
  sidebar.addEventListener('pointerdown', carryPosition);
  sidebar.addEventListener('click', carryPosition);
  sidebar.addEventListener('auxclick', carryPosition);
  window.addEventListener('pagehide', remember);
})();
