# 专题 · 审批、沙箱与自动审查

> **本节问题：** 获准执行之后，为什么仍可能失败？

**承接：** 先完成主线 06，已看到 apply_patch 的真实调用路径。

## 从要求、决定、环境三个位置读权限

先问工具要求什么，再问谁作出决定，最后问执行环境限制什么。编排器会取得当前审批策略，并根据工具提供的要求或默认要求分流。

源码：`codex-rs/core/src/tools/orchestrator.rs` · L174–217

<!-- source: policy-branches -->

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

- [L179](#policy-branches-L179)、[L197](#policy-branches-L197)

    **代码作用：** 严格自动审查会进入 request_approval；追这个条件与调用，才能判断具体动作的决定来源。

    **讲解衔接：** 承接主线审批概览，这里再次进入编排器，细读 Skip 内部的审查决定来源。明确这一条件后，再比较禁止与需要批准的分支。

- [L209](#policy-branches-L209)、[L210](#policy-branches-L210)、[L212](#policy-branches-L212)

    **代码作用：** 禁止和需要批准分别控制是否继续；不要将它们仅理解为界面上不同的按钮样式。

    **讲解衔接：** 这组行补齐另外两种审批要求的控制去向。读完决定阶段，下一段返回具体补丁 handler，查获准或拒绝最终怎样体现在实际结果中。


这里有一个不能略过的例外：`Skip` 分支内仍检查 `strict_auto_review`，启用时会调用 `request_approval`。因此 Skip 不能简单翻译成“完全没有审查”；应把实际条件与决定来源一起读。

Skip 内部的实际分支还受严格自动审查条件影响；无论采用哪个审批分支，后续执行仍受环境限制。对写入动作，目录权限仍由具体环境和 sandbox 路径实施；拒绝应成为结果而不是改名后重试。

## 为什么自动审查要继续追决定的来源

仓库有 `core/src/guardian/` 等自动审查路径，不能由“auto”一个模式名推导为完全不检查。实际阅读时保持同一个 call_id，记录工具生成的动作、审批决定以及运行时最终结果。

审批分支只能回答动作怎样获得决定。要回答本专题的“获准后为什么仍可能失败”，现在返回具体补丁工具，观察 orchestrator.run 返回成功或错误时分别保存了什么。

源码：`codex-rs/core/src/tools/handlers/apply_patch.rs` · L606–622

<!-- source: policy-apply-result -->

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

- [L609](#policy-apply-result-L609)、[L613](#policy-apply-result-L613)、[L614](#policy-apply-result-L614)

    **代码作用：** 编排器返回后分别保存成功输出或错误，并附上变更信息；这里可以区分获准与执行结果。

    **讲解衔接：** 这里回到上一段编排器的调用方，闭合“审批及运行 → 返回结果”的过程。先看成功、错误与已提交变更怎样一起保存，再追这些信息交给谁。

- [L622](#policy-apply-result-L622)

    **代码作用：** 结果交给 emitter.finish，向后回接工具结果与界面事件通路。

    **讲解衔接：** 这是具体工具把结果交给输出处理的位置，接回主线第 07 节。至此审批决定、执行结果与后续反馈有了连续的对应关系。

教学检查表可按同一动作填写：补丁参数是否合法 → 请求哪个环境 → 审批要求是什么 → 谁返回决定 → 执行是否成功 → 模型收到什么结果。主线第 06 节只走最小链路，这里补上定位方法。

不要把控制工具、MCP 工具与补丁工具的审批路径强行合并。遇到新工具时，从它自己的 handler 向下追，而不是从模式名称猜实现。


## 从审批决定追到执行结果

本专题没有停在策略名称，而是回到了编排器的实际返回处。现在检查决定与结果是否都能定位。

**检查问题：** Skip 分支什么时候仍会请求批准？补丁运行失败后，调用处是否只保留一段错误文字？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：strict_auto_review 为真时，Skip 分支仍会请求批准。**

它会构造审批上下文，再调用 `request_approval`；决定是否走这条路径的是该条件。

**依据：** [条件 L179](#policy-branches-L179)与[请求批准 L197](#policy-branches-L197)。

**第二问：不是。失败分支既保留 error，也保留 runtime.committed_delta() 中已提交的变更信息。**

因此即使动作失败，调用处仍能向后传递已经发生的变更；不能只凭失败标签断言文件完全没有变化。

**依据：** [失败分支 L614](#policy-apply-result-L614)：`(Err(error), Some(runtime.committed_delta().clone()))`。

</details>

## 为什么这么设计，好处是什么？

**为什么审批决定与实际变更信息都要保留？** [审批分支](#source-policy-branches)控制动作是否能继续，并显式处理严格自动审查等条件；[补丁返回分支](#source-policy-apply-result)同时携带成功或错误结果，以及运行时记录的已提交变更。这两类信息分别说明“如何获得执行决定”和“执行后发生了什么”。

**放回案例，好处是什么？** 修改筛选组件失败时，后续处理仍可以检查是否已有部分变更，而不必假设工作区完全没动过。用户也能把获准执行、执行错误与文件变化对应起来，决定下一步需要检查或修复什么。代价是不能用一个“成功／失败”标签描述整个过程；审批状态、环境限制和最终变更需要分别读取。

## 接下来追什么

回到[06 · 执行条件](codex-06-permissions.md)，将具体工具的决定、执行与结果重新连起来。
