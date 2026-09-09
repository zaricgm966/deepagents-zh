# 02 · 一轮任务怎样开始

> **本节问题：** 收到输入后，哪段代码真正启动 run_turn？

**承接：** TUI 已经提交 turn/start，输入仍需要交给核心运行时。

## 服务端先转换输入类型

上一节得到的是客户端协议中的输入项。服务端在 `turn_start_inner` 中加载线程、校验请求，再把普通输入转为核心的 `TurnInput::UserInput`。同样叫输入，跨模块时类型仍可能不同：这里的 `into_core` 就是明确转换位置。

源码：`codex-rs/app-server/src/request_processors/turn_processor.rs` · L599–608

<!-- source: start-convert -->

```rust
        } else {
            TurnInput::UserInput {
                content: params
                    .input
                    .into_iter()
                    .map(V2UserInput::into_core)
                    .collect(),
                client_id: params.client_user_message_id,
            }
        };
```

**为什么看这些行：**

- [L600](#start-convert-L600)、[L604](#start-convert-L604)

    **代码作用：** 构造核心的 UserInput，并逐项调用 into_core；客户端输入在这个转换点获得核心使用的类型。

    **讲解衔接：** 承接上一章发出的 TurnStartParams.input，这里从协议类型转换为核心类型。先认清这一转换，才能理解下一段 TurnInputRequest 为什么使用新的输入值。

- [L605](#start-convert-L605)

    **代码作用：** collect 将转换后的项重新组成列表，供下面 TurnInputRequest 使用。

    **讲解衔接：** 转换后的输入项在此重新收拢为列表，完成类型转换这一小步。接下来追这个列表被放入哪个请求、交给哪个核心方法。


输入现在已经转成核心的 TurnInput，但仍只是一个值。往下看同一函数怎样用 TurnInputRequest 包住它，并调用线程的提交方法。

源码：`codex-rs/app-server/src/request_processors/turn_processor.rs` · L638–667

<!-- source: start-request -->

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
            )
            .await
            .map_err(|err| {
                let error = internal_error(format!("failed to submit turn input: {err}"));
                self.track_error_response(&request_id, &error, /*error_type*/ None);
                error
            })?;
        let (turn_id, started) = match submission {
            TurnInputSubmission::Started { turn_id } => (turn_id, true),
            TurnInputSubmission::Steered { turn_id } => (turn_id, false),
            TurnInputSubmission::NotSubmitted { reason } => {
                let error = internal_error(format!("failed to submit turn input: {reason:?}"));
                self.track_error_response(&request_id, &error, /*error_type*/ None);
                return Err(error);
            }
        };
```

**为什么看这些行：**

- [L639](#start-request-L639)、[L640](#start-request-L640)

    **代码作用：** 输入被放入 TurnInputRequest 并交给 start_or_steer_turn；后续要追这个方法如何送达会话。

    **讲解衔接：** 上一段已得到核心输入，这里把它交给线程的提交方法。接下来进入该方法委托的会话 I/O，追请求如何送达核心分发循环。

- [L660](#start-request-L660)、[L661](#start-request-L661)

    **代码作用：** 两个分支分别保留新启动和补充已有任务的结果；它们解释调用返回后服务端拿到的是什么。

    **讲解衔接：** 这里先展示提交方法返回后的两种正常结果，建立“新启动或补充”的问题。下面再追发送与接收两端，解释这些结果由谁作出、怎样送回来。

理解 `start_or_steer_turn`，可以先抓住本章普通输入的这条判断主线：

**没有正在运行的 Turn → Start；已经有 Turn 在运行 → Steer。**

这里的 **Turn** 指一轮任务的处理过程。**Start** 是启动新的一轮任务；**Steer** 是把新输入补充到正在运行的这一轮，让后续处理结合补充要求继续进行。

代入我们的筛选案例：

- 第一次发送“给待办列表增加已完成筛选，并运行测试”时，如果没有任务正在运行，就走 **Start**，开始处理这条需求。
- 如果 Codex 还在修改代码或运行测试，你又补充“保留显示全部任务的选项”，就走 **Steer**，将这条要求交给当前正在运行的 Turn。

源码在这里采取“先尝试 Steer”的顺序：`steer_input(...)` 成功时返回 `Steered`；如果返回 `NoActiveTurn`，才准备上下文并启动新任务，返回 `Started`。其他未能提交的情况仍会返回 `NotSubmitted`，所以这条判断主线描述的是正常提交路径。

回到上面的 `match`：`Started` 和 `Steered` 都表示输入已被接受，但一个启动了新 Turn，另一个补充了已有 Turn。下面继续追这次提交请求怎样送到核心，以及结果怎样返回。

## 核心如何收到这个请求

`CodexThread` 的提交方法继续委托给会话 I/O。下面同时展示通道发送和接收处：发送 `Op::TurnInput` 时附上一次性答复通道，核心分发循环再调用 `turn_input::handle`，并把处理结果送回来。

源码：`codex-rs/core/src/session/mod.rs` · L903–924

<!-- source: start-channel -->

```rust
    pub(crate) async fn submit_turn_input(
        &self,
        mut request: TurnInputRequest,
        mode: TurnInputMode,
    ) -> CodexResult<TurnInputSubmission> {
        let id = new_submission_id();
        let (reply_tx, reply_rx) = oneshot::channel();
        let trace = request.trace.take();
        self.submit_with_id(Submission {
            id,
            op: Op::TurnInput {
                request: Box::new(request),
                mode,
                reply: reply_tx,
            },
            trace,
            parent_turn_id: None,
            root_turn_id: None,
        })
        .await?;
        reply_rx.await.unwrap_or(Err(CodexErr::InternalAgentDied))
    }
```

**为什么看这些行：**

- [L913](#start-channel-L913)、[L914](#start-channel-L914)、[L916](#start-channel-L916)

    **代码作用：** Op::TurnInput 携带请求和 reply 发送端，把工作与回信地址一起交给核心分发。

    **讲解衔接：** 现在从线程提交方法进入它委托的会话 I/O。这组行是请求的发送端；下一段要找 Op::TurnInput 的接收分支，并核对同一个 request 与 reply。

- [L923](#start-channel-L923)

    **代码作用：** reply_rx.await 等待提交结果；下一段的 reply.send 正好与这里配对。

    **讲解衔接：** 这是发送端等待回信的位置。带着“谁会向 reply 写入什么结果”进入下一段接收分支，便能区分提交确认与任务执行结果。


上一段已经把 Op::TurnInput 送出并等待 reply。下面切换到核心分发的接收分支，寻找同名操作和它的 reply.send；它们是发送端与接收端的配对证据。

源码：`codex-rs/core/src/session/handlers.rs` · L585–593

<!-- source: start-receive -->

```rust
                Op::TurnInput {
                    request,
                    mode,
                    reply,
                } => {
                    let result = turn_input::handle(&sess, *request, mode, sub.id.clone()).await;
                    let _ = reply.send(result);
                    false
                }
```

**为什么看这些行：**

- [L590](#start-receive-L590)

    **代码作用：** 接收方把请求交给 turn_input::handle，真正的启动或补充决策在它后面发生。

    **讲解衔接：** 这里切到通道接收端，与上一段发送的 Op::TurnInput 配对。后面将沿 handle 的普通启动路径追到 RegularTask，而不是把通道收信当作模型调用。

- [L591](#start-receive-L591)

    **代码作用：** 决策结果通过 reply 送回上一段等待者；到此闭合了提交请求与确认结果的通道。

    **讲解衔接：** 这行闭合了上一段 reply_rx.await 的等待，先把提交确认的去向解释完整。随后教学视角回到 handle 内部，继续追实际任务如何被创建。

“等待提交确认”与“等待整个任务做完”是两种等待。否则很容易把 API 返回误读成任务结束。

## 从任务对象进入主循环

上一段的 turn_input::handle 会按提交模式选择处理路径。普通 StartOrSteer 模式进入 start_or_steer：先尝试向活跃任务补充输入，没有活跃任务时再准备上下文、创建 RegularTask。下面摘录这条新启动分支的交接处。

源码：`codex-rs/core/src/session/turn_input.rs` · L293–306

<!-- source: start-spawn -->

```rust
            if let SubmittedTurnInput::UserInput { content, .. } = &input {
                turn_context.session_telemetry.user_prompt(content);
            }
            let mut task_input = merge_additional_context_input(session, additional_context).await;
            if has_explicit_input {
                task_input.push(pending_turn_input(session, input).await);
            }
            session
                .spawn_task(turn_context, task_input, RegularTask::new())
                .await;
            Ok(TurnInputSubmission::Started {
                turn_id: submission_id,
            })
        }
```

**为什么看这些行：**

- [L296](#start-spawn-L296)、[L298](#start-spawn-L298)

    **代码作用：** 将附加上下文和用户输入整理为 task_input；它是新任务开始时接收的数据。

    **讲解衔接：** 经过前面的启动或补充决策，这里只读没有活跃 Turn 的新启动路径。先将整理出的 task_input 记住，下一步核对它怎样交给任务对象。

- [L301](#start-spawn-L301)

    **代码作用：** spawn_task 同时接收上下文、输入和 RegularTask；因此下一步要读 RegularTask 的 run，而不是寻找一次直接的模型调用。

    **讲解衔接：** 这行完成“决定新启动 → 创建 RegularTask”的交接。下一段转到被创建任务的 run 实现，寻找真正接收这些输入的 run_turn 调用。


spawn_task 接收的任务对象是 RegularTask。下面进入这个任务的 run 实现，看 task_input 如何作为 next_input 传入 run_turn；这是从任务创建位置转到被创建任务的执行位置。

源码：`codex-rs/core/src/tasks/regular.rs` · L75–99

<!-- source: start-regular -->

```rust
        let mut next_input = input;
        let mut prewarmed_client_session = prewarmed_client_session;
        let mut mcp_startup_requirements = McpStartupRequirements::default();
        loop {
            let last_agent_message = run_turn(
                Arc::clone(&sess),
                Arc::clone(&ctx),
                next_input,
                &mut mcp_startup_requirements,
                prewarmed_client_session.take(),
                cancellation_token.child_token(),
            )
            .instrument(run_turn_span.clone())
            .await?;
            // Terminal errors are already reported. Let task completion preserve pending
            // input instead of restarting the failed turn for that same input.
            if ctx.terminal_error.lock().await.is_some() {
                return Ok(last_agent_message);
            }
            if !sess.input_queue.has_pending_input(&sess.active_turn).await {
                return Ok(last_agent_message);
            }
            next_input = Vec::new();
        }
    }
```

**先明确这段代码在负责什么：** 它把第一次收到的任务交给 `run_turn`；等 `run_turn` 返回后，再决定当前普通任务能否退出，还是需要继续处理队列里剩下的输入。

**为什么看这些行：**

- [L75](#start-regular-L75)

    **代码作用：** 第一次进入这里时，input 是启动任务时收到的输入。本例包含“给待办列表增加已完成筛选，并运行测试”。next_input = input 把它设为这次要交给 run_turn 的输入。

    **讲解衔接：** 上一段把 task_input 交给 RegularTask，这里在任务执行入口接住它。接下来用 next_input 与 run_turn 的第三个参数对应起来，闭合首次输入的传递。

- [L79](#start-regular-L79)、[L82](#start-regular-L82)、[L88](#start-regular-L88)

    **代码作用：** 调用 run_turn，并将 next_input 传进去。它会在内部组织模型请求、处理工具调用和结果；这里的 await 等待这次 run_turn 调用返回。成功返回的 last_agent_message 是可选的最后一条助手消息，不是整段会话记录；如果返回 Err，? 会直接把错误向上传递。

    **讲解衔接：** 这是本章“输入最终交给谁执行”的核心落点。先确认实际调用，再读它返回后的分支；下一章才进一步进入 run_turn，展开请求上下文准备。

- [L91](#start-regular-L91)、[L92](#start-regular-L92)

    **代码作用：** run_turn 返回后，先看本轮是否已记录终止性错误。若有，就把最后消息交回上层，让任务进入结束处理；即使队列还有输入，也不在这里继续重启失败的处理。Ok(last_agent_message) 只表示这个 Rust 函数正常返回，不能单凭 Ok 判断业务任务成功。

    **讲解衔接：** 阅读视角已从调用 run_turn 转到调用返回之后。这组行先排除必须终止的情况，只有未走此返回分支，才继续检查剩余输入。

- [L94](#start-regular-L94)、[L95](#start-regular-L95)

    **代码作用：** 没有终止性错误时，再问输入队列“还有没有没处理的补充消息”。前面的 ! 表示取反，所以没有待处理输入时进入这个分支，返回最后消息，退出 RegularTask 的这段循环。

    **讲解衔接：** 承接上一组的无终止性错误路径，这里决定 RegularTask 是否可以退出。若队列仍有输入，就沿后面的 next_input 赋值继续读循环。

- [L97](#start-regular-L97)

    **代码作用：** 能执行到这里，说明队列中仍有待处理输入。将 next_input 设为空列表后，loop 会再次调用 run_turn。这只清空下一次调用的初始输入参数，不会清空会话历史，也不会删除队列中的补充消息。

    **讲解衔接：** 这是继续分支回到循环起点的连接处。读完后需要对照下文 run_turn 取待处理输入的代码，才能理解参数为空时任务怎样接续，而不会误以为补充需求被删掉。

### 用“修改筛选时又补充要求”走一遍

假设你先发送了筛选需求，在 Codex 处理时又补充：“保留显示全部任务的选项。”先看没有补充输入的情况，再看返回时队列里仍有补充输入的情况：

| 走到哪里 | 没有待处理的补充输入 | 返回时队列里仍有补充输入 |
| --- | --- | --- |
| 第一次调用 run_turn | next_input 包含最初的筛选需求 | 同样先传入最初的筛选需求 |
| run_turn 内部处理 | 请求模型，按需要读取、修改和测试 | 处理过程中可能已经读取并消费补充输入 |
| 返回后检查队列 | has_pending_input 为 false，退出这个循环 | has_pending_input 为 true，继续往下执行 |
| 是否再次调用 | 不再调用，由上层继续结束处理 | 将 next_input 设为空，再进入 run_turn |

这张表假设没有需要终止的错误。补充输入也可能在第一次 `run_turn` 内部就被处理完，因此 **Steer 并不一定导致外层 loop 再执行一次**。这里再次检查，是为了接住 `run_turn` 返回时仍然留在队列中的输入。

### 为什么传空列表，还能继续处理用户消息

因为“这次函数调用的初始输入”与“会话中的待处理输入队列”是两个不同位置：`next_input` 是前者，`sess.input_queue` 是后者。第一次提交的需求已经交给 `run_turn`，后续无需再次把它作为初始输入传入；新的补充要求则从队列中取得。

这一点可以在 `codex-rs/core/src/session/turn.rs` 中对照：L289 用 `input.is_empty()` 设置是否可以取待处理输入，L338—341 在允许时调用 `sess.input_queue.get_pending_input(...)`。因此传入空列表并不表示“没有任何任务信息”，而是让这次推进从会话队列接续输入。已有历史仍保留在同一个 `sess` 中。

再看调用时传入的 `Arc::clone(&sess)` 和 `Arc::clone(&ctx)`：这里继续使用同一个会话和本轮上下文。因此外层再次调用 `run_turn`，也不等于另建一个新的 Turn。`run_turn` 内部可能包含多次模型请求，外层这段循环则在它返回后检查是否还有遗漏的待处理输入。

## 把提交确认与任务执行对上

本章从服务端输入一直追到 RegularTask，也看到了 reply 的发送与接收两端。现在沿两个返回结果检查自己是否分清了它们。

**检查问题：** `reply_rx.await` 收到的是什么结果？真正将任务输入交给 `run_turn` 的调用在哪里？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：`reply_rx.await` 等到的是“这次输入提交得怎么样”的答复。**

正常收到答复时，其内容是 `CodexResult<TurnInputSubmission>`。具体可能是：

- `Ok(Started { turn_id })`：已接受输入，并启动了新一轮任务；`turn_id` 是新轮次的编号。
- `Ok(Steered { turn_id })`：已接受输入，将它补充到正在运行的轮次；`turn_id` 是已有轮次的编号。
- `Ok(NotSubmitted { reason })`：输入没有提交，`reason` 说明原因。
- `Err(...)`：提交处理发生错误。

例如，第一次发送筛选需求，成功启动后收到的是 `Started { turn_id: … }` 这类结果，含义是“任务已启动”。它不是“筛选功能已经完成”的回答，也不包含测试结论。

**依据：** [发送答复的位置](#start-receive-L590)先执行 `turn_input::handle(...)`，下一行用 `reply.send(result)` 发送它的结果；[等待答复的位置](#start-channel-L923)接收的就是这份结果。如果答复通道关闭而没有收到消息，这一行会将其转成 `InternalAgentDied` 错误。

**第二问：实际调用在 `codex-rs/core/src/tasks/regular.rs` 的 `RegularTask::run` 中，L79 开始调用 `run_turn(...)`，L82 将 `next_input` 作为第三个参数传进去。**

这里的 `next_input` 第一次来自 L75 的 `let mut next_input = input`，因此本例的筛选需求就是通过这个参数交给 `run_turn` 的。L88 的 `.await?` 等待这次调用返回。

**依据：** 直接查看[调用位置 L79](#start-regular-L79)、[输入参数 L82](#start-regular-L82)和[等待返回 L88](#start-regular-L88)。这些行位于任务的执行代码中；第一问的 `reply_rx.await` 位于输入提交代码中。

</details>

## 为什么这么设计，好处是什么？

**为什么把提交确认与任务执行分开？** [reply 通道](#source-start-channel)回答的是输入是否被接受、属于 Start 还是 Steer；[RegularTask 调用 run_turn](#start-regular-L79)才负责实际推进工作。修改和测试可能持续很久，先返回提交结果，可以让调用方确认任务已经接收，再通过后续事件跟踪进展。

**为什么已有 Turn 时接收 Steer？** 运行中的补充要求可以留在当前任务中处理，沿用会话历史和本轮上下文。案例里补充“保留显示全部任务的选项”时，已有读取结果仍可供后续请求使用。[返回前检查待处理输入](#start-regular-L94)则让当前普通任务在退出前再确认队列中是否还有工作。这个设计需要同时维护提交状态与执行状态，因此“提交成功”必须与“功能完成、测试通过”分别表达。

## 接下来追什么

RegularTask 已把输入交给 run_turn；接下来检查历史、说明和工具怎样组成请求。
