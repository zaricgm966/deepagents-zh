# 变更日志


> Python 包的更新和改进日志


**订阅**：我们的变更日志包括一个 [RSS feed](https://docs.langchain.com/oss/python/releases/changelog/rss.xml)，可以与 [Slack](https://slack.com/help/articles/218688467-Add-RSS-feeds-to-Slack)、[电子邮件](https://zapier.com/apps/email/integrations/rss/1441/send-new-rss-feed-entries-via-email)、Discord 机器人（如 [Readybot](https://readybot.io/) 或 [RSS Feeds to Discord Bot](https://rss.app/en/bots/rssfeeds-discord-bot)）集成，和其他订阅工具。


**2026 年 9 月 1 日**


  ## `langchain` v1.4.0


MCP 支持现在在 LangChain 的 `langchain.mcp` 命名空间中提供，基于 [FastMCP](https://gofastmcp.com) 构建。它取代了独立的 `langchain-mcp-adapters` 软件包。使用 `mcp` 额外安装：


  


```bash
pip install "langchain[mcp]"
```


```bash
uv add "langchain[mcp]"
```


  


  


 `langchain.mcp` 命名空间处于测试阶段。从它导入会引发 `LangChainBetaWarning`。

  


  ### 特征


  * **一个适配器，任何传输**：`MCPAdapter` 从其目标推断传输 — URL、stdio 上的本地脚本、进程内服务器、[多个服务器](https://docs.langchain.com/oss/python/langchain/mcp/connections#multiple-servers) 的 `MCPConfig` 字典或预构建的 `fastmcp.Client`。 `await adapter.list_tools()`返回为`create_agent`准备的LangChain工具。参见[MCP概述](https://docs.langchain.com/oss/python/langchain/mcp)。
  * **中断驱动的启发**：当服务器在调用中请求输入时，`MCPAdapter` 将问题显示为 LangGraph `interrupt()`，因此人类会回答并继续运行。请参阅[启发](https://docs.langchain.com/oss/python/langchain/mcp/tools#elicitation)。
  * **通过 FastMCP 进行身份验证**：不记名令牌、具有动态客户端注册的完整 OAuth 2.1 或任何 `httpx.Auth`，包括部署中的[每用户身份验证](https://docs.langchain.com/oss/python/langchain/mcp/auth#per-user-authentication)。请参见[验证](https://docs.langchain.com/oss/python/langchain/mcp/auth)。
  * **更丰富的工具元数据**：每个工具都在其元数据的 `mcp` 命名空间下携带其 MCP 出处，包括 `destructive_hint` 等注释，用于[控制批准后的破坏性工具](https://docs.langchain.com/oss/python/langchain/mcp/tools#human-in-the-loop)。请参阅[工具元数据](https://docs.langchain.com/oss/python/langchain/mcp/tools#tool-metadata)。


  ### 迁移


从 `langchain-mcp-adapters` 迁移？ `MultiServerMCPClient` 已替换为 `MCPAdapter`，并且多个功能已更改或删除。请参阅[迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters)。


**2026 年 7 月 24 日**


  ## `deepagents` v0.7.0


默认情况下，更精简、更可配置的线束。在默认代理轮流中，输入令牌下降 **65%** (5,395 → 1,895)，根据我们的[改进的评估套件](https://www.langchain.com/blog/how-we-benchmark-deep-agents) 进行验证，没有质量回归。


  ### 优化


  * **默认情况下的精益提示**：编写的基本提示以空内容开头，并且工具使用散文已删除重复的工具架构。与默认代理的工具模式隔离，总描述标记下降 **43%** (4,005 → 2,302)；结合空基本提示和选择加入待办事项，默认代理回合的输入令牌下降 **65%** (5,395 → 1,895)。工具行为未改变。 ([#4859](https://github.com/langchain-ai/deepagents/pull/4859)、[#4979](https://github.com/langchain-ai/deepagents/pull/4979)、[#5009](https://github.com/langchain-ai/deepagents/pull/5009))


  ### 特征


  * **[覆盖默认中间件实例](customization.md#middleware)**：`.name` 与内置实例匹配的 `middleware=`（或子智能体 `middleware`）实例现在会就地替换该默认值，而不是在重复时出错。例如，传递您自己的 `SummarizationMiddleware(...)` 来更改令牌触发器或摘要模型，而无需禁用内置默认值。 ([#4251](https://github.com/langchain-ai/deepagents/pull/4251))
  * **文件系统工具**：新的 [`delete`](tools.md#built-in-harness-tools) 工具可删除文件或递归删除目录（[#3659](https://github.com/langchain-ai/deepagents/pull/3659)、[#3851](https://github.com/langchain-ai/deepagents/pull/3851)）； `write_file` 现在覆盖现有文件而不是出错 ([#4109](https://github.com/langchain-ai/deepagents/pull/4109))； `FilesystemMiddleware` 接受[工具白名单](overview.md#virtual-filesystem-access)，以仅公开选定的内置工具（[#4325](https://github.com/langchain-ai/deepagents/pull/4325)、[#4698](https://github.com/langchain-ai/deepagents/pull/4698)）；读取和搜索针对开放模型进行了调整 - 分页 `read_file` 报告总行数和剩余行数以及下一个 `offset` ([#4540](https://github.com/langchain-ai/deepagents/pull/4540))，`grep`/`glob` 使用 `truncated` 标志返回部分结果，而不是挂在大树上([#4063](https://github.com/langchain-ai/deepagents/pull/4063))，`grep` 通过流式输出和可选上下文行获得 1,000 场比赛上限 ([#4570](https://github.com/langchain-ai/deepagents/pull/4570)、[#4706](https://github.com/langchain-ai/deepagents/pull/4706))。
  * **更多提示缓存支持**：通过 `deepagents[aws]` 额外功能 ([#4108](https://github.com/langchain-ai/deepagents/issues/4108)) 进行基岩提示缓存，以及自动 Fireworks 提示缓存会话亲和性 ([#4598](https://github.com/langchain-ai/deepagents/pull/4598))。
  * **NVIDIA 支持**：内置 Nemotron 3 Ultra 线束配置文件以及 NIM 应用程序来源归属。 （[#4192]（https://github.com/langchain-ai/deepagents/pull/4192），[#4455]（https://github.com/langchain-ai/deepagents/pull/4455））


  ### 重大变化


  * **规划待办事项是可选的**：默认情况下，`create_deep_agent` 不再包含 `TodoListMiddleware`，因此 `write_todos` 工具、`todos` 状态通道和待办事项规划提示不存在，除非使用 `middleware=[TodoListMiddleware()]` 恢复。 （OpenAI Codex 线束配置文件仍然自动选择加入。）（[#4929](https://github.com/langchain-ai/deepagents/pull/4929)）
  * **删除后端兼容性垫片**：传递具体的 `BackendProtocol` 实例而不是工厂，使用显式 `namespace` 配置 `StoreBackend`，并使用当前的 `ls` / `glob` / `grep` / `ReadResult` API。删除的符号包括 `BackendFactory`、`BACKEND_TYPES`、`FileFormat` 和 `Unset`。新文件存储字符串`FileData.content`；旧的 `list[str]` 内容保持可读并在下次写入时转换。 ([#4541](https://github.com/langchain-ai/deepagents/pull/4541))
  * **输出格式更改**：空的 `ls` / `glob` 输出现在是 `No files found` 而不是 `[]`，并且 `read_file` 不再呈现固定宽度的 `cat -n` 样式装订线 - 更新原始工具输出的任何解析器。 ([#4561](https://github.com/langchain-ai/deepagents/pull/4561))


将以下提示复制到您的 AI 编码助手中，以迁移这些重大更改的代码库：


  

将 deepagents 代码库从 v0.6.x 迁移到 v0.7。


将此代码库从 `deepagents` v0.6.x 迁移到 v0.7 以考虑以下重大更改：


    1. 默认情况下，`create_deep_agent` 不再包含 `TodoListMiddleware`。如果此代码库依赖于 `write_todos` 工具、`todos` 状态通道或待办事项计划提示，请通过从 `langchain.agents.middleware`（不是 `deepagents`）导入 `TodoListMiddleware` 并将其传递给 `create_deep_agent` 来恢复它：


```python
from langchain.agents.middleware import TodoListMiddleware
from deepagents import create_deep_agent

agent = create_deep_agent(middleware=[TodoListMiddleware()])
```


    2. 后端兼容性垫片已删除：`BackendFactory`、`BACKEND_TYPES`、`FileFormat` 和 `Unset` 不再存在。将任何后端工厂替换为具体的 `BackendProtocol` 实例，并将显式 `namespace` 添加到每个 `StoreBackend` 配置中：


```python
from deepagents import create_deep_agent
from deepagents.backends import StoreBackend

# Before (v0.6.x): factory callable, and StoreBackend with no explicit namespace
agent = create_deep_agent(backend=lambda rt: StoreBackend())  # [!code --]

# After (v0.7): concrete backend instance with an explicit namespace
agent = create_deep_agent(backend=StoreBackend(namespace=lambda rt: (rt.server_info.user.identity,)))  # [!code ++]
```


 还更新调用以使用当前的 `ls`、`glob`、`grep` 和 `ReadResult` API。


    3. 工具输出格式已更改：空的 `ls` / `glob` 输出现在是字符串 `No files found` 而不是 `[]`，并且 `read_file` 不再呈现固定宽度的 `cat -n` 样式的行号装订线。更新解析这些工具输出的任何代码。


在代码库中搜索已删除符号的用法以及依赖于旧输出格式的解析逻辑，应用必要的更改，并标记任何需要手动检查的内容。

  

**2026 年 5 月 12 日**


  ## `deepagents` v0.6.0


  * **[`CodeInterpreterMiddleware`](interpreters.md)**：（实验）`deepagents` 现在支持通过作用域 QuickJS 运行时执行代码和编程工具调用。
  * 支持 `stream_events` / `astream_events` 中的 `version="v3"`。有关详细信息，请参阅[事件流](event-streaming.md) 指南。
  * **[`DeltaChannel`](https://docs.langchain.com/oss/python/langgraph/pregel#deltachannel)（测试版）**（[博客](https://www.langchain.com/blog/delta-channels-evolving-agent-runtime)）：Deep Agents 现在使用 `DeltaChannel` 来存储消息历史记录和代理文件。不是将完整的累积值重新序列化到每个检查点中，而是仅存储在每个步骤中写入的增量增量 - 随着线程变长，检查点大小保持较小。


  

**线程持久化后，不支持从 v0.6.0 回滚。** Deep Agents v0.6.0 将持久化消息历史记录和代理文件更改为 `DeltaChannel`，它以早期版本无法读取的新格式写入检查点。降级到较早的 Deep Agents 版本会将这些通道切换回非增量通道，从而使现有的增量检查点无法读取并导致状态重建不完整或不正确。如果需要回滚，请在降级之前使用 [delta-channel-dump 恢复脚本](https://github.com/langchain-ai/langgraph/tree/main/examples/delta-channel-dump) 迁移受影响的线程，或丢弃它们。更一般地说，避免在增量和非增量表示之间切换持久化通道。请参见[版本兼容性和通道变更](https://docs.langchain.com/oss/python/langgraph/pregel#version-compatibility-and-rollbacks)。

  


  * **[Harness 配置文件](profiles.md)**：注册每个提供商或每个模型的配置包 (`HarnessProfile`)，选择模型时 `create_deep_agent` 自动应用 - 系统提示调整、工具覆盖、中间件更改和子智能体默认值 - 无需修改调用站点。
  * **[`ContextHubBackend`](backends.md#contexthubbackend)** ([博客](https://www.langchain.com/blog/introducing-context-hub))：由 LangSmith Hub 支持的新文件系统后端。代理文件（技能、记忆和其他持久上下文）存储为 Hub 提交，为您提供每次写入的版本历史记录和 LangSmith 原生的持久性，而无需配置单独的 LangGraph 存储。


**2026 年 5 月 12 日**


  ## `langchain` v1.3.0


此版本在 `stream_events` / `astream_events` 中为 `langchain` 代理添加了对 `version="v3"` 的支持。有关详细信息，请参阅[事件流](https://docs.langchain.com/oss/python/langchain/event-streaming) 指南。


**2026 年 5 月 12 日**


  ## `langgraph` v1.2.0


此版本增加了对节点执行的更细粒度的控制（超时、错误恢复和正常关闭）、一种可减少长时间运行线程的检查点开销的新通道类型，以及具有类型化、每通道投影的新的以内容块为中心的流 API (v3)。


  * **[`DeltaChannel`](https://docs.langchain.com/oss/python/langgraph/pregel#deltachannel)（测试版）**：一种新的通道类型，仅存储每一步的增量增量，而不是重新序列化完整的累积值。对于随着时间的推移而变大的通道最有用，例如长时间运行的线程中的消息列表。使用 `snapshot_frequency=K` 每 K 步写入完整快照并限制读取延迟。


  * **[每节点超时](https://docs.langchain.com/oss/python/langgraph/fault-tolerance#timeouts)**：将 `timeout=` 传递到 [`add_node`](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node) 以限制单次尝试可以运行的时间。通过 [`TimeoutPolicy`](https://reference.langchain.com/python/langgraph/types/TimeoutPolicy) 设置硬挂钟限制 (`run_timeout`)、在进度时重置的空闲限制 (`idle_timeout`) 或两者。当限制触发时，LangGraph 会引发 [`NodeTimeoutError`](https://reference.langchain.com/python/langgraph/errors/NodeTimeoutError)，清除该尝试中的写入，并将重试策略移交给重试策略。仅限异步节点。


  * **[节点级错误处理程序](https://docs.langchain.com/oss/python/langgraph/fault-tolerance#error-handling)**：将 `error_handler=` 传递给 [`add_node`](https://reference.langchain.com/python/langgraph/graph/state/StateGraph/add_node) 以在所有重试结束后运行恢复功能。处理程序接收类型化的 [`NodeError`](https://reference.langchain.com/python/langgraph/errors/NodeError) 并可以返回 [`Command`](https://reference.langchain.com/python/langgraph/types/Command) 来更新状态并路由到不同的节点，这对于 Saga/补偿模式很有用。


  * **[正常关闭](https://docs.langchain.com/oss/python/langgraph/fault-tolerance#graceful-shutdown)**：当前超级步完成后，协同停止正在进行的运行，并保存可恢复的检查点。创建一个 [`RunControl`](https://reference.langchain.com/python/langgraph/runtime/RunControl) 并从任何线程调用 `request_drain()`；运行会引发 `GraphDrained`，并且可以稍后使用相同的配置恢复。


  * **新的事件流 API（测试版）**：将 `version="v3"` 传递到 `stream_events()` / `astream_events()`，以实现以内容块为中心的协议，具有类型化、每通道投影（`run.values`、`run.messages`、`run.lifecycle`、`run.subgraphs`）以及选择加入用于更新、自定义事件、检查点、任务和调试的转换器。 `run.messages` 每个 LLM 调用都会生成一个 `ChatModelStream`，其中包含用于文本、推理、工具调用和使用的类型化子投影。 `version="v1"` 和 `version="v2"` 不变。


超时和错误处理程序仅适用于 Python；重试策略在 Python 和 TypeScript 中继续有效。


**2026 年 4 月 7 日**


  ## `deepagents` v0.5.0


  * **[异步子智能体](async-subagents.md)**：深度智能体可以启动非阻塞后台任务，因此用户可以在子智能体同时工作时继续与代理交互。子智能体需要 [LangSmith 部署](https://docs.langchain.com/langsmith/deployment)。


  * **多模式支持**：`read_file` 工具现在除了图像之外还支持 PDF、音频和视频文件。


  * **后端更改**：我们对 Deep Agents [后端协议](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/backends/protocol.py) 进行了向后兼容的更改：
    * 更新了存储在[状态和存储后端](backends.md)中的文件格式以支持二进制文件。
    * 改进了从后端到工具的错误传播。
    * 您现在可以直接实例化 `StateBackend()` 和 `StoreBackend()`。不推荐使用工厂指定（例如 `backend=(lambda rt: StateBackend(rt))`）。


  * **Anthropic提示缓存改进**：我们进行了一些改进，以提高Anthropic模型的提示缓存性能。


**2026 年 3 月 10 日**


  ## `langgraph` v1.1.0


  * **类型安全流 (`version="v2"`)**：将 `version="v2"` 传递到 `stream()` / `astream()`，以实现统一的 `StreamPart` 输出，每个块上带有 `type`、`ns` 和 `data` 键。每种模式都有自己的 `TypedDict`，全部可从 `langgraph.types` 导入。请参阅[流媒体文档](https://docs.langchain.com/oss/python/langgraph/streaming#stream-output-format-v2)。


  * **类型安全调用（`version="v2"`）**：将 `version="v2"` 传递给 `invoke()` / `ainvoke()` 以获取具有 `.value` 和 `.interrupts` 属性的 `GraphOutput` 对象。请参阅[调用文档](https://docs.langchain.com/oss/python/langgraph/streaming#v2-invoke-format)。


  * **Pydantic 和数据类强制**：使用 `version="v2"`、`invoke()` 和 `values` 模式流输出会自动强制为您声明的 Pydantic 模型或数据类类型。


  * **修复了带有中断和子图的时间旅行**：重放不再重用过时的 `RESUME` 值，并且子图正确恢复父级历史状态的检查点。


  * **完全向后兼容**：`version="v2"` 是可选的。 `GraphOutput` 支持已弃用的字典式访问以进行逐步迁移。


**2026 年 2 月 10 日**


  ## `deepagents` v0.4.0


  * 用于可插拔沙箱的新集成包：[`langchain-modal`](https://pypi.org/project/langchain-modal/)、[`langchain-daytona`](https://pypi.org/project/langchain-daytona/) 和 [`langchain-runloop`](https://pypi.org/project/langchain-runloop/)。请参阅[沙箱指南](sandboxes.md)和示例[数据分析教程](data-analysis.md)。
  * [对话历史摘要](context-engineering.md#summarization) 的更改：
    * 现在，通过 `wrap_model_call` 事件在模型节点中进行汇总。因此，我们在图形状态中保留完整的消息历史记录。
    * 更准确的令牌计数。
    * 如果聊天模型引发 [`ContextOverflowError`](https://reference.langchain.com/python/langchain-core/exceptions/ContextOverflowError)（在 `langchain-core` 中定义），现在将自动触发摘要。目前`langchain-anthropic`和`langchain-openai`支持此功能。
  * 现在，我们默认使用前缀为 `"openai:"` 的模型字符串的响应 API。


      
**使用 Responses API 禁用数据保留**


```python
from langchain.chat_models import init_chat_model

agent = create_deep_agent(
    model=init_chat_model(
        "openai:...",
        use_responses_api=True,
        store=False,
        include=["reasoning.encrypted_content"],
    )
)
```


      


 **2025 年 12 月 15 日**


  ## `langchain` v1.2.0


  * [`create_agent`](https://docs.langchain.com/oss/python/langchain/agents)：通过[工具](https://docs.langchain.com/oss/python/langchain/tools)上的新[`extras`](https://reference.langchain.com/python/langchain/tools/#langchain.tools.BaseTool.extras)属性简化了对特定于提供商的工具参数和定义的支持。示例：
    * 特定于提供商的配置，例如 Anthropic 的[编程工具调用](https://docs.langchain.com/oss/python/integrations/chat/anthropic#programmatic-tool-calling) 和[工具搜索](https://docs.langchain.com/oss/python/integrations/chat/anthropic#tool-search)。
    * 在客户端执行的内置工具，由 [Anthropic](https://docs.langchain.com/oss/python/integrations/chat/anthropic#built-in-tools)、[OpenAI](https://docs.langchain.com/oss/python/integrations/chat/openai#responses-api) 和其他提供商支持。
  * 支持代理 `response_format` 中严格的架构遵守（请参阅 [`ProviderStrategy`](https://docs.langchain.com/oss/python/langchain/structured-output#provider-strategy) 文档）。


**2025 年 12 月 8 日**


  ## `langchain-google-genai` v4.0.0


我们重新编写了 Google GenAI 集成，以使用 Google 的综合 Generative AI SDK，该 SDK 提供了在同一界面下访问 Gemini API 和 Gemini Enterprise Agent Platform 的权限。这包括最小的重大更改以及 `langchain-google-vertexai` 中已弃用的软件包。


有关详细信息，请参阅完整的[发行说明和迁移指南](https://github.com/langchain-ai/langchain-google/discussions/1422)。


**2025 年 11 月 25 日**


  ## `langchain` v1.1.0


  * [模型配置文件](https://docs.langchain.com/oss/python/langchain/models#model-profiles)：聊天模型现在通过 `.profile` 属性公开支持的特性和功能。这些数据来源于[models.dev](https://models.dev)，一个提供模型能力数据的开源项目。
  * [摘要中间件](https://docs.langchain.com/oss/python/langchain/middleware/built-in#summarization)：已更新以支持使用模型配置文件进行上下文感知摘要的灵活触发点。
  * [结构化输出](https://docs.langchain.com/oss/python/langchain/structured-output)：现在可以从模型配置文件推断 `ProviderStrategy` 支持（本机结构化输出）。
  * [`SystemMessage` for `create_agent`](https://docs.langchain.com/oss/python/langchain/middleware/custom#dynamic-prompt)：支持将 `SystemMessage` 实例直接传递到 `create_agent` 的 `system_prompt` 参数，从而启用缓存控制和结构化内容块等高级功能。
  * [模型重试中间件](https://docs.langchain.com/oss/python/langchain/middleware/built-in#model-retry)：新的中间件，用于通过可配置的指数退避自动重试失败的模型调用。
  * [内容审核中间件](https://docs.langchain.com/oss/python/integrations/middleware/openai#content-moderation)：OpenAI 内容审核中间件，用于检测和处理代理交互中的不安全内容。支持检查用户输入、模型输出和工具结果。


**2025 年 10 月 20 日**


  ## v1.0.0


  ### `langchain`


  * [发行说明](https://docs.langchain.com/oss/python/releases/langchain-v1)
  * [迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1)


  ### `langgraph`


  * [发行说明](https://docs.langchain.com/oss/python/releases/langgraph-v1)
  * [迁移指南](https://docs.langchain.com/oss/python/migrate/langgraph-v1)


  

如果您遇到任何问题或有反馈，请[打开问题](https://github.com/langchain-ai/docs/issues/new?template=01-langchain.yml)，以便我们改进。要查看 v0.x 文档，[转到存档内容](https://github.com/langchain-ai/langchain/tree/v0.3/docs/docs) 和 [API 参考](https://reference.langchain.com/v0.3/python/)。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/python/releases/changelog.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

