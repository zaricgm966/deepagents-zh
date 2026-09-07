# Codex 源码解析

**GitHub：** [OpenAI Codex 官方源码](https://github.com/openai/codex) · [本章固定版本](codex-source-analysis.md)

> 本章为独立中文源码讲解，核对日期为 2026-09-07，固定提交 `121f91fd5d9dc66017866ce9bdc49f1e182721df`。仓库采用 Apache-2.0 许可。我们研究公开客户端与运行时，不由此推断模型权重、训练过程或全部桌面与云端服务。机制可能受配置、功能开关及宿主影响，下文讲解的是指定版本的具体路径。

离线对照：[源码文件索引与许可](../source-snapshots/README.md)。

## 导读：先看一次任务怎样走完

用“给待办应用增加状态筛选，完成后运行测试”贯穿本章：终端接收请求，核心层准备上下文，模型决定读哪些文件或调用哪些工具，运行时执行并记录结果，结果再进入下一次模型请求。用户看到的流式文字、审批弹窗和任务进度，是这条执行链向外发送的事件。

```text
TUI 输入 / 其他宿主输入
  → 命令分发或会话输入
  → run_turn：准备上下文并请求模型
  → 解析响应项，形成工具调用
  → 工具调度 → 权限与环境检查 → 实际执行
  → 工具结果、进度事件、持久化记录
  → 需要后续处理则继续，否则结束本轮
```

阅读时抓住四个对象：**输入是什么、状态存在哪、由谁改变状态、结果如何回到模型或用户。** 不必从仓库第一行读到最后一行。每节给出可跳转的 GitHub 文件和离线源码，文中的简化流程与练习是教学说明，不是从其他教程复制的实现，也不代表本次实际运行过模型或项目测试。

## 01. Coding Agent 的命令系统

**先理解：`/status` 这类命令不必经过模型才能生效。** TUI 的 `SlashCommand` 枚举统一列出命令、显示顺序和说明；`chatwidget/slash_dispatch.rs` 的 `dispatch_command()` 再根据命令分支执行本地操作或向核心层提交请求。CLI 启动时的子命令则在 `cli/src/main.rs`，与对话框中的斜杠命令属于不同层次。

例如 `/new` 走新会话相关的应用事件；`/compact` 会进入压缩请求路径；`/mention` 操作文件引用输入；`/status` 展示状态。枚举描述不等于完整行为，还要继续看分发函数：是否允许在任务进行中使用、是否接收参数、是否需要排队，都是交互契约的一部分。

这个拆分的好处是，界面命令可以快速且确定地响应，模型不会把“退出”误读成写一段退出说明。不同 UI 又可以通过核心协议复用任务能力，而不必模拟终端文字。

**动手观察：** 从 `SlashCommand::Compact` 追到分发分支，再追到核心请求；从 `SlashCommand::Status` 做同样追踪，比较哪里只更新界面，哪里改变会话。扩展命令时至少考虑名称、参数、运行中行为和错误反馈。[命令枚举](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/tui/src/slash_command.rs)（[离线源码](../source-snapshots/codex/codex-rs/tui/src/slash_command.rs)） · [命令分发](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/tui/src/chatwidget/slash_dispatch.rs)（[离线源码](../source-snapshots/codex/codex-rs/tui/src/chatwidget/slash_dispatch.rs)） · [启动参数入口](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/cli/src/main.rs)（[离线源码](../source-snapshots/codex/codex-rs/cli/src/main.rs)）

## 02. Agent 循环的逐步输出

**模型流结束不等于任务已经完成。** `core/src/session/turn.rs` 的 `run_turn()` 负责一轮任务内的推进；`stream_events_utils.rs` 从响应项中识别工具调用，形成执行 future，并标记需要后续处理。工具返回的新证据会参与下一次请求，所以“读文件 → 修改 → 运行测试 → 根据失败继续修复”可以在一轮用户任务里发生多次。

界面更新走事件，而不是核心库随处 `println!`。`core/src/lib.rs` 甚至禁止直接打印到 stdout/stderr。TUI 的 streaming 代码消费流式信息，再转换成终端呈现。这样模型文字、工具开始、工具结果和任务结束可以各有事件，不必从一整段日志里猜发生了什么。

要分清增量和完成两种信号：文字 delta 适合及时显示；一个完整工具调用必须有可解析的参数后才能按其契约执行；任务完成还要看后续工具与待处理输入。展示层如果把增量和完整消息重复拼接，就会出现重复答案。

**动手观察：** 记录一次“先读文件再回答”的事件顺序，给事件带上 turn ID、调用 ID 与时间。检查 UI 在工具运行时是否仍能显示进展，而不是等整个函数返回才更新。[run_turn 主循环](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/turn.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/turn.rs)） · [响应项与工具执行](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/stream_events_utils.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/stream_events_utils.rs)） · [终端流式呈现](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/tui/src/chatwidget/streaming.rs)（[离线源码](../source-snapshots/codex/codex-rs/tui/src/chatwidget/streaming.rs)）

## 03. Agent 的错误处理与重试

错误处理的第一步是分类：参数错误应回给模型修正；命令非零退出通常是工具结果；连接故障可能值得重试；权限拒绝需要解释约束。把这几种失败都包装成“再试一次”，会掩盖真正的问题。

`responses_retry.rs` 集中处理 Responses 流的重试与传输回退：常规路径读取重试次数和延迟，必要时尝试从 WebSocket 回退到 HTTPS，并发送重连提示。这个版本还存在由 `UnboundedConnectionRetries` 控制的特定连接失败路径，延迟逐步增加并封顶。因此不能概括成“所有错误固定重试三次”，也不能说“一律无限重试”。

工具调度层还有自己的取消与完成时序。取消发生在执行前与发生在执行后是两种事实：前者不应显示动作已经成功，后者也不能把已完成的外部副作用当作从未发生。重试模型请求尤其不能直接等同于安全地重放所有工具。

**动手观察：** 对比可重试连接错误、语法错误和权限拒绝的路径；再用测试工具模拟“已写入但响应丢失”，先验证状态再决定是否重做。源码中的测试可以帮助找边界，但本章没有执行它们。[重试、退避与传输回退](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/responses_retry.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/responses_retry.rs)） · [工具生命周期与取消](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/parallel.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/parallel.rs)）

## 04. 持久化聊天记录

**内存历史、磁盘日志和 UI 展示不是同一份数据。** 模型下一次请求使用的历史可能已截断或压缩；界面只展示其中一部分；持久化记录则必须支持恢复和重建。只保存最终回答，下一次就难以知道工具结果、会话配置和回退发生在哪里。

这个版本把日志实现放在独立的 `codex-rs/rollout` crate，`core/src/rollout.rs` 主要负责重导出与配置适配。`RolloutRecorder` 接收事件项，后台写入器序列化 JSONL，并提供 flush 路径。会话初始化的恢复分支读取 rollout，再调用历史重建逻辑，而不是把屏幕文字原样塞回模型。

为什么单独看 flush？事件已经入队，不代表已经写到存储；写到系统缓冲，也不能随意宣称满足任意断电耐久性。需要沿确认返回与错误路径理解实际保证。恢复时还要正确解释压缩和回退标记，否则旧消息可能重新出现。

**动手观察：** 在测试会话完成一轮后关闭并恢复，检查工具关联和后续推理是否连续；模拟持久化失败时，应准确报告失败，而不是仅看 UI 里有消息就声称已保存。[RolloutRecorder 与 JSONL 写入](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/rollout/src/recorder.rs)（[离线源码](../source-snapshots/codex/codex-rs/rollout/src/recorder.rs)） · [恢复与历史重建](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/mod.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/mod.rs)） · [核心层适配](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/rollout.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/rollout.rs)）

## 05. 工具调用的权限检查

**“模型想做什么”与“环境允许做什么”是两个决策。** `ToolOrchestrator` 把审批需求、沙箱选择、实际执行和某些失败后的处理放在一起。工具 handler 负责自己的业务输入，编排层负责把它放到当前权限与环境下执行。

概念上可以这样追踪：解析工具参数 → 判断是否需要审批 → 确定当前环境和沙箱 → 执行动作 → 对明确的失败类型决定是否还能采取后续路径。具体顺序与分支应以所读函数为准，并非所有工具都走完全相同的一条线。

源码中能看到环境级网络策略、是否支持升级、当前审批策略等限制。它们说明审批不是一句“允许”就自动覆盖整台机器的约束。某些动作得到工具层允许后，仍可能被执行环境拒绝；反过来，已经在现有权限范围内的动作未必需要重复询问。

**动手观察：** 在独立测试目录中比较普通读取、允许范围内写入和范围外写入，记录决策原因、请求的能力与实际执行结果。不要用文本提示词代替真实执行入口的政策判断。[工具审批与执行编排](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/orchestrator.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/orchestrator.rs)） · [文件编辑的权限路径](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/apply_patch.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/apply_patch.rs)）

## 06. auto 模式自动进行权限审批

本节借用“auto”作为功能主题，讲的是源码里的自动审查路径，不把它当成一个在所有宿主中名称与行为都相同的开关。`core/src/guardian` 的模块说明明确描述了：提取与授权有关的会话内容，交给专用审查会话评估具体动作，解析严格结果，并在超时、运行失败或格式错误时拒绝放行。

这是一条“有判断的自动审批”路径，和关闭沙箱、从不询问的完全访问配置不同。审查对象应是准备执行的具体动作，而不是只审一句泛化的任务描述。模型计划变了、动作路径变了，原结论不能不加区分地套用。

这个提交还包含 `ext/guardian-v2` 扩展，说明审批机制有不同实现路径和安装入口。本节选取 core guardian 作为阅读起点，不声称所有运行环境都只使用它。真正采用哪条路径，还需结合 feature 和宿主配置追踪。

**工程收益与代价：** 自动审查能减少低风险动作的人工等待，但增加一次审查的成本与失败面。超时、无效结果、重复拒绝和解释原因都要有明确处理；它也不能替代底层环境约束。**动手观察：** 阅读 guardian 的 review 与 review_session，找到结果解析、取消和拒绝的出口。[自动审查总览](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/guardian/mod.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/guardian/mod.rs)） · [具体审查路径](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/guardian/review.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/guardian/review.rs)） · [另一代扩展入口](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/ext/guardian-v2/src/lib.rs)（[离线源码](../source-snapshots/codex/codex-rs/ext/guardian-v2/src/lib.rs)）

## 07. 可靠的文件编辑工具

编辑不是让模型重新生成整个项目，而是把一个明确的变更应用到现有文件。`ApplyPatchHandler` 负责调用边界、环境和事件；`codex-rs/apply-patch` 负责解析及应用补丁。补丁可以表达新增、删除和带上下文的更新，模型不必每次重发整份文件。

```diff
# 补丁形状示意，不是本次实际执行的修改。
*** Begin Patch
*** Update File: src/filter.ts
@@
-return tasks;
+return tasks.filter(task => task.status === selectedStatus);
*** End Patch
```

读源码时重点看：上下文怎样匹配、找不到匹配时如何报错、重命名和删除如何处理、权限如何计算、执行结果怎样关联回调用 ID。`seek_sequence` 和更新逻辑能帮助理解“为什么旧内容不匹配时需要重新读取”，而不是靠盲目重试碰碰运气。

这里不能凭“先验证补丁”就承诺跨多个文件的数据库式事务，也不能把语法上能应用等同于代码正确。读文件、改文件、检查 diff、运行验证构成不同步骤，缺哪一步都可能漏掉问题。

**动手观察：** 在临时文件中放两个相似片段，构造带上下文的补丁；再改变原文，观察匹配失败如何回给模型。[编辑工具入口](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/apply_patch.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/apply_patch.rs)） · [补丁执行](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/apply-patch/src/lib.rs)（[离线源码](../source-snapshots/codex/codex-rs/apply-patch/src/lib.rs)） · [上下文匹配](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/apply-patch/src/seek_sequence.rs)（[离线源码](../source-snapshots/codex/codex-rs/apply-patch/src/seek_sequence.rs)）

## 08. 用 @ 引用文件

**文件引用首先解决“把目标路径准确带进输入”这一交互问题。** TUI 的 `ChatComposer` 接收异步文件搜索结果，再由 `insert_selected_file_path()` 等方法把选中的路径放入编辑区。源码特别处理相邻 token、空格和路径边界，相关测试说明这些细节会影响最终提交给 Agent 的输入。

例如用户输入 `@fil` 后选中 `src/filter.ts`，需要保证替换的是当前 token，不是另一段同名文字；用户已经移到下一个输入位置时，旧的搜索结果也不能覆盖新的内容。这个机制和“模型现在已经读过文件全文”不是一回事。

协议的 `UserInput` 有文本、图片、Skill 和结构化 Mention 等类型，但普通文件补全不能一概解释成“每个 @ 都变成同一种 Mention 对象”。当前版本还存在 mention 功能开关和不同目标类型，要沿实际提交路径判断。

**动手观察：** 从 `on_file_search_result()` 追到路径插入，再到输入提交；测试含空格路径、相邻两个 @ 和过期搜索结果。随后查看 Agent 是否又调用读取工具，区分“引用路径”和“获得文件内容”。[文件补全及测试](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/tui/src/bottom_pane/chat_composer.rs)（[离线源码](../source-snapshots/codex/codex-rs/tui/src/bottom_pane/chat_composer.rs)） · [结构化输入类型](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/protocol/src/user_input.rs)（[离线源码](../source-snapshots/codex/codex-rs/protocol/src/user_input.rs)）

## 09. 更灵活的上下文注入机制

一个真实编程请求的上下文通常不只有用户刚输入的一句话，还包括项目说明、工作目录、环境权限、工具信息和运行时事件。Codex 将许多这类内容建模为 context fragment，而不是把所有字符串随意塞进一个大变量。

`agents_md.rs` 的 `load_project_instructions()` 加载项目说明与宿主提供的用户指令；它检查项目是否受信任，并维护项目文档的字节预算。`context/mod.rs` 列出环境说明、用户指令、hook 补充、子 Agent 消息等不同片段。再沿会话与 prompt 构建路径看它们何时进入当前请求。

这种拆分使来源和用途更明确：项目约束解释“这个仓库怎么做事”，工具结果解释“刚才实际发生了什么”，环境约束解释“这次能访问哪里”。这些内容不应在展示、缓存或重建时被混成来源不明的文字。

**动手观察：** 在测试项目中改变 `AGENTS.md` 的一条明确规则，比较实际加载内容；再给一份普通资料文件写上冲突指令，确认资料不会自动获得同等权限。项目文档的加载策略还受信任状态和配置影响，不能简单承诺所有目录文件都会被无限递归读取。[项目说明加载](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/agents_md.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/agents_md.rs)） · [上下文片段](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/context/mod.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/context/mod.rs)） · [项目说明管理](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/agents_md_manager.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/agents_md_manager.rs)）

## 10. 让 Agent 主动向你提问

`request_user_input` 把澄清问题表示为结构化工具调用：模型提供问题，运行时发给宿主，宿主收集回答，再把结果送回等待中的调用。这比模型输出一句问号更明确，因为界面知道当前存在一个待回答请求。

`RequestUserInputHandler` 会验证调用来源与可用模式、解析并归一化参数，再调用 `session.request_user_input()`。这个版本明确拒绝非 root agent 直接使用该入口；`is_blocking` 根据是否处于 Plan mode 设置。由此可见“所有模式永远阻塞”或“所有子 Agent 都能弹问题”都不是这段源码的行为。

拿“筛选功能按状态还是按标签”举例，回答应按 question ID 回传，而不是靠文本顺序猜匹配。取消时 handler 返回取消结果；在相应 feature 开启时，回答还会进入授权证据或保留上下文路径。用户明确回答的约束因此可以被后续处理引用。

**动手观察：** 追踪同一个调用 ID 从工具请求到宿主回答的往返，再测试取消与无效模式。没有回答和回答了默认选项必须是两个不同状态。[问题工具处理器](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/request_user_input.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/request_user_input.rs)） · [问题与回答协议](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/protocol/src/request_user_input.rs)（[离线源码](../source-snapshots/codex/codex-rs/protocol/src/request_user_input.rs)）

## 11. 让 Agent 跟踪多步任务

`update_plan` 管理的是可展示的工作清单。工具 schema 为每一步定义 `step` 与 `status`，状态包括 `pending`、`in_progress`、`completed`。模型负责提出和更新步骤，handler 解析参数后发出 `EventMsg::PlanUpdate`，再返回结果。

对于“读取筛选组件 → 修改 → 运行测试”，用户因此能看出 Agent 自报的进展，并及时纠正范围。但 `PlanHandler` 不会自动执行测试，也不会看到 `completed` 就核验 Git diff。schema 或工具说明中的约束，同样不能自动当作 handler 已实现完整状态机校验。

还有一个重要区别：任务清单不等于产品的 Plan mode。这个固定版本的 handler 会拒绝在 `ModeKind::Plan` 下使用该 TODO 工具。前者是执行进度数据，后者是协作行为模式，不宜只因名字相似就合并理解。

**动手观察：** 先更新清单，再检查是否真正启动了任何工具；给自己的 Agent 面板加入“完成证据”，例如测试命令、退出码和变更文件。这属于面板或业务层增强，不能说原 handler 已替你做了验收。[计划 schema](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/plan_spec.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/plan_spec.rs)） · [计划事件处理](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/plan.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/plan.rs)）

## 12. 给 Agent 加上长期记忆

**长期记忆是从历史提取可复用信息，而不只是恢复原会话。** 这个版本把读取和写入分别放在 `memories/read`、`memories/write`，还有 `ext/memories` 提供工具入口。读取目录与离线生成流水线分开，有助于在当前会话使用记忆时不依赖整个生成过程。

可以沿 `start_memories_startup_task()` → Phase 1 → Phase 2 阅读。第一阶段处理符合条件的历史、生成结构化记忆材料；第二阶段整合这些材料与工作区状态。源码中能看到作业认领、并发限制、失败结果和租约等工程设施：后台任务可能重入或中断，因此不能只写一个“循环读日志然后保存摘要”的脚本就宣称等价。

目录辅助函数包含 `raw_memories.md`、`rollout_summaries` 等产物；扩展还暴露 list、read、search 和临时记事入口。哪些能力实际启用，要结合当前配置和扩展安装，不能把源码里存在某个文件等同于所有会话都已开启。

**动手观察：** 选择一条稳定的项目事实和一条短期运行状态，比较它们是否适合跨任务复用；查阅 Phase 1 的过滤与测试，再看 Phase 2 如何整合旧材料。新代码与旧记忆冲突时，仍应回到文件和运行结果核对。[记忆启动流程](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/memories/write/src/start.rs)（[离线源码](../source-snapshots/codex/codex-rs/memories/write/src/start.rs)） · [第一阶段提取](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/memories/write/src/phase1.rs)（[离线源码](../source-snapshots/codex/codex-rs/memories/write/src/phase1.rs)） · [第二阶段整合](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/memories/write/src/phase2.rs)（[离线源码](../source-snapshots/codex/codex-rs/memories/write/src/phase2.rs)） · [记忆工具入口](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/ext/memories/src/lib.rs)（[离线源码](../source-snapshots/codex/codex-rs/ext/memories/src/lib.rs)）

## 13. 支持 rewind 回退对话和代码

先把“回退”拆成两个坐标：模型会话走到哪一轮，以及工作目录里的文件处于哪个版本。用户常想同时回退两者，但一段会话回退代码不一定负责修改磁盘文件。

`session/handlers.rs` 的 `thread_rollback()` 是直接可读的会话路径：它拒绝在当前轮进行中回退，要求存在持久化历史，先 flush 并读取记录，再加入 `ThreadRolledBack` 事件进行重建，最后持久化回退标记。`thread_rollout_truncation.rs` 则解释怎样按有效历史计算回退后的消息位置。

**这一实现不能当作“自动恢复任意文件”的证据。** 文件版本应通过独立的检查点、工作区快照或 Git 机制研究；本节没有把早期版本的 ghost snapshot 说成当前调用链的一部分。已经发送的网络请求和外部系统变更更不会因聊天记录回退而自动撤销。

**动手观察：** 先在临时项目中记录 diff，再回退会话，分别检查消息与文件。若自己实现“一键回退”，应明确让用户选择回退范围，并在数据模型中把会话位置和文件检查点关联起来；这是一项额外设计，不是该 handler 的隐含能力。[thread_rollback](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/handlers.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/handlers.rs)） · [回退后的有效历史](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/thread_rollout_truncation.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/thread_rollout_truncation.rs)）

## 14. 支持 compact 压缩上下文

上下文窗口有限，而源码读取和测试日志会持续增长。压缩会用更短的表示替换模型当前需要携带的一部分历史，使任务继续推进。它和删除持久化日志、清空会话、生成长期记忆是不同操作。

`compact.rs` 的本地路径会收集用户消息与压缩结果，构建替换历史，并根据策略恢复初始上下文，再更新历史和 token 使用情况；`run_turn()` 中包含自动压缩相关调用。仓库还存在远端压缩实现，所以本地路径只是一个明确的阅读入口，不是所有模型与运行方式的唯一算法。

```text
本地压缩的概念流程：
当前历史 + 压缩请求 → 获得摘要
  → 结合保留的用户信息重建历史
  → 按策略补回初始上下文
  → 更新会话与用量 → 继续任务
```

压缩是有损过程。好摘要需要保留任务目标、后续纠正、已改文件、验证结果与未解决问题；仅写“正在开发筛选功能”不足以保证连续性。**动手观察：** 在压缩前提出一个明确限制，压缩后继续任务，检查限制是否保留，同时确认磁盘日志与当前模型输入不是同一份长度。[本地压缩与历史重建](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/compact.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/compact.rs)） · [运行中的压缩触发](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/turn.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/turn.rs)） · [远端压缩入口](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/compact_remote.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/compact_remote.rs)）

## 15. 给 Agent 注册 MCP 服务器

注册 MCP 不只是把一个 URL 写进工具列表。配置要先转换成有效服务器集合，运行时建立连接并获得能力，再把工具暴露给模型；调用时还要带上服务器身份、工具名、参数和权限上下文。

`core/src/mcp.rs` 的 `McpManager` 负责配置与有效服务器相关的组织；独立的 `codex-mcp` crate 承担运行时能力。实际工具调用可从 `mcp_tool_call.rs` 继续跟踪，观察请求如何到达服务器、结果如何变成 Agent 可处理的内容。把配置发现、连接状态和工具执行拆开，可以避免“配置文件里有名字，所以它一定能用”的误判。

这里还有两个常见边界：工具同名不意味着来自同一服务器；服务器返回的内容也不等于用户授权。调用结果要保留来源，并继续服从权限检查。大量工具还会带来上下文与发现成本，不能无限堆进一个静态提示词。

**动手观察：** 接入一个只读测试 server，记录启动、发现工具、一次调用和断开后的失败；核对界面状态是否反映连接结果，而不是只反映配置存在。[McpManager](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/mcp.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/mcp.rs)） · [MCP 运行时模块](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/codex-mcp/src/lib.rs)（[离线源码](../source-snapshots/codex/codex-rs/codex-mcp/src/lib.rs)） · [MCP 调用路径](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/mcp_tool_call.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/mcp_tool_call.rs)）

## 16. 让 Agent 在后台运行命令

长命令不一定在一次工具等待期间结束。`exec_command` 接受 `yield_time_ms`，等待一段时间后可以交还控制；尚未结束的执行保留会话标识，后续 `write_stdin` 用来读取新输出或发送输入。**让出工具调用与停止进程不是一回事。**

`UnifiedExecHandler` 解析命令、工作目录、环境和权限参数，再交给统一执行管理；`unified_exec/process_manager.rs` 管理进程与输出生命周期。输出的退出码、会话标识和新增内容决定调用者下一步该等待、继续交互还是处理完成。

例如测试需要一分钟，Agent 可以先拿到正在运行的状态，再做独立的只读工作，最后读取测试结果。不能仅因为超出了第一次等待时间就重新启动同一个测试，更不能把“正在运行”显示成“验证成功”。输出限制与截断也意味着空白或短输出并不一定等价于进程结束。

**动手观察：** 在独立目录运行一个先打印、短暂停顿、再退出的测试命令，区分第一次返回的会话 ID 与最终退出码；再检查取消后的资源清理。[命令与 stdin 工具](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/unified_exec.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/unified_exec.rs)） · [进程和输出管理](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/unified_exec/process_manager.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/unified_exec/process_manager.rs)）

## 17. 实现 Sub Agent 机制

子 Agent 需要自己的任务、上下文和状态，还需要父任务能够识别它的结果。`multi_agents` 工具处理器把 spawn、send input、wait、close 等调用转换成 `AgentControl` 操作；子任务从当前有效配置出发，继承环境、目录和权限等状态，并可能叠加角色配置。

读取 `spawn.rs` 时看参数如何变成子线程，读 `wait.rs` 时看怎样按线程 ID 等待状态；再进入 `agent/control.rs` 追到实际生命周期。不要把“收到子线程 ID”当成子任务完成，也不要把等待某个子任务的状态当成主任务已经通过验收。

子 Agent 并行和工具并行也不同。`tools/parallel.rs` 用共享或独占闸门调度单次工具调用；子 Agent 是另一条能继续调用模型和工具的任务。两者都不自动解决业务依赖。共享目录里同时修改同一文件依然可能冲突，角色不同不等于文件系统隔离。

**动手观察：** 给子任务一个独立的只读问题，例如定位测试入口，要求返回路径和依据；主任务随后使用结论并自己验证。再模拟子任务失败，确认父任务能区分失败、等待和成功，而不是只拿一句总结继续。[协作工具总览](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/multi_agents.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/multi_agents.rs)） · [创建子任务](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs)） · [等待子任务](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/multi_agents/wait.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/multi_agents/wait.rs)） · [AgentControl](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/agent/control.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/agent/control.rs)）

## 18. 让 Agent 监听外部事件

持续工作的 Agent 需要在模型调用之外接收新信息：用户补充、子任务结果、环境状态变化等。核心难点是如何把信息注入正在进行的任务，而不是让多个来源同时直接修改历史数组。

`session/turn_input.rs` 明确区分启动和 steer 路径：有的输入可以启动空闲任务，有的输入需要匹配正在运行的轮次，并通过待处理输入机制进入后续步骤。`run_turn()` 的继续条件也会考虑待处理输入。上下文模块还为 Agent 间消息保留单独的类型，帮助区分来源。

这能解释运行时如何接纳新事件，但**不能由此宣称当前 TUI 内置了用户参考教程中的同名 `monitor` 工具或任意 webhook 服务。** 文件监听、CI webhook、定时器等事件源可以由宿主实现，再通过受控输入接口投递；事件鉴权、去重和持续保存是这层集成的职责。

**动手观察：** 在一个受控任务执行过程中提交补充限制，追踪它是被接纳为 steer、排队还是拒绝。设计外部事件时保留事件 ID、来源和时间，只在相关变化出现时触发任务，并把外部文字当作资料处理。[启动、steer 与待处理输入](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/turn_input.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/turn_input.rs)） · [后续输入的循环条件](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/session/turn.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/session/turn.rs)） · [带来源的消息片段](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/context/mod.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/context/mod.rs)）

## 19. 支持图片输入

图片有两条常见入口：用户直接附加图片，或者 Agent 通过工具读取一张本地图片。`protocol/src/user_input.rs` 区分 `Image` 与 `LocalImage`，本地路径会在后续准备中变成模型可接收的内容；不能只把路径写进普通文本就当作已经把像素交给模型。

`ViewImageHandler` 则检查模型是否支持图片输入，解析路径与环境，读取图像并形成图片工具结果。`image_preparation.rs` 集中处理输入图片的准备。沿这几处可以看清“选文件 → 读取与编码 → 进入请求”的客户端链路，但不能据此推断模型内部如何识别图片。

工程上要同时看有效性、体积和用途：格式损坏应清楚报错；超大图片需要遵守预算；缩放可能影响小字识别；读取成功也不代表模型判断必然正确。对于“按钮被遮挡”这样的 UI 问题，图片应与组件源码和实际尺寸信息相互印证。

**动手观察：** 用一张含已知文字的小图分别走附件与 `view_image` 路径，比较消息结构；再测试不存在的路径和无效图片，检查错误是否作为可理解的工具结果返回。[图片输入类型](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/protocol/src/user_input.rs)（[离线源码](../source-snapshots/codex/codex-rs/protocol/src/user_input.rs)） · [查看图片工具](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/tools/handlers/view_image.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/tools/handlers/view_image.rs)） · [图片准备](https://github.com/openai/codex/blob/121f91fd5d9dc66017866ce9bdc49f1e182721df/codex-rs/core/src/image_preparation.rs)（[离线源码](../source-snapshots/codex/codex-rs/core/src/image_preparation.rs)）

## 阅读路线与自测

第一遍读 1、2、5、7 节，建立“输入—模型—工具—执行结果”的主干；第二遍读 4、9、12、13、14 节，理解不同状态怎样保存和重建；最后读 6、10、11、15、16、17、18、19 节，补齐交互、扩展和多任务能力。

| 要回答的问题 | 需要拿出的源码证据 |
| --- | --- |
| 工具执行后为什么会再请求模型？ | 后续处理标记与 run_turn 的继续条件 |
| 为什么清单写 completed 不等于通过测试？ | PlanHandler 的实际职责 |
| 为什么权限允许后仍可能执行失败？ | 审批与环境执行是不同层次 |
| 为什么回退聊天不代表文件恢复？ | thread_rollback 修改的状态范围 |
| 为什么后台命令第一次返回不是结束？ | 会话标识、让出等待与退出码 |
| 为什么另一个子 Agent 不能天然避免冲突？ | 配置继承与共享执行环境 |

以上“动手观察”帮助形成自己的验证方法。本章执行的是文档构建与引用检查，不是对整个 Codex 仓库的编译、性能评测或安全审计。对照阅读：[Claude Code 源码解析](claude-code-source-analysis.md)。两章按相同的 19 个主题组织，方便快速定位差异。
