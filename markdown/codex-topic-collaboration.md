# 专题 · 澄清、计划与运行中输入

> **本节问题：** 新答案和补充要求怎样影响正在执行的任务？

**承接：** 先完成主线 02 和 07。

## 澄清答案也是有类型的结果

问题工具先检查可用模式、规范化参数，然后交给会话请求输入。取消之前没有得到答复时，它返回错误，而不是自己编一个用户选择。

源码：`codex-rs/core/src/tools/handlers/request_user_input.rs` · L74–103

<!-- source: question-wait -->

```rust
        let mode = turn.collaboration_mode().mode;
        if let Some(message) = request_user_input_unavailable_message(mode, &self.available_modes) {
            return Err(FunctionCallError::RespondToModel(message));
        }

        let args: RequestUserInputToolArgs = parse_arguments(&arguments)?;
        let args = normalize_request_user_input_tool_args(args)
            .map_err(FunctionCallError::RespondToModel)?;
        let args = RequestUserInputArgs {
            questions: args.questions,
            is_blocking: mode == ModeKind::Plan,
            auto_resolution_ms: None,
        };
        let questions = args.questions.clone();
        let accepted = session
            .request_user_input(turn.as_ref(), call_id.clone(), args)
            .await
            .ok_or_else(|| {
                FunctionCallError::RespondToModel(format!(
                    "{REQUEST_USER_INPUT_TOOL_NAME} was cancelled before receiving a response"
                ))
            })?;

        let response = accepted.response;

        let content = serde_json::to_string(&response).map_err(|err| {
            FunctionCallError::Fatal(format!(
                "failed to serialize {REQUEST_USER_INPUT_TOOL_NAME} response: {err}"
            ))
        })?;
```

**为什么看这些行：**

- [L84](#question-wait-L84)、[L85](#question-wait-L85)

    **代码作用：** 阻塞方式随模式决定，自动解决时间在这里未设置；这是本段提问等待行为的具体配置。

    **讲解衔接：** 本专题先看澄清工具，这两行解释它向会话提出输入请求时采用什么等待设置。明确这些条件后，再沿实际答复追它如何变成工具结果。

- [L89](#question-wait-L89)、[L99](#question-wait-L99)

    **代码作用：** 先等待会话接受的回答，再序列化 response；这给出用户答案变成工具输出内容的交接顺序。

    **讲解衔接：** 这里完成“收到用户答复 → 生成可回传内容”的交接，随后接回第 07 节。下一段的计划更新是另一项工具调用，用来对照返回成功的不同含义。

固定版本中，`is_blocking` 根据模式决定，`auto_resolution_ms` 在这里设为 None。不能把所有提问一概描述成阻塞，也不能把等待超时推断成用户同意。答复最终成为工具结果，回接主线 07。

## 计划更新与执行工作分开

用户回答补齐了需求后，界面还可能显示“读取、修改、测试”的计划。这个计划更新是另一种工具调用，因此切换到 PlanHandler，核对它成功时究竟更新了什么。

源码：`codex-rs/core/src/tools/handlers/plan.rs` · L87–99

<!-- source: plan-event -->

```rust
        if turn.mode() == ModeKind::Plan {
            return Err(FunctionCallError::RespondToModel(
                "update_plan is a TODO/checklist tool and is not allowed in Plan mode".to_string(),
            ));
        }

        let args = parse_update_plan_arguments(&arguments)?;
        session
            .send_event(turn.as_ref(), EventMsg::PlanUpdate(args))
            .await;

        Ok(boxed_tool_output(PlanToolOutput))
    }
```

**为什么看这些行：**

- [L93](#plan-event-L93)、[L95](#plan-event-L95)

    **代码作用：** 解析计划参数后发送 PlanUpdate，实际动作是发布计划状态。

    **讲解衔接：** 从澄清答复切到计划工具后，这组行定位真正发生的动作：发送计划状态。先确认这个动作，才能正确解释下面的成功返回。

- [L98](#plan-event-L98)

    **代码作用：** 立即返回计划工具输出；结合前面的事件调用，才能确定成功指的是计划更新而非业务代码测试。

    **讲解衔接：** 这是计划工具的返回出口，闭合上一组事件发送的流程。后文再转到 Steer 补充输入，比较答案、计划和新要求各自怎样影响任务。

这里能直接看到模式限制，以及发送 `PlanUpdate` 后返回工具输出。把一项标成完成不会自动运行测试，是否完成仍需要实际执行证据。

## 运行中输入怎样接回循环

主线第 02 节的 `Started` 与 `Steered` 区分了新任务与补充输入。主线第 07 节的 `has_pending_input` 则影响后续推进。假设测试运行时用户又补充“保留显示全部任务的选项”，这是一条新的输入。沿它检查提交是否被识别为 Steered，再回主线 07 看 has_pending_input 如何让后续处理有机会消费这条补充。


## 区分答案返回与计划更新

用户提问工具产生答复内容，计划工具发布计划状态。两者都通过工具通路返回，但返回成功的含义不同。

**检查问题：** 问题工具在哪一步把答案变成可返回的文本？计划工具解析参数后实际发出了什么？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：在取出 accepted.response 之后，L99 用 serde_json::to_string(&response) 将答案序列化为文本。**

序列化结果保存到 `content`；这一步把收到的结构化答复转换成后续输出使用的文本内容。

**依据：** [取答复 L97](#question-wait-L97)与[序列化 L99](#question-wait-L99)。

**第二问：计划工具发出 EventMsg::PlanUpdate(args) 事件。**

它把解析得到的计划参数 `args` 交给 `session.send_event(...)`，随后返回计划工具输出。这里成功完成的是计划状态更新。

**依据：** [解析参数 L93](#plan-event-L93)、[发送计划事件 L95](#plan-event-L95)与[返回 L98](#plan-event-L98)。

</details>

## 为什么这么设计，好处是什么？

**为什么用户答复、计划更新与运行中补充输入要分别表示？** [提问工具](#source-question-wait)取得结构化答复后将它转成工具输出；[计划工具](#source-plan-event)发送计划状态事件；补充要求则通过主线中的 Steer 进入已有任务。它们分别提供决策信息、展示工作安排和改变后续任务输入，各自的返回值有清晰含义。

**放回案例，好处是什么？** “筛选后是否保留显示全部选项”的用户答复可以成为后续实现依据，计划更新让用户知道当前安排，运行中再补充要求也有专门入口。任务因此可以边执行边接收信息。计划状态更新成功只证明计划已更新，仍要由补丁、测试等实际工具结果支撑工作完成的判断。

## 接下来追什么

回到[07 · 下一次请求](codex-07-results.md)，查看答案和补充输入怎样影响后续处理。
