# 专题 · MCP 工具如何接回主循环

> **本节问题：** 远程工具返回的内容在哪里变成模型可用信息？

**承接：** 先完成主线 05—07。

## 外部能力仍要回到同一个工具循环

MCP 将服务器上的工具接入运行时。发现工具、让模型看见规格、批准调用和实际调用成功是不同状态。主线 05 讲通用工具路由，本节看获准 MCP 调用中的准备与结果处理。

源码：`codex-rs/core/src/mcp_tool_call.rs` · L441–456

<!-- source: mcp-call -->

```rust
    let turn_context = step_context.turn.as_ref();
    let server = invocation.server.clone();
    let tool_name = invocation.tool.clone();
    let arguments_value = invocation.arguments.clone();
    let connector_id = metadata.connector_id.as_deref();
    let connector_name = metadata.connector_name.as_deref();
    let server_origin = prepared_call.server_origin().map(str::to_string);

    let start = Instant::now();
    let mut tool_input = arguments_value
        .clone()
        .unwrap_or_else(|| JsonValue::Object(serde_json::Map::new()));
    let result = async {
        let result = async {
            let mut result = prepared_call
                .call_with_preparation(/*requested_timeout*/ None, || async {
```

**为什么看这些行：**

- [L442](#mcp-call-L442)、[L443](#mcp-call-L443)、[L444](#mcp-call-L444)

    **代码作用：** 从 invocation 取服务器、工具名和参数，建立这次外部调用的身份。

    **讲解衔接：** 承接通用工具路由，这里进入已经获准的 MCP 调用路径。先核对 invocation 中的外部工具身份与参数，再看准备好的调用对象如何使用它们。

- [L455](#mcp-call-L455)、[L456](#mcp-call-L456)

    **代码作用：** 使用已准备的调用对象执行；下一段要追这个调用返回的 result 怎样整理。

    **讲解衔接：** 这是外部调用的执行交接点。下一段仍追同一次调用，沿返回的 result 看外部格式怎样被整理为后续可用内容。


call_with_preparation 返回之后，result 进入下面的处理段。仍沿同一次外部调用追踪，查看工具返回值怎样从外部格式整理为模型可用的内容。

源码：`codex-rs/core/src/mcp_tool_call.rs` · L534–561

<!-- source: mcp-result -->

```rust
            let mcp_tool = McpToolContext::from_prepared_call(
                &prepared_call,
                turn_context.config.mcp_servers.get().get(&server),
            );
            process_mcp_tool_result(
                sess,
                turn_context,
                call_id,
                &mcp_tool,
                &tool_input,
                &mut result,
            )
            .await;
            let result = sanitize_mcp_tool_result_for_model(
                &turn_context.model_info().input_modalities,
                Ok(result),
            )?;
            Ok(maybe_request_codex_apps_auth_elicitation(
                sess,
                turn_context,
                prepared_call.config().approval_policy.value(),
                call_id,
                &invocation.server,
                Some(&metadata),
                result,
            )
            .await)
        }
```

**为什么看这些行：**

- [L538](#mcp-result-L538)、[L547](#mcp-result-L547)

    **代码作用：** 先处理外部工具结果，再按模型输入模态整理内容；这说明外部 result 不会原样无条件送入下一次请求。

    **讲解衔接：** 上一段外部调用已返回，这组行依次处理同一个 result，完成模型输入适配这一步。接下来还要查是否进入认证交互相关处理，才能继续追最终回传。

- [L551](#mcp-result-L551)

    **代码作用：** 整理后的结果进入后续认证交互处理，这一分支解释外部调用返回后为什么还可能有额外处理。

    **讲解衔接：** 这行补查结果整理后的条件分支，说明调用返回与最终结果交出之间仍有处理。随后回第 07 节，把工具输出接到统一的记录与再次请求通路。

第一段的 `prepared_call` 说明连接和准备已经在更早路径完成；这段不是服务器发现入口。第二段把外部返回整理成模型可用内容。连接成功不等于拿到了本次动作结果。

排查外部工具无效时，可以从 `codex-rs/core/src/mcp.rs` 的管理层向下检查，再回到此处的调用结果。关注服务器身份、工具名、参数和错误标志，避免把通信正常但工具业务失败报告成成功。

外部返回的文本提供信息，不会自行成为用户批准。结果仍经过统一记录，下一次模型请求才据此继续，这与本地读取文件遵循同样的交接原则。


## 沿 result 检查外部调用回传

我们从服务器、工具名和参数定位同一次调用，再看返回的 result 如何整理。检查题继续沿这个返回值走。

**检查问题：** `call_with_preparation` 的结果回来后，哪两个函数先后处理它？整理时使用了哪项模型信息？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：本节展示的处理顺序是先 process_mcp_tool_result，再 sanitize_mcp_tool_result_for_model。**

前者处理外部工具结果，后者继续整理成模型可使用的结果；本题问的这两步发生在调用返回之后。

**依据：** [第一步 L538](#mcp-result-L538)与[第二步 L547](#mcp-result-L547)。

**第二问：整理时使用的是当前模型的 input_modalities，即支持的输入模态。**

参数表达式是 `turn_context.model_info().input_modalities`，它作为整理函数的输入，帮助决定返回内容怎样适配当前模型。

**依据：** [整理函数参数 L548](#mcp-result-L548)。

</details>

## 为什么这么设计，好处是什么？

**为什么外部工具调用完成后，还要整理返回内容？** [调用代码](#source-mcp-call)用服务器、工具名和参数定位外部动作；[结果处理代码](#source-mcp-result)再处理返回值，并结合当前模型支持的输入模态进行整理。外部服务的返回格式与模型能够接收的内容未必相同，因此需要一个明确的适配过程。

**放回案例，好处是什么？** 如果通过外部工具取得需求说明或界面资料，整理后的结果可以接入已有的工具结果通路，后续请求便能结合它继续处理筛选任务。模型输入适配集中在回传阶段，也便于检查外部结果在何处发生变化。连接成功、工具动作成功和结果可被模型使用仍是不同状态，排错时需要逐一核对。

## 接下来追什么

回到[07 · 工具结果回传](codex-07-results.md)，沿整理后的外部结果追到下一次请求。
