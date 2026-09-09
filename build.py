# -*- coding: utf-8 -*-
"""从 markdown 重新生成中文离线阅读版；不访问网络、不运行示例代码。"""
from pathlib import Path
import sys,re,json,html
from urllib.parse import urljoin,urlsplit,unquote
R=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'vendor'))
import markdown
from bs4 import BeautifulSoup
import source_reader as reader
reader.validate_sources()
rows=json.loads((R/'manifest.json').read_text());assets=json.loads((R/'assets.json').read_text())
TITLES={'overview':'Deep Agents 概览','quickstart':'快速入门','models':'模型选择','comparison':'与 Claude Agent SDK 的对比','code-link':'Deep Agents Code 简介','customization':'自定义 Deep Agents','tools':'工具','profiles':'配置档案','backends':'文件系统后端','interpreters':'代码解释器','sandboxes':'沙箱','memory':'记忆','skills':'技能','permissions':'权限','human-in-the-loop':'人工介入','multimodal':'多模态输入与输出','context-engineering':'上下文工程','subagents':'子智能体','dynamic-subagents':'动态子智能体','async-subagents':'异步子智能体','streaming':'流式输出','event-streaming':'事件流','fault-tolerance':'容错','retrieval':'检索','rubric':'评分标准','data-analysis':'构建数据分析智能体','content-builder':'构建内容创作智能体','deep-research':'构建深度研究智能体','rag':'构建检索增强生成（RAG）智能体','mcp':'模型上下文协议（MCP）','acp':'智能体客户端协议（ACP）','a2a':'A2A 服务器','frontend--overview':'前端集成概览','frontend--sandbox':'前端沙箱','frontend--subagent-streaming':'前端子智能体流式输出','frontend--todo-list':'前端待办事项列表','going-to-production':'部署到生产环境','openwiki':'OpenWiki','changelog-py':'Python 更新日志','changelog-js':'JavaScript / TypeScript 更新日志'}
TITLES.update({'codex-source-analysis': 'Codex 源码解析', 'claude-code-source-analysis': 'Claude Code 源码解析：公开 SDK 与运行时边界'})
GROUPS=[('入门与选型','overview quickstart models comparison code-link'),('配置与核心能力','customization tools profiles backends interpreters sandboxes memory skills permissions human-in-the-loop multimodal'),('任务与上下文管理','context-engineering subagents dynamic-subagents async-subagents streaming event-streaming fault-tolerance retrieval rubric'),('应用教程','data-analysis content-builder deep-research rag'),('协议与集成','mcp acp a2a'),('前端开发','frontend--overview frontend--sandbox frontend--subagent-streaming frontend--todo-list'),('生产环境与知识库','going-to-production openwiki'),('Coding Agent 源码解析','codex-source-analysis claude-code-source-analysis'),('版本更新','changelog-py changelog-js')]
TITLES['codex-source-analysis']='Codex 源码精读'
TITLES.update({c['slug']:c['title'] for c in reader.COURSE['chapters']})
GROUPS.insert(-1,('Codex 连续主线',' '.join(c['slug'] for c in reader.COURSE['chapters'] if c['kind']=='main')))
GROUPS.insert(-1,('Codex 深入专题',' '.join(c['slug'] for c in reader.COURSE['chapters'] if c['kind']=='topic')))
lookup={r['file'][:-3]:r for r in rows};assert set(lookup)==set(' '.join(s for _,s in GROUPS).split())
urlmap={r['url'].rstrip('/'):r['file'][:-3] for r in rows if r.get('kind') != 'source-analysis'}
for r in rows:
 if r.get('kind') == 'source-analysis':continue
 urlmap['https://docs.langchain.com/oss/python/deepagents/'+r['file'][:-3].replace('--','/')]=r['file'][:-3]
urlmap['https://docs.langchain.com/oss/python/deepagents']='overview'
def rewrite(u,extension='.html'):
 if u.startswith('#'):return u
 full=urljoin('https://docs.langchain.com',u)
 if full in assets and isinstance(assets[full],str):return '../'+assets[full]
 base=full.split('#')[0].split('?')[0].removesuffix('.md').rstrip('/');frag=urlsplit(u).fragment
 if base in urlmap:return urlmap[base]+extension+('#'+frag if frag else '')
 if u.split('#')[0].removesuffix('.md') in lookup:return u.split('#')[0][:-3]+extension+('#'+frag if frag else '') if '.md' in u else u
 return full if u.startswith('/') else u

def nav(prefix='',index='../index.html'):
 out='<a class="brand" href="'+index+'">Deep Agents<span>中文离线文档</span></a>'
 for group,slugs in GROUPS:
  if group.startswith('Codex '):continue
  out+='<h3>'+group+'</h3>'+''.join('<a href="'+prefix+slug+'.html">'+TITLES[slug]+'</a>' for slug in slugs.split())
 return out
css='''*{box-sizing:border-box}body{margin:0;color:#243b32;background:#fafcf9;font:17px/1.8 -apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:280px;overflow:auto;padding:26px 24px;background:#edf2eb;border-right:1px solid #dbe3d8}aside a{display:block;font-size:14px;padding:4px 0}aside a[aria-current=page]{font-weight:700;color:#174d35;background:#dce8d5;border-radius:4px}aside h3{font-size:17px;font-weight:700;line-height:1.5;letter-spacing:0;color:#304c3c;margin:30px 0 10px;padding-bottom:8px;border-bottom:1px solid #cddac8}.brand{font-size:24px;font-weight:700}.brand span{display:block;font-size:13px;font-weight:400}main{margin-left:280px;padding:42px 56px;max-width:1120px}a{color:#246b4d;text-decoration:none}a:hover{text-decoration:underline}h1{font-size:34px;line-height:1.35}h2{font-size:25px;margin-top:2em;padding-bottom:8px;border-bottom:1px solid #dce5d8}h3{font-size:20px}pre{padding:20px;background:#192c23;color:#eaf5eb;overflow:auto;font-size:14px;line-height:1.55;border-radius:5px}code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}p code,li code{background:#e7eee3;padding:2px 4px}blockquote{border-left:3px solid #92ab87;margin:20px 0;padding-left:18px;color:#53644f}img,video{max-width:100%;height:auto}table{display:block;overflow:auto;border-collapse:collapse;font-size:15px}td,th{border:1px solid #d3dfce;padding:10px;min-width:110px}th{background:#edf3e8}.meta{font-size:13px;color:#6c7b65}.intro{font-size:19px;max-width:750px}.toc{font-size:14px;background:#eef3eb;padding:12px 20px;border-radius:4px}.toc ul{padding-left:20px}summary{cursor:pointer}footer{margin-top:60px;border-top:1px solid #dce5d8;padding-top:16px;font-size:13px;color:#6c7b65}input{font:inherit;width:100%;padding:12px 16px;border:1px solid #c7d6bf;border-radius:4px;background:white}.chapter{padding:0;list-style:none}.chapter li{padding:6px 0}@media(max-width:800px){aside{position:static;width:auto;max-height:240px}main{margin:0;padding:24px}h1{font-size:28px}}'''
css += '\n.reading-layout{margin-left:280px;display:grid;grid-template-columns:minmax(0,1fr) 260px;gap:32px;max-width:1480px;padding:42px 32px 42px 48px;align-items:start}\n.reading-layout main{margin:0;padding:0;min-width:0;max-width:none}\n.page-toc{position:sticky;top:24px;max-height:calc(100vh - 48px);overflow:auto;overscroll-behavior:contain;border-left:1px solid #dbe3d8;padding:0 0 8px 20px;font-size:13px;line-height:1.65;scrollbar-width:thin}\n.page-toc h2{font-size:14px;margin:0 0 12px;padding:0;border:0;color:#53644f}\n.page-toc ul{list-style:none;margin:0;padding:0}\n.page-toc li{margin:0 0 9px}\n.page-toc a{display:block;overflow-wrap:anywhere}\n.reading-layout main h2,.reading-layout main h3{scroll-margin-top:24px}\n@media(max-width:1150px) and (min-width:801px){.reading-layout{grid-template-columns:minmax(0,1fr) 200px;gap:20px;padding:32px 20px}.page-toc{padding-left:14px;font-size:12px}}\n@media(max-width:800px){.reading-layout{margin:0;padding:24px;display:flex;flex-direction:column;gap:24px}.reading-layout main{width:100%}.page-toc{position:static;order:-1;width:100%;max-height:240px;padding:12px 16px;background:#eef3eb;border:0;border-radius:4px}}\n'
css += '.diagram{margin:24px 0;padding:16px;background:white;border:1px solid #dbe3d8;border-radius:6px}.diagram-canvas{overflow:auto;text-align:center}.diagram-canvas svg{height:auto;max-width:100%}.diagram details{margin-top:12px;font-size:13px}.diagram pre{text-align:left}'
(R/'style.css').write_text(css);(R/'pages').mkdir(exist_ok=True)
issues=[]
for slug,r in lookup.items():
 p=R/'markdown'/r['file'];s=p.read_text()
 # Only rewrite prose targets, retaining code blocks byte for byte.
 blocks=re.split(r'(^```[^\n]*\n.*?^```\s*$)',s,flags=re.M|re.S)
 for i in range(0,len(blocks),2):
  blocks[i]=re.sub(r'(!?\[[^\]]*\]\()([^\s)]+)',lambda m:m[1]+rewrite(m[2],'.md'),blocks[i])
  blocks[i]=re.sub(r'((?:src|href)=")([^"]+)',lambda m:m[1]+rewrite(m[2],'.md'),blocks[i])
 s=''.join(blocks);p.write_text(s)
 engine=markdown.Markdown(extensions=['fenced_code','tables','toc','sane_lists','md_in_html'])
 soup=BeautifulSoup(engine.convert(s),'html.parser')
 # Retain English section IDs so existing inbound fragment links still work.
 authored=r.get('kind')=='source-analysis'
 original_text=s if authored else (R/'normalized-english'/r['file']).read_text()
 original=BeautifulSoup(markdown.markdown(original_text,extensions=['fenced_code','tables','toc','md_in_html']),'html.parser')
 eh=original.find_all(re.compile('^h[1-6]$'));zh=soup.find_all(re.compile('^h[1-6]$'))
 if len(eh)==len(zh):
  for a,b in zip(eh,zh):
   if a.get('id'):b['id']=a['id']
 else:issues.append({'page':slug,'english_headings':len(eh),'chinese_headings':len(zh)})
 # Component section titles were expanded into bold paragraphs.
 es=original.find_all('strong');zs=soup.find_all('strong')
 if len(es)==len(zs):
  from markdown.extensions.toc import slugify
  for a,b in zip(es,zs):
   ident=slugify(a.get_text(),'-')
   if ident and not soup.find(id=ident):b['id']=ident
 if slug=='skills':
  anchor=soup.find(id='reference-files-from-skillmd')
  if anchor:
   alias=soup.new_tag('span',id='reference-files-from-skill-md');anchor.insert_before(alias)
 if soup.h1:soup.h1.string=TITLES[slug]
 for e in soup.find_all(['script','iframe','style']):e.decompose()
 for a in soup.find_all('a',href=True):
  if a['href'].startswith('{'):a.unwrap();continue
  a['href']=rewrite(a['href'])
 for e in soup.find_all(True):
  for key in list(e.attrs):
   if key.lower().startswith('on'):del e[key]
  if e.has_attr('src'):e['src']=rewrite(e['src'])
 toc='<nav class="page-toc" aria-label="本页目录"><h2>本页目录</h2><ul>'+''.join('<li><a href="#'+h.get('id','')+'">'+html.escape(h.get_text())+'</a></li>' for h in soup.find_all('h2'))+'</ul></nav>'
 meta='<div class="meta">中文机器翻译 · 文档快照 2026-09-07 · <a href="'+r['url']+'">在线原文</a> · <a href="../markdown/'+r['file']+'">编辑中文 Markdown</a> · <a href="../original-markdown/'+r['file']+'">英文原稿</a></div>'
 if authored:
  meta='<div class="meta">中文原创源码分析 · 核对日期 2026-09-07 · <a href="'+r['url']+'">固定版本源码</a> · <a href="../markdown/'+r['file']+'">编辑 Markdown</a> · <a href="../source-snapshots/README.md">离线源码与许可</a></div>'
 diagram_scripts = '<script defer src="../assets/mermaid/mermaid.min.js"></script><script defer src="../assets/mermaid/render-diagrams.js"></script>' if soup.select('code.language-mermaid') else ''
 page='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+TITLES[slug]+' · Deep Agents</title><link rel="stylesheet" href="../style.css">'+diagram_scripts+'<aside>'+nav()+'</aside><script src="../sidebar.js"></script><div class="reading-layout"><main>'+meta+str(soup)+'<footer>非官方中文离线整理版。代码与原图保留；在线演示需要联网。© LangChain · <a href="../LICENSE">MIT 许可</a></footer></main>'+toc+'</div></html>'
 if authored:
  page=page.replace('非官方中文离线整理版。代码与原图保留；在线演示需要联网。© LangChain · <a href="../LICENSE">MIT 许可</a>', '新增非官方源码分析，不属于 LangChain 文档译文。引用源码的版权与许可见 <a href="../source-snapshots/README.md">来源说明</a>。')
 if reader.is_course(slug):
  reader.decorate(soup,slug)
  links='<link rel="stylesheet" href="../assets/source-reader/reader.css"><link rel="stylesheet" href="../assets/source-reader/highlight.css"><script defer src="../assets/source-reader/reader.js"></script>'
  course_meta='<div class="meta">非官方源码教学 · 固定提交 '+reader.COMMIT[:12]+' · <a href="../markdown/'+r['file']+'">本页 Markdown</a> · <a href="../source-snapshots/README.md">源码与许可</a></div>'
  page='<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>'+TITLES[slug]+' · Deep Agents</title><link rel="stylesheet" href="../style.css">'+links+diagram_scripts+'</head><body class="course-page"><aside>'+reader.course_nav()+'</aside><script src="../sidebar.js"></script><div class="reading-layout"><main>'+reader.before(slug)+str(soup)+reader.after(slug)+course_meta+'<footer>依据公开固定版本源码编写。案例为教学示例，源码引用保留原许可。</footer></main>'+toc+'</div></body></html>'
 (R/'pages'/(slug+'.html')).write_text(page)
items=''.join('<section><h2>'+group+'</h2><ul class="chapter">'+''.join('<li><a href="pages/'+slug+'.html">'+TITLES[slug]+'</a></li>' for slug in slugs.split())+'</ul></section>' for group,slugs in GROUPS)
(R/'index.html').write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Deep Agents 中文离线文档</title><link rel="stylesheet" href="style.css"><aside>'+nav('pages/','index.html')+'</aside><script src="sidebar.js"></script><main><div class="meta">40 篇 Deep Agents 文档 + 2 篇源码解析</div><h1>Deep Agents 中文离线文档</h1><p class="intro">从入门配置到应用开发，按主题重新整理。中文正文可离线阅读，译文附英文原稿，新增源码解析附固定版本源码快照。</p><p><a href="pages/data-analysis.html">从「构建数据分析智能体」开始 →</a></p><p class="meta">Deep Agents 正文采用机器翻译；新增 Coding Agent 源码解析为独立中文分析，并标明公开实现的范围。</p><input aria-label="筛选文章标题" placeholder="输入关键词筛选目录，例如：沙箱、记忆、前端" oninput="document.querySelectorAll(\'.chapter li\').forEach(x=>x.hidden=!x.textContent.toLowerCase().includes(this.value.toLowerCase()))">'+items+'<footer>编辑 markdown 中的文件后，运行 python3 build.py 更新阅读版。<br><a href="README.md">使用说明</a> · <a href="LICENSE">MIT 许可</a></footer></main></html>')
home=(R/'index.html').read_text()
home=home.replace('<link rel="stylesheet" href="style.css">','<link rel="stylesheet" href="style.css"><link rel="stylesheet" href="assets/source-reader/reader.css">')
home=home.replace('40 篇 Deep Agents 文档 + 2 篇源码解析','40 篇 Deep Agents 文档 · Codex 源码精读与 Claude Code 解析')
home=home.replace('<input aria-label="筛选文章标题"',reader.homepage()+'<input aria-label="筛选文章标题"')
(R/'index.html').write_text(home)
source_pages=reader.build_source_pages()
(R/'build-report.json').write_text(json.dumps({'pages':len(rows),'heading_warnings':issues,'codex_chapters':len(reader.COURSE['chapters']),'verified_snippets':len(reader.SNIPPETS),'source_pages':source_pages},ensure_ascii=False,indent=2));print('已生成',len(rows),'个页面；标题结构警告',len(issues),'；源码片段',len(reader.SNIPPETS))
