# 专题 · 流式事件、重试与取消

> **本节问题：** 网络断开、测试失败和取消各自怎样收束？

**承接：** 先完成主线 04、07 和 09。

## 三种失败分别定位

测试进程返回非零退出码，是工具结果；模型流连接失败，进入通信恢复；用户取消，则沿取消信号清理任务。它们不能只用一个“重试”标签解释。

源码：`codex-rs/core/src/responses_retry.rs` · L58–83

<!-- source: retry-connection -->

```rust
    if turn_context
        .config
        .features
        .enabled(Feature::UnboundedConnectionRetries)
        && matches!(request, ResponsesStreamRequest::Sampling)
        && matches!(err.details(), CodexErrorDetails::ConnectionFailed(_))
        && !turn_context.session_source.is_internal()
        && !turn_context.provider.info().is_amazon_bedrock()
    {
        let retry_delay = retry_state.connection_retry_delay;
        warn!(
            turn_id = %turn_context.sub_id,
            error = %err,
            ?retry_delay,
            "stream connection failed; waiting to retry"
        );
        sess.notify_stream_error(turn_context, "Reconnecting... waiting for network", err)
            .await;
        retry_state.connection_retries = retry_state.connection_retries.saturating_add(1);
        codex_client::record_retry!(retry_state.connection_retries, retry_delay, operation);
        tokio::time::sleep(retry_delay).await;
        retry_state.connection_retry_delay = retry_delay
            .saturating_mul(2)
            .min(MAX_CONNECTION_RETRY_DELAY);
        return Ok(());
    }
```

**为什么看这些行：**

- [L62](#retry-connection-L62)、[L63](#retry-connection-L63)

    **代码作用：** 分支同时限制采样请求和连接失败类型；测试断言失败不会仅因为含有“失败”二字就进入这里。

    **讲解衔接：** 从主线的模型响应流切到故障处理后，先用这组条件判断错误是否适用当前恢复路径。符合条件才继续读下面的等待与退避，测试失败则要回工具结果通路分析。

- [L78](#retry-connection-L78)、[L79](#retry-connection-L79)

    **代码作用：** 先等待当前延时，再更新下一次延时；要理解退避，就追这个状态怎样跨尝试变化。

    **讲解衔接：** 这组行解释当前恢复分支怎样准备下一次尝试。下一段是本函数另一个条件分支的传输回退，不是每次等待结束都必然执行的步骤。


前一段是满足特定条件时的连接失败处理；返回后本次错误处理就结束。下面展示同一函数随后检查的另一条分支，它在前面的特定路径没有生效时判断是否切换传输，并非每次退避后必然执行。

源码：`codex-rs/core/src/responses_retry.rs` · L85–100

<!-- source: retry-fallback -->

```rust
    if retry_state.retries >= max_retries
        && client_session.try_switch_fallback_transport(
            &turn_context.session_telemetry,
            turn_context.model_info(),
        )
    {
        sess.send_event(
            turn_context,
            EventMsg::Warning(WarningEvent {
                message: format!("Falling back from WebSockets to HTTPS transport. {err:#}"),
            }),
        )
        .await;
        retry_state.retries = 0;
        return Ok(());
    }
```

**为什么看这些行：**

- [L85](#retry-fallback-L85)、[L86](#retry-fallback-L86)

    **代码作用：** 次数达到上限且能够切换传输时才走回退分支；它与上一段特定连接错误的等待策略有不同条件。

    **讲解衔接：** 前面的特定连接错误路径未生效时，才继续看这里的回退条件。这组行先判断能否切换传输，成功后再看计数如何更新。

- [L98](#retry-fallback-L98)

    **代码作用：** 切换后重置请求重试计数，供后续请求尝试使用；这个变量不记录文件工具是否已经执行。

    **讲解衔接：** 这是回退成功后为后续请求准备状态的位置，至此通信恢复的局部路线结束。下一段转到工具取消，处理对象变了，不沿这个重试计数继续执行工具。

这些分支受功能开关、错误类型、来源和服务商约束。代码里的 `max_retries` 是传入参数，不应在教程中写成所有环境固定重试几次。回退成功后计数清零，也不意味着重做所有已完成的工具动作。

## 取消如何进入工具等待

连接重试处理的是模型通信。现在把场景切换为“工具正在运行时用户取消”，因此要进入工具运行时的等待代码，看取消信号如何与工具完成结果竞争。

源码：`codex-rs/core/src/tools/parallel.rs` · L180–209

<!-- source: cancel-tool -->

```rust
        async move {
            let _tool_call_timing_guard = tool_call_timing_guard;
            tokio::select! {
                res = &mut dispatch_handle => res.map_err(Self::tool_task_join_error)?,
                _ = cancellation_token.cancelled() => {
                    if terminal_outcome_reached.load(Ordering::Acquire) || dispatch_handle.is_finished() {
                        dispatch_handle.await.map_err(Self::tool_task_join_error)?
                    } else {
                        let secs = started.elapsed().as_secs_f32().max(0.1);
                        abort_dispatch_span.record("aborted", true);
                        dispatch_handle.abort();
                        match dispatch_handle.await {
                            Ok(result) => return result,
                            Err(err) if err.is_cancelled() => {}
                            Err(err) => return Err(Self::tool_task_join_error(err)),
                        }
                        let response = Self::aborted_response(&call, secs);
                        notify_tool_aborted(
                            abort_session.as_ref(),
                            abort_turn.as_ref(),
                            call.call_id.as_str(),
                            &call.tool_name,
                            abort_source,
                        )
                        .await;
                        Ok(response)
                    }
                },
            }
        }
```

**为什么看这些行：**

- [L182](#cancel-tool-L182)、[L184](#cancel-tool-L184)、[L185](#cancel-tool-L185)

    **代码作用：** 等待工具完成与等待取消发生竞争；观察到取消时还会确认任务是否已经达到终态。

    **讲解衔接：** 现在从模型通信恢复切到工具运行时的取消等待。这组行先判断完成与取消竞争时应走哪条分支，下面才定位尚未完成时的中止动作。

- [L190](#cancel-tool-L190)

    **代码作用：** 尚未完成的分支中止 dispatch_handle；读此行是为了确定取消实际作用于哪个执行任务。

    **讲解衔接：** 这是取消分支作用到执行任务的实际位置。与上一组的已完成结果返回对照后，再回主线区分工具状态、界面通知及任务结束。

`tokio::select!` 等待多个异步分支。取消时还会检查是否已达到终态或已完成，避免把刚完成的操作随意改写成未执行。阅读写入类工具时，应同时关心“是否有变更发生”和“取消被何时观察到”。

至此，连接恢复与工具取消各自的处理对象已经明确。回到主线 04 的事件接收端时，可以据此区分“连接正在恢复”和“工具执行已经取消”这两种状态。


## 按故障发生的位置选择代码

我们分别读了模型连接错误的恢复和在途工具的取消。检查时先确定发生故障或取消的是哪一个对象。

**检查问题：** 模型连接需要切换传输时，哪两个条件共同决定进入分支？工具等待时收到取消，又为什么先检查是否已完成？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：两个条件是：已达到最大重试次数，并且 try_switch_fallback_transport(...) 返回成功。**

条件用 `&&` 连接，两者同时满足才进入传输回退分支；成功切换后会重置重试计数。

**依据：** [次数条件 L85](#retry-fallback-L85)、[切换条件 L86](#retry-fallback-L86)与[重置计数 L98](#retry-fallback-L98)。

**第二问：先检查是否已完成，是为了保留已经产生的执行结果，避免把完成的工具当作仍需中止的任务。**

如果已达到终态或 handle 已完成，就等待并返回现有结果；否则才进入 `dispatch_handle.abort()` 所在的分支。

**依据：** [完成状态检查 L185](#cancel-tool-L185)、[取得现有结果 L186](#cancel-tool-L186)与[中止调用 L190](#cancel-tool-L190)。

</details>

## 为什么这么设计，好处是什么？

**为什么连接恢复与工具取消要采用不同的处理分支？** [连接重试代码](#source-retry-connection)按错误类型和来源选择等待策略，[传输回退](#source-retry-fallback)另有次数与切换条件；它们处理的是模型通信。[工具取消代码](#source-cancel-tool)处理的是正在执行的工具，还会先检查工具是否已经完成，再决定返回现有结果还是中止等待中的执行任务。

**放回案例，好处是什么？** 模型连接中断时，程序可以尝试恢复通信；测试断言失败则保留为业务反馈，供后续修复使用。用户取消恰好与工具完成相遇时，已有结果也有机会被保留。按发生位置处理，能避免把所有“失败”都理解为同一种重试；尤其涉及文件写入时，还必须结合工具结果确认已经发生的变更。

## 接下来追什么

回到[04 · 响应与显示](codex-04-stream.md)，区分核心处理状态与界面接收的通知。
