# 专题 · 客户端与核心的边界

> **本节问题：** 哪些实现可以复用理解，哪些必须重新核对？

**承接：** 先完成全部 9 节主线。

## 用两段代码确认我们实际读的是哪条路径

客户端构造 `TurnStartParams`，服务端将输入转换为核心请求。这就是主线选取的 TUI → app-server → 核心边界，不能跳过中间层，也不能把它误认为 TUI 直接发送模型请求。

源码：`codex-rs/tui/src/app_server_session.rs` · L1319–1333

<!-- source: boundary-client -->

```rust
        let request_id = self.next_request_id();
        let (sandbox_policy, permissions) =
            turn_permissions_overrides(permissions_override, cwd.as_path())?;
        self.client
            .request_typed(ClientRequest::TurnStart {
                request_id,
                params: TurnStartParams {
                    thread_id: thread_id.to_string(),
                    turn_trigger: None,
                    client_user_message_id: Some(client_user_message_id),
                    input: items,
                    tool_output: None,
                    responsesapi_client_metadata: None,
                    additional_context: None,
                    environments: None,
```

**为什么看这些行：**

- [L1323](#boundary-client-L1323)、[L1329](#boundary-client-L1329)

    **代码作用：** 客户端以 TurnStart 请求传递 input；确认发送接口和字段后，才能去服务端找对应接收位置。

    **讲解衔接：** 这是协议两端对照的发送端，先记住请求类型和 input 字段。下一段转到服务端，不依赖两个文件相邻，而是沿同一份输入的转换继续找核心入口。


客户端请求中的 input 已经发出。下面切到服务端 turn_start_inner：它先把客户端输入转换为核心输入，然后在此处构造 TurnInputRequest。两个片段展示协议两端，而不是同一函数内的连续语句。

源码：`codex-rs/app-server/src/request_processors/turn_processor.rs` · L638–651

<!-- source: boundary-server -->

```rust
        let submission = thread
            .start_or_steer_turn(
                TurnInputRequest::new(input)
                    .with_thread_settings(thread_settings)
                    .on_start(TurnStartOptions {
                        turn_trigger: params.turn_trigger,
                        final_output_json_schema: params.output_schema,
                        service_tier: params.service_tier_for_turn,
                        cyber_access_program: params.cyber_access_program.map(Into::into),
                        ..Default::default()
                    })
                    .with_additional_context(additional_context)
                    .with_responses_metadata(params.responsesapi_client_metadata)
                    .with_trace(self.request_trace_context(&request_id).await),
```

**为什么看这些行：**

- [L639](#boundary-server-L639)、[L640](#boundary-server-L640)

    **代码作用：** 服务端将转换后的输入放入核心 TurnInputRequest，再调用线程方法；到这里才跨到核心任务提交层。

    **讲解衔接：** 这是上一段客户端请求经过接收、校验及类型转换后的核心提交位置。把两端接起来后，再回第 02 节追 RegularTask；比较其他客户端时也先寻找这样的交接点。

## 阅读另一种客户端时，哪些部分要重新验证

先找它的输入入口、协议适配和通知接收位置；只有追到相同核心调用，才复用本课程的核心解释。公开仓库中的路径不自动证明某个桌面版本内部采用完全相同的 UI 和传输实现。

| 边界 | 本课程的证据 | 不应由此推断 |
| --- | --- | --- |
| TUI 到 app-server | TurnStartParams 与 request_typed | 所有客户端共享同一界面代码 |
| app-server 到核心 | start_or_steer_turn | 提交确认就是任务结束 |
| 核心到模型 | client_session.stream | app-server 就是模型 API 服务 |
| 工具到环境 | 具体 handler 与 runtime | 每个工具拥有相同权限路径 |

开始读非交互入口时，可以从 `codex-rs/cli/src/main.rs` 找模式分发，再跟实际调用链。先确认边界，再复用主线的历史、工具与生命周期概念。


## 用 input 字段对照协议两端

客户端和服务端代码分开存放，但本章已用 input 把两端接起来。检查时只使用已经展示的边界，不推测其他客户端。

**检查问题：** 客户端把 items 写入哪里？服务端转换输入后，又构造哪种核心请求并调用哪个方法？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：客户端把 items 写入 TurnStartParams 的 input 字段。**

赋值语句是 `input: items`，这个参数结构包含在 `ClientRequest::TurnStart` 请求中。

**依据：** [客户端字段赋值 L1329](#boundary-client-L1329)。

**第二问：服务端构造 TurnInputRequest，并调用 thread.start_or_steer_turn(...)。**

转换后的核心输入被放进 `TurnInputRequest::new(input)`，再连同设置等交给线程提交方法。

**依据：** [核心请求构造 L640](#boundary-server-L640)与[线程方法调用 L639](#boundary-server-L639)。

</details>

## 为什么这么设计，好处是什么？

**为什么客户端协议与核心请求之间保留转换层？** [客户端构造 TurnStartParams](#source-boundary-client)，服务端再[构造 TurnInputRequest 并调用核心](#source-boundary-server)，让界面如何收集输入与核心如何执行任务分别使用适合自己的类型。服务端承担协议请求进入核心前的适配，核心的任务处理便不必直接依赖输入框的实现。

**放回案例，好处是什么？** 排查筛选需求在哪一步丢失时，可以逐段对照客户端 `input`、服务端转换结果和核心提交调用。阅读另一种客户端时，也能先找它如何到达同一个核心入口，再复用后面的任务循环知识。转换层增加了需要追踪的位置，但把不同模块之间的数据约定显式写在了代码中。

## 接下来追什么

回到[02 · 核心启动](codex-02-turn.md)，从服务端请求继续追到 RegularTask 与 run_turn。
