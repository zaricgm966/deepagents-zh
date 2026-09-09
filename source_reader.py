"""Offline, source-verified reading views for the Codex course."""
from pathlib import Path
from functools import lru_cache
import hashlib
import html
import json
import re
import textwrap

from bs4 import BeautifulSoup, Comment
from pygments import highlight
from pygments.lexers import RustLexer, get_lexer_by_name
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound

ROOT = Path(__file__).resolve().parent
COURSE = json.loads((ROOT / 'source-reading/codex-course.json').read_text())
SNIPPETS = json.loads((ROOT / 'source-reading/codex-snippets.json').read_text())
CHAPTERS = {c['slug']: c for c in COURSE['chapters']}
COMMIT = COURSE['commit']
FORMATTER = HtmlFormatter(nowrap=True, style='friendly')


def is_course(slug):
    return slug == 'codex-source-analysis' or slug in CHAPTERS


@lru_cache(maxsize=None)
def file_lines(path):
    return (ROOT / 'source-snapshots/codex' / path).read_text().splitlines(keepends=True)


def snippet_text(spec):
    return ''.join(file_lines(spec['path'])[spec['start'] - 1:spec['end']])


def validate_sources():
    for key, spec in SNIPPETS.items():
        assert 1 <= spec['start'] <= spec['end'] <= len(file_lines(spec['path'])), key
        assert all(spec['start'] <= n <= spec['end'] for n in spec['focus']), key
        notes = spec.get('focus_notes', [])
        assert notes and all(note['reason'].strip() for note in notes), f'{key}: missing reading explanation'
        assert set(spec['focus']) == {n for note in notes for n in note['lines']}, f'{key}: unexplained highlight'
        raw = (ROOT / 'source-snapshots/codex' / spec['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == spec['file_sha256'], f'{key}: source changed'
        assert hashlib.sha256(snippet_text(spec).encode()).hexdigest() == spec['sha256'], f'{key}: snippet changed'


def source_name(path):
    return hashlib.sha256(path.encode()).hexdigest()[:16] + '.html'


def code_rows(text, start=1, focus=(), prefix='', dedent=False):
    # Only remove common indentation in excerpts; copying retains original source.
    if dedent:
        text = textwrap.dedent(text)
    lines = highlight(text, RustLexer(stripnl=False, ensurenl=False), FORMATTER).splitlines()
    out = []
    for number, line in enumerate(lines, start):
        marked = ' focus-line' if number in focus else ''
        ident = f'{prefix}L{number}'
        out.append(f'<span class="code-line{marked}" id="{ident}"><a class="line-number" href="#{ident}" aria-label="源码第 {number} 行">{number}</a><span class="line-text">{line or " "}</span></span>')
    return '<pre class="source-code"><code>' + ''.join(out) + '</code></pre>'


def snippet_view(key):
    s = SNIPPETS[key]
    first, last = s['start'], s['end']
    a, b = max(1, first-12), min(len(file_lines(s['path'])), last+12)
    before = html.escape(s['path'])
    text = snippet_text(s)
    context = ''.join(file_lines(s['path'])[a-1:b])
    source_link = 'codex-source/' + source_name(s['path']) + f'#L{first}'
    focus = ', '.join(map(str, s['focus']))
    note = f'关注行：{focus}。' if focus else ''
    return f'''<section class="source-panel" id="source-{key}" aria-label="{html.escape(s['title'])}">
<header class="source-header"><div><span class="source-label">固定版本源码 · L{first}–{last}</span><strong>{html.escape(s['title'])}</strong><span class="source-path">{before}</span></div>
<div class="source-actions"><button type="button" data-copy-path="{before}">复制路径</button><button type="button" data-copy-code>复制代码</button><button type="button" data-wrap aria-pressed="false">自动换行</button></div></header>
<p class="source-hint">{note}保留原始行号，展示时略去公共缩进。</p>
{code_rows(text, first, s['focus'], key+'-', True)}
<textarea class="copy-source" hidden aria-hidden="true">{html.escape(text)}</textarea>
<details class="source-context"><summary>展开前后文 · L{a}–{b}</summary>{code_rows(context,a,range(first,last+1),key+'-context-',True)}</details>
<div class="source-footer"><a href="{source_link}">阅读完整文件 ↗</a><span>{COMMIT[:12]} · Rust · 只读</span></div></section>'''


def decorate(soup, slug):
    if not is_course(slug):
        return
    for comment in list(soup.find_all(string=lambda t: isinstance(t, Comment))):
        m = re.fullmatch(r'\s*source:\s*([a-z0-9-]+)\s*', str(comment))
        if not m:
            continue
        key = m[1]
        pre = comment.find_next_sibling('pre')
        assert key in SNIPPETS and pre and pre.code, f'{slug}: missing source fence {key}'
        assert pre.code.get_text().rstrip('\n') == snippet_text(SNIPPETS[key]).rstrip('\n'), f'{slug}: edited source {key}'
        # The path is also retained above the fence in Markdown for plain-text readers.
        previous = comment.find_previous_sibling('p')
        if previous and previous.get_text().startswith('源码：'):
            previous.decompose()
        view = BeautifulSoup(snippet_view(key), 'html.parser').section
        pre.replace_with(view)
        comment.extract()
    # Highlight teaching examples, never present these as verified source excerpts.
    for code in soup.select('pre > code'):
        if code.find_parent(class_='source-panel'):
            continue
        language = next((c[9:] for c in code.get('class',[]) if c.startswith('language-')), '')
        if language in ('', 'mermaid'):
            continue
        try:
            lexer = get_lexer_by_name(language)
        except ClassNotFound:
            continue
        content = highlight(code.get_text(), lexer, FORMATTER)
        code.clear()
        for element in list(BeautifulSoup(content, 'html.parser').contents):
            code.append(element)
        code.parent['class'] = ['teaching-code']


def course_nav():
    out = '<a class="brand" href="../index.html">Deep Agents<span>中文离线文档</span></a><a class="course-home" href="codex-source-analysis.html">← Codex 源码精读 · 总览</a>'
    for kind,title in [('main','跟完一次任务'),('topic','按问题深入')]:
        out += f'<h3>{title}</h3>'
        for c in COURSE['chapters']:
            if c['kind']==kind:
                out+=f'<a href="{c["slug"]}.html">{html.escape(c["title"])}</a>'
    return out


def before(slug):
    c=CHAPTERS.get(slug)
    toolbar='<div class="reader-toolbar"><a href="../index.html">文档首页</a><a href="codex-source-analysis.html">课程总览</a><button type="button" data-reading-width aria-pressed="false">宽屏阅读</button></div>'
    if not c:
        return toolbar+'<p class="course-kicker">CODEX / 源码精读 · 2026-09-09 本地扩展版</p>'
    steps=['输入','启动','上下文','响应','工具','权限','回传','改与测','结束']
    mains=[x for x in COURSE['chapters'] if x['kind']=='main']
    progress='<nav class="task-route" aria-label="任务主线">'
    for i,(label,item) in enumerate(zip(steps,mains)):
        attr=' aria-current="step"' if c['kind']=='main' and i==c['position'] else ''
        progress+=f'<a href="{item["slug"]}.html"{attr}><span>{i+1:02d}</span>{label}</a>'
    progress+='</nav>'
    label=f'主线 {c["position"]+1:02d} / 09' if c['kind']=='main' else '深入专题'
    return toolbar+f'<p class="course-kicker">CODEX / {label} · 固定版本 {COMMIT[:12]}</p>'+progress


def after(slug):
    if slug not in CHAPTERS:
        return '<a class="course-start" href="codex-01-input.html">从第 01 节开始阅读 →</a>'
    c=CHAPTERS[slug]
    peers=[x for x in COURSE['chapters'] if x['kind']==c['kind']]
    i=peers.index(c)
    prev=peers[i-1] if i else {'slug':'codex-source-analysis','title':'课程总览'}
    nxt=peers[i+1] if i+1<len(peers) else {'slug':'codex-source-analysis','title':'选择深入专题'}
    out='<nav class="chapter-pagination" aria-label="章节翻页">'
    out+=f'<a href="{prev["slug"]}.html"><small>上一节</small>{html.escape(prev["title"])}</a>'
    out+=f'<a href="{nxt["slug"]}.html"><small>下一节</small>{html.escape(nxt["title"])}</a></nav>'
    if c.get('related'):
        out+='<div class="related-reading">延伸阅读：'+' · '.join(f'<a href="{s}.html">{html.escape(CHAPTERS[s]["title"])}</a>' for s in c['related'])+'</div>'
    return out


def homepage():
    return '''<section class="course-feature" aria-labelledby="codex-feature-title"><p class="course-kicker">本地扩展版 · 2026-09-09</p><h2 id="codex-feature-title">Codex 源码精读</h2><p>跟着一次任务，读懂输入、模型请求、工具执行与结果回传。</p><p class="feature-detail">9 节连续主线 / 12 篇深入专题 / 真实源码高亮与上下文</p><div><a class="course-start" href="pages/codex-source-analysis.html">进入源码精读 →</a><a href="pages/codex-07-results.html">先读样章：工具结果如何回传</a></div></section>'''


def build_source_pages():
    target=ROOT/'pages/codex-source';target.mkdir(exist_ok=True)
    paths=sorted({s['path'] for s in SNIPPETS.values()})
    for path in paths:
        raw=''.join(file_lines(path))
        references=[(key,s) for key,s in SNIPPETS.items() if s['path']==path]
        # Fixed source files are pre-rendered: no fetch, CDN, server or model required.
        body=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>{html.escape(path)} · Codex 源码</title><link rel="stylesheet" href="../../assets/source-reader/reader.css"><link rel="stylesheet" href="../../assets/source-reader/highlight.css"><script defer src="../../assets/source-reader/reader.js"></script></head><body class="full-source"><header class="full-source-header"><a href="../codex-source-analysis.html">← 课程总览</a><button type="button" data-go-back>返回讲解</button><span>固定版本 {COMMIT[:12]} · 只读</span><h1>{html.escape(path)}</h1><div class="source-actions"><button type="button" data-copy-path="{html.escape(path)}">复制路径</button><button type="button" data-wrap aria-pressed="false">自动换行</button><form data-line-jump><label>跳转行 <input aria-label="源码行号" type="number" min="1" max="{len(file_lines(path))}" required></label><button>跳转</button></form></div></header><main>{code_rows(raw)}</main><div class="copy-notice" role="status" aria-live="polite"></div></body></html>'''
        (target/source_name(path)).write_text(body)
    asset=ROOT/'assets/source-reader';asset.mkdir(exist_ok=True)
    (asset/'highlight.css').write_text(FORMATTER.get_style_defs('.source-code, .teaching-code')+'\n')
    return len(paths)
