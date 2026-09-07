# 与 Claude Agent SDK 的比较


> 将 LangChain Deep Agent 与 Claude Agent SDK 进行比较，选择适合您的用例的工具。


本页介绍了 [LangChain Deep Agents](overview.md) 与 [Claude Agent SDK](https://platform.anthropic.com/docs/en/agent-sdk/overview) 的比较。两者都是用于构建自定义代理的工具，但它们在执行环境、部署和供应商耦合方面做出了不同的权衡。


[OpenSWE](https://github.com/langchain-ai/open-swe) 和 [LangSmith Fleet](https://docs.langchain.com/langsmith/fleet/index) 在生产中使用 Deep Agents。


## 一目了然


||**Deep Agents**|**Claude Agent SDK**|
| ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|**代理运行的地方**|在沙箱内部，或在沙箱外部远程执行命令|沙箱内|
|**执行后端**|可插拔：[本地、虚拟文件系统、远程沙箱或自定义](backends.md)|它运行的沙箱的本地文件系统|
|**模型提供者**|任何（Anthropic、OpenAI、Google、100 多个其他）|Claude（Anthropic、Bedrock、Vertex、Azure）|
|**每个提供商/模型调整**|[Harness 配置文件](profiles.md)（测试版）：系统提示、工具、中间件和子智能体调整的声明性捆绑包，按提供商或特定模型注册|在每个模型调用站点的代码中进行配置|
|**部署**|LangSmith 中的[托管深度智能体](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview)，或通过 [`langgraph build`](https://docs.langchain.com/langsmith/cli#build) 自托管一个[独立映像](https://docs.langchain.com/langsmith/deploy-standalone-server)|[自托管](https://code.claude.com/docs/en/agent-sdk/hosting)。您构建服务器、身份验证和流层。 [Claude 管理代理](https://platform.claude.com/docs/en/managed-agents/overview) 是一个单独的产品|
|**多租户**|[内置](going-to-production.md#multi-tenancy)：作用域线程、每用户沙箱、RBAC|自己构建|
|**许可证**|MIT|MIT（Claude Code本身是专有的）|


## 主要区别


### 代理和执行环境


有[两种将代理连接到沙箱的模式](https://www.langchain.com/blog/the-two-patterns-by-which-agents-connect-sandboxes)：在沙箱*内部*运行代理，或者在沙箱外部运行代理并**使用沙箱作为工具**。


Claude Agent SDK 仅支持第一种。您的代理在沙箱内运行，并针对沙箱的本地文件系统执行工具。 Anthropic 的托管模型 [Claude 托管代理](https://platform.claude.com/docs/en/managed-agents/overview) 使用解耦模型，该模型反映了生产代理架构的发展方向。


Deep Agents 支持两者，并允许您选择一个[后端](backends.md#quickstart) 将它们连接在一起。实际上，这意味着您可以：


* 在沙箱内运行代理（与 Claude Agent SDK 模型相同）。
* 在长期容器中运行代理并[使用远程沙箱作为工具](https://www.langchain.com/blog/the-two-patterns-by-which-agents-connect-sandboxes)，通过网络执行命令。
* 交换用于测试的虚拟文件系统，或用于您自己的基础设施的自定义后端。


### 多租户


当您将应用程序投入生产时，通常会将其暴露给许多最终用户，并且必须隔离每个用户的环境。


在 Claude Agent SDK 中，SDK 将代理绑定到其沙箱。为了给每个用户一个隔离的执行环境，您必须构建一个 API 包装器，为每个用户启动一个沙箱，跟踪哪个沙箱属于谁，然后将其拆除。


Deep Agents 直接处理此问题：在工具箱中配置一个沙箱[每个用户或每个助手](going-to-production.md#lifecycle)，其中包含范围线程、运行历史记录和 [RBAC](going-to-production.md#team-access-control-rbac)。如果您使用 [LangSmith Sandbox](https://docs.langchain.com/langsmith/sandbox-auth-proxy)，您还可以获得一个开箱即用的身份验证代理，以便最终用户可以从沙箱调用第三方 API，而无需为每个用户配置凭据。


### 生产代理服务器


要向最终用户公开[自托管 Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/hosting) 应用程序，您需要编写自己的 HTTP/WebSocket 或 SSE 服务器来调用代理、流回令牌并管理对话线程。该服务器由您构建、操作和保护。


Deep Agents 部署包括开箱即用的[代理服务器](https://docs.langchain.com/langsmith/agent-server)：流端点、线程管理、运行历史记录、Webhooks 和[身份验证](https://docs.langchain.com/langsmith/auth)。


### 托管云或自托管


Claude Agent SDK 部署是[自托管](https://code.claude.com/docs/en/agent-sdk/hosting)。 SDK 和 [Claude 托管代理](https://platform.claude.com/docs/en/managed-agents/overview) 是单独的产品。针对 SDK 编写的代码不会直接部署到托管产品。


Deep Agents 以两种模式运行，无需更改代码：


* **托管：** 使用 LangSmith 中的 [托管深度智能体](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview) 创建、运行和操作深度智能体。
* **自托管：**运行 [`langgraph build`](https://docs.langchain.com/langsmith/cli#build) 生成可以部署在任何地方的 [独立 Docker 映像](https://docs.langchain.com/langsmith/deploy-standalone-server)。


对于跨任何模型提供商工作的托管代理平台，请使用 [LangSmith Fleet](https://docs.langchain.com/langsmith/fleet/index)。 [Claude 管理代理](https://platform.claude.com/docs/en/managed-agents/overview) 仅限于 Anthropic 生态系统。


### 法学硕士


Claude Agent SDK 执行捆绑了模型、后端和部署，并优化了这三者之间的支持。


使用 Deep Agents，您可以独立选择模型提供程序、执行后端和部署目标。通过选择该线束，您可以在选择模型和基础设施时保持最大的灵活性。


### 生态系统


Claude Agent SDK 专为 Claude 和 Anthropic 的产品界面而构建。 Deep Agents 与更广泛的 LangChain 生态系统集成，包括用于可观察性、评估和部署的 LangSmith，并且可以跨任何模型提供商工作。


## 概括


* **如果您想要模型和基础设施灵活性、内置多租户部署以及无需更改代码即可运行托管或自托管的选项，请选择 Deep Agents。
* **如果您已经投资了 Anthropic 生态系统并希望自行托管和构建 API、身份验证和多租户层，请选择 Claude Agent SDK。


**注意到一个错误吗？**


我们于 2026 年 4 月 16 日起草了此比较。如果产品发生更改，请[提交问题](https://github.com/langchain-ai/docs/issues)。


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/comparison.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

