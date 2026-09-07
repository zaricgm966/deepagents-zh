# 流媒体


> 从深度智能体运行和子智能体执行中传输实时更新


对于新应用程序，我们推荐[事件流](event-streaming.md)——Deep Agents v0.6 中引入的类型化投影 API。事件流为每个投影提供单独的迭代器（子智能体、消息、工具调用、值），因此您可以独立使用它们，而不是在 `stream_mode` 块上分支。


Deep Agents 构建在 LangGraph 的流基础设施之上，为子智能体流提供一流的支持。当深度智能体将工作委托给子智能体时，您可以独立地传输来自每个子智能体的更新 - 实时跟踪进度、LLM 令牌和工具调用。


深度智能体流可以实现什么：


* 
[**流子智能体进度**](#subagent-progress)—跟踪每个子智能体并行运行时的执行情况。* 
[**流 LLM 令牌**](#llm-tokens) — 来自主代理和每个子智能体的流令牌。* 
[**流工具调用**](#tool-calls) — 查看子智能体执行中的工具调用和结果。* 
[**流式自定义更新**](#custom-updates) — 从内部子智能体节点发出用户定义的信号。


## 启用子图流


深度智能体使用 LangGraph 的子图流来显示子智能体执行中的事件。要接收子智能体事件，请在流式传输时启用 `stream_subgraphs`。


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    system_prompt="You are a helpful research assistant",
    subagents=[
        {
            "name": "researcher",
            "description": "Researches a topic in depth",
            "system_prompt": "You are a thorough researcher.",
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="updates",
    subgraphs=True,  # [!code highlight]
    version="v2",  # [!code highlight]
):
    if chunk["type"] == "updates":
        if chunk["ns"]:
            # Subagent event - namespace identifies the source
            print(f"[subagent: {chunk['ns']}]")
        else:
            # Main agent event
            print("[main agent]")
        print(chunk["data"])
```


## 命名空间


启用 `subgraphs` 后，每个流事件都包含一个**命名空间**，用于标识哪个代理生成了该事件。命名空间是代表代理层次结构的节点名称和任务 ID 的路径。


|命名空间|来源|
| ------------------------------------------ | ---------------------------------------------------------------- |
|`()`（空）|主要代理|
|`("tools:abc123",)`|由主代理的 `task` 工具调用 `abc123` 生成的子智能体|
|`("tools:abc123", "model_request:def456")`|子智能体内的模型请求节点|


使用命名空间将事件路由到正确的 UI 组件：


```python
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Plan my vacation"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Check if this event came from a subagent
        is_subagent = any(
            segment.startswith("tools:") for segment in chunk["ns"]
        )

        if is_subagent:
            # Extract the tool call ID from the namespace
            tool_call_id = next(
                s.split(":")[1] for s in chunk["ns"] if s.startswith("tools:")
            )
            print(f"Subagent {tool_call_id}: {chunk['data']}")
        else:
            print(f"Main agent: {chunk['data']}")
```


## 分代理进度


使用 `stream_mode="updates"` 跟踪每个步骤完成时的子智能体进度。这对于显示哪些子智能体处于活动状态以及它们已完成哪些工作非常有用。


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    system_prompt=(
        "You are a project coordinator with no research knowledge. "
        "For every user request, you must call the task() tool with "
        "subagent_type set to researcher. Never answer research questions yourself. "
        "Keep your final response to one sentence."
    ),
    subagents=[
        {
            "name": "researcher",
            "description": "Researches topics thoroughly",
            "system_prompt": (
                "You are a thorough researcher. Research the given topic "
                "and provide a concise summary in 2-3 sentences."
            ),
        },
    ],
)

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Write a short summary about AI safety"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        # Main agent updates (empty namespace)
        if not chunk["ns"]:
            for node_name, data in chunk["data"].items():
                if node_name == "tools":
                    # Subagent results returned to main agent
                    for msg in data.get("messages", []):
                        if msg.type == "tool":
                            print(f"\nSubagent complete: {msg.name}")
                            print(f"  Result: {str(msg.content)[:200]}...")
                else:
                    print(f"[main agent] step: {node_name}")

        # Subagent updates (non-empty namespace)
        else:
            for node_name, data in chunk["data"].items():
                print(f"  [{chunk['ns'][0]}] step: {node_name}")
```


```shell
[main agent] step: model_request
  [tools:call_abc123] step: model_request
  [tools:call_abc123] step: tools
  [tools:call_abc123] step: model_request

Subagent complete: task
  Result: ## AI Safety Report...
[main agent] step: model_request
```


## 法学硕士代币


使用 `stream_mode="messages"` 从主代理和子智能体流式传输各个令牌。每个消息事件都包含标识源代理的元数据。


```python
current_source = ""

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing advances"}]},
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]

        # Check if this event came from a subagent (namespace contains "tools:")
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])

        if is_subagent:
            # Token from a subagent
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            if subagent_ns != current_source:
                print(f"\n\n--- [subagent: {subagent_ns}] ---")
                current_source = subagent_ns
            if token.content:
                print(token.content, end="", flush=True)
        else:
            # Token from the main agent
            if "main" != current_source:
                print("\n\n--- [main agent] ---")
                current_source = "main"
            if token.content:
                print(token.content, end="", flush=True)

print()
```


## 工具调用


当子智能体使用工具时，您可以流式传输工具调用事件以显示每个子智能体正在执行的操作。工具调用块出现在 `messages` 流模式中。


```python
from langchain.messages import AIMessageChunk, ToolMessage

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research recent quantum computing advances"}]},
    stream_mode="messages",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "messages":
        token, metadata = chunk["data"]

        # Identify source: "main" or the subagent namespace segment
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        source = next((s for s in chunk["ns"] if s.startswith("tools:")), "main") if is_subagent else "main"

        # Tool call chunks (streaming tool invocations)
        if isinstance(token, AIMessageChunk) and token.tool_call_chunks:
            for tc in token.tool_call_chunks:
                if tc.get("name"):
                    print(f"\n[{source}] Tool call: {tc['name']}")
                # Args stream in chunks - write them incrementally
                if tc.get("args"):
                    print(tc["args"], end="", flush=True)

        # Tool results
        if isinstance(token, ToolMessage):
            print(f"\n[{source}] Tool result [{token.name}]: {str(token.content)[:150]}")

        # Regular AI content (skip tool call messages)
        if (
            isinstance(token, AIMessageChunk)
            and token.content
            and not token.tool_call_chunks
        ):
            print(token.content, end="", flush=True)

print()
```


## 自定义更新


在子智能体工具中使用 [`get_stream_writer`](https://reference.langchain.com/python/langgraph/config/get_stream_writer) 来发出自定义进度事件：


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="openai:gpt-5.5",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```python
import time
from langchain.tools import tool
from langgraph.config import get_stream_writer
from deepagents import create_deep_agent


@tool
def analyze_data(topic: str) -> str:
    """Run a data analysis on a given topic.

    This tool performs the actual analysis and emits progress updates.
    You MUST call this tool for any analysis request.
    """
    writer = get_stream_writer()

    writer({"status": "starting", "topic": topic, "progress": 0})
    time.sleep(0.5)

    writer({"status": "analyzing", "progress": 50})
    time.sleep(0.5)

    writer({"status": "complete", "progress": 100})
    return (
        f'Analysis of "{topic}": Customer sentiment is 85% positive, '
        "driven by product quality and support response times."
    )


agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    system_prompt=(
        "You are a coordinator. For any analysis request, you MUST delegate "
        "to the analyst subagent using the task tool. Never try to answer directly. "
        "After receiving the result, summarize it in one sentence."
    ),
    subagents=[
        {
            "name": "analyst",
            "description": "Performs data analysis with real-time progress tracking",
            "system_prompt": (
                "You are a data analyst. You MUST call the analyze_data tool "
                "for every analysis request. Do not use any other tools. "
                "After the analysis completes, report the result."
            ),
            "tools": [analyze_data],
        },
    ],
)

custom_event_count = 0
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze customer satisfaction trends"}]},
    stream_mode="custom",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "custom":
        custom_event_count += 1
        is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
        if is_subagent:
            subagent_ns = next(s for s in chunk["ns"] if s.startswith("tools:"))
            print(f"[{subagent_ns}]", chunk["data"])
        else:
            print("[main]", chunk["data"])
```


```shell
[tools:call_abc123] {'status': 'starting', 'topic': 'customer satisfaction trends', 'progress': 0}
[tools:call_abc123] {'status': 'analyzing', 'progress': 50}
[tools:call_abc123] {'status': 'complete', 'progress': 100}
```


## 流式传输多种模式


结合多种流模式来全面了解代理执行情况：


```python
# Skip internal middleware steps - only show meaningful node names
INTERESTING_NODES = {"model", "tools"}

last_source = ""
mid_line = False  # True when we've written tokens without a trailing newline

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Analyze the impact of remote work on team productivity"}]},
    stream_mode=["updates", "messages", "custom"],
    subgraphs=True,
    version="v2",
):
    is_subagent = any(s.startswith("tools:") for s in chunk["ns"])
    source = "subagent" if is_subagent else "main"

    if chunk["type"] == "updates":
        for node_name in chunk["data"]:
            if node_name not in INTERESTING_NODES:
                continue
            if mid_line:
                print()
                mid_line = False
            print(f"[{source}] step: {node_name}")

    elif chunk["type"] == "messages":
        token, metadata = chunk["data"]
        if token.content:
            # Print a header when the source changes
            if source != last_source:
                if mid_line:
                    print()
                    mid_line = False
                print(f"\n[{source}] ", end="")
                last_source = source
            print(token.content, end="", flush=True)
            mid_line = True

    elif chunk["type"] == "custom":
        if mid_line:
            print()
            mid_line = False
        print(f"[{source}] custom event:", chunk["data"])

print()
```


## 常见模式


### 跟踪子智能体生命周期


监视子智能体何时启动、运行和完成：


```python
active_subagents = {}

for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research the latest AI safety developments"}]},
    stream_mode="updates",
    subgraphs=True,
    version="v2",
):
    if chunk["type"] == "updates":
        for node_name, data in chunk["data"].items():
            # ─── Phase 1: Detect subagent starting ────────────────────────
            # When the main agent's model node contains task tool calls,
            # a subagent has been spawned.
            if not chunk["ns"] and node_name == "model":
                for msg in data.get("messages", []):
                    for tc in getattr(msg, "tool_calls", []):
                        if tc["name"] == "task":
                            active_subagents[tc["id"]] = {
                                "type": tc["args"].get("subagent_type"),
                                "description": tc["args"].get("description", "")[:80],
                                "status": "pending",
                            }
                            print(
                                f'[lifecycle] PENDING  → subagent "{tc["args"].get("subagent_type")}" '
                                f'({tc["id"]})'
                            )

            # ─── Phase 2: Detect subagent running ─────────────────────────
            # When we receive events from a tools:UUID namespace, that
            # subagent is actively executing.
            if chunk["ns"] and chunk["ns"][0].startswith("tools:"):
                pregel_id = chunk["ns"][0].split(":")[1]
                # Check if any pending subagent needs to be marked running.
                # Note: the pregel task ID differs from the tool_call_id,
                # so we mark any pending subagent as running on first subagent event.
                for sub_id, sub in active_subagents.items():
                    if sub["status"] == "pending":
                        sub["status"] = "running"
                        print(
                            f'[lifecycle] RUNNING  → subagent "{sub["type"]}" '
                            f"(pregel: {pregel_id})"
                        )
                        break

            # ─── Phase 3: Detect subagent completing ──────────────────────
            # When the main agent's tools node returns a tool message,
            # the subagent has completed and returned its result.
            if not chunk["ns"] and node_name == "tools":
                for msg in data.get("messages", []):
                    if msg.type == "tool":
                        sub = active_subagents.get(msg.tool_call_id)
                        if sub:
                            sub["status"] = "complete"
                            print(
                                f'[lifecycle] COMPLETE → subagent "{sub["type"]}" '
                                f"({msg.tool_call_id})"
                            )
                            print(f"  Result preview: {str(msg.content)[:120]}...")

# Print final state
print("\n--- Final subagent states ---")
for sub_id, sub in active_subagents.items():
    print(f"  {sub['type']}: {sub['status']}")
```


## v2 流媒体格式


需要 LangGraph >= 1.1。


本页上的所有示例均使用 v2 流格式 (`version="v2"`)，这是推荐的方法。每个块都是一个带有 `type`、`ns` 和 `data` 键的 `StreamPart` 字典 - 无论流模式、模式数量或子图设置如何，形状都相同。


v2 格式消除了嵌套元组解包，从而可以直接处理深度智能体中的子图流。比较两种格式：


```python
# Unified format — no nested tuple unpacking
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing"}]},
    stream_mode=["updates", "messages", "custom"],
    subgraphs=True,
    version="v2",
):
    print(chunk["type"])  # "updates", "messages", or "custom"
    print(chunk["ns"])    # () for main agent, ("tools:<id>",) for subagent
    print(chunk["data"])  # payload
```


```python
# Must handle (namespace, (mode, data)) nested tuples
for namespace, chunk in agent.stream(
    {"messages": [{"role": "user", "content": "Research quantum computing"}]},
    stream_mode=["updates", "messages", "custom"],
    subgraphs=True,
):
    mode, data = chunk[0], chunk[1]
    print(mode)       # "updates", "messages", or "custom"
    print(namespace)  # () for main agent, ("tools:<id>",) for subagent
    print(data)       # payload
```


 有关 v2 格式的更多详细信息，包括类型缩小和 Pydantic/dataclass 强制，请参阅 [LangGraph 流文档](https://docs.langchain.com/oss/python/langgraph/streaming#stream-output-format-v2)。


## 有关的


* [子智能体](subagents.md) - 配置子智能体并将其与深度智能体一起使用
* [前端流](frontend--overview.md) - 使用 [`useStream`](https://reference.langchain.com/javascript/langchain-react/index/useStream) 为深度智能体构建 React UI
* [LangChain事件流](https://docs.langchain.com/oss/python/langchain/event-streaming)—LangChain代理的一般流概念


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/streaming.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

