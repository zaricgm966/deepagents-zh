"""Validate the generated offline course against its fixed source files."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys
import textwrap
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'vendor'))
from bs4 import BeautifulSoup

course=json.loads((ROOT/'source-reading/codex-course.json').read_text())
snippets=json.loads((ROOT/'source-reading/codex-snippets.json').read_text())
raw_cache={}
def raw(path):
    if path not in raw_cache:raw_cache[path]=path.read_text()
    return raw_cache[path]

paths=[ROOT/'index.html',ROOT/'pages/codex-source-analysis.html']+[ROOT/'pages'/f'{c["slug"]}.html' for c in course['chapters']]
count=0
for path in paths:
    soup=BeautifulSoup(raw(path),'html.parser')
    assert '打开本节源码入口' not in soup.get_text(),path
    ids=[x['id'] for x in soup.select('[id]')]
    assert len(ids)==len(set(ids)),f'duplicate IDs: {path}'
    for tag in soup.select('[href], [src]'):
        target=tag.get('href') or tag.get('src')
        link=urlsplit(target)
        if link.scheme or link.netloc:continue
        local=(path.parent/unquote(link.path)).resolve() if link.path else path
        assert local.exists(),f'broken link {path.name}: {target}'
        if link.fragment and local.suffix=='.html':
            assert f'id="{unquote(link.fragment)}"' in raw(local),f'broken anchor {path.name}: {target}'
    for panel in soup.select('.source-panel'):
        key=panel['id'][7:];spec=snippets[key]
        file=ROOT/'source-snapshots/codex'/spec['path']
        code=''.join(file.read_text().splitlines(keepends=True)[spec['start']-1:spec['end']])
        assert hashlib.sha256(code.encode()).hexdigest()==spec['sha256'],key
        assert hashlib.sha256(file.read_bytes()).hexdigest()==spec['file_sha256'],key
        assert panel.select_one('.copy-source').get_text()==code,key+' copied source'
        rows=panel.select_one('pre').select('.code-line')
        numbers=[int(x.select_one('.line-number').get_text()) for x in rows]
        assert numbers==list(range(spec['start'],spec['end']+1)),key+' line numbers'
        displayed='\n'.join(x.select_one('.line-text').get_text() for x in rows)
        expected=textwrap.dedent(code).splitlines()
        assert [x.rstrip() for x in displayed.splitlines()]==[x.rstrip() for x in expected],key+' displayed code'
        context=panel.select_one('details pre')
        a=max(1,spec['start']-12);b=min(len(file.read_text().splitlines()),spec['end']+12)
        assert [int(x.get_text()) for x in context.select('.line-number')]==list(range(a,b+1)),key+' context lines'
        count+=1
    if path.stem in {c['slug'] for c in course['chapters']}:
        assert soup.select_one('.chapter-pagination'),path
        assert len(soup.select('.task-route a'))==9,path
        assert soup.select_one('.answer summary'),path

# Old deep links should still resolve on the course overview.
previous=subprocess.check_output(['git','show','HEAD:pages/codex-source-analysis.html'],cwd=ROOT,text=True)
old=BeautifulSoup(previous,'html.parser')
current=raw(ROOT/'pages/codex-source-analysis.html')
for h in old.select('main h2[id]'):
    assert f'id="{h["id"]}"' in current, 'missing legacy chapter anchor: '+h['id']
assert count==len(snippets),(count,len(snippets))
print(json.dumps({'course_pages_checked':len(paths),'source_snippets_checked':count,'legacy_chapter_anchors':len(old.select('main h2[id]')),'result':'passed'},ensure_ascii=False))
