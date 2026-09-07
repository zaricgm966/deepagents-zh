# Deep Agents 中文离线文档

## 开始阅读

双击 `index.html`，或在 macOS 上双击 `打开中文文档.command`。无需联网，也无需启动服务器。

目录已按入门选型、配置与核心能力、任务与上下文、应用教程、协议集成、前端开发、生产环境、版本更新分组，共 42 篇页面（40 篇译文 + 2 篇源码解析）。首页支持按中文标题筛选。

## 修改自己的版本

1. 用你喜欢的编辑器打开 `markdown/` 中的 `.md` 文件并修改。
2. 在本文件夹打开终端，执行 `python3 build.py`。
3. 刷新浏览器即可看到修改后的阅读版。

渲染依赖已包含在 `vendor/` 中，不需要在线安装。构建过程不会执行示例代码。`pages/` 是生成结果，建议修改 Markdown 后重新生成，避免直接修改 HTML 被下次构建覆盖。

## 文件目录

- `index.html`：中文阅读入口。
- `markdown/`：可编辑的中文正文。
- `pages/`：中文 HTML 阅读版。
- `assets/`：18 个原文引用资源，已下载本地化。
- `original-markdown/`：官方英文 Markdown 原始快照。
- `normalized-english/`：清理网页组件源码后的英文对照文本。
- `manifest.json`：文章名称、英文标题与原文链接。
- `original-index.txt`：官方英文机器可读索引，作为来源记录保留。
- `LICENSE`：官方 MIT 许可原文；`vendor/` 保留第三方渲染库许可。
- `build-report.json`：阅读版构建检查记录。

## 翻译范围与说明

已翻译全部 40 页的自然语言正文、标题、列表、表格和图片替代说明。正文通过 Google 在线翻译服务批量翻译，标题和部分术语经过整理，属于非官方机器翻译，未做逐句人工校译。遇到歧义可用每页的“英文原稿”链接核对。

为保留代码示例的完整性，代码块、注释、字符串、命令、API 标识符保持英文原样；原图及图内文字保留原样。英语源文件、来源索引及许可证也作为对照材料保留。Markdown 格式中的代码块已经与清理后的英文版逐一核对，内容一致。

交互选项卡、折叠组件展开为静态内容。网站组件自身的 JavaScript 源码已从阅读版去除，原始版本仍保留在 `original-markdown/`。在线演示、外部链接、联网模型与 API 服务不属于离线功能。

## 来源与许可

文档快照：2026-09-07。范围为当时官方 Python Deep Agents 索引的 40 个入口，含两个更新日志及 Deep Agents Code 介绍页；不包含整个 LangChain 网站。

- 文档：https://docs.langchain.com/oss/python/deepagents/data-analysis
- 源码：https://github.com/langchain-ai/docs
- 许可：https://github.com/langchain-ai/docs/blob/main/LICENSE

文档版权归 LangChain，采用 MIT 许可。允许复制和修改，需保留随附版权和许可声明。

## 新增：Coding Agent 源码解析

首页与侧栏新增独立分组，包含「Codex 源码解析」和「Claude Code 源码解析：公开 SDK 与运行时边界」。这是基于固定提交撰写的中文分析，不属于 LangChain 官方译文，也不冒称 Claude Code 核心引擎已经开源。

两章均包含源码入口、实际控制流、解决的问题、设计取舍及不能从源码得出的结论。原始代码选段以完整文件快照保存于 `source-snapshots/`，并附各自许可证及哈希；没有复制整仓库或运行这些 agent。新增章节没有英文原稿，因此不显示英文原稿入口。

## 源码章节扩写（2026-09-07）

Codex 与 Claude Code 两章已统一按 19 个功能主题组织，覆盖命令、流式循环、重试、存档、权限、自动审批、编辑、文件引用、上下文、提问、任务、记忆、回退、压缩、MCP、后台命令、子 Agent、外部事件和图片。每节提供机制讲解、源码入口和动手观察建议；开头提供 GitHub 与固定提交链接。Claude Code 部分区分公开 SDK 实现和 CLI 内部边界。练习未执行，源码仅用于阅读。


## 使用 Git 更新网站

本地工作副本通过 SSH 连接此仓库。修改 `markdown/` 后运行：

```sh
python3 -m pip install -r requirements.txt
python3 build.py
git add markdown pages index.html style.css build-report.json
git commit -m "更新文档"
git push origin main
```

GitHub Pages 会自动部署 main 分支。Mermaid 11.12.2 的脚本及 MIT 许可证位于 `assets/mermaid/`，无需 CDN，离线也可绘图。更新渲染样式或脚本时请同时提交相关文件。
