# 事件流


> 流式传输子智能体、消息、工具调用和深度智能体的最终输出。


本页涵盖了特定于深度智能体的流式传输问题 - 最重要的是，通过 `stream.subagents` 从委托子智能体进行流式传输。对于一般代理流（`stream.messages`、`stream.values`、工具调用、自定义更新），请参阅[LangChain事件流](https://docs.langchain.com/oss/python/langchain/event-streaming)。


## 流子智能体


深度智能体在 LangGraph 流之上添加了子智能体投影。当您希望每个委托的 `task` 调用有一个流句柄时，请使用 `stream.subagents`。投影是轻量级的：它首先发现子智能体任务，并且仅当您在子智能体句柄上访问消息、工具调用和价值流时才会打开它们。


每个句柄的 `name` 是子智能体的配置名称：协调器在调用 `task` 工具时传递的 `subagent_type`。 Deep Agents 将该名称绑定到委托运行，因此您在子智能体规范中定义的相同标签就是您在流中过滤和路由的标签。


```python
stream = agent.stream_events(
    {
        "messages": [{"role": "user", "content": "Write me a haiku about the sea"}],
    },
    version="v3",
)

subagent_names: list[str] = []
for subagent in stream.subagents:
    print(subagent.name, subagent.path, subagent.status)

    for message in subagent.messages:
        print(message.text)

    subagent_names.append(subagent.name)
```


## 子智能体流字段


每个子智能体流都公开与父运行相同类型的投影，例如消息、工具调用、嵌套子智能体和最终输出。一般的父运行流模型请参见[LangChain事件流](https://docs.langchain.com/oss/python/langchain/event-streaming)。


Python 使用 Snake\_case 投影名称，例如 `tool_calls`。每个子智能体流可以公开 `.messages`、`.tool_calls`、`.values`、`.subagents` 和 `.output`。


|场地|描述|
| ------------ | ------------------------------------------------------------------------------------------ |
|`name`|子智能体名称，取自协调器在其 `task` 调用中选择的 `subagent_type`。|
|`messages`|子智能体发出的消息。|
|`subagents`|嵌套子智能体调用。|
|`output`|最终子智能体状态，或委派任务的完成信号。|
|`path`|子智能体流的命名空间路径。|
|`status`|生命周期状态，例如 `started`、`completed`、`failed` 或 `interrupted`。|
|`tool_calls`|工具调用范围为子智能体。|


## 跟踪子智能体生命周期


当您只需要显示哪些子智能体已启动和完成时，请使用 `stream.subagents`。您不需要订阅消息或价值流，除非您访问单个子智能体上的这些预测。


```python
stream = agent.stream_events(input, version="v3")

running = 0
completed = 0
failed = 0

for subagent in stream.subagents:
    running += 1
    print(f"{subagent.name}: started")

    try:
        _ = subagent.output
        running -= 1
        completed += 1
        print(f"{subagent.name}: completed")
    except Exception:
        running -= 1
        failed += 1
        print(f"{subagent.name}: failed")
```


## 流式传输消息


深度智能体可以从协调器代理和委派的子智能体发出消息。对顶级消息使用 `stream.messages`，对每个委派的子智能体使用 `subagent.messages`。


```python
stream = agent.stream_events(input, version="v3")

coordinator_messages: list[str] = []
for message in stream.messages:
    print("[coordinator]", message.text)
    coordinator_messages.append(message.text)

for subagent in stream.subagents:
    for message in subagent.messages:
        print(f"[{subagent.name}]", message.text)
```


## 流工具调用


深度智能体在代理树的每个级别公开工具调用。将顶级 `stream.tool_calls` 用于协调器工具，将每个 `subagent.tool_calls` 用于委派工作。


```python
stream = agent.stream_events(input, version="v3")

coordinator_tool_names: list[str] = []
for call in stream.tool_calls:
    print("[coordinator tool]", call.tool_name, call.input)
    print(call.completed, call.error)
    coordinator_tool_names.append(call.tool_name)

for subagent in stream.subagents:
    for call in subagent.tool_calls:
        print(f"[{subagent.name} tool]", call.tool_name, call.input)
        for delta in call.output_deltas:
            print(delta, end="", flush=True)

        if call.completed and call.error is None:
            print(call.output)
        elif call.error is not None:
            print(call.error)
```


## 流式嵌套工作


您可以递归到子智能体流以观察嵌套的子智能体、消息和工具调用。


```python
stream = agent.stream_events(input, version="v3")

subagent_names: list[str] = []
for subagent in stream.subagents:
    print(f"subagent {subagent.name}: {subagent.status}")

    for tool_call in subagent.tool_calls:
        print(f"{tool_call.tool_name}({tool_call.input})")
        for delta in tool_call.output_deltas:
            print(delta, end="", flush=True)

    for nested in subagent.subagents:
        print(f"nested subagent {nested.name}: {nested.status}")

    subagent_names.append(subagent.name)
```


## 同时消费


协调器和子智能体的输出经常交错。当您需要实时 UI 更新时，同时使用投影。


对于异步代码中的并发消耗，请将 `astream_events` 与 `asyncio.gather` 结合使用：


```py
import asyncio

stream = await agent.astream_events(input, version="v3")

async def consume_coordinator():
    async for message in stream.messages:
        print("[coordinator]", await message.text)

async def consume_subagents():
    async for subagent in stream.subagents:
        async for message in subagent.messages:
            print(f"[{subagent.name}]", await message.text)

await asyncio.gather(consume_coordinator(), consume_subagents())
```


 对于同步代码，请改用 `stream.interleave(...)`：


```python
stream = agent.stream_events(input, version="v3")

for name, item in stream.interleave("messages", "subagents"):
    if name == "messages":
        print("[coordinator]", item.text)
    else:
        for message in item.messages:
            print(f"[{item.name}]", message.text)
```


 当您需要协调器和所有子智能体之间的准确到达顺序时，请迭代原始协议事件并使用 `namespace` 来识别源：


```python
stream = agent.stream_events(input, version="v3")

text_deltas: list[str] = []
for event in stream:
    if event.get("method") != "messages":
        continue

    payload = event["params"]["data"][0]
    if not isinstance(payload, dict):
        continue
    if payload.get("event") != "content-block-delta":
        continue

    block = payload.get("delta") or {}
    if block.get("type") == "text-delta":
        source = "subagent" if event["params"]["namespace"] else "coordinator"
        print(f"[{source}] {block['text']}")
        text_deltas.append(block["text"])
```


## 子智能体与子图


`stream.subgraphs` 显示图执行结构。 `stream.subagents` 显示产品级深度智能体任务委派。将 `stream.subagents` 用于面向用户的 UI，因为它隐藏内部图形节点并直接公开子智能体概念。


## 有关的


* [LangChain事件流](https://docs.langchain.com/oss/python/langchain/event-streaming)涵盖了一般代理消息和工具调用流概念。
* [子智能体前端流](frontend--subagent-streaming.md) 显示将协调器消息与子智能体卡分开的 UI 模式。
* [LangGraph Event Streaming](https://docs.langchain.com/oss/python/langgraph/event-streaming) 涵盖了底层图流模型。


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/event-streaming.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

