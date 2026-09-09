(() => {
  const body = document.body;
  let notice = document.querySelector('.copy-notice');
  if (!notice) {
    notice = document.createElement('div');
    notice.className = 'copy-notice';
    notice.setAttribute('role', 'status');
    notice.setAttribute('aria-live', 'polite');
    body.append(notice);
  }
  let timer;
  function inform(text) {
    notice.textContent = text;
    notice.classList.add('visible');
    clearTimeout(timer);
    timer = setTimeout(() => notice.classList.remove('visible'), 2200);
  }
  async function copy(text) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_) { /* Local files can require the legacy clipboard path. */ }
    const active = document.activeElement;
    const field = document.createElement('textarea');
    field.value = text;
    field.style.cssText = 'position:fixed;left:-10000px;top:0;';
    body.append(field);
    field.select();
    let ok = false;
    try { ok = document.execCommand('copy'); } catch (_) { /* Report a usable fallback. */ }
    field.remove();
    if (active instanceof HTMLElement) active.focus({preventScroll:true});
    return ok;
  }
  document.addEventListener('click', async event => {
    const button = event.target.closest('button');
    if (!button) return;
    if (button.hasAttribute('data-copy-path') || button.hasAttribute('data-copy-code')) {
      const text = button.hasAttribute('data-copy-path') ? button.dataset.copyPath : button.closest('.source-panel').querySelector('.copy-source').value;
      inform(await copy(text) ? '已复制' : '复制未获浏览器允许，请直接选择代码复制');
    }
    if (button.hasAttribute('data-wrap')) {
      const scope = button.closest('.source-panel') || body;
      const on = scope.classList.toggle('wrap-code');
      button.setAttribute('aria-pressed', String(on));
      button.textContent = on ? '取消换行' : '自动换行';
    }
    if (button.hasAttribute('data-reading-width')) {
      const on = body.classList.toggle('reading-wide');
      button.setAttribute('aria-pressed', String(on));
      button.textContent = on ? '恢复目录' : '宽屏阅读';
    }
    if (button.hasAttribute('data-go-back')) {
      if (history.length > 1) history.back();
      else location.href = '../codex-source-analysis.html';
    }
  });
  document.querySelector('[data-line-jump]')?.addEventListener('submit', event => {
    event.preventDefault();
    const value = event.currentTarget.querySelector('input').value;
    const line = document.getElementById('L' + value);
    if (line) {
      location.hash = 'L' + value;
      line.scrollIntoView({block:'center'});
    }
  });
  function revealHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (!id) return;
    const element = document.getElementById(id);
    if (!element) return;
    const details = element.closest('details');
    if (details) details.open = true;
    requestAnimationFrame(() => element.scrollIntoView({block:'center'}));
  }
  window.addEventListener('hashchange', revealHash);
  if (location.hash) revealHash();
  const sections = [...document.querySelectorAll('.course-page main h2[id]')];
  if (sections.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const item = entries.find(e => e.isIntersecting);
      if (!item) return;
      for (const a of document.querySelectorAll('.page-toc a')) {
        if (a.hash === '#' + item.target.id) a.setAttribute('aria-current','true');
        else a.removeAttribute('aria-current');
      }
    }, {rootMargin:'-5% 0px -65% 0px',threshold:0});
    sections.forEach(s => observer.observe(s));
  }
})();
