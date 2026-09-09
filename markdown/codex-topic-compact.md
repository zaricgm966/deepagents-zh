# 专题 · 上下文压缩

> **本节问题：** 日志越来越长时，后续请求怎样继续？

**承接：** 先完成主线 03 和 07，理解请求从历史取输入。

## 压缩改变的是后续请求使用的历史

长日志持续占用上下文时，需要用较短信息接替部分历史。下面展示本地压缩路径的重建入口，它接收初始上下文、用户消息和摘要，再按预算选择内容。

源码：`codex-rs/core/src/compact.rs` · L683–715

<!-- source: compact-select -->

```rust
fn build_compacted_history_with_limit(
    mut history: Vec<ResponseItemEnvelope>,
    user_messages: &[CompactedUserMessage],
    summary_text: &str,
    max_tokens: usize,
) -> Vec<ResponseItemEnvelope> {
    let mut selected_messages: Vec<CompactedUserMessage> = Vec::new();
    if max_tokens > 0 {
        let mut remaining = max_tokens;
        for message in user_messages.iter().rev() {
            if remaining == 0 {
                break;
            }
            let tokens = approx_token_count(&message.message);
            if tokens <= remaining {
                selected_messages.push(message.clone());
                remaining = remaining.saturating_sub(tokens);
            } else {
                let truncated =
                    truncate_text(&message.message, TruncationPolicy::Tokens(remaining));
                selected_messages.push(CompactedUserMessage {
                    id: message.id.clone(),
                    message: truncated,
                    internal_chat_message_metadata_passthrough: message
                        .internal_chat_message_metadata_passthrough
                        .clone(),
                    harness_metadata: message.harness_metadata.clone(),
                });
                break;
            }
        }
        selected_messages.reverse();
    }
```

**为什么看这些行：**

- [L693](#compact-select-L693)、[L697](#compact-select-L697)、[L702](#compact-select-L702)

    **代码作用：** 预算决定何时停止、整条保留或截断文本；这些分支解释压缩后哪些输入可能减少。

    **讲解衔接：** 承接主线中历史持续增长的问题，这里进入压缩后的用户消息选择步骤。先看哪些消息能进入 selected_messages，再看如何恢复它们的顺序。

- [L714](#compact-select-L714)

    **代码作用：** 选取后恢复时间顺序，再交给后续重建；因此下面应追新历史如何替换旧历史。

    **讲解衔接：** 这行结束消息选择阶段，为重建历史准备有序材料。下一段回到调用此重建函数的位置，追 new_history 怎样真正替换当前历史。

先逆序选择，再反转回来：优先保留较近内容与恢复原有阅读顺序是两步。预算不足时可以截断一条消息，所以压缩不能被当作无损备份。

上一段解释了重建时如何挑选用户消息。现在回到调用重建函数的位置，跟随 new_history 看它何时替换当前会话历史。只有完成替换，主线中的下一次请求才会使用它。

源码：`codex-rs/core/src/compact.rs` · L367–400

<!-- source: compact-replace -->

```rust
    let mut new_history = build_compacted_history(Vec::new(), &user_messages, &summary_text);
    if let Some(summary_item) = new_history.last_mut() {
        // This replacement history skips `record_conversation_items`; only the appended summary
        // belongs to this compaction turn.
        summary_item.set_turn_id_if_missing(&turn_context.sub_id);
    }
    let (window_number, window_ids) = sess.advance_auto_compact_window().await;

    let (initial_context, world_state_baseline) =
        build_compaction_initial_context(sess.as_ref(), &initial_context_injection).await;
    if !initial_context.is_empty() {
        new_history =
            insert_initial_context_before_last_real_user_or_summary(new_history, initial_context);
    }
    let reference_context_item = match initial_context_injection {
        InitialContextInjection::DoNotInject => None,
        InitialContextInjection::BeforeLastUserMessage { .. } => {
            Some(turn_context.to_turn_context_item())
        }
    };
    sess.replace_compacted_history(
        new_history,
        reference_context_item,
        world_state_baseline,
        CompactedHistoryMetadata {
            message: summary_text,
            window_number,
            window_ids,
            compaction_response_id: Some(compaction_response_id),
            compaction_model_hash: turn_context.model_info().comp_hash.clone(),
        },
    )
    .await;
    sess.recompute_token_usage(&turn_context).await;
```

**为什么看这些行：**

- [L367](#compact-replace-L367)、[L387](#compact-replace-L387)

    **代码作用：** 先生成 new_history，再调用 replace_compacted_history；前者只是构造结果，后者才改变后续请求使用的历史。

    **讲解衔接：** 上一段展开了重建函数内的选择逻辑，这里回到调用方，区分构造 new_history 与让它生效。完成替换后，再到第 07 节的历史读取处观察后续请求输入如何改变。

## 回接主线

下一次请求仍通过 `clone_history().for_prompt(...)` 取输入，但历史已发生替换。例如原任务中“只显示已完成任务”的要求在长日志之后被忽略，应比较压缩前后的历史，检查这条需求是否仍被保留。

这里展示的是本地压缩路径；`codex-rs/core/src/compact_remote.rs` 有另一条远端路径，不能把本地的所有实现细节套用过去。长期记忆也属于不同流程，另见记忆专题。


## 找出新历史真正生效的位置

挑选用户消息会生成重建材料，但后续模型请求使用的会话历史要经过替换才改变。下面把构造与生效位置分开。

**检查问题：** 预算不足时，选择代码会怎样处理消息？哪一个调用让 new_history 成为后续请求的历史？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：如果还有预算但放不下整条消息，就截断这条消息后停止选择；如果预算已经为零，就直接停止。**

前一种情况调用 `truncate_text(..., TruncationPolicy::Tokens(remaining))`，把截断结果加入列表后 `break`；后一种情况不再截取下一条消息。

**依据：** [零预算停止 L693—694](#compact-select-L693)、[按剩余预算截断 L701—702](#compact-select-L701)与[随后停止 L711](#compact-select-L711)。

**第二问：让新历史生效的调用是 sess.replace_compacted_history(...)。**

`build_compacted_history(...)` 只构造 `new_history`；将它交给 `replace_compacted_history` 后，会话中供后续请求使用的历史才被替换。

**依据：** [构造新历史 L367](#compact-replace-L367)与[替换调用 L387](#compact-replace-L387)。

</details>

## 为什么这么设计，好处是什么？

**为什么按预算选择消息，再替换后续请求使用的历史？** 上下文容量有限，长任务不能无限追加原始记录。[选择代码](#source-compact-select)从较近的用户消息开始，按剩余预算保留或截断内容，再恢复原有顺序；[替换代码](#source-compact-replace)让构造好的新历史成为后续请求的输入来源。这让历史缩减有明确的生效位置。

**放回案例，好处是什么？** 多轮修改和测试产生大量日志后，任务仍能用较短历史继续推进，较新的用户要求也有优先被选择的机会。代价是信息可能被摘要化、截断或未被保留。若后来遗漏“只显示已完成任务”的要求，就应检查压缩后的实际内容；“能够继续请求”与“所有细节完整保留”是需要分别验证的两件事。

## 接下来追什么

回到[07 · 结果回传](codex-07-results.md)，从再次读取历史的位置观察压缩替换的影响。
