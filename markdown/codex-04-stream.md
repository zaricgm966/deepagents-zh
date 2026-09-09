# 04 · 一次请求怎样持续返回结果

> **本节问题：** 文字和工具调用如何从响应流中被分开处理？

**承接：** 请求输入已经准备好，现在要跨过模型通信边界。

## 找到真正开始读取响应的位置

`run_sampling_request` 包含请求准备及错误恢复，它进一步调用 `try_run_sampling_request`。下面的 `client_session.stream(...)` 取得响应流，后面的循环逐个处理事件。

源码：`codex-rs/core/src/session/turn.rs` · L2296–2313

<!-- source: stream-open -->

```rust
    let mut stream = client_session
        .stream(
            prompt,
            &step_context.settings.model_info,
            &step_context.session_telemetry,
            step_context.settings.reasoning_effort().cloned(),
            step_context.settings.reasoning_summary,
            step_context.settings.service_tier.clone(),
            responses_metadata,
            &inference_trace,
        )
        .instrument(trace_span!("stream_request"))
        .or_cancel(&cancellation_token)
        .await??;
    let mut in_flight: FuturesOrdered<InFlightFuture<'static>> = FuturesOrdered::new();
    let mut needs_follow_up = false;
    let mut last_agent_message: Option<String> = None;
    let mut active_item: Option<TurnItem> = None;
```

**为什么看这些行：**

- [L2297](#stream-open-L2297)、[L2308](#stream-open-L2308)

    **代码作用：** stream 取得模型响应流，并将取消信号接到等待过程；这是上一章 Prompt 的消费者。

    **讲解衔接：** 这是上一章请求组装之后的下一站：在采样实现中使用已经准备好的 Prompt，取得响应流。后面将从“发出请求”转为“逐项消费返回事件”。

- [L2310](#stream-open-L2310)、[L2311](#stream-open-L2311)

    **代码作用：** 初始化工具等待队列和后续处理标记；下一段产生工具结果时会更新这两份状态。

    **讲解衔接：** 这组行提前建立后面处理事件时使用的状态。记住 in_flight 与 needs_follow_up，下一段便能辨认完整响应项怎样改变它们。

`await` 表示等待异步结果，`or_cancel` 把取消信号接到等待过程。这里使用的模型参数来自前面建立的 step context，客户端协议请求和模型请求不是同一个请求。

## 完整响应项与文本增量分开处理

流里既有逐步到达的文本，也有完成的响应项。工具参数尚未完整时不能简单地把一半 JSON 当作可执行请求。主线先追完成项的处理，细分增量和取消见专题。

取得响应流后，运行时会逐个处理事件。下面跳到完整输出项分支中的处理位置，观察它如何更新刚才建立的 in_flight 与 needs_follow_up。中间的事件读取与其他类型分支在此省略。

源码：`codex-rs/core/src/session/turn.rs` · L2479–2493

<!-- source: stream-completed-item -->

```rust
                let output_result =
                    match handle_output_item_done(&mut ctx, item, previously_streamed_item)
                        .instrument(handle_responses)
                        .await
                    {
                        Ok(output_result) => output_result,
                        Err(err) => break Err(err),
                    };
                if let Some(tool_future) = output_result.tool_future {
                    in_flight.push_back(tool_future);
                }
                if let Some(agent_message) = output_result.last_agent_message {
                    last_agent_message = Some(agent_message);
                }
                needs_follow_up |= output_result.needs_follow_up;
```

**为什么看这些行：**

- [L2480](#stream-completed-item-L2480)

    **代码作用：** 完成项交给 handle_output_item_done 分类，返回的是后续处理所需的信息。

    **讲解衔接：** 从响应流创建处跳到完整输出项分支后，这行是项处理器的调用点。第 05 节会沿这个调用展开工具识别，本节先看返回值怎样影响当前响应处理。

- [L2487](#stream-completed-item-L2487)、[L2488](#stream-completed-item-L2488)、[L2493](#stream-completed-item-L2493)

    **代码作用：** 有工具 future 就入队，并汇总后续需求；这解释为什么读完一个响应项后还可能需要继续工作。

    **讲解衔接：** 承接同一处理器的返回值，这组行把它接回前面初始化的队列和标记。工具结果何时真正取得留到第 07 节，本节接下来切到界面端看通知显示。

看 `output_result` 的三个出口：`tool_future` 进入等待队列；`last_agent_message` 保存可用的助手消息；`needs_follow_up` 汇总本次请求是否还需后续处理。一个响应项不一定同时具有三个值。

## 用户为什么能边等边看

界面收到的是 app-server 通知。下面可以直接对照：轮次开始、轮次结束、单个响应项完成和助手文本增量分别进入不同处理函数。

前面读的是核心如何处理响应，现在暂时切到用户看到的那一端：TUI 接收 app-server 通知并更新显示。这段展示接收端的分类，不是紧接在上一个函数后的直接调用；事件转换的中间过程在本节未展开。

源码：`codex-rs/tui/src/chatwidget/protocol.rs` · L62–84

<!-- source: stream-ui -->

```rust
            ServerNotification::TurnStarted(notification) => {
                if replay_kind.is_none() {
                    self.clear_misalignment_for_new_turn(&notification.turn.id);
                }
                self.turn_lifecycle.last_turn_id = Some(notification.turn.id);
                self.last_non_retry_error = None;
                if !matches!(replay_kind, Some(ReplayKind::ResumeInitialMessages)) {
                    self.warning_display_state.startup_complete = true;
                    self.on_task_started();
                }
            }
            ServerNotification::TurnCompleted(notification) => {
                self.handle_turn_completed_notification(notification, replay_kind);
            }
            ServerNotification::ItemStarted(notification) => {
                self.handle_item_started_notification(notification, replay_kind);
            }
            ServerNotification::ItemCompleted(notification) => {
                self.handle_item_completed_notification(notification, replay_kind);
            }
            ServerNotification::AgentMessageDelta(notification) => {
                self.on_agent_message_delta(notification.delta);
            }
```

**为什么看这些行：**

- [L82](#stream-ui-L82)、[L83](#stream-ui-L83)

    **代码作用：** 文字增量进入 on_agent_message_delta，解释用户看到的新文字由哪类通知触发。

    **讲解衔接：** 这里从核心处理切换到 TUI 通知接收端，中间通知转换未展开。这两行回答用户为何能逐步看到文字，补齐本章的界面视角。

- [L73](#stream-ui-L73)、[L76](#stream-ui-L76)、[L79](#stream-ui-L79)

    **代码作用：** 轮次完成与单个 item 的开始、完成使用不同分支；对照这些分支才能区分“文字出现”和“任务结束”。

    **讲解衔接：** 与文字增量分支对照，这组行标出其他状态通知的接收位置。分清显示与执行状态后，下一章再回到核心的完成项处理器追工具调用。

案例中，模型可能先解释“我先检查列表组件”，再提出读取命令。解释文字出现在屏幕上不证明读取已经完成；工具执行有自己的开始、结果和状态。


## 分别检查工具处理与界面显示

本章读了两个不同视角：核心收集完成项的处理结果，TUI 接收通知更新显示。下面分别找出这两端对应的分支。

**检查问题：** 完成项处理器返回 `tool_future` 时，核心把它放到哪里？用户看到新文字时，TUI 走的是哪个通知分支？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：核心把 tool_future 放入 in_flight 队列。**

使用的语句是 `in_flight.push_back(tool_future)`，为后续等待工具结果保留这个 future。

**依据：** [L2487](#stream-completed-item-L2487)检查是否存在 `tool_future`，[L2488](#stream-completed-item-L2488)执行入队。

**第二问：新文字走 ServerNotification::AgentMessageDelta 分支。**

这个分支调用 `self.on_agent_message_delta(notification.delta)` 更新界面文字；本题所问的是文字增量，不是轮次完成通知。

**依据：** [通知分支 L82](#stream-ui-L82)与[文字更新调用 L83](#stream-ui-L83)。

</details>

## 为什么这么设计，好处是什么？

**为什么把文字增量、完成项和轮次状态分开处理？** [文字增量通知](#stream-ui-L82)可以让界面立即更新；[完整输出项处理](#source-stream-completed-item)则提取工具 future、最后消息及后续处理标记。两者对数据完整性的要求不同：显示一小段文字有用，而执行工具需要完整、可解析的调用参数。

**放回案例，好处是什么？** 用户可以先看到“我先检查列表组件”，随后再看到读取动作及结果。界面不必等整轮任务结束才显示内容，核心也能单独管理尚待完成的工具工作。代价是要维护多个层次的状态：一段文字显示完、一个响应项完成和整个 Turn 结束，需要各自的通知与判断。

## 接下来追什么

完成项被交给 handle_output_item_done；下一节看它如何识别工具调用并找到处理器。
