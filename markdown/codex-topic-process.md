# 专题 · 后台命令与持续输出

> **本节问题：** 测试跑得很久时，如何继续读取而不重复启动？

**承接：** 先完成主线 08，知道命令返回的是工具输出。

## 一次等待结束，进程未必结束

`exec_command` 可以返回已完成结果，也可能返回仍可继续交互的进程状态。继续读取时使用工具返回的 session_id，不能重新启动一遍测试来代替等待。

源码：`codex-rs/core/src/tools/handlers/unified_exec/exec_command.rs` · L441–449

<!-- source: process-start -->

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

- [L443](#process-start-L443)、[L446](#process-start-L446)

    **代码作用：** 根据调用约束进入两条进程管理路径；这一步提交命令，下面再看如何找到已存在的进程。

    **讲解衔接：** 承接主线的测试命令，这里重看首次提交到进程管理器的位置。只有返回仍在运行的进程标识，下一段才使用它继续操作已有进程。


如果首次执行返回仍在运行的进程标识，后续读取需要找到同一个进程。下面进入 write_stdin 的 handler，重点寻找 session_id 被传给进程管理器的哪个字段。

源码：`codex-rs/core/src/tools/handlers/unified_exec/write_stdin.rs` · L81–101

<!-- source: process-continue -->

```rust
        let args: WriteStdinArgs = parse_arguments(&arguments)?;
        let context =
            UnifiedExecContext::new(session.clone(), step_context, cancellation_token, call_id);
        let response = session
            .services
            .unified_exec_manager
            .write_stdin(
                &context,
                WriteStdinRequest {
                    process_id: args.session_id,
                    input: &args.chars,
                    yield_time_ms: args.yield_time_ms,
                    max_output_tokens: args.max_output_tokens,
                    truncation_policy: turn.model_info().truncation_policy.into(),
                    interaction_event: Some(WriteStdinInteractionEvent {
                        session: &session,
                        turn: &turn,
                    }),
                },
            )
            .await
```

**为什么看这些行：**

- [L87](#process-continue-L87)、[L90](#process-continue-L90)

    **代码作用：** write_stdin 使用 session_id 填入 process_id，这个映射说明继续操作针对哪一个已有进程。

    **讲解衔接：** 现在进入后续一次 write_stdin 调用，与首次 exec_command 并非同一个 handler。这个字段映射先证明找到的是已有进程，下面再看本次要对它做什么。

- [L91](#process-continue-L91)、[L92](#process-continue-L92)

    **代码作用：** 输入内容和本次等待时长随请求传入；它们控制一次后续交互，不是重新构造原来的测试命令。

    **讲解衔接：** 确认进程身份后，这组行补齐本次交互的输入和等待设置。返回输出仍走第 07 节的结果通路，后续据结束状态判断测试是否已完成。

这里已经直接解释了 ID：`args.session_id` 赋给 `process_id`，标识的是进程会话，不是聊天会话。`chars` 是写入标准输入的内容；空输入可用于继续获取输出。

## 结果怎样回到任务

`write_stdin` 自己也是一次工具调用，有自己的 call_id；它返回的进程输出仍走主线 07 的工具响应与历史记录通路。同一个进程可以对应多次读取输出，不能把这两类编号混用。

教学记录应保留：首次命令、返回的进程标识、每次增量输出、最后退出码。只有取得结束状态后才报告测试结束；需要终止时再追进程清理和工具取消逻辑。


## 把后续交互对应到同一个进程

首次命令提交后，后续工具调用需要用返回的进程标识找到已有进程。下面只检查这次标识映射。

**检查问题：** `write_stdin` 将 `args.session_id` 放入哪个字段？`chars` 在这次请求中代表什么？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：args.session_id 被填入 WriteStdinRequest.process_id 字段。**

这个值用于定位之前已经创建的进程会话。

**依据：** [字段映射 L90](#process-continue-L90)：`process_id: args.session_id`。

**第二问：chars 是这次要写入已有进程标准输入的内容。**

代码将 `&args.chars` 填入请求的 `input` 字段。空内容可以用于继续等待输出；非空内容则用于与该进程继续交互。

**依据：** [输入字段 L91](#process-continue-L91)：`input: &args.chars`。

</details>

## 为什么这么设计，好处是什么？

**为什么长命令返回进程标识，后续再用 write_stdin 接续？** 一次工具等待的时长与进程的生命周期不一定相同。[后续请求](#source-process-continue)通过 `session_id → process_id` 找到已有进程，再传入输入内容与等待时长。这样，同一个命令可以跨多次工具交互持续运行。

**放回案例，好处是什么？** 测试尚未完成时，任务可以继续取得输出，而不必重复启动测试、再次消耗资源或重复产生副作用。需要输入时，也能把字符写给同一个进程。相应地，程序必须保存进程标识，并区分“本次读取返回了”与“测试进程退出了”；最终测试结论需要依据结束状态与输出。

## 接下来追什么

回到[08 · 修改与测试](codex-08-edit-test.md)，把最终进程结果接回测试反馈。
