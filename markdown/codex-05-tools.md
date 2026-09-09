# 05 · 工具调用怎样变成真实动作

> **本节问题：** 从响应项到工具处理器，中间传递了哪些数据？

**承接：** 模型返回了一个完成响应项，运行时现在要识别它的用途。

## 完成项如何成为工具调用

模型输出项先经过 `ToolRouter::build_tool_call`。`Ok(Some(call))` 表示成功识别出工具；`Ok(None)` 是非工具响应；错误分支另行处理。`Option` 表达“有或没有”，`Result` 表达“成功或错误”。

源码：`codex-rs/core/src/stream_events_utils.rs` · L290–307

<!-- source: tool-identify -->

```rust
pub(crate) async fn handle_output_item_done(
    ctx: &mut HandleOutputCtx,
    item: ResponseItem,
    previously_active_item: Option<TurnItem>,
) -> Result<OutputItemResult> {
    let mut output = OutputItemResult::default();
    let plan_mode = ctx.turn_context.mode() == ModeKind::Plan;

    match ToolRouter::build_tool_call(item.clone()) {
        // The model emitted a tool call; log it, persist the item immediately, and queue the tool execution.
        Ok(Some(call)) => {
            ctx.sess
                .input_queue
                .accept_mailbox_delivery_for_current_turn(
                    &ctx.sess.active_turn,
                    &ctx.turn_context.sub_id,
                )
                .await;
```

**为什么看这些行：**

- [L298](#tool-identify-L298)、[L300](#tool-identify-L300)

    **代码作用：** 转换结果为 Some(call) 才进入工具分支；这一步决定后面要准备执行，还是继续处理普通消息。

    **讲解衔接：** 承接第 04 节 handle_output_item_done 的调用，这里进入其内部的工具识别步骤。确认得到 Some(call) 后，下一段才能沿这个 call 追执行安排。


我们已经进入 Ok(Some(call)) 分支，拿到识别出的 call。继续读同一分支的下半段：它怎样记录这次调用，并把工作交给工具运行时。

源码：`codex-rs/core/src/stream_events_utils.rs` · L317–329

<!-- source: tool-schedule -->

```rust
            record_completed_response_item(ctx.sess.as_ref(), ctx.turn_context.as_ref(), &item)
                .await;

            let cancellation_token = ctx.cancellation_token.child_token();
            let tool_future: InFlightFuture<'static> = Box::pin(
                ctx.tool_runtime
                    .clone()
                    .handle_tool_call(call, cancellation_token),
            );

            output.needs_follow_up = true;
            output.tool_future = Some(tool_future);
        }
```

**为什么看这些行：**

- [L317](#tool-schedule-L317)、[L324](#tool-schedule-L324)

    **代码作用：** 先保存模型提出的调用，再把 call 交给工具运行时，得到一个待等待的 future。

    **讲解衔接：** 上一段已经识别出 call，这组行继续读同一分支，完成“识别工具 → 记录调用并安排执行”的交接。随后查看返回值如何把这项工作交回上层。

- [L327](#tool-schedule-L327)、[L328](#tool-schedule-L328)

    **代码作用：** 将继续处理标记和 future 一起返回；上一章的 in_flight 入队代码消费的正是这两个字段。

    **讲解衔接：** 这是工具安排阶段的返回出口，与第 04 节的 in_flight 入队代码配对。交代上层如何接手后，再向工具运行时内部追路由与处理器。

第一段回答“这是什么”，第二段回答“接下来安排什么”。调用先被记录，然后生成携带取消信号的执行 future，同时设置后续处理标记。此刻仍不能把“已安排”当作“已成功”。

## 路由时到底传递了什么

工具名称用于查找处理器，`call_id` 关联请求和结果，`payload` 承载参数。路由把它们与会话、环境和取消信号组装成 `ToolInvocation`，交给注册表分发。

源码：`codex-rs/core/src/tools/router.rs` · L358–381

<!-- source: tool-route -->

```rust
        let ToolCall {
            tool_name,
            call_id,
            payload,
            ..
        } = call;

        // Keep the legacy ToolInvocation.turn field tied to the same request state until handlers migrate.
        let turn = Arc::clone(&step_context.turn);
        let invocation = ToolInvocation {
            session,
            turn,
            step_context,
            cancellation_token,
            tracker,
            call_id,
            tool_name,
            source,
            payload,
        };

        self.registry
            .dispatch_any_with_terminal_outcome(invocation, terminal_outcome_reached)
            .await
```

**为什么看这些行：**

- [L360](#tool-route-L360)、[L373](#tool-route-L373)、[L374](#tool-route-L374)

    **代码作用：** call_id 与 tool_name 从 call 进入 invocation；编号用于关联这一调用，名称用于选择处理能力。

    **讲解衔接：** 从工具运行时继续追到路由时，先核对 call 的身份如何进入 ToolInvocation。这样后面切到具体 handler，仍能认出它处理的是同一次调用。

- [L380](#tool-route-L380)

    **代码作用：** 注册表接收完整 invocation 并分发；这是从工具身份到具体处理器的交接位置。

    **讲解衔接：** 这一行是路由交给注册表的分发出口。本节随后回到路由的调用方补查并发条件，下一章才选 apply_patch 进入具体 handler。

为后续章节明确一个示例：假设列表组件位于 `src/App.tsx`，模型通过当前可用的 `exec_command` 请求读取它。这是教学中约定的文件位置，当前没有配套应用。路由需要保留这次命令的名称、参数和调用编号，执行结果才能再对应回它。

## 回到调用方，检查分发前的并发条件

读完路由后，我们知道 invocation 最终交给注册表。还有一个调用前的问题：多个工具同时到达时，谁先进入路由？工具运行时通过共享读锁或独占写锁控制这个进入时机。

上一段已经定位到“分发做什么”。现在回到它的调用方 tools/parallel.rs，检查“什么时候允许分发”。阅读顺序是在补查调用前的条件，执行顺序则是先取得锁，再调用刚才的路由。

源码：`codex-rs/core/src/tools/parallel.rs` · L155–177

<!-- source: tool-parallel -->

```rust
                let _guard = if supports_parallel {
                    Either::Left(lock.read().await)
                } else {
                    Either::Right(lock.write().await)
                };
                // Admission through the parallel-execution gate marks the end
                // of dispatch waiting and the start of handler execution.
                if let Some(execution_started_at) = execution_started_at {
                    let _ = execution_started_at.set(Instant::now());
                }

                router
                    .dispatch_tool_call_with_terminal_outcome(
                        session,
                        step_context,
                        invocation_cancellation_token,
                        tracker,
                        dispatch_call,
                        source,
                        dispatch_terminal_outcome_reached,
                    )
                    .instrument(dispatch_span.clone())
                    .await
```

**为什么看这些行：**

- [L155](#tool-parallel-L155)、[L156](#tool-parallel-L156)、[L158](#tool-parallel-L158)

    **代码作用：** 并行能力决定取得共享锁还是独占锁；两种工具由这里控制进入执行区的时机。

    **讲解衔接：** 这里是阅读顺序中的回查：上一段先看了路由做什么，现在回到它的调用方看何时允许进入。先获得对应锁，才会执行下面的分发调用。

- [L167](#tool-parallel-L167)

    **代码作用：** 取得锁后才调用路由分发，因此这段是调用分发之前的门控，不是分发完成后的补充操作。

    **讲解衔接：** 这行将并发检查重新接回刚读过的路由。至此工具识别、执行安排与分发条件已串好，下一章沿具体处理器继续查参数和审批。

如果模型尚未取得文件内容，生成补丁仍缺少依据。工具能并行与业务步骤没有依赖，是两件需要分别判断的事。


## 沿同一个 call 检查分发过程

我们先识别 call，再安排执行，最后查看路由与它之前的并发门控。下面按实际执行顺序把这几个位置连起来。

**检查问题：** 识别出 `call` 后，哪些返回字段让上层继续等待工具？进入注册表之前，`call_id` 是否还保留着？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：返回字段是 tool_future 和 needs_follow_up，它们分别提供待等待的执行结果与后续处理标记。**

代码将 `output.tool_future` 设为 `Some(tool_future)`，并将 `output.needs_follow_up` 设为 `true`。前者让上层取得工具 future，后者说明响应链仍需后续处理。

**依据：** [设置后续标记的 L327](#tool-schedule-L327)与[返回 future 的 L328](#tool-schedule-L328)。

**第二问：是，call_id 被保留在 ToolInvocation 中，再随 invocation 交给注册表。**

路由先从 `call` 中取出 `call_id`，构造 `ToolInvocation` 时放回同名字段，因此分发前没有丢掉这一调用的编号。

**依据：** [取出编号 L360](#tool-route-L360)、[放入 invocation 的 L373](#tool-route-L373)、[注册表分发 L380](#tool-route-L380)。

</details>

## 为什么这么设计，好处是什么？

**为什么先识别调用，再通过路由分发？** [工具识别](#source-tool-identify)负责从模型响应中找出调用，[路由](#source-tool-route)负责把工具名、参数、`call_id` 和执行上下文交给处理器。这样，解析响应的代码不必为每种工具直接写一套执行逻辑；具体工具的行为可以留在各自的 handler 中。保留 `call_id` 还能将稍后返回的结果对应到原调用。

**放回案例，好处是什么？** 读取组件、应用补丁、运行测试可以共用调用与结果的交接方式。运行时还在[分发前按并行条件取锁](#source-tool-parallel)，为不同工具控制进入时机。不过锁只落实运行时的并发规则；“先读文件，再根据内容修改”这种业务依赖，仍需要任务按结果安排后续步骤。

## 接下来追什么

我们已经找到执行处理器，但涉及文件和命令时还需要检查参数、审批与执行环境。
