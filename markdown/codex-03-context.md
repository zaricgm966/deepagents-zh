# 03 · 模型第一次会收到什么

> **本节问题：** 历史、说明和工具如何组成模型请求？

**承接：** 我们已进入 run_turn，接下来必须给模型提供可用的信息。

## 先看本次请求实际使用的列表

会话历史不只包含用户和助手的文字，也可能包含工具请求、工具结果和上下文记录。`run_turn` 在每次采样前重新取得历史，因此前一次工具返回的内容才有机会进入后一次请求。

源码：`codex-rs/core/src/session/turn.rs` · L420–444

<!-- source: prompt-history -->

```rust
            // Construct the input that we will send to the model.
            let sampling_request_input: Vec<ResponseItem> = async {
                sess.clone_history()
                    .await
                    .for_prompt(&step_context.settings.model_info.input_modalities)
            }
            .instrument(trace_span!("run_turn.prepare_sampling_request_input"))
            .await;

            let responses_metadata = sess
                .responses_metadata(turn_context.as_ref(), CodexResponsesRequestKind::Turn)
                .await;
            run_sampling_request(
                Arc::clone(&sess),
                Arc::clone(&step_context),
                Arc::clone(&turn_context.extension_data),
                Arc::clone(&turn_diff_tracker),
                &mut client_session,
                &responses_metadata,
                sampling_request_input,
                cancellation_token.child_token(),
            )
            .await
        }
        .await;
```

**为什么看这些行：**

- [L421](#prompt-history-L421)、[L424](#prompt-history-L424)

    **代码作用：** 从会话历史生成 sampling_request_input；for_prompt 是本次追踪中需要展开的转换步骤。

    **讲解衔接：** 上一章已进入 run_turn，这里开始回答“模型这次能看到什么”。先取得 sampling_request_input，随后展开 for_prompt，核对历史怎样变成请求输入。

- [L432](#prompt-history-L432)、[L439](#prompt-history-L439)

    **代码作用：** 同一个输入变量交给 run_sampling_request，建立请求准备与后续采样处理之间的联系。

    **讲解衔接：** 这组行给出输入准备后的交出位置。教学上会先补读 for_prompt 的实现，再进入 run_sampling_request 中的 build_prompt 调用，沿同一份输入向前追。

`Vec<ResponseItem>` 是响应项组成的列表。先跟变量：`clone_history()` 取历史，`for_prompt(...)` 转成请求使用的输入，`sampling_request_input` 作为参数传给 `run_sampling_request`。

这段说明输入来自哪里，但不能仅靠函数名推断转换规则。继续看 `for_prompt` 的实现。

源码：`codex-rs/core/src/context_manager/history.rs` · L421–435

<!-- source: prompt-normalize -->

```rust
    pub(crate) fn for_prompt(self, input_modalities: &[InputModality]) -> Vec<ResponseItem> {
        self.for_prompt_annotated(input_modalities)
            .into_iter()
            .map(ResponseItemEnvelope::into_item)
            .collect()
    }

    /// Returns normalized history envelopes for internal consumers that must retain metadata.
    pub(crate) fn for_prompt_annotated(
        mut self,
        input_modalities: &[InputModality],
    ) -> Vec<ResponseItemEnvelope> {
        self.normalize_history(input_modalities);
        Arc::unwrap_or_clone(self.items)
    }
```

**为什么看这些行：**

- [L422](#prompt-normalize-L422)、[L424](#prompt-normalize-L424)

    **代码作用：** for_prompt 委托给保留注解的版本，再取出每个 envelope 中的响应项；这解释返回列表从何而来。

    **讲解衔接：** 这是对上一段 for_prompt 调用的向下展开，解释 sampling_request_input 内的响应项从哪里来。读完转换过程后，应回到请求准备链，继续找 Prompt 的构造。

- [L433](#prompt-normalize-L433)

    **代码作用：** 历史在取出前先 normalize；本段只能确认调用顺序，具体整理规则还需展开该方法。

    **讲解衔接：** 这行补查响应项取出前的整理步骤，界定当前片段能够证明的处理顺序。本节随后回到采样函数，不在这里继续展开全部历史整理规则。

现在我们知道，for_prompt 返回的是整理后的响应项列表。接下来还差一个步骤：列表要与工具规格、基础说明一起装进 Prompt，才能交给采样处理。

## 不只传消息，还要声明能力

`build_prompt` 把输入列表、模型可见的工具规格、基础说明和最终输出约束放入 `Prompt`。工具规格告诉模型可以请求什么；真实执行器留在运行时一侧。

先看 run_sampling_request 内部的调用处，确认前面得到的输入怎样交给 build_prompt，返回值又会交给谁。

源码：`codex-rs/core/src/session/turn.rs` · L1462–1478

<!-- source: prompt-call -->

```rust
        let prompt = build_prompt(
            prompt_input,
            step_context.as_ref(),
            base_instructions.clone(),
        );
        let err = match try_run_sampling_request(
            tool_runtime.clone(),
            Arc::clone(&sess),
            Arc::clone(&step_context),
            Arc::clone(&turn_store),
            client_session,
            responses_metadata,
            Arc::clone(&turn_diff_tracker),
            &prompt,
            cancellation_token.child_token(),
        )
        .await
```

**为什么看这些行：**

- [L1462](#prompt-call-L1462)、[L1463](#prompt-call-L1463)

    **代码作用：** prompt_input 成为 build_prompt 的实参，补上“输入列表怎样进入 Prompt”的调用证据。

    **讲解衔接：** 补读完 for_prompt 后，现在来到 run_sampling_request 内部。这组行是下一段 build_prompt 实现的调用依据，让“已有输入列表 → 构造 Prompt”连续起来。

- [L1467](#prompt-call-L1467)、[L1475](#prompt-call-L1475)

    **代码作用：** 返回的 prompt 被传入 try_run_sampling_request；读完构造函数后，就沿这个参数进入下一章。

    **讲解衔接：** 这里先标出 Prompt 构造完毕后的接收者。下一段解释各字段如何赋值后，再沿 try_run_sampling_request 进入第 04 节的响应流处理。


下面展开刚才调用的 build_prompt。先把实参 prompt_input 与形参 input 对上，再看消息、工具规格、基础说明分别写入哪些字段。

源码：`codex-rs/core/src/session/turn.rs` · L1386–1403

<!-- source: prompt-build -->

```rust
pub(crate) fn build_prompt(
    input: Vec<ResponseItem>,
    step_context: &StepContext,
    base_instructions: BaseInstructions,
) -> Prompt {
    let turn_context = &step_context.turn;
    Prompt {
        input,
        tools: step_context.tool_router.model_visible_specs(),
        parallel_tool_calls: true,
        base_instructions,
        output_schema: turn_context.final_output_json_schema.clone(),
        output_schema_strict: !crate::guardian::is_basic_session_source(
            &turn_context.session_source,
        ),
        cyber_access_program: turn_context.cyber_access_program,
    }
}
```

**为什么看这些行：**

- [L1393](#prompt-build-L1393)、[L1394](#prompt-build-L1394)

    **代码作用：** input 放入消息列表，tools 放入模型可见的工具规格；两者共同决定本次模型可依据的信息与可请求的动作。

    **讲解衔接：** 沿上一段 build_prompt 调用进入这里，先核对两个核心字段：输入列表与工具规格。它们说明前面准备的信息最后落在 Prompt 的什么位置。

- [L1396](#prompt-build-L1396)、[L1397](#prompt-build-L1397)

    **代码作用：** 基础说明和输出 schema 单独保存，说明 Prompt 并非把一切拼成一段用户文字。

    **讲解衔接：** 这组行补齐同一个 Prompt 中的约束信息，完成本章的请求组装解释。读完后回到上一段的调用方，跟随返回的 prompt 进入采样与响应流。

回到当前案例，Prompt 已将“增加筛选”的需求、准备好的说明与可用工具规格组织在一起。下一章从这个 Prompt 继续，查看请求发出后如何接收模型的响应。项目文件的实际读取将在工具章节引入。

`parallel_tool_calls: true` 是请求中的能力声明，不能由此推断所有工具会无条件并发。执行侧还有独立的并发门控，主线第 05 节会展示。


## 把历史列表与 Prompt 对上

前面依次看到了历史整理、build_prompt 的调用与构造，以及 prompt 被传给采样处理的位置。检查时继续沿变量走，不需要猜测模型内部如何理解文本。

**检查问题：** `sampling_request_input` 怎样进入 Prompt？Prompt 中除 input 外，哪些已展示字段影响本次请求？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：它作为 run_sampling_request 的输入传入，再由 build_prompt 放进 Prompt.input。**

具体路线是：`sampling_request_input` 作为实参传入 `run_sampling_request`；函数内准备出的 `prompt_input` 再传给 `build_prompt`，由构造函数写入 `Prompt` 的 `input` 字段。

**依据：** [传入采样处理的 L439](#prompt-history-L439)、[调用 build_prompt 的 L1462—1463](#prompt-call-L1462)、[写入 Prompt.input 的 L1393](#prompt-build-L1393)。

**第二问：除 input 外，展示的字段有 tools、parallel_tool_calls、base_instructions、output_schema、output_schema_strict 和 cyber_access_program。**

`tools` 提供可见工具规格，`parallel_tool_calls` 声明并行工具调用能力，`base_instructions` 提供基础说明；`output_schema` 与 `output_schema_strict` 携带输出结构约束及严格性设置，`cyber_access_program` 携带同名配置。本题只需确认这些字段分别进入请求准备结构，不要求展开每项配置的内部行为。

**依据：** [Prompt 构造函数](#source-prompt-build)的 L1394—1401 逐项赋值；其中[工具规格 L1394](#prompt-build-L1394)、[基础说明 L1396](#prompt-build-L1396)与[输出 schema L1397](#prompt-build-L1397)是本章重点。

</details>

## 为什么这么设计，好处是什么？

**为什么从历史重新准备输入，再统一构造 Prompt？** 每次请求前通过[clone_history 与 for_prompt](#source-prompt-history)取得当前可用的历史，再由[build_prompt](#source-prompt-build)组合消息、工具规格和基础说明。历史负责保存已经发生的交互，Prompt 负责描述本次请求需要什么信息、可以请求哪些能力，两者可以分别检查。

**放回案例，好处是什么？** 第一次请求只有需求和已有上下文；读取组件后，后续请求可以包含文件结果；测试失败后，又能包含失败输出。同一套准备过程适用于这些阶段。工具规格进入 Prompt，也让模型有明确的调用格式可用；实际执行仍由工具运行时处理。排查模型遗漏信息时，就可以检查最终请求输入，而不必只凭界面上显示过什么来判断。

## 接下来追什么

Prompt 已就绪；下一节沿 client_session.stream 看响应如何持续到达。
