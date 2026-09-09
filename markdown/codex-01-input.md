# 01 · 点击发送后，任务去了哪里

> **本节问题：** 用户的文字怎样跨过界面与核心之间的边界？

**承接：** 我们只有一条用户需求，还没有任何模型输出。

## 先把文字变成数据

假设你正在开发一个待办事项应用，列表目前会显示所有任务。你希望增加一个筛选选项，让列表只显示已完成的任务，于是在项目目录中打开 Codex，输入“给待办列表增加已完成筛选，并运行测试”，然后按下发送。这就是[课程总览](codex-source-analysis.md)中贯穿各章的假设案例。

本节从按下发送开始，先追踪文字怎样离开输入框、提交给核心运行时。界面中的字符串必须先成为程序能传递的数据。下面的 `items` 是输入项列表，普通文字放入 `UserInput::Text`。`UserInput` 用枚举区分输入种类，本节只沿 Text 这一种输入继续。

源码：`codex-rs/tui/src/chatwidget/input_submission.rs` · L207–212

<!-- source: input-text -->

```rust
        if !text.is_empty() {
            items.push(UserInput::Text {
                text: text.clone(),
                text_elements: app_server_text_elements(&text_elements),
            });
        }
```

**为什么看这些行：**

- [L207](#input-text-L207)

    **代码作用：** 非空判断决定本例的文字是否进入列表；这是用户输入与下面数据构造之间的条件。

    **讲解衔接：** 这是整条提交链的起点：先确认筛选需求能进入输入列表，下面才有必要看 Text 的构造。

- [L208](#input-text-L208)、[L209](#input-text-L209)

    **代码作用：** 构造 Text 变体并加入 items，text 字段保存需求原文；后面要追的正是这个 items。

    **讲解衔接：** 这一步把界面文字交接为 items。读完后带着这个变量进入下一段 user_turn，确认同一份需求怎样成为任务命令。

把刚才的需求代入这段代码：`text` 保存“给待办列表增加已完成筛选，并运行测试”这句话。因为文字不为空，程序构造一个 `UserInput::Text`，再通过 `items.push(...)` 把它加入输入项列表。`text_elements` 用来记录输入框中特殊元素的位置；本例只输入普通文字，先关注 `text` 如何被放进 `items` 即可。

执行到这里，这句话已经被包装成一个输入项，但这段代码还没有把它发送出去。接下来要看：谁接过 `items`，将它作为一次任务提交。

## 把输入列表包装成任务命令

上一段得到的是 `items`，它只回答“用户输入了什么”。提交任务还需要知道项目目录以及本次运行设置，所以代码将它们一起交给 `AppCommand::user_turn`，得到名为 `op` 的命令。先看 `items` 从哪里传入、`op` 在哪里接收返回值，再看工作目录为何随任务一起传递。

源码：`codex-rs/tui/src/chatwidget/input_submission.rs` · L370–383

<!-- source: input-command -->

```rust
        let op = AppCommand::user_turn(
            client_user_message_id,
            items,
            self.config.cwd.to_path_buf(),
            AskForApproval::from(self.config.permissions.approval_policy.value()),
            active_permission_profile,
            effective_mode.model().to_string(),
            effective_mode.reasoning_effort(),
            /*summary*/ None,
            service_tier,
            /*final_output_json_schema*/ None,
            collaboration_mode,
            personality,
        );
```

**为什么看这些行：**

- [L370](#input-command-L370)、[L372](#input-command-L372)

    **代码作用：** items 作为参数进入 user_turn，返回值被保存为 op；这一行解释了输入列表怎样变成可提交的任务命令。

    **讲解衔接：** 承接上一段的 items，这里完成“输入列表 → 任务命令 op”的转换。下一段要寻找 op 的实际使用处，确认它何时被提交。

- [L373](#input-command-L373)

    **代码作用：** 命令同时携带项目工作目录，让后续处理知道这次需求针对哪个目录；先认清这个参数的用途，再把注意力放回 op。

    **讲解衔接：** 这行补齐命令的项目环境，解释为什么不能只传一句需求。随后继续追 op，同时在后面的 turn_start 参数中核对 cwd 是否跟着传递。


到这里我们有了 `op`，但构造一个命令还不会把它交给接收方。继续留在同一个 `input_submission.rs`，寻找谁使用刚才的 `op`。

## 调用 submit_op，把命令交给应用处理

下面仍在同一个输入提交函数中。我们要找的是构造 op 之后的调用语句，先确认 op 被交给谁，再进入接收它的方法。

源码：`codex-rs/tui/src/chatwidget/input_submission.rs` · L409–415

<!-- source: input-submit-call -->

```rust
        if !self.submit_op(op.clone()) {
            return (false, None);
        }
        self.dismiss_backend_banner_for_new_turn();
        if render_in_history {
            self.input_queue.user_turn_pending_start = true;
        }
```

**为什么看这些行：**

- [L409](#input-submit-call-L409)

    **代码作用：** 把刚构造的 op 传给 submit_op；有了这个调用点，才有理由进入下一段函数实现。

    **讲解衔接：** 上一段只得到 op，这里首次给出交出它的调用点。下一段进入 submit_op 的实现，是沿此处的调用向下读。

- [L410](#input-submit-call-L410)、[L414](#input-submit-call-L414)

    **代码作用：** 提交返回 false 时立即报告失败；后面的 pending_start 标记记录等待任务启动的 UI 状态。它说明提交阶段怎样影响界面。

    **讲解衔接：** 这组行补查提交调用对界面的影响：失败时报告错误，通过后等待启动。确认这一分界后，再向下追命令的发送去向。


现在有了 `self.submit_op(op.clone())` 这个实际调用，才进入 `chatwidget.rs` 中的 `submit_op`。下面摘录它完成前置检查后的发送分支；前置拒绝条件保留在完整文件中。两条分支选择不同的应用处理入口，都传递同一个任务命令。

源码：`codex-rs/tui/src/chatwidget.rs` · L1804–1817

<!-- source: input-submit -->

```rust
        match &self.codex_op_target {
            CodexOpTarget::Direct(codex_op_tx) => {
                crate::session_log::log_outbound_op(&op);
                if let Err(e) = codex_op_tx.send(op) {
                    tracing::error!("failed to submit op: {e}");
                    return false;
                }
            }
            CodexOpTarget::AppEvent => {
                self.app_event_tx.send(AppEvent::CodexOp(op));
            }
        }
        true
    }
```

**为什么看这些行：**

- [L1807](#input-submit-L1807)

    **代码作用：** Direct 分支将 op 发送到对应通道；接收方将继续处理这个命令。

    **讲解衔接：** 现在已进入上一段调用的 submit_op。这行展示 Direct 模式的发送出口；后面的线程路由是接收并处理命令的位置，不是本行之后的直接函数调用。

- [L1813](#input-submit-L1813)、[L1816](#input-submit-L1816)

    **代码作用：** AppEvent 分支把同一个 op 包进 CodexOp 事件；true 表示这段提交过程通过。两条分支是可选去向，不是先后执行的两步。

    **讲解衔接：** 这里补齐另一种发送出口，并说明 submit_op 何时返回 true。两种出口读完后，教学流程转到应用路由，追同一个 op 被接收后的用途。

命令已经交给应用处理，接下来追接收后的用途。中间的应用事件分发在本节不逐个展开；我们跳到 `app/thread_routing.rs` 处理 `AppCommand::UserTurn` 的普通启动分支。这不是 `submit_op` 内部紧接着执行的下一行，而是应用接收并路由命令后的处理位置。

## 应用从命令取出输入，准备启动任务

这个分支将命令中的输入和设置交给 `app_server.turn_start(...)`。看下面的 `items.to_vec()`：它把输入列表继续传给客户端方法，所以我们接下来要进入 `turn_start` 看这个参数最后写到哪里。

源码：`codex-rs/tui/src/app/thread_routing.rs` · L798–816

<!-- source: input-route -->

```rust
                    let response = app_server
                        .turn_start(
                            thread_id,
                            client_user_message_id.clone(),
                            items.to_vec(),
                            cwd.clone(),
                            turn_approval_policy,
                            turn_approvals_reviewer,
                            permissions_override,
                            config.permissions.user_visible_workspace_roots(),
                            model.to_string(),
                            effort.clone(),
                            *summary,
                            service_tier.clone(),
                            collaboration_mode.clone(),
                            *personality,
                            final_output_json_schema.clone(),
                        )
                        .await?;
```

**为什么看这些行：**

- [L799](#input-route-L799)、[L802](#input-route-L802)

    **代码作用：** 应用路由调用 turn_start，并把从命令中取得的 items 传进去；这连接了应用内命令与下一段的客户端方法。

    **讲解衔接：** 这是从发送端切到应用处理端：中间的事件分发已省略。此处取出 items 并调用 turn_start，为下一段进入该客户端方法提供实际调用点。

- [L803](#input-route-L803)

    **代码作用：** cwd 也随输入继续传递，表明前面打包的项目环境没有在这次交接中丢掉。

    **讲解衔接：** 这一行与前面 user_turn 中的 cwd 配对，核对项目环境没有在应用路由中丢失。核对后继续沿同一次 turn_start 调用进入协议请求构造。

## 将同一份输入写入 turn/start 请求

上一段调用的是 TUI 内部的 `turn_start` 方法。要让服务端接收任务，这个方法还需要把参数变成双方约定的请求结构；这里的“协议边界”，就是从应用内命令转为发给 app-server 的请求。下面用 `input: items` 把同一份输入接起来，再由 `request_typed` 提交 `ClientRequest::TurnStart`。`request_id` 为这次客户端请求提供编号。

源码：`codex-rs/tui/src/app_server_session.rs` · L1319–1340

<!-- source: input-rpc -->

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
                    cwd: Some(cwd),
                    runtime_workspace_roots: Some(workspace_roots.to_vec()),
                    approval_policy,
                    approvals_reviewer,
                    sandbox_policy,
                    permissions,
                    model: Some(model),
```

**为什么看这些行：**

- [L1323](#input-rpc-L1323)、[L1325](#input-rpc-L1325)

    **代码作用：** request_typed 接收 TurnStart 请求及它的参数结构；这里是应用内数据变成服务请求的位置。

    **讲解衔接：** 沿上一段 turn_start 调用进入这里后，应用内数据开始包装成客户端协议请求。本章在此到达发送端的协议边界，下一章从服务端接收后继续。

- [L1329](#input-rpc-L1329)

    **代码作用：** input: items 给出最直接的数据对应关系：之前的输入列表成为服务端将读取的 input 字段。

    **讲解衔接：** 这是本章输入追踪的落点：最初的 items 成为请求 input。下一章先找服务端怎样转换这个 input，便能把协议两端接起来。

到这里，我们的那句话已经从输入框进入 `TurnStartParams.input`。app-server 接收任务后还要决定如何交给核心，下一章就从它的接收端继续。本节跟的是没有活跃任务时的普通启动路径；运行中补充输入另见协作专题。


## 把本章的输入交接串起来

本章一直追的是同一句用户需求：先成为 text，再进入 items，随后被包装为 op，最后成为 turn/start 的 input。下面只检查这条已经展示的数据路线。

**检查问题：** 从 `items` 到服务请求的 `input`，中间经过了哪几次交接？哪一行是“构造命令之后，实际开始提交”的证据？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：输入依次经过“items → op → 应用处理 → turn_start → TurnStartParams.input”。**

先将 `items` 交给 `AppCommand::user_turn` 得到 `op`，再用 `submit_op(op.clone())` 提交；应用的普通启动路由将命令中的 `items` 传给 `turn_start`，最后写入服务请求的 `input` 字段。

**依据：** [命令构造 L370](#input-command-L370)、[提交 L409](#input-submit-call-L409)、[路由传参 L802](#input-route-L802)、[写入 input 的 L1329](#input-rpc-L1329)。

**第二问：实际开始提交的调用是 input_submission.rs 的 L409：self.submit_op(op.clone())。**

前面的 `let op = AppCommand::user_turn(...)` 只是构造命令；L409 才将这个命令交给提交方法。

**依据：** [调用 submit_op 的 L409](#input-submit-call-L409)。它进入的方法中，[L1807](#input-submit-L1807) 或 [L1813](#input-submit-L1813) 按当前分支发送命令。

</details>

## 为什么这么设计，好处是什么？

**为什么先包装输入，再提交命令？** `UserInput` 让输入种类明确，`AppCommand::user_turn` 再把输入与工作目录、运行设置组合起来。这样，后面的应用路由可以处理一份完整任务，而不必回到输入框读取界面状态。代码依据是[构造任务命令](#source-input-command)和[提交 op](#input-submit-call-L409)：构造数据与交出数据各有明确位置。

**放回案例，好处是什么？** “增加已完成筛选”与项目目录一起向后传递，接收方能知道需求针对哪个项目；排查“点击发送后没有反应”时，也能依次检查输入是否构造、命令是否提交、请求是否发出。分层增加了交接步骤，但每一步都有可观察的数据，方便定位问题。

## 接下来追什么

沿着 TurnStartParams.input 进入 app-server 服务端，看它怎样启动或补充一轮任务。
