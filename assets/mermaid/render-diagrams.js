(async () => {
  const blocks = [...document.querySelectorAll('pre > code.language-mermaid')];
  if (!blocks.length || !window.mermaid) return;
  mermaid.initialize({ startOnLoad: false, securityLevel: 'strict', theme: 'default' });
  for (const [index, code] of blocks.entries()) {
    const pre = code.parentElement;
    const figure = document.createElement('figure');
    figure.className = 'diagram';
    const canvas = document.createElement('div');
    canvas.className = 'diagram-canvas';
    const details = document.createElement('details');
    const summary = document.createElement('summary');
    summary.textContent = '查看 Mermaid 源码';
    details.append(summary);
    pre.before(figure);
    figure.append(canvas, details);
    details.append(pre);
    try {
      const { svg } = await mermaid.render(`diagram-${index}`, code.textContent);
      canvas.innerHTML = svg;
    } catch (error) {
      canvas.textContent = '图表暂时无法绘制，可查看下方源码。';
      details.open = true;
      console.warn('Mermaid rendering failed', error);
    }
  }
})();
