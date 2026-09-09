# 06 · 执行前需要满足哪些条件

> **本节问题：** 参数验证、审批和沙箱分别在哪一步起作用？

**承接：** 工具路由已找到处理器，但调用意图还没有变成成功结果。

## 先选一个真实会修改文件的工具

这一节用 `apply_patch` 作为证据，避免把不同工具的路径混为一谈。它的 handler 先检查 payload 形态并解析补丁。格式不对时直接返回面向模型的错误，还没到真实写入。

源码：`codex-rs/core/src/tools/handlers/apply_patch.rs` · L375–389

<!-- source: permission-payload -->

```rust
        let ToolPayload::Custom { input: patch_input } = payload else {
            return Err(FunctionCallError::RespondToModel(
                "apply_patch handler received unsupported payload".to_string(),
            ));
        };
        let args = match codex_apply_patch::parse_patch(&patch_input) {
            Ok(args) => args,
            Err(parse_error) => {
                return Err(FunctionCallError::RespondToModel(format!(
                    "apply_patch verification failed: {parse_error}"
                )));
            }
        };
        let selected_environment_id =
            require_environment_id(args.environment_id.as_deref(), self.multi_environment)?;
```

**为什么看这些行：**

- [L375](#permission-payload-L375)、[L380](#permission-payload-L380)

    **代码作用：** 先要求 Custom payload，再解析其中补丁文本；两步回答能否构造有效的补丁请求。

    **讲解衔接：** 上一章已定位具体处理器，现在用 apply_patch 进入执行前检查的第一步。先认清可接受的参数形态，再看检查失败时怎样结束这条路径。

- [L382](#permission-payload-L382)、[L384](#permission-payload-L384)

    **代码作用：** 解析失败返回可交给模型的错误描述，下面的执行路径只在通过这些检查后才有意义。

    **讲解衔接：** 这组行标明第一步的失败出口；下面的验证后执行入口只讨论通过检查的路径。这样从参数解析跳到编排器时，就不会漏掉进入它的前提。

## 验证后的补丁交给哪个执行入口

格式解析通过后，handler 还会验证补丁对应的文件变更，详见主线 08。本节先跳到 execute_verified_patch 中的调用点，确认这个具体工具使用的是哪个编排器。

源码：`codex-rs/core/src/tools/handlers/apply_patch.rs` · L606–622

<!-- source: permission-patch-run -->

```rust
    let mut orchestrator = ToolOrchestrator::new();
    let mut runtime = ApplyPatchRuntime::new();
    let result = orchestrator
        .run(&mut runtime, &request, &tool_ctx)
        .await
        .map(|result| result.output);
    let (result, delta) = match result {
        Ok(output) => (Ok(output.exec_output), Some(output.delta)),
        Err(error) => (Err(error), Some(runtime.committed_delta().clone())),
    };
    let event_ctx = ToolEventCtx::new(
        tool_ctx.session.as_ref(),
        tool_ctx.step_context.turn.as_ref(),
        &tool_ctx.call_id,
        tracker,
    );
    emitter.finish(event_ctx, result, delta.as_ref()).await
```

**为什么看这些行：**

- [L609](#permission-patch-run-L609)

    **代码作用：** 具体补丁工具调用编排器 run；这是从 handler 跳到审批编排逻辑的调用依据。

    **讲解衔接：** 通过前置检查后，这行给出补丁 handler 调用编排器的实际位置。下一段进入 orchestrator.run 的审批分支，就是沿此调用向下展开。

- [L613](#permission-patch-run-L613)、[L614](#permission-patch-run-L614)、[L622](#permission-patch-run-L622)

    **代码作用：** 返回后同时收集结果和已提交变更，再交给输出处理；失败分支也保留变更信息，所以要读真实执行结果。

    **讲解衔接：** 这里先标出编排器返回后的接收位置。读完下一段的允许或拒绝分支，要回到这组行理解决定如何变成结果，再交给后续输出处理。

先记住这个调用与返回位置：run 接收具体 runtime 和 request，返回值再交给 match result。下一段进入 run 内部，解释它怎样决定是否继续执行。



## 审批要求不是一个布尔开关

刚才的调用把 runtime、request 与 tool_ctx 交给了 orchestrator.run。现在进入 tools/orchestrator.rs，读取该方法中的审批分支；读完以后，结果会返回上一段的 match result。

源码：`codex-rs/core/src/tools/orchestrator.rs` · L174–217

<!-- source: permission-requirement -->

```rust
        let requirement = tool.exec_approval_requirement(req).unwrap_or_else(|| {
            default_exec_approval_requirement(approval_policy, &file_system_sandbox_policy)
        });
        match &requirement {
            ExecApprovalRequirement::Skip { .. } => {
                if strict_auto_review {
                    let action = tool
                        .approval_action(req, &tool_ctx.call_id)
                        .map_err(|err| {
                            ToolError::Rejected(format!("could not prepare approval action: {err}"))
                        })?;
                    let approval_ctx = ApprovalContext {
                        review_context: GuardianReviewContext::from(&tool_ctx.step_context),
                        cancellation_token: Some(tool_ctx.cancellation_token.clone()),
                        call_id: tool_ctx.call_id.clone(),
                        tool_name: tool_ctx.tool_name.clone(),
                        strict_auto_review,
                        approval_reason: None,
                        retry_reason: None,
                        network_approval_context: None,
                    };
                    tool_ctx
                        .session
                        .request_approval(action, approval_ctx)
                        .await?;
                    already_approved = true;
                } else {
                    otel.tool_decision(
                        &tool_ctx.tool_name,
                        otel_ci,
                        &ReviewDecision::Approved,
                        Some(ToolDecisionSource::Config),
                    );
                }
            }
            ExecApprovalRequirement::Forbidden { reason } => {
                return Err(ToolError::Rejected(reason.clone()));
            }
            ExecApprovalRequirement::NeedsApproval { reason, .. } => {
                let action = tool
                    .approval_action(req, &tool_ctx.call_id)
                    .map_err(|err| {
                        ToolError::Rejected(format!("could not prepare approval action: {err}"))
                    })?;
```

**为什么看这些行：**

- [L178](#permission-requirement-L178)、[L179](#permission-requirement-L179)、[L197](#permission-requirement-L197)

    **代码作用：** Skip 分支内仍有 strict_auto_review 检查，条件成立时请求批准；这解释为什么不能只看枚举名称判断审查行为。

    **讲解衔接：** 沿上一段 run 调用进入编排器后，这组行细读 Skip 的内部条件，补齐“要求如何变成决定”这一步。确认它的条件后，再与其余要求分支对照。

- [L209](#permission-requirement-L209)、[L210](#permission-requirement-L210)、[L212](#permission-requirement-L212)

    **代码作用：** Forbidden 直接拒绝，NeedsApproval 进入审批准备；不同要求会改变动作是否继续执行。

    **讲解衔接：** 这组行补齐禁止与需要审批的去向，完成本节的分支判断。随后回到 handler 的 match result，看本次调用的决定与执行结果如何交出。


读完这些分支后，回到上一段的 match result：允许的路径还要执行具体 runtime，拒绝或运行错误则成为返回结果。这样，审批要求就与同一次补丁调用的结果接上了。

审批解决“这次动作是否被允许”，沙箱解决“执行环境能够访问什么”。审批通过后仍可能遇到环境限制或执行失败；也不能假设每次动作都出现人工弹窗。

## 对照调用处与审批分支

本章已展示补丁 handler 怎样调用编排器，以及编排器内不同要求如何分支。检查时先判断分支，再回到调用处看结果交给谁。

**检查问题：** 如果审批要求是 `Forbidden`，代码在哪里返回？如果是 `Skip`，还需要检查哪一个条件？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：Forbidden 在 tools/orchestrator.rs 的 L210 直接返回 ToolError::Rejected。**

返回语句是 `return Err(ToolError::Rejected(reason.clone()));`，使用审批要求中携带的拒绝原因。

**依据：** [Forbidden 分支 L209](#permission-requirement-L209)与[拒绝返回 L210](#permission-requirement-L210)。

**第二问：Skip 分支仍需检查 strict_auto_review 是否为真。**

为真时会准备审批上下文并调用 `request_approval`；因此进入 `Skip` 不能直接推导出完全没有审查。

**依据：** [条件 L179](#permission-requirement-L179)与[请求批准 L197](#permission-requirement-L197)。

</details>

## 为什么这么设计，好处是什么？

**为什么把参数检查、审批与实际执行拆开？** 它们回答不同的问题：补丁参数能否被解析，这次动作是否允许，以及执行环境能否完成写入。[handler 检查 payload](#source-permission-payload)后，具体请求才进入[编排器的审批分支](#source-permission-requirement)。格式错误可以在前面直接反馈，策略决定也能在实际运行前单独处理。

**放回案例，好处是什么？** 给组件增加筛选时，如果补丁格式错误，模型能收到参数问题；如果动作被禁止，收到的则是拒绝原因。后续处理由此可以针对真实原因作出调整。审批与执行分开也保留了明确的结果边界：获得许可后，仍要读取[编排器返回的执行结果](#source-permission-patch-run)，才能判断文件是否修改成功。

## 接下来追什么

执行器将成功、拒绝或错误交回工具运行时；接下来把结果一路追到下一次模型请求。
