# 专题 · 会话记录、恢复与回退

> **本节问题：** 关闭程序后，什么信息能被接续使用？

**承接：** 先完成主线 09。

## 接收记录与写到磁盘之间还有写入器

`record_canonical_items` 把记录送给后台写入器。只有队列发送成功不能推断数据已经满足所有持久化保证。

源码：`codex-rs/rollout/src/recorder.rs` · L970–982

<!-- source: history-queue -->

```rust
    pub async fn record_canonical_items(&self, items: &[RolloutItem]) -> std::io::Result<()> {
        if items.is_empty() {
            return Ok(());
        }
        self.tx
            .send(RolloutCmd::AddItems(items.to_vec()))
            .await
            .map_err(|e| {
                self.writer_task.terminal_failure().unwrap_or_else(|| {
                    IoError::other(format!("failed to queue rollout items: {e}"))
                })
            })
    }
```

**为什么看这些行：**

- [L975](#history-queue-L975)、[L976](#history-queue-L976)

    **代码作用：** 记录被送入写入器队列；这段 await 等的是发送操作，下面需要另外寻找写入完成的确认。

    **讲解衔接：** 本专题先从记录提交方开始，定位“交给写入器”的位置。下面另外读 Flush，寻找写入器完成处理后的确认，避免把这次发送等待当作刷新完成。


AddItems 已经发送到写入队列。若调用者需要等待写入器完成刷新，就要看另一项操作 Flush；下面把它携带的 ack 与随后等待的 rx 对上。

源码：`codex-rs/rollout/src/recorder.rs` · L1005–1024

<!-- source: history-flush -->

```rust
    /// Flush all queued writes and wait until they are committed by the writer task.
    ///
    /// If the first writer attempt fails, the writer drops and reopens the file handle before
    /// retrying. This returns an error only when that retry also fails or the writer task is gone.
    pub async fn flush(&self) -> std::io::Result<()> {
        let (tx, rx) = oneshot::channel();
        self.tx
            .send(RolloutCmd::Flush { ack: tx })
            .await
            .map_err(|e| {
                self.writer_task.terminal_failure().unwrap_or_else(|| {
                    IoError::other(format!("failed to queue rollout flush: {e}"))
                })
            })?;
        rx.await.map_err(|e| {
            self.writer_task
                .terminal_failure()
                .unwrap_or_else(|| IoError::other(format!("failed waiting for rollout flush: {e}")))
        })?
    }
```

**为什么看这些行：**

- [L1012](#history-flush-L1012)、[L1019](#history-flush-L1019)

    **代码作用：** Flush 命令带着 ack 通道，调用方再等 rx 的答复；这两端共同解释“已要求刷新”如何变为“收到刷新确认”。

    **讲解衔接：** 这是与 AddItems 对照的另一项写入器操作，不是每次 AddItems 后都会自动调用的下一行。发送端与确认端配对后，再看回退为什么既重建内存历史又提交持久记录。

`oneshot` 是一次性答复通道。它把“发送 flush 指令”和“等待完成确认”区分开。这里的确认仍不能代替对底层文件系统持久性语义的分析。

## 恢复与回退读的是有效历史

resume 需要加载记录并重建上下文，不能把 UI 的显示文本直接当成请求历史。rollback 也要从持久记录和回退标记重建保留的部分。

源码：`codex-rs/core/src/session/handlers.rs` · L329–349

<!-- source: history-rollback -->

```rust
    let rollback_event = ThreadRolledBackEvent { num_turns };
    let rollback_msg = EventMsg::ThreadRolledBack(rollback_event.clone());
    let replay_items = stored_history
        .items
        .into_iter()
        .chain(std::iter::once(RolloutItem::EventMsg(rollback_msg.clone())))
        .collect::<Vec<_>>();
    sess.apply_rollout_reconstruction(turn_context.as_ref(), replay_items.as_slice())
        .await;
    sess.services
        .thread_extension_data
        .remove::<NodeReplReviewEvidence>();
    sess.guardian_review_session.invalidate().await;
    sess.services
        .agent_control
        .rollout_budget()
        .rearm_reminder(sess.thread_id());
    sess.recompute_token_usage(turn_context.as_ref()).await;

    sess.persist_rollout_items(&[RolloutItem::EventMsg(rollback_msg.clone())])
        .await;
```

**为什么看这些行：**

- [L334](#history-rollback-L334)、[L336](#history-rollback-L336)

    **代码作用：** 把回退标记加入已有记录，再执行历史重建；输入记录变了，保留的对话也随之改变。

    **讲解衔接：** 了解记录与刷新后，现在切到回退处理的使用场景。这组行先解释当前有效历史怎样改变，下一组再补上供以后恢复使用的记录。

- [L348](#history-rollback-L348)

    **代码作用：** 单独保存回退标记，使后续恢复能够看到这次回退；重建内存与持久化标记是两步。

    **讲解衔接：** 这是回退流程中的持久记录提交处，和上面的内存历史重建配成两步。读完后回第 03 节，核对恢复或回退后的有效历史如何进入后续请求。

这段关注的是会话历史。它不能证明外部 API 动作被撤销，也不能证明工作区文件自动回到某个 Git 提交。阅读回退功能时，要分别跟踪对话状态与文件状态。

案例完成以后再打开会话，应该能重建需求和有效结果；磁盘上的源码是否仍与当时相同，则需要重新检查工作区。


## 区分送入队列与收到写入确认

AddItems、Flush 和回退重建分别改变不同阶段的状态。先把前两个等待的对象区分清楚，再看为什么回退还要保存标记。

**检查问题：** AddItems 的 await 等待什么？Flush 为什么还要等待 rx？回退后哪一步保存了回退标记？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：AddItems 后的 await 等待的是“把记录命令发送到写入器队列”这个操作完成。**

它不等待写入器对这些记录逐条写完磁盘，也没有在这里接收写入确认。

**依据：** [发送 AddItems 的 L975](#history-queue-L975)与[等待发送的 L976](#history-queue-L976)。

**第二问：Flush 等待 rx，是为了接收写入器处理完刷新请求后的确认或错误。**

把 `Flush { ack: tx }` 送入队列只完成了请求提交；写入器通过 `tx` 回信，调用方再通过 `rx.await` 得知结果。

**依据：** [携带答复通道 L1012](#history-flush-L1012)与[等待答复 L1019](#history-flush-L1019)。

**第三问：回退标记由 L348 的 sess.persist_rollout_items(...) 保存。**

代码先重建有效历史，再将 `rollback_msg` 包装成 `RolloutItem::EventMsg` 交给持久化方法。

**依据：** [历史重建 L336](#history-rollback-L336)与[保存回退标记 L348](#history-rollback-L348)。

</details>

## 为什么这么设计，好处是什么？

**为什么普通记录通过队列写入，Flush 又要单独确认？** [AddItems](#source-history-queue)把记录交给后台写入器，使记录提交与后续文件写入分开；当调用处需要明确等待刷新结果时，[Flush 携带的 ack 通道](#source-history-flush)提供确认。程序由此可以区分“已经交给写入器”与“写入器已答复刷新请求”。

**为什么回退还要保存标记？** [回退处理](#source-history-rollback)既重建当前有效历史，又记录回退事件，让以后恢复会话时有依据重建同样的取舍。案例里重新打开筛选任务时，后续请求因此可以沿有效对话接续。会话记录描述的是交互历史；工作区文件属于另一种状态，恢复或回退对话后仍需核对实际文件。

## 接下来追什么

回到[03 · 历史成为输入](codex-03-context.md)，确认恢复后的有效历史怎样被后续请求读取。
