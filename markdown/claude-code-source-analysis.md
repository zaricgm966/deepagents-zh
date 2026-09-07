# Claude Code 源码解析：公开 SDK 与运行时边界

**GitHub：** [Claude Code 官方仓库](https://github.com/anthropics/claude-code) · [Claude Agent SDK Python 源码](https://github.com/anthropics/claude-agent-sdk-python) · [本章固定版本](claude-code-source-analysis.md)

> 本章为独立中文源码讲解，核对日期为 2026-09-07。SDK 固定提交为 `efd4d865ef1795daffee3cd24cce45307aed8a51`。Claude Code 官方公开仓库不是完整 CLI 引擎源码；本章能逐行核对的是 MIT 许可的 Python SDK。涉及 CLI 内部的能力会标明“公开接口”或“官方行为说明”，不把自己设计的实现当作官方源码。

离线对照：[源码文件索引与许可](../source-snapshots/README.md)。

## 导读：沿着一条消息读懂整套系统

假设用户说：“给待办应用增加状态筛选，完成后运行测试。”这句话会经过 Python 客户端、子进程传输层，再到 Claude Code 运行时。运行时产生文字、工具请求和控制请求，SDK 再把它们路由到界面、权限回调或业务工具。**SDK 不是一次 `messages.create()` 的薄包装，而是一个双向的进程控制客户端；但它也没有在 Python 中重写 Claude Code 的全部 Agent loop。**

```text
用户输入 / 应用事件
  → ClaudeSDKClient.query
  → Transport.write：一行一个 JSON
  → Claude Code CLI：模型请求、内置工具和任务调度
  → stdout 消息流
      ├─ assistant / result / system → 应用展示与状态更新
      └─ control_request → SDK 回调 → control_response → CLI 继续
```

阅读时分清三类证据：**SDK 实现**能解释 Python 做了什么；**协议字段**能说明 Python 和 CLI 交换什么；**官方行为说明**说明产品如何使用，但不能证明闭源内部采用某种算法。下文的“动手观察”均是供你在独立测试项目里验证的练习，本次没有运行模型或执行这些示例。

## 01. Coding Agent 的命令系统

**先理解：斜杠命令、SDK 方法与模型消息是三个入口。** `/compact` 是交互产品的命令，`client.interrupt()` 是 SDK 控制操作，“请压缩上下文”则只是一段自然语言。不能因为文字相似就认为它们经过同一条分发路径。

在公开 SDK 中，`SubprocessCLITransport._build_command()` 把 Python 配置变成 CLI 参数；`Query.initialize()` 建立控制协议并保存初始化结果；`get_server_info()` 则让应用读取初始化信息。运行中的 `set_model()`、`set_permission_mode()`、`interrupt()` 都发送带 `subtype` 的控制请求。这些明确的接口比模拟终端按键稳定。

读参数拼接还有一个容易忽略的细节：恢复会话使用 `--resume=值`，不是把不可信的值当成独立参数。这样即使值以短横线开头，也不会被 CLI 误解析成另一个开关。它说明“命令系统”既包括用户交互，也包括进程边界上的参数约束。

**动手观察：** 在 SDK 应用中分别记录初始化信息、发送普通文本和调用 `interrupt()`，比较消息类型。自己实现 `/help` 时可以在应用本地处理；不要假定把任意 `/xxx` 送给 SDK 都会得到交互终端中的相同效果。[参数与进程入口](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)） · [initialize 与控制协议](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [公开客户端方法](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)）

## 02. Agent 循环的逐步输出

**先理解：“收到一块文字”不等于“这一轮结束”。** SDK 的数据面包含 `AssistantMessage`、`ToolUseBlock`、`ToolResultBlock`、`StreamEvent` 和 `ResultMessage`。开启 `include_partial_messages` 后，应用还会得到增量事件；完整消息和增量消息并存时，界面需要避免重复拼接文本。

底层先由 Transport 拼出完整 JSON 行，再由消息解析器创建类型化对象。`ClaudeSDKClient.receive_response()` 会把消息逐个交给调用者，并在交付 `ResultMessage` 后返回；`receive_messages()` 则是更一般的持续消息入口。这能解释为什么“用一次响应迭代器收消息”和“持续监听整个会话”不是一回事。

```python
# 教学示例：展示完整文字块；不是逐 token 渲染器，也未在本次运行。
from claude_agent_sdk import ClaudeSDKClient, AssistantMessage, TextBlock, ResultMessage

async def show_turn():
    async with ClaudeSDKClient() as client:
        await client.query("概括当前项目结构，先不要修改文件。")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
            elif isinstance(msg, ResultMessage):
                print("本轮结束：", msg.subtype)
```

**动手观察：** 让模型先读一个文件再回答，比较工具调用前后的消息顺序。不要把 `ResultMessage` 当成所有后台任务都已终止的证明，后台任务在第 16 节另有生命周期。[receive_response](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)） · [消息解析](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/message_parser.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/message_parser.py)） · [消息与增量事件类型](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)）

## 03. Agent 的错误处理与重试

这里至少存在三类失败：启动失败、协议失败和任务失败。`CLINotFoundError` 表示没有可用 CLI；`ProcessError` 带进程退出信息；`SDKJSONDecodeError` 指向消息解码问题。另一些失败则通过结果消息交给应用。应先看错误处在哪一层，再决定是否重试。

`Query._send_control_request()` 生成请求 ID，把等待事件放进表里，写入控制消息，再在超时范围内等待对应响应；结束时清理等待状态。Transport 对 stdout 进行分帧，并限制缓冲区大小。这两处分别解决“永远等不到回复”和“半条消息无限积累”，不是为了笼统地吞掉所有异常。

**不能从 SDK 推断的部分：** 模型 API 的退避策略、CLI 内置工具是否重试、服务端如何处理限流，不应由 Python 包里的一个异常类反推。重新调用整轮任务可能重复之前已经完成的写入、提交或外部操作。

**动手观察：** 用假的 transport 分别返回无效 JSON、进程退出和工具失败，检查应用是否区分报错来源；再模拟“动作完成但响应丢失”，先查询实际状态，避免无条件重放。[异常类型](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_errors.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_errors.py)） · [请求等待与清理](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [分帧、缓冲及退出处理](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)）

## 04. 持久化聊天记录

**一条消息流不是完整的可恢复存档。** SDK 返回给 UI 的消息，是展示和交互接口；CLI 的 transcript 还承担会话重建职责。直接把屏幕上的文字存进数据库，未必足以恢复工具关联、压缩边界和子会话。

这个固定版本公开了 `SessionStore` 协议：核心是 `append()` 与 `load()`，以 `project_key`、`session_id` 和可选 `subpath` 区分主会话与子会话。SDK 镜像 transcript 给外部存储，CLI 仍会维护本地副本。数据项被定义为不透明 JSON，适配器应保留不认识的字段，而不是只挑 `role` 和 `content` 保存。

恢复时，`materialize_resume_session()` 从存储载入会话，在临时配置目录中物化，再以恢复参数启动 CLI。`resume`、`continue_conversation` 和 `fork_session` 因而有不同用途：指定已有会话、继续已有对话、或从已有会话分出新分支。

**动手观察：** 先完成一轮，再关闭客户端并恢复；验证的不应只是文字是否回来，还应包括第二轮能否接着使用此前的文件结论。为多租户服务设置独立 `project_key`，不要把同一个工作目录当成所有用户的存储隔离键。[SessionStore 与会话选项](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [恢复物化流程](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/session_resume.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/session_resume.py)） · [存储镜像实现](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/session_store.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/session_store.py)）

## 05. 工具调用的权限检查

**模型负责提出动作，运行时和应用负责决定动作能否发生。** 当 CLI 发出 `can_use_tool` 控制请求，SDK 从中取出工具名、输入和权限上下文，调用应用注册的函数，再把 `PermissionResultAllow` 或 `PermissionResultDeny` 转回协议响应。允许结果可以包含经过调整的输入；拒绝结果包含原因，并可要求中断。

这条链路很适合连接审批界面：显示“要操作什么路径、用什么工具”，等待人的决定，再回复同一个请求 ID。请求处理被安排成独立异步任务，因此审批等待不必阻止主消息读取。但应用仍须处理页面关闭、用户取消和请求失效，不能把“没有点击拒绝”当成同意。

**关键边界：** `can_use_tool` 不是每次工具执行的通用监听器。已由规则或模式批准的调用可能不进入它；需要在执行前统一检查的业务条件，可研究 `PreToolUse` hook。SDK 也会对可能使回调失效的配置给出提示。这个回调本身不提供操作系统层的隔离。

**动手观察：** 对同一个测试工具设置普通模式和提前允许规则，比较权限回调出现的次数，再用 hook 记录实际调用。[can_use_tool 分支](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [权限结果及 hook 类型](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [配置组合测试](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/tests/test_option_warnings.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/tests/test_option_warnings.py)）

## 06. auto 模式自动进行权限审批

**自动审批和跳过权限检查要分开读。** 在这个 SDK 版本里，`PermissionMode` 明确包含 `auto`；Transport 把它转成 `--permission-mode auto`，已连接的客户端也能发送 `set_permission_mode` 控制请求。我们因此能确认“配置怎样到达 CLI”，不能在 SDK 中读到分类器的完整策略与实现。

[官方权限说明](https://code.claude.com/docs/en/permissions)把 auto 描述为带后台检查的自动审批；`acceptEdits`、`dontAsk`、`bypassPermissions` 有各自语义，不能简单看成一个“自动化程度”开关。

如果你自己设计审批器，值得单独保存动作、用户授权依据、结论和拒绝原因，并把异常作为明确的失败结果处理。**这是工程建议，不是 Claude 私有审批器的源码描述。** 即使某次模型生成的审批结论是允许，外部环境也仍可能拒绝访问。

**动手观察：** 在测试环境切换模式，记录模式设置的响应和后续权限事件。SDK 接受字符串、CLI 支持该模式、当前账号能够启用它，是三个不同条件。[PermissionMode](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [权限模式参数](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)） · [set_permission_mode](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)）

## 07. 可靠的文件编辑工具

读这一节时分清“内置 Edit 的实现”和“应用如何约束 Edit”。SDK 并不实现 Claude Code 内置编辑器的字符串匹配或补丁算法，但 `PreToolUseHookInput`、`PostToolUseHookInput` 与 `PermissionResultAllow.updated_input` 让应用能观察或修改工具边界上的输入输出。

可以将编辑过程拆成：定位文件 → 验证请求 → 审批 → 执行 → 检查结果。SDK 对前后回调和协议传输提供证据；具体如何匹配旧字符串、怎样检测并发改动，属于 CLI 运行时，不能仅凭字段名下结论。

自己实现编辑工具时，实用的最小契约是：“基于刚读到的内容修改，找不到目标就报错；返回具体改了什么；必要时重新读文件再生成修改。”这比失败后直接覆盖整个文件容易发现误改。需要特别区分文本修改成功与程序行为正确，后者还要测试。

**动手观察：** 在测试项目中先读取文件，再由另一个编辑器修改同一位置，观察工具返回和 hook 顺序。不要拿函数名叫 `Edit` 当成“具备事务性、原子性和自动冲突合并”的证明。[工具前后 hook 契约](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [更新输入的权限响应](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [编辑约束示例](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/examples/hooks.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/examples/hooks.py)）

## 08. 用 @ 引用文件

**交互界面的 `@` 是一个上下文入口，SDK 中没有同名的文件补全引擎。** 当前公开 Python 客户端会把字符串提示放到 `message.content`，或透传异步迭代器提供的消息字典。这里看不到终端如何弹出候选项，也看不到内置文件引用如何展开。

因此，开发自己的界面时要先决定 `@src/app.ts` 的产品契约：只传路径，让 Agent 调用读取工具；还是由应用读取受允许的文件，并以附带来源的内容块送入上下文。前者保留按需读取，后者更确定，但会增加上下文体积，也需要处理过期内容。**这两种是应用设计方案，不是声称 CLI 采用了其中一种。**

路径存在不等于已经把文件全文给了模型。需要结合随后是否出现读取工具调用、读取结果和任务回答来判断。来自文件的文字还应作为资料处理，不能因文件写着“忽略用户要求”就让它改变应用权限。

**动手观察：** 对同一份测试文件，分别只发送路径和附带少量有来源的内容，比较工具调用与回答依据。[官方交互说明](https://code.claude.com/docs/en/interactive-mode)提供产品入口；Python 层的实际证据见 [query 的字符串与消息字典分支](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)）。

## 09. 更灵活的上下文注入机制

SDK 提供三个值得分开研究的来源：`system_prompt` 设置基础行为；`setting_sources` 控制配置来源；hooks 在某个生命周期节点补充信息。`UserPromptSubmit` 与 `PostToolUse` 的专用输出类型都能携带 `additionalContext`，前者适合当前任务约束，后者适合刚获得的工具证据。

`Query.initialize()` 会给 Python 回调分配 ID，把事件名称、匹配器和回调 ID 交给 CLI。之后 CLI 发来 hook 控制请求，SDK 找到原来的 Python 函数执行。跨进程传递的是回调标识与数据，不是把 Python 函数序列化给 CLI。

例如，“项目只支持移动端”可以成为启动时的项目约束；“刚才测试失败在第几项”可以随工具结果补充。注入时记录来源、时机和用途，比把所有资料反复追加进一条巨大 system prompt 更容易解释行为。路径访问配置和项目配置加载也不要混为一谈。

**动手观察：** 为 `UserPromptSubmit` 注册只返回一条上下文的 hook，记录触发顺序，再把同样信息放在长期配置中比较作用范围。[hook 注册与回调分发](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [additionalContext 与配置来源](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [配置来源示例](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/examples/setting_sources.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/examples/setting_sources.py)）

## 10. 让 Agent 主动向你提问

权限审批问“这个动作能不能做”，澄清问题问“用户究竟想要什么”。它们都可能让执行暂停，但应用展示和保存的内容不同。[官方用户输入说明](https://code.claude.com/docs/en/agent-sdk/user-input)把 `AskUserQuestion` 接到权限回调通道：应用展示模型提供的问题与选项，再返回用户回答。

在 SDK 源码层，能追踪的是 `can_use_tool` 请求、回调等待，以及 `updated_input` 回传。问题工具如何生成题目和做决策，仍由 CLI 与模型完成。自己加一个聊天输入框，不会自动接通这个正在等待的工具请求。

可靠的交互需要给每个问题保留请求标识和会话归属；用户选项回来了，才能关联回原请求。让用户等待期间可以阅读其他内容，但不能把超时、页面关闭或没有回答自动转换成推荐项。若要把等待持久化到另一个进程生命周期，需要单独研究 SDK 的延后执行契约，不能仅挂起一个内存 future。

**动手观察：** 让 Agent 在实现筛选前询问“按状态还是按标签”，记录问题请求、用户回答与继续执行的对应关系；再取消本轮，确认旧回答不会进入下一轮。[控制请求与取消](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [PermissionResultAllow 与延后执行类型](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)）

## 11. 让 Agent 跟踪多步任务

**待办清单和运行中的后台任务是两种状态。** 清单描述“准备做什么、声称做到哪一步”；`TaskStartedMessage`、`TaskProgressMessage`、`TaskNotificationMessage`、`TaskUpdatedMessage` 则描述运行时任务的生命周期。不能用某条文本里的“已完成”替代任务的结束事件，也不能把运行时任务结束视为需求验收通过。

SDK 给任务消息提供 `task_id`、进度、用量和结束状态，并为终止状态定义集合。内部 `_track_task_lifecycle()` 用任务 ID 维护正在执行的委派工作，同时接受 notification 与带终止状态的 update；用集合的 `discard` 使重复到达的结束信息不会再次移除出错。

如果要做任务面板，可将“检查代码、实施修改、运行验证”存成业务清单，再把相应的工具调用和结果关联上去。SDK 的任务事件提供运行状态，证据是否足以完成该清单仍由应用或验收逻辑决定。

**动手观察：** 模拟同一个任务先发 completed update、再发 notification，面板应只结束一次。进一步模拟任务完成但测试失败，清单中的“验证通过”应保持未完成。[任务消息与终止状态](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [_track_task_lifecycle](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)）

## 12. 给 Agent 加上长期记忆

先区分三件事：会话存档保存曾经发生的事件；上下文保存本轮模型能看见的输入；长期记忆保存跨任务可复用的信息。把 transcript 原样放进数据库，只完成了第一件事。

公开 SDK 中可以看到 `AgentDefinition.memory` 的 `user`、`project`、`local` 配置，以及项目配置来源和上下文用量中的 `memoryFiles` 字段。它们说明存在记忆作用域与加载结果的接口，不能说明 CLI 内部如何决定记下哪句话、怎样淘汰旧记忆。产品层面的记忆文件与规则见 [官方记忆说明](https://code.claude.com/docs/en/memory)。

自己构建长期记忆时，可以先保存稳定事实：项目使用的测试入口、明确的用户偏好、已确认的系统限制；为每条记录附带来源和更新时间。像“当前测试进程 PID”这样的短期状态不应无限期留作项目知识。读取时仍需核对实际仓库，旧记忆不是覆盖当前代码的权威。

**动手观察：** 在测试项目中改变一项配置，开启新会话并检查可见记忆信息，再确认回答能根据当前文件纠正旧结论。[AgentDefinition.memory 与 memoryFiles](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [文件系统中的 Agent 配置](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/examples/filesystem_agents.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/examples/filesystem_agents.py)）

## 13. 支持 rewind 回退对话和代码

**恢复会话、回退文件、回退对话位置要分别处理。** `ClaudeSDKClient.rewind_files(user_message_id)` 发出 `rewind_files` 控制请求；调用前需要启用 `enable_file_checkpointing`。这里的定位点是用户消息 UUID，不能随便换成当前会话 ID。

另有 `resume_session_at`、`fork_session` 等恢复配置，它们影响会话从哪里继续。这解释了为什么“代码回去了，但聊天仍记得后续尝试”并不矛盾：文件状态与对话状态不是同一份数据。

[官方 checkpointing 说明](https://code.claude.com/docs/en/agent-sdk/file-checkpointing)也明确了适用范围。源码能证明 SDK 会发送回退请求，不能证明任意 shell 命令、外部数据库或网络动作都能撤销。要研究具体磁盘快照格式和恢复算法，还需要 CLI 内部实现，Python 包没有提供这部分。

**动手观察：** 记录用户消息 UUID，让内置文件工具修改一份临时文件，再调用文件回退；分别检查文件内容和会话消息，不把两者混为同一个断言。[rewind_files](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)） · [回退控制请求](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [文件检查点与恢复位置](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)）

## 14. 支持 compact 压缩上下文

压缩的目标是在模型窗口有限时继续任务，不是删除磁盘上的所有聊天记录。SDK 提供 `PreCompact` hook，并能通过 `get_context_usage()` 查询上下文用量；返回类型包括上下文大小、自动压缩相关状态等字段。它们为应用提供观察入口，但压缩摘要的生成算法并未在 SDK 中实现。

可以按这条线阅读：客户端发 `get_context_usage` → 内部 Query 发控制请求 → CLI 返回统计 → 应用展示；另一路是 CLI 触发压缩前 hook，SDK 调用你的回调。统计、通知与实际摘要生成是不同职责。

做自己的 Agent 时，压缩后仍应保留任务目标、用户更正、已改文件、验证结果和待解决问题。仅保留一份“聊了什么”的泛化摘要，可能无法继续执行。这是设计建议，不能当作该产品对摘要完整性的保证。

**动手观察：** 在较长测试会话中记录压缩前后的用量，随后要求继续一个尚未完成的步骤，检查任务约束是否仍然生效。不要假定给 SDK 发送字符串 `/compact` 就等价于一个公开的 `compact()` 方法。[get_context_usage](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)） · [PreCompactHookInput 与 ContextUsageResponse](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)）

## 15. 给 Agent 注册 MCP 服务器

MCP 把业务能力组织成可发现、可调用的工具接口。SDK 支持外部服务器配置，也支持 Python 进程内的 `create_sdk_mcp_server()`。进程内工具可以直接复用应用已有的数据库客户端或服务对象，不必为了一个查询单独搭 HTTP 服务。

跨进程时 Python 对象不能直接写进 JSON。Transport 构造 MCP 配置时去掉进程内 server 的 `instance`，只把可序列化的身份信息交给 CLI；真正的对象留在 Python。CLI 发来 MCP 控制请求后，SDK 根据服务器名找到 bridge，再执行对应协议操作。

阅读顺序是 `tool()` 声明 → `create_sdk_mcp_server()` 组织 → transport 配置 → `Query._handle_sdk_mcp_request()` 路由。`get_mcp_status()`、`reconnect_mcp_server()` 和 `toggle_mcp_server()` 补齐运行时管理。注册成功不代表工具永远健康，也不代表其权限已经被批准。

**动手观察：** 注册一个只做整数加法的进程内工具，记录其名称、参数和返回内容；再传错参数或关闭服务器，检查失败是怎样回到模型和应用的。[工具装饰器与 MCP server](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/__init__.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/__init__.py)） · [MCP 请求路由](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [去除 instance 的序列化边界](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)）

## 16. 让 Agent 在后台运行命令

后台化解决的是长命令占住当前对话的问题，同时引入另一个问题：什么时候整个运行真正结束？SDK 内部注释明确区分“一个 result 帧结束一轮”和“整个 run 已经没有后续工作”。

`_track_task_lifecycle()` 只对指定的委派 Agent 任务维护等待集合。代码特意不把持续运行的后台 shell 当成必须等待结束的 Agent 任务，否则 `tail -f` 或开发服务器可能导致 stdin 永远不关闭。`wait_for_result_and_end_input()` 再结合双向通信需求决定何时关闭输入流。这是 SDK 中真实可读的生命周期处理，不是对 CLI 进程管理器的猜测。

`stop_task(task_id)` 是发送停止请求的公开入口。请求已发送、任务进入终止态、子进程资源已经清理也应分别观察。源码注释还列出了“任务已结束但父任务后续轮次尚未开始”的竞态，不能把本实现描述成已彻底消除所有后台收尾问题。

**动手观察：** 分别模拟一个会完成的子 Agent 与一个持续运行的 shell，查看任务集合和连接收尾是否不同。[任务跟踪与输入流关闭](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [stop_task](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)）

## 17. 实现 Sub Agent 机制

子 Agent 是带任务边界的另一段执行过程，不只是再起一个协程。公开的 `AgentDefinition` 包括描述、提示词、工具、模型、记忆、后台执行等配置。SDK 把这些定义放在初始化控制请求的 `agents` 字段中，而不是靠 Python 自行调度 Claude 的下一步推理。

接下来可以观察 `parent_tool_use_id`、任务 ID 和任务生命周期消息，理解父任务怎样把子任务结果关联回来。若你只把所有子任务输出拼到同一个文本框里，完成顺序一变就很难知道结论属于哪个任务。

适合委派的例子是“独立检查测试入口”，主任务同时调查 UI 代码；不适合的是让两个子任务不加协调地修改同一文件。定义不同提示词不会自动创建独立工作目录，也不会自动合并 Git 冲突。工具范围和执行环境仍须明确设计。

**动手观察：** 注册一个仅允许读取与检索的分析子 Agent，让它交付文件路径、依据和待确认点；父 Agent 再据此实施修改。检查结果中是否保留来源，而不是只有一句“已经看过”。[AgentDefinition 与任务关联字段](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [agents 初始化传递](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [官方子 Agent 示例](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/examples/agents.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/examples/agents.py)）

## 18. 让 Agent 监听外部事件

这里需要区分三条事件流：模型输出、Agent 自己的生命周期 hook、应用接收的外部事件。SDK 的 hooks 是运行时回调，不是通用的 webhook 服务器；`TaskNotificationMessage` 则是任务系统的信息，也不能直接当作任意业务事件队列。

Python 应用可以自己接收文件变化、CI 结果或 webhook，再通过持续连接的客户端发送新消息。`query()` 的异步消息字典分支和 `_read_messages()` 的持续读取构成输入输出基础；外部事件的鉴权、去重、落盘与消费确认需要由宿主完成。

```text
教学架构，非 CLI 内部源码：
外部事件 → 校验来源与事件 ID → 持久队列 → 选定会话
          → 发送为有来源的用户资料 → Agent 工作 → 记录处理结果
```

只检测到“有新日志”通常不值得唤醒模型；筛选出“构建从成功变为失败”这样的变化，才能降低无用运行。若事件文本带有指令，它仍是外部数据，不能自动获得用户授权。

**动手观察：** 给应用两次同一个模拟事件 ID，确认只投递一次；再在发送前断开连接，检查是否能够恢复投递而不重复执行。[持续客户端的 query](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)） · [数据与控制消息分流](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/_internal/query.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)） · [TaskNotificationMessage 与 HookEventMessage](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)）

## 19. 支持图片输入

图片输入要把媒体数据交给模型，仅发送本地文件名通常不够。Python 客户端接受异步消息字典，因此可以承载包含文本与图片的结构化 `content`；它负责 JSON 传输，不会因为字符串看起来像 `.png` 就在这里自动读图。

在这一层最值得观察的是边界：应用准备图片内容、格式和来源 → SDK 写入消息 → CLI 和模型服务处理多模态输入 → 应用展示结果。CLI 的图像解码、缩放策略和模型视觉推理不在 Python SDK 的这段代码中。

反向输出也可能包含图片。仓库的 MCP 集成测试验证了工具返回 image 内容的路径，这与“用户给模型上传图片”是两个方向，不应拿一个测试证明另一个方向的所有行为。JSON 消息越大越容易触发缓冲或传输约束，不能把整个图片二进制直接塞进普通文本提示。

**动手观察：** 使用一张内容已知的小图片，对比只传路径与传结构化图片内容的结果；记录媒体类型和尺寸，不在日志中打印整份 base64。[结构化输入透传](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/client.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/client.py)） · [消息内容与工具结果](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/src/claude_agent_sdk/types.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/src/claude_agent_sdk/types.py)） · [图片工具结果测试](https://github.com/anthropics/claude-agent-sdk-python/blob/efd4d865ef1795daffee3cd24cce45307aed8a51/tests/test_sdk_mcp_integration.py)（[离线源码](../source-snapshots/claude-agent-sdk-python/tests/test_sdk_mcp_integration.py)）

## 阅读路线与自测

第一遍只读 1、2、5、15 节，掌握“客户端—控制协议—CLI”这一主干；第二遍读 4、13、14 节，区分存档、文件回退和上下文压缩；最后读 11、16、17、18 节，研究任务生命周期和并发事件。

读完后应能回答：为什么一个 result 帧不一定代表所有任务结束？为什么已允许的工具可能不触发权限回调？为什么恢复聊天记录不等于回退代码？为什么 SDK 开源仍不足以逐行讲解 CLI 的所有行为？能用具体接口和消息流回答这些问题，比背下所有目录名更有用。

对照阅读：[Codex 源码解析](codex-source-analysis.md)。两章采用相同的 19 个主题，便于逐项比较。本文没有复制参考教程的正文；功能主题沿用用户提供的阅读方向，解释基于公开源码与明确标注的官方行为说明。
