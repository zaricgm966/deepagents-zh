# 变更日志


> 我们的 JavaScript/TypeScript 包的更新和改进日志


**订阅**：我们的变更日志包括一个 [RSS feed](https://docs.langchain.com/oss/javascript/releases/changelog/rss.xml)，可以与 [Slack](https://slack.com/help/articles/218688467-Add-RSS-feeds-to-Slack)、[电子邮件](https://zapier.com/apps/email/integrations/rss/1441/send-new-rss-feed-entries-via-email)、Discord 机器人（如 [Readybot](https://readybot.io/) 或 [RSS Feeds to Discord Bot](https://rss.app/en/bots/rssfeeds-discord-bot)）集成，和其他订阅工具。


**2026 年 3 月 24 日**


  ## `deepagents` v1.9.0-alpha.0


`deepagents` v1.9.0 的 Alpha 版本。


  * **[异步子智能体](https://docs.langchain.com/oss/javascript/deepagents/async-subagents)**：深度智能体可以启动非阻塞后台任务，因此用户可以在子智能体同时工作时继续与代理交互。子智能体需要 [LangSmith 部署](https://docs.langchain.com/langsmith/deployment)。


  * **[后端](https://docs.langchain.com/oss/javascript/deepagents/backends) 协议 v2**：我们引入了新的 v2 后端协议 (`BackendProtocolV2`)，并对 Deep Agents 后端接口进行了向后兼容的更改。主要变化：
    * **结构化结果类型**：所有方法现在都返回结构化 `Result` 对象（例如，`ReadResult`、`LsResult`、`GrepResult`、`GlobResult`），并通过 `error` 字段进行一致的错误处理，而不是返回原始值或引发异常。
    * **多模式文件支持**：`read()` 返回带有 `.content` 字段的 `ReadResult`，而不是纯字符串。对于二进制文件（图像、PDF、音频、视频），完整的原始 `Uint8Array` 内容通过 `readRaw()` 返回，使代理能够本地处理多模式文件。
    * **简化方法名称**：`lsInfo` -> `ls`、`grepRaw` -> `grep`、`globInfo` -> `glob`。
    * **向后兼容**：现有的 v1 后端可以使用 `adaptBackendProtocol` 适应 v2 接口。 v1 接口（`BackendProtocolV1`、`SandboxBackendProtocolV1`）已弃用，但为了兼容性而保留。


**2026 年 1 月 14 日**


  ## v1.1.0


  ### `@langchain/langgraph`


引入 **StateSchema** - 一种更清晰、与库无关的方式来定义图形状态，可与任何 [标准模式](https://github.com/standard-schema/standard-schema) 兼容的验证库配合使用。


  ### 标准 JSON 架构支持


LangGraph 现在支持 [标准 JSON 模式](https://standardschema.dev/json-schema)，这是由 Zod 4、Valibot、ArkType 和其他模式库实现的开放规范。这意味着您可以使用您喜欢的验证库而无需锁定：


```typescript
import { z } from "zod"; // or valibot, arktype, etc.
import { StateSchema, ReducedValue, MessagesValue } from "@langchain/langgraph";

const AgentState = new StateSchema({
  messages: MessagesValue,
  currentStep: z.string(),
  count: z.number().default(0),
  history: new ReducedValue(
    z.array(z.string()).default(() => []),
    {
      inputSchema: z.string(),
      reducer: (current, next) => [...current, next],
    }
  ),
});

// Type-safe state and update types
type State = typeof AgentState.State;
type Update = typeof AgentState.Update;

const graph = new StateGraph(AgentState)
  .addNode("agent", (state) => ({ count: state.count + 1 }))
  .addEdge(START, "agent")
  .addEdge("agent", END)
  .compile();
```


  ### 新的状态值原语


  * **ReducedValue**：使用自定义缩减器定义字段以累积值。支持类型安全减速器输入的单独输入和输出模式。
  * **UntrackedValue**：定义执行期间存在但从未设置检查点的瞬态 - 对于数据库连接、缓存或仅运行时配置有用。
  * **MessagesValue**：使用标准消息缩减器预先构建的 `ReducedValue`，用于聊天消息。


  ### 类型助手导出


用于在图形生成器外部键入函数的新导出类型实用程序：


  * `图节点
` - 具有完全推理功能的类型节点函数  * `条件边缘路由器
` - 键入条件边缘路由器


```typescript
// Type standalone node functions
const myNode: GraphNode<typeof AgentState> = (state, config) => {
  return { count: state.count + 1 };
};

// Use schema type helpers directly
const processState = (state: typeof AgentState.State) => {
  console.log(state.count);
};
```


 现有的 `Annotation` 和基于 zod 的 API 继续保持不变 - `StateSchema` 对于那些喜欢模式优先定义的人来说是一个额外的选项。


  
**了解有关状态模式的更多信息**


[查看相关页面](https://docs.langchain.com/oss/javascript/langgraph/graph-api#schema)


请参阅使用 StateSchema、ReducedValue 和 UntrackedValue 定义图形状态的完整文档。

  


  
**了解类型实用程序**


[查看相关页面](https://docs.langchain.com/oss/javascript/langgraph/graph-api#type-utilities)


使用 GraphNode 和 ConditionalEdgeRouter 在图形生成器外部键入函数。

  

**2025 年 12 月 12 日**


  ## v1.2.0


  ### `langchain`


  * [结构化输出](https://docs.langchain.com/oss/javascript/langchain/structured-output)：增加了使用 `providerStrategy` 进行结构化输出时手动设置 `strict` 模式的功能。


  ### `@langchain/openai`


  * **新的提供商内置工具：** 支持由提供商在服务器端执行的文件搜索、网页搜索、代码解释器、图像生成、计算机使用、shell 和 MCP 连接器工具。请参阅[服务器端工具使用](https://docs.langchain.com/oss/javascript/langchain/tools#server-side-tool-use)和[OpenAI](https://docs.langchain.com/oss/javascript/integrations/chat/openai)聊天集成。
  * **内容审核：** `ChatOpenAI` 上的新 `moderateContent` 选项用于检测和处理不安全内容。
  * 首选 GPT-5.2 Pro 模型的响应 API。


  ## v1.3.0


  ### `@langchain/anthropic`


  * **新的提供商内置工具：** 支持由提供商在服务器端执行的文本编辑器、Web 获取、计算机使用、工具搜索和 MCP 工具集工具。请参阅[服务器端工具使用](https://docs.langchain.com/oss/javascript/langchain/tools#server-side-tool-use) 和[Anthropic](https://docs.langchain.com/oss/javascript/integrations/chat/anthropic) 聊天集成。
  * 暴露的 `ChatAnthropicInput` 类型可提高类型安全性。


  ## v1.1.0


  ### `@langchain/ollama`


  * **本机结构化输出：** 通过 `withStructuredOutput` 添加了对本机结构化输出的支持。
  * 支持自定义 `baseUrl` 配置。


  ## v1.0.0


  ### `@langchain/community`


  * Jira 文档加载器更新为使用 v3 API。
  * LanceDB：添加了 `similaritySearch()` 和 `similaritySearchWithScore()` 支持。
  * Elasticsearch 混合搜索支持。
  * 全新 `GoogleCalendarDeleteTool`。
  * 针对 LlamaCppEmbeddings、PrismaVectorStore、IBM WatsonX 的各种错误修复以及安全性改进。


  ### 其他套餐


  * **@langchain/xai：** 本机实时搜索支持。
  * **@langchain/tavily：** 添加了 Tavily 的研究端点。
  * **@langchain/mongodb:** 新的 MongoDB LLM 缓存。
  * **@langchain/mcp-adapters：** 添加了 `onConnectionError` 选项。
  * **@langchain/google-common：** `withStructuredOutput` 中的 `jsonSchema` 方法支持。
  * **@langchain/core：** 安全修复、美人鱼图中更好的子图嵌套、运行 ID 的 UUID7。


**2025 年 11 月 25 日**


  ## v1.1.0


  * [模型配置文件](https://docs.langchain.com/oss/javascript/langchain/models#model-profiles)：聊天模型现在通过 `.profile` getter 公开支持的特性和功能。这些数据来源于[models.dev](https://models.dev)，一个提供模型能力数据的开源项目。
  * [模型重试中间件](https://docs.langchain.com/oss/javascript/langchain/middleware/built-in#model-retry)：新的中间件，用于自动重试失败的模型调用，并具有可配置的指数退避，提高代理可靠性。
  * [内容审核中间件](https://docs.langchain.com/oss/javascript/langchain/middleware/built-in#provider-specific-middleware)：OpenAI 内容审核中间件，用于检测和处理代理交互中的不安全内容。支持检查用户输入、模型输出和工具结果。
  * [摘要中间件](https://docs.langchain.com/oss/javascript/langchain/middleware/built-in#summarization)：已更新以支持使用模型配置文件进行上下文感知摘要的灵活触发点。
  * [结构化输出](https://docs.langchain.com/oss/javascript/langchain/structured-output)：现在可以从模型配置文件推断 `ProviderStrategy` 支持（本机结构化输出）。
  * [`SystemMessage` for `createAgent`](https://docs.langchain.com/oss/javascript/langchain/middleware/custom#dynamic-prompt)：支持将 `SystemMessage` 实例直接传递给 `createAgent` 的 `systemPrompt` 参数，以及用于扩展系统消息的新 `concat` 方法。启用缓存控制和结构化内容块等高级功能。
  * [动态系统提示中间件](https://docs.langchain.com/oss/javascript/langchain/short-term-memory)：`dynamicSystemPromptMiddleware` 的返回值现在是纯累加的。当返回 [`SystemMessage`](https://reference.langchain.com/javascript/langchain-core/messages/SystemMessage) 或 `string` 时，它们会与现有系统消息合并而不是替换它们，从而更容易组合多个修改提示的中间件。
  * **兼容性改进：** 修复了结构化输出和工具架构中 Zod v4 验证错误的错误处理，确保正确显示详细的错误消息。


**2025 年 10 月 20 日**


  ## v1.0.0


  ### `langchain`


  * [发行说明](https://docs.langchain.com/oss/javascript/releases/langchain-v1)
  * [迁移指南](https://docs.langchain.com/oss/javascript/migrate/langchain-v1)


  ### `langgraph`


  * [发行说明](https://docs.langchain.com/oss/javascript/releases/langgraph-v1)
  * [迁移指南](https://docs.langchain.com/oss/javascript/migrate/langgraph-v1)


  

如果您遇到任何问题或有反馈，请[打开问题](https://github.com/langchain-ai/docs/issues/new?template=01-langchain.yml)，以便我们改进。要查看 v0.x 文档，[转到存档内容](https://github.com/langchain-ai/langchainjs/tree/v0.3/docs/core_docs/docs)。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/javascript/releases/changelog.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

