# 专题 · 启动参数与斜杠命令

> **本节问题：** 为什么有些输入不进入模型请求？

**承接：** 先完成主线 01，理解 AppCommand 与 turn/start。

## 同样是键盘输入，接收者可以不同

主线跟的是普通用户任务。斜杠命令先进入 UI 分发；状态分支更新界面，并可能请求刷新额度；压缩命令则提交压缩操作。刷新额度也可能通信，但不等于请求模型生成。比较两个实际分支，比背诵整份命令枚举更容易理解。

源码：`codex-rs/tui/src/chatwidget/slash_dispatch.rs` · L480–494

<!-- source: command-status -->

```rust
            SlashCommand::Status => {
                if self.should_prefetch_rate_limits() {
                    let request_id = self.next_status_refresh_request_id;
                    self.next_status_refresh_request_id =
                        self.next_status_refresh_request_id.wrapping_add(1);
                    self.add_status_output(/*refreshing_rate_limits*/ true, Some(request_id));
                    self.app_event_tx.send(AppEvent::RefreshRateLimits {
                        origin: RateLimitRefreshOrigin::StatusCommand { request_id },
                    });
                } else {
                    self.add_status_output(
                        /*refreshing_rate_limits*/ false, /*request_id*/ None,
                    );
                }
            }
```

**为什么看这些行：**

- [L481](#command-status-L481)、[L485](#command-status-L485)、[L486](#command-status-L486)

    **代码作用：** 需要刷新额度时，先输出带刷新状态的信息，再发出额度刷新事件；不能将它解释为一次模型采样。

    **讲解衔接：** 本专题先用 Status 建立命令分发的第一个样本。这组行定位状态刷新时交给谁处理，为后面与 Compact 的动作去向作对照。

- [L490](#command-status-L490)

    **代码作用：** 另一分支直接显示状态，便于与下面必须提交压缩操作的命令对照。

    **讲解衔接：** 这里补齐 Status 无需刷新的分支，完成状态命令的局部路线。下一段切换到另一种输入 /compact，不是本分支执行完后自动压缩。


状态命令的接收者已经看清楚。现在把输入换成 /compact，对照它在同一分发函数中的分支：关注最终提交的动作是否仍是状态展示。

源码：`codex-rs/tui/src/chatwidget/slash_dispatch.rs` · L270–288

<!-- source: command-compact -->

```rust
            SlashCommand::Compact => {
                if self.blocks_direct_input {
                    self.add_error_message(PARENT_OWNED_INPUT_MESSAGE.to_string());
                    return;
                }
                self.clear_token_usage();
                if !self.bottom_pane.is_task_running() {
                    self.bottom_pane.set_task_running(/*running*/ true);
                }
                self.bottom_pane.ensure_status_indicator();
                self.set_status(
                    compaction::COMPACTION_HEADER.to_string(),
                    Some(compaction::COMPACTION_DETAILS.to_string()),
                    StatusDetailsCapitalization::Preserve,
                    STATUS_DETAILS_DEFAULT_MAX_LINES,
                );
                self.input_queue.user_turn_pending_start = true;
                self.app_event_tx.compact();
            }
```

**为什么看这些行：**

- [L286](#command-compact-L286)、[L287](#command-compact-L287)

    **代码作用：** 标记等待启动并提交 compact 操作；与上一段的状态展示相比，接收动作已经变化，后续要继续去核心追压缩。

    **讲解衔接：** 与上一段 Status 对照，这里展示另一种命令怎样交出实际操作。确认 compact 的提交位置后，要追执行就进入核心压缩路径；要比较普通任务则回第 01 节。

## 如何继续读启动配置

启动参数从 `codex-rs/cli/src/main.rs` 进入，随后选择启动模式。它与运行中输入 `/status` 不在同一个时间点。本课程主线从已有 TUI 会话的普通输入开始；分析启动失败时，应先回 CLI 入口，再看配置如何进入界面的 `config`。

排查时先问：命令只更新本地显示，还是发送了 AppCommand？发送后有没有对应服务端请求？只有沿后续路径找到模型请求，才能判断是否调用模型。


## 对照两个命令的接收动作

同一个斜杠分发函数对 Status 和 Compact 做了不同处理。先按实际动作分类，再决定后面要追 UI 还是核心。

**检查问题：** 需要刷新额度时，Status 发出什么事件？Compact 分支最后提交什么动作？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：Status 发出 AppEvent::RefreshRateLimits 事件。**

需要刷新额度时，先显示刷新中的状态，再将额度刷新事件交给应用处理。

**依据：** [显示刷新状态 L485](#command-status-L485)与[发送 RefreshRateLimits 的 L486](#command-status-L486)。

**第二问：Compact 最后通过 self.app_event_tx.compact() 提交压缩操作。**

此前将 `user_turn_pending_start` 设为 `true`，表明界面正在等待这项工作启动。

**依据：** [等待启动标记 L286](#command-compact-L286)与[提交 compact 的 L287](#command-compact-L287)。

</details>

## 为什么这么设计，好处是什么？

**为什么斜杠命令先走明确的命令分发？** 查看额度与要求模型修改代码是两类意图。[Status 分支](#source-command-status)直接显示状态或发出额度刷新事件，[Compact 分支](#source-command-compact)则提交压缩操作。将已知命令映射到确定动作，可以让程序直接处理这些控制需求。

**放回案例，好处是什么？** 修改筛选过程中查看状态，可以取得运行时掌握的信息，不必再让模型解释用户意图；显式压缩也有专门的启动标记与提交位置。不同入口因此可以采用适合自己的处理方式。阅读和排错时，需要先确认输入落到哪个分支，再沿对应动作追踪，不能仅因用户在同一个输入框中输入就假设后续路径相同。

## 接下来追什么

回到[01 · 普通输入提交](codex-01-input.md)，将本专题的命令分发与普通 user_turn 命令对照。
