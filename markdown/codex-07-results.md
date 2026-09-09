# 07 · 工具结果怎样回到下一次请求

> **本节问题：** 为什么工具读到文件后，模型下一次才有依据修改？

**承接：** 工具已经执行，当前需要把结果接回模型请求循环。

## 先认清这五个交接位置

工具 handler 的返回 → 转成响应项 → 等待执行完成 → 记入会话历史 → 下一次请求重新读历史。少看任何一段，都可能误以为模型自动看见了工具结果。

## 第一步：工具返回值转成会话可记录的响应

从上一章的具体 handler 返回后，工具运行时需要把它变成会话能记录的统一结构。下面展示等待这个返回值以及转换成功、失败结果的代码。

源码：`codex-rs/core/src/tools/parallel.rs` · L74–90

<!-- source: result-envelope -->

```rust
    pub(crate) fn handle_tool_call(
        self,
        call: ToolCall,
        cancellation_token: CancellationToken,
    ) -> impl std::future::Future<Output = Result<ResponseItemEnvelope, CodexErr>> {
        let error_call = call.clone();
        let source = call.direct_source();
        let future = self.handle_tool_call_with_source(call, source, cancellation_token);
        async move {
            match future.await {
                Ok(response) => Ok(response.into_response()),
                Err(FunctionCallError::Fatal(message)) => Err(CodexErr::Fatal(message)),
                Err(other) => Ok(ResponseItemEnvelope::new(
                    Self::failure_response(error_call, other).into(),
                )),
            }
        }
```

**为什么看这些行：**

- [L83](#result-envelope-L83)、[L84](#result-envelope-L84)

    **代码作用：** 等待 handler 的结果，并将成功值转换为响应 envelope；后面记录历史的方法接收这种结构。

    **讲解衔接：** 上一章的具体 handler 已有返回，这里切到工具运行时接收它的位置。先看结果如何变成 envelope，后面的历史写入才有明确的记录对象。

- [L85](#result-envelope-L85)、[L86](#result-envelope-L86)、[L87](#result-envelope-L87)

    **代码作用：** Fatal 向上返回，其他错误变成失败响应；由此可以定位哪些错误作为模型输入继续参与任务。

    **讲解衔接：** 这是同一转换位置的错误分流，补齐成功路径之外的结果去向。只有能形成响应项的路径，才继续接到下面的结果收集与历史记录。

注意错误也有区别：`Fatal` 向上返回核心错误，其他工具错误可以被转换成一个失败响应项。不是所有错误都会让会话立刻结束，也不是所有错误都适合重试。

## 第二步：收集完成结果，而不是只创建 future

第 04 节已把工具 future 加入 `in_flight`。采样处理在返回前调用 `drain_in_flight`；下面把调用点和函数体放在一起。

源码：`codex-rs/core/src/session/turn.rs` · L2840–2846

<!-- source: result-drain-call -->

```rust
    let tool_blocking_timing_guard = if in_flight.is_empty() {
        None
    } else {
        Some(turn_context.turn_timing_state.begin_tool_blocking())
    };
    drain_in_flight(&mut in_flight, sess.clone(), turn_context.clone()).await?;
    drop(tool_blocking_timing_guard);
```

**为什么看这些行：**

- [L2845](#result-drain-call-L2845)

    **代码作用：** 传入 in_flight 并等待 drain 完成；要证明工具结果进入历史，就必须继续展开这个调用。

    **讲解衔接：** 前面解释了单个工具返回的结构，现在回到采样函数看谁等待在途工具。这行提供下一段 drain_in_flight 实现的调用依据。


上一个片段给出 drain_in_flight 的调用点，现在进入它的实现。沿着同一个 in_flight 参数，寻找等待队列结果和写入会话历史这两个动作。

源码：`codex-rs/core/src/session/turn.rs` · L2216–2240

<!-- source: result-drain -->

```rust
#[instrument(level = "trace", skip_all)]
async fn drain_in_flight(
    in_flight: &mut FuturesOrdered<InFlightFuture<'static>>,
    sess: Arc<Session>,
    turn_context: Arc<TurnContext>,
) -> CodexResult<()> {
    while let Some(res) = in_flight.next().await {
        match res {
            Ok(envelope) => {
                mark_thread_memory_mode_polluted_if_external_context(
                    sess.as_ref(),
                    turn_context.as_ref(),
                    &envelope.item,
                )
                .await;
                sess.record_annotated_conversation_items(&turn_context, vec![envelope])
                    .await;
            }
            Err(err) => {
                error_or_panic(format!("in-flight tool future failed during drain: {err}"));
            }
        }
    }
    Ok(())
}
```

**为什么看这些行：**

- [L2222](#result-drain-L2222)、[L2224](#result-drain-L2224)

    **代码作用：** 依次取得队列中的完成结果并拆出 envelope；这是“已安排工具”到“拿到结果”的转换。

    **讲解衔接：** 沿上一段 drain_in_flight 调用进入函数体后，先接住第 04 节放入队列的工作结果。取得 envelope 后，继续向下找它的保存位置。

- [L2231](#result-drain-L2231)

    **代码作用：** 把 envelope 记入会话历史；这一行才回答结果保存到了哪里。

    **讲解衔接：** 这是“工具完成 → 会话历史更新”的交接点。下一段回到 run_turn 判断是否继续，再核对后续请求是否重新读取了这份历史。

`while let Some(res)` 持续等待队列中的结果。拿到 `envelope` 后调用 `record_annotated_conversation_items`。这才是“工具已完成的内容进入历史”的直接证据。

## 第三步：决定继续，并重新取历史

工具结果已经写入历史，控制流回到 run_turn 的采样结果处理处。接下来需要决定是否再次请求：除了本次响应要求继续，还要检查用户有没有新输入。

源码：`codex-rs/core/src/session/turn.rs` · L461–475

<!-- source: result-follow-up -->

```rust
                drain_async_hook_results(&sess, &turn_context, /*before_user_prompt*/ false).await;
                let (has_pending_input, token_status) = async {
                    let has_pending_input =
                        sess.input_queue.has_pending_input(&sess.active_turn).await;
                    let token_status = super::context_window::context_window_token_status(
                        sess.as_ref(),
                        turn_context.as_ref(),
                    )
                    .await;
                    (has_pending_input, token_status)
                }
                .instrument(trace_span!("run_turn.collect_post_sampling_state"))
                .await;
                let needs_follow_up = model_needs_follow_up || has_pending_input;
                let token_limit_reached = token_status.token_limit_reached;
```

**为什么看这些行：**

- [L463](#result-follow-up-L463)、[L464](#result-follow-up-L464)

    **代码作用：** 检查队列是否还有输入，获得 has_pending_input，补足模型响应以外的继续原因。

    **讲解衔接：** 工具结果收集结束后，阅读视角回到 run_turn 的采样结果处理。这两行补上来自用户输入队列的继续理由，下面再与模型返回的后续需求合并。

- [L474](#result-follow-up-L474)

    **代码作用：** 与模型后续需求取逻辑或；正常继续时将回到下面的请求输入准备位置。

    **讲解衔接：** 这行把两类继续理由合成一个判断依据。正常继续路径会回到下一段展示的输入准备位置；后面的结束检查另在第 09 节展开。

当前响应链需要后续处理，或者有新输入，都会影响 `needs_follow_up`。这还不是全部退出逻辑：压缩、取消、stop hooks 等也会参与后面的控制流。正常继续时，再次走回第 03 节的历史读取位置。

源码：`codex-rs/core/src/session/turn.rs` · L420–427

<!-- source: result-next-input -->

```rust
            // Construct the input that we will send to the model.
            let sampling_request_input: Vec<ResponseItem> = async {
                sess.clone_history()
                    .await
                    .for_prompt(&step_context.settings.model_info.input_modalities)
            }
            .instrument(trace_span!("run_turn.prepare_sampling_request_input"))
            .await;
```

**为什么看这些行：**

- [L422](#result-next-input-L422)、[L424](#result-next-input-L424)

    **代码作用：** 再次从更新后的历史取输入；把这里与上面的历史写入调用连起来，才能说明文件结果如何到达下一次请求。

    **讲解衔接：** 这里展示的是继续处理时回到的循环位置，与第 03 节同源。将它和本章 record_annotated_conversation_items 对上，就闭合了“工具输出 → 历史 → 下一次请求”的整条路线。

## 用一组数据走一遍

下面是教学示例，不是实际模型运行日志，字段表达的是关联关系。

| 时刻 | 同一次读取调用的状态 | 模型何时有机会使用 |
| --- | --- | --- |
| 模型提出 | `call_id = read_01`，要求读取 App.tsx | 此时还没有文件结果 |
| 工具完成 | `read_01` 对应文件内容或读取错误 | 结果先交给运行时 |
| 记录历史 | 完成响应写入会话 | 历史已经包含这次结果 |
| 再次请求 | 整理后的历史成为输入 | 下一次模型处理据此决定修改 |

如果模型重复读文件，排查顺序就是：执行是否成功 → 结果是否被记录 → 下一次输入是否包含它 → 上下文整理或压缩是否改变了内容。


## 把工具结果接到下一次请求

现在已经找到结果转换、等待、历史写入和再次读取四个位置。检查题只要求用这些位置证明“工具结果为什么能被后续请求使用”。

**检查问题：** 如果只看到 `tool_future` 入队，还缺哪两个关键动作？下一次请求又在哪里取得已更新的历史？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：还缺“等待工具完成”和“把完成结果写入会话历史”两个动作。**

`in_flight.next().await` 取得完成结果；得到 `envelope` 后，`record_annotated_conversation_items(...)` 才将它记录到历史。

**依据：** [等待结果 L2222](#result-drain-L2222)与[记录历史 L2231](#result-drain-L2231)。

**第二问：下一次请求在 run_turn 的输入准备代码中，通过 clone_history().await.for_prompt(...) 取得更新后的历史。**

工具结果先写入同一份会话历史，继续请求时再重新取这份历史，结果才有机会进入模型输入。

**依据：** [取历史 L422](#result-next-input-L422)与[整理请求输入 L424](#result-next-input-L424)。

</details>

## 为什么这么设计，好处是什么？

**为什么工具结果要先进入历史，再用于下一次请求？** 工具执行发生在运行时一侧，模型后续能使用什么取决于请求输入。[收集并记录完成结果](#source-result-drain)，再[重新读取历史](#source-result-next-input)，就把这两个阶段连成了明确的数据通路。成功输出和可回传的工具错误都可以成为后续判断的依据。

**放回案例，好处是什么？** 读取 `src/App.tsx` 后，文件内容通过这条通路进入后续请求，模型才有依据提出补丁；如果读取失败，后续请求也有机会根据错误调整路径。相同机制还能接收补丁与测试结果，减少为每个工具定制续接流程的需要。结果不断积累会增加上下文体积，因此历史整理与压缩也会影响最终可见的信息。

## 接下来追什么

我们已闭合一次读取；下一节沿同样的结果通路，执行补丁并处理测试输出。
