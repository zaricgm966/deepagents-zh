# 08 · 从修改文件到测试反馈

> **本节问题：** 修改和测试怎样复用工具结果循环？

**承接：** 模型已通过工具结果了解当前文件，现在可以提出具体修改。

## 先区分补丁解析与应用

模型已经看到组件内容，现在提出补丁。补丁写出增加、删除或修改的片段；旧上下文用于匹配当前文件。解析合法不保证目标文件仍与模型读取时相同，所以 handler 还会对选定环境执行验证。

源码：`codex-rs/core/src/tools/handlers/apply_patch.rs` · L401–428

<!-- source: patch-verify -->

```rust
        let fs = turn_environment.environment.get_filesystem();
        let sandbox = turn_environment.sandbox_context(/*additional_permissions*/ None);
        match codex_apply_patch::verify_apply_patch_args_with_mode(
            args,
            turn_environment.cwd(),
            apply_patch_file_update_mode(&turn),
            fs.as_ref(),
            Some(&sandbox),
        )
        .await
        {
            codex_apply_patch::MaybeApplyPatchVerified::Body(changes) => {
                let tool_ctx = ToolCtx {
                    session,
                    step_context: Arc::clone(&step_context),
                    cancellation_token,
                    call_id,
                    tool_name,
                };
                let content = execute_verified_patch(
                    changes,
                    turn_environment.clone(),
                    Some(&tracker),
                    tool_ctx,
                )
                .await?;
                Ok(boxed_tool_output(ApplyPatchToolOutput::from_text(content)))
            }
```

**为什么看这些行：**

- [L403](#patch-verify-L403)、[L412](#patch-verify-L412)

    **代码作用：** 在当前环境验证补丁，Body 分支取得可应用的 changes；它连接了文本解析与实际文件变更。

    **讲解衔接：** 第 06 节已介绍解析与审批，这里补读两者之间的补丁验证步骤。得到 changes 后，才能继续向下追真正执行文件变更的调用。

- [L420](#patch-verify-L420)、[L427](#patch-verify-L427)

    **代码作用：** 将 changes 交给 execute_verified_patch，再包装它的结果；读到这里可以继续追修改结果，而不是只看到补丁文本。

    **讲解衔接：** 这是验证结果交给执行入口的位置，执行结果随后回接第 07 节。下一段测试代码属于后续可能发生的另一项工具调用，不是 execute_verified_patch 内的下一步。

只有沿验证后的执行路径继续，才能判断文件是否变化。第 06 节已展示 `orchestrator.run`，它的结果交给事件输出，最终复用第 07 节的结果通路。看到补丁文本本身不能证明它已经应用。

## 测试是一条真实命令

在教学任务里，模型可能请求 `npm test`。命令 handler 把请求交给进程管理器；有完成超时约束时等待到完成，无此约束时走普通执行路径。两者返回后都需要检查实际响应。

补丁结果回到模型后，后续请求才可能提出测试命令。我们因此从编辑 handler 切换到命令 handler；这不是补丁函数自动调用测试。下面只追命令交给进程管理器并返回结果的部分。

源码：`codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs` · L441–449

<!-- source: test-exec -->

```rust
        let result = match completion_timeout {
            Some(timeout) => {
                UnifiedExecProcessManager::exec_command_to_completion(request, &context, timeout)
                    .await
            }
            None => manager.exec_command(request, &context).await,
        };
        match result {
            Ok(response) => Ok(boxed_tool_output(response)),
```

**为什么看这些行：**

- [L443](#test-exec-L443)、[L446](#test-exec-L446)

    **代码作用：** 根据 completion_timeout 选择等待完成的执行路径或普通执行路径；从这里知道命令交给了哪一个管理方法。

    **讲解衔接：** 从补丁结果切换到后续测试工具调用后，这组行定位命令被交给哪个进程管理方法。确认提交位置后，再看管理器返回值怎样成为模型可接收的反馈。

- [L449](#test-exec-L449)

    **代码作用：** 把管理器响应包装成工具输出；下一次模型读取测试反馈仍使用前一章的结果回传通路。

    **讲解衔接：** 这是本章测试动作的返回出口，与第 07 节工具结果通路相接。后面的失败修复示例，就以这份实际测试反馈进入后续请求为前提。

退出码为非零通常提供失败线索；返回了进程会话标识时，则可能仍在运行。后者不能被记成“测试通过”，应继续取得结束状态。长时间命令专题会追 `write_stdin`。

## 把失败变成下一步依据

继续假设这个筛选案例：第一次实现错误地保留了一条未完成任务，测试输出指出筛选后的列表数量不符。运行时不负责替模型理解断言，它负责把输出准确交回历史。模型在后续请求中生成修复，再次修改、再次测试。

```text
教学流程，省略取消与权限分支：
已读取 App.tsx
  → 提交补丁 → 取得应用结果
  → 提交测试命令 → 取得结束状态和输出
  → 若失败：把失败证据交给下一次模型请求
  → 根据新决定继续修改或给出最终说明
```

补丁成功只说明文本变更结果；测试成功也只覆盖实际执行的测试。最终说明应区分修改了什么、验证了什么、还有什么未验证。


## 区分修改结果与测试结果

本章先读补丁 handler，再切到后续可能被模型调用的命令 handler。两条路径都返回工具输出，但对应不同动作。

**检查问题：** 哪一行把验证后的 `changes` 交给补丁执行？测试命令的管理器响应又在哪一行变成工具输出？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：L420 开始调用 execute_verified_patch，L421 将验证后的 changes 传入。**

调用位于 `core/src/tools/handlers/apply_patch.rs`；它在 `MaybeApplyPatchVerified::Body(changes)` 分支内处理已验证的变更。

**依据：** [执行调用 L420](#patch-verify-L420)与[changes 参数 L421](#patch-verify-L421)。

**第二问：L449 将测试命令的管理器响应包装成工具输出。**

语句是 `Ok(response) => Ok(boxed_tool_output(response))`，位于 `core/src/tools/handlers/unified_exec/exec_command.rs`。这里返回的是命令响应，是否通过测试还需读取其中的结束状态与输出。

**依据：** [响应包装 L449](#test-exec-L449)。

</details>

## 为什么这么设计，好处是什么？

**为什么补丁要先验证，测试又是独立工具动作？** [补丁验证分支](#source-patch-verify)将确认过的变更交给执行入口，能在执行前发现当前文件与预期不符等问题；[命令 handler](#source-test-exec)则负责真正启动测试并返回响应。文件变更与验证行为各有输入和结果，后续任务可以根据每一步的反馈继续。

**放回案例，好处是什么？** 如果组件在读取后被修改，补丁验证能提供不匹配的线索；如果修改成功但筛选逻辑错误，测试输出又能提供断言失败的线索。模型可以据此修复并再测。这样的分工也意味着执行补丁不会自动保证测试已经运行，结束时仍需核对实际执行了哪条测试命令，以及它是否已经完成。

## 接下来追什么

下一节检查“没有后续工作”如何变成轮次结束事件，而不是看到一次测试输出就直接退出。
