# 开放维基


> 用于编写和维护代理 wiki 的 CLI，以便编程智能体更快地工作


OpenWiki 是一个开源 CLI，用于编写和维护有关您的代码库或个人知识的 Markdown wiki。该 wiki 捕获了架构、集成、评估和工作流程等详细信息，因此 [编程智能体](overview.md) 可以将其用作持久上下文，而不是在每个任务上重新发现存储库。


这使得代理的工作速度更快，代币成本更低：代理首先阅读精选的 wiki，然后仅在需要更多详细信息的地方检查源。人类可以浏览相同的 Markdown（以及本地 [可视化工具](https://docs.langchain.com/oss/openwiki/visualize)），但主要受众是代理。


OpenWiki 基于 [Deep Agents](overview.md) 构建，并支持使用 [LangSmith](https://docs.langchain.com/langsmith/observability-quickstart) 进行跟踪。


## 开始使用


安装 CLI，然后初始化当前存储库的文档：


```bash
npm install -g openwiki
openwiki --init
```


 请参阅[快速入门](https://docs.langchain.com/oss/openwiki/quickstart) 选择模型提供程序、生成文档并使其保持最新。要在 Codex、Claude Code、OpenCode 或 Cursor 中运行 OpenWiki，而不是在独立模型会话中运行，请参阅[编程智能体集成](https://docs.langchain.com/oss/openwiki/integrations)。


## 模式


OpenWiki 有两种模式：


|模式|命令|输出|使用时|
| ------------------ | ---------------------------- | ------------------------------------- | --------------------------------------------------------------- |
|**代码**（默认）|`openwiki` / `openwiki code`|当前存储库中的 `openwiki/`|您需要编程智能体的存储库上下文和文档|
|**个人的**|`openwiki personal`|`~/.openwiki/wiki`|您想要来自配置来源的本地个人大脑|


裸机 `openwiki --init` 和 `openwiki --update` 在代码模式下运行。使用 `openwiki personal --init` 或 `openwiki personal --update` 作为个人 wiki。


## 能力


  
**存储库维基**


[查看相关页面](https://docs.langchain.com/oss/openwiki/code-mode)


在 `openwiki/` 下生成 Markdown 文档，然后将它们连接到 `AGENTS.md` 和 `CLAUDE.md` 中，以便编程智能体可以找到它们。

  


  
**编程智能体集成**


[查看相关页面](https://docs.langchain.com/oss/openwiki/integrations)


使用主机模型和存储库工具在 Codex、Claude Code、OpenCode 或 Cursor 中运行 OpenWiki。

  


  
**个人大脑**


[查看相关页面](https://docs.langchain.com/oss/openwiki/personal-mode)


从 git 存储库、自定义 MCP、Gmail、Notion、网络搜索、黑客新闻和 X/Twitter 构建本地 wiki。

  


  
**有根据的主张**


[查看相关页面](https://docs.langchain.com/oss/openwiki/code-mode#grounded-claims)


将重要事实跟踪回版本化源证据，并在证据发生变化时刷新页面。

  


  
**自动更新**


[查看相关页面](https://docs.langchain.com/oss/openwiki/automate-updates)


从 GitHub Actions、GitLab CI 或 Bitbucket Pipelines 刷新文档，并在内容更改时打开 PR。

  


  
**模型提供商**


[查看相关页面](https://docs.langchain.com/oss/openwiki/providers)


使用 OpenAI、Anthropic、Gemini、Bedrock、OpenRouter、GitHub Copilot 和其他开箱即用的提供商。

  


  
**开放知识格式**


[查看相关页面](https://docs.langchain.com/oss/openwiki/code-mode#open-knowledge-format)


发出 OKF v0.2 Markdown 捆绑包，其中包含前言、索引和链接概念。

  


  
**朗史密斯追踪**


[查看相关页面](https://docs.langchain.com/oss/openwiki/quickstart#trace-with-langsmith)


跟踪文档通过 LangSmith 运行。

  

## 后续步骤


  
**快速入门**


[查看相关页面](https://docs.langchain.com/oss/openwiki/quickstart)


安装 OpenWiki、配置提供程序并生成您的第一个 wiki。

  


  
**CLI 参考**


[查看相关页面](https://docs.langchain.com/oss/openwiki/cli-reference)


查看命令、标志和连接器子命令。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/openwiki/overview.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

