# 09 · 什么时候结束，用户看到什么

> **本节问题：** 一次响应完成为什么不等于本轮任务完成？

**承接：** 案例已经历读取、修改和测试，现在必须判断是否还需继续。

## 先看继续条件，再看结束分支

第 07 节中 `needs_follow_up` 合并了模型后续需求和待处理输入。为 false 时，代码进入结束候选分支，但先运行 stop hooks；hook 可能要求继续。因此不能把这个布尔值解释成唯一结束条件。

源码：`codex-rs/core/src/session/turn.rs` · L551–559

<!-- source: finish-hooks -->

```rust
                if !needs_follow_up {
                    last_agent_message = sampling_request_last_agent_message;
                    let stop_outcome = run_turn_stop_hooks(
                        &sess,
                        &step_context,
                        stop_hook_active,
                        last_agent_message.clone(),
                    )
                    .await;
```

**为什么看这些行：**

- [L551](#finish-hooks-L551)、[L553](#finish-hooks-L553)

    **代码作用：** 没有后续需求时先调用 stop hooks，返回 stop_outcome；下一段就是消费这个结果的地方。

    **讲解衔接：** 承接第 07 节合并出的 needs_follow_up，这里进入没有后续需求时的结束候选分支。先取得 stop_outcome，下一段再沿它判断本轮能否真的退出。


上一个调用返回 stop_outcome。下面继续在同一个结束分支里读它的消费者，看看 should_block 成立且有补充文本时，程序选择退出还是回到循环。

源码：`codex-rs/core/src/session/turn.rs` · L570–587

<!-- source: finish-continuation -->

```rust
                    if stop_outcome.should_block {
                        if let Some(hook_prompt_message) =
                            build_hook_prompt_message(&stop_outcome.continuation_fragments)
                        {
                            sess.record_response_item_and_emit_turn_item(
                                &turn_context,
                                hook_prompt_message,
                            )
                            .await;
                            sess.input_queue
                                .accept_mailbox_delivery_for_current_turn(
                                    &sess.active_turn,
                                    &turn_context.sub_id,
                                )
                                .await;
                            stop_hook_active = true;
                            continue;
                        } else {
```

**为什么看这些行：**

- [L570](#finish-continuation-L570)、[L574](#finish-continuation-L574)

    **代码作用：** hook 请求继续且提供补充文本时，把这段文本写回历史；继续任务需要有可处理的新信息。

    **讲解衔接：** 上一段已得到 stop_outcome，这里消费它，并为继续处理准备历史输入。完成这一步后，再看控制流是否真的返回循环。

- [L586](#finish-continuation-L586)

    **代码作用：** continue 返回循环，而不是进入完成事件；这条控制流是检查题判断任务是否结束的依据。

    **讲解衔接：** 这行给出继续分支的明确去向，说明当前路径还未走到任务完成。下一段改看生命周期的结束路径，不能把它理解成 continue 后紧接着执行的代码。

正常退出还需要通过后面的分支。回到 `RegularTask`，它再次检查是否有待处理输入；因此运行中到达的新消息不能简单丢弃。

## 结束事件与最后一段文字是两个概念

任务生命周期处理在正常结束路径构造 `TurnCompleteEvent`，带上轮次 ID、最后消息、错误和时间信息，再发送事件。取消则使用另一种结束事件。

源码：`codex-rs/core/src/tasks/mod.rs` · L819–836

<!-- source: finish-event -->

```rust
            let time_to_first_token_ms = turn_context
                .turn_timing_state
                .time_to_first_token_ms()
                .await;
            let error = turn_context.terminal_error.lock().await.clone();
            self.emit_turn_stop_lifecycle(turn_context.extension_data.as_ref())
                .await;
            EventMsg::TurnComplete(TurnCompleteEvent {
                turn_id: turn_context.sub_id.clone(),
                last_agent_message,
                error,
                started_at,
                completed_at,
                duration_ms,
                time_to_first_token_ms,
            })
        };
        self.send_event(turn_context.as_ref(), event).await;
```

**为什么看这些行：**

- [L826](#finish-event-L826)、[L829](#finish-event-L829)

    **代码作用：** 构造轮次完成事件并携带 error，完成状态和成功状态因此可以区分。

    **讲解衔接：** 这里从 run_turn 的结束判断切到上层任务生命周期处理，观察任务收束时生成什么事件。先看事件内容，再核对谁将它发出去。

- [L836](#finish-event-L836)

    **代码作用：** send_event 发出生命周期结果；与前面生成普通助手文字的路径不同，界面据此收束本轮状态。

    **讲解衔接：** 这是本章生命周期通知的发送出口，与第 04 节的界面完成通知处理相呼应。读到这里，用户输入到最终状态显示的主线才闭合。

`error` 字段也在结束事件中：结束不天然代表成功。界面经 app-server 通知路径接收完成通知，第 04 节的 TUI 代码会将它交给专门的完成处理器。

## 把整条任务重新读成一句话

用户输入成为结构化请求；核心启动任务、整理历史并请求模型；工具调用经校验执行，结果被记录并成为后续输入；直到结束条件满足，生命周期发出结束事件，界面显示结果。

| 容易混淆的状态 | 精确含义 |
| --- | --- |
| 客户端请求已受理 | 任务已提交或加入已有轮次 |
| 一次模型响应完成 | 当前流结束，仍可能要处理工具或再次请求 |
| 工具完成 | 一个动作有了结果，未必是整个任务的终点 |
| 本轮任务结束 | 生命周期已收束，可能成功、失败或取消 |

学习到这里，可以在纸上画出这四种状态的先后关系，再沿片段定位每一种状态的代码证据。


## 沿结束候选分支检查是否真的退出

本章先获得 stop_outcome，再查看它可能要求继续的分支，最后才切到生命周期完成事件。下面沿这个顺序判断一次具体情况。

**检查问题：** 如果 `needs_follow_up` 为 false，但 stop hook 要求继续且提供补充文本，程序下一步做什么？最终完成事件从哪里发出？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：程序先把 hook 提供的补充文本写回历史，然后执行 continue，继续当前循环。**

在本章普通任务路径里，既然 `should_block` 成立且能构造补充消息，就暂时不走结束，而是让后续处理有新的输入依据。

**依据：** [写入补充消息 L574](#finish-continuation-L574)与[继续循环 L586](#finish-continuation-L586)。

**第二问：最终完成事件由 core/src/tasks/mod.rs 的任务生命周期处理发出。**

L826 构造 `EventMsg::TurnComplete(TurnCompleteEvent { ... })`，L836 调用 `self.send_event(...)` 发送。构造事件与发出事件是两个可分别定位的动作。

**依据：** [事件构造 L826](#finish-event-L826)与[事件发送 L836](#finish-event-L836)。

</details>

## 为什么这么设计，好处是什么？

**为什么结束前还要检查继续条件，并单独发送结束事件？** 模型的一次响应结束后，可能仍有工具结果、新输入或 hook 提供的补充工作。[stop hook 的继续分支](#source-finish-continuation)把补充内容写入历史再继续循环；任务真正收束后，才由[生命周期代码发送 TurnComplete](#source-finish-event)。这样，“还能否继续推进”与“如何通知结束”分别有明确的负责位置。

**放回案例，好处是什么？** 测试输出到达后，任务仍有机会解释结果、处理补充要求，然后通知界面停止运行状态。完成事件包含轮次 ID、最后消息和错误等信息，界面可以据此处理本轮结果，而无需从一句“已完成”的自然语言推测生命周期状态。结束事件本身仍需结合错误与验证结果理解，不能直接等同于业务成功。

## 接下来追什么

主线已经闭合。按遇到的问题进入专题：长任务看压缩与进程，重启接续看会话记录，外部工具看 MCP。
