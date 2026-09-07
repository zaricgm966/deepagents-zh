# 代理服务器中的 A2A 端点


> 使用 A2A 协议通过 LangSmith 中的分布式跟踪启用代理间通信。


[Agent2Agent (A2A)](https://a2a-protocol.org/latest/) 是 Google 的协议，用于实现对话式 AI 代理之间的通信。 [LangSmith 实现了 A2A 支持](https://docs.langchain.com/langsmith/server-api-ref#tag/a2a/post/a2a/\{assistant_id})，允许您的代理通过标准化协议与其他 A2A 兼容代理进行通信。


A2A 端点可在位于 `/a2a/{assistant_id}` 的 [代理服务器](https://docs.langchain.com/langsmith/agent-server) 中使用。


## 协议版本


代理服务器采用 A2A **v1.0** JSON-RPC 绑定，并且还接受 v0.3 方法名称，因此现有 v0.3 客户端可以继续工作。代理卡声明一个接口：


```json
"supportedInterfaces": [
  {
    "url": "https://your-deployment/a2a/{assistant_id}",
    "protocolBinding": "JSONRPC",
    "protocolVersion": "1.0"
  }
]
```


 您发送的方法名称还会选择响应中的枚举大小写。 v1.0 名称返回 SCREAMING\_SNAKE\_CASE (`TASK_STATE_WORKING`, `ROLE_AGENT`)； v0.3 名称返回小写字母（`working`、`agent`）。为每个客户选择一个家庭并坚持下去。


信封因方法而异，而不是因系列而异：`SendMessage` 将任务包装在 `result.task` 中，而 `GetTask` 和所有 v0.3 方法直接在 `result` 上返回它。 `ListTasks` 返回 `result.tasks`。


## 支持的方法


|v1.0名称|v0.3名称|支持|
| ----------------------------- | ---------------- | ----------------------------- |
|`SendMessage`|`message/send`|是的|
|`SendStreamingMessage`|`message/stream`|是 - 服务器发送的事件|
|`GetTask`|`tasks/get`|是的|
|`CancelTask`|`tasks/cancel`|是的|
|`ListTasks`|—|是的|
|`GetExtendedAgentCard`|—|是的，仅在 v1.0 名称下|
|`SubscribeToTask`|—|还没有 — 返回 `-32601`|
|`*TaskPushNotificationConfig`|—|还没有 — 返回 `-32601`|


只接受四个 v0.3 名称：`message/send`、`message/stream`、`tasks/get` 和 `tasks/cancel`。其他任何内容（包括 `agent/getAuthenticatedExtendedCard` 和 `tasks/resubscribe`）都会返回 `-32601 Method not found`。


仅 JSON-RPC 绑定可用。 gRPC 和 HTTP+JSON 未实现。


### 回复中的任务历史记录


上下文包含许多任务。默认情况下，`SendMessage`、`GetTask` 和 `ListTasks` 返回**整个上下文**的历史记录，而不仅仅是您询问的任务。上下文中的第二个任务会重播第一个任务的消息，因此呈现每个历史条目的客户端会再次显示较早的轮次 - 包括较早的工具结果和 A2UI 有效负载。


将 `historyScope` 设置为 `task` 以仅取回属于您询问的任务的消息。默认值保持 `context`，因此现有集成不受影响。


选项的去向取决于方法。 `SendMessage` 从 `configuration` 读取：


```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [{"text": "Second request"}],
      "messageId": "message-2",
      "contextId": "8b1f0e5c-9a3d-4f27-b0c8-2e6a5d4c1b7a"
    },
    "configuration": {"historyScope": "task"}
  }
}
```


 `GetTask`和`ListTasks`直接从`params`读取：


```json
{"jsonrpc": "2.0", "id": "2", "method": "GetTask",
 "params": {"id": "<taskId>", "historyScope": "task"}}
```


 如果您的客户端无法将字段添加到请求正文，请改为发送标头。请求中的显式值胜过标头。


```
LangGraph-A2A-History-Scope: task
```


 代理卡在 `capabilities.extensions` 下宣传这一点，因此您可以检测支持而不是假设它：


```json
{
  "uri": "https://langchain.com/a2a/extensions/history-scope/v1",
  "description": "Choose task-only or full-context response history",
  "required": false,
  "params": {
    "header": "LangGraph-A2A-History-Scope",
    "values": ["context", "task"],
    "default": "context",
    "methods": ["SendMessage", "GetTask", "ListTasks"]
  }
}
```


 值得了解的三个限制：


* 流式传输会忽略这两个历史选项。 `SendStreamingMessage` 既不读取 `historyScope` 也不读取 `historyLength`，并且如果您发送它们，也不会返回错误 - 因此不要通过 SSE 依赖任何一个。
* `historyLength` 上限为 10。较大的值将返回 `-32602` 和 `historyLength cannot exceed 10`。
* 范围在 `historyLength` 之前应用，因此您可以获得*该任务*的最后 N 条消息。


无法识别的值将返回 `-32602` 和 `historyScope must be 'context' or 'task'`。像 `historyscope` 这样大小写错误的键并不是一个错误——它会被忽略，并且您会默默地获得完整的上下文历史记录，因此如果过滤似乎不起作用，请检查拼写。


请勿从已完成的任务中重新发送 `taskId`。每个新回合都会在同一上下文中启动一个新任务 - 单独发送 `contextId`。命名终端任务的消息将被拒绝，并显示为 `-32004`，并且由另一个代理创建的 `taskId` 将被拒绝，并显示为 `-32001`。


## 代理卡发现


每个助手都会自动公开一个 A2A 代理卡，该卡描述其功能并提供其他代理连接所需的信息。您可以使用以下方式检索任何助理的代理卡：


```
GET /.well-known/agent-card.json?assistant_id={assistant_id}
```


 座席卡包含助理的姓名、描述、可用技能、支持的输入/输出模式以及用于通信的 A2A 端点 URL。


## 可选功能


这些是通过助手 API 上的 `metadata.a2a` 对每个助手进行配置的。 `langgraph.json` 无法设置助手元数据，因此请在部署后修补助手。


### 声明输入和输出模式


```json
{
  "metadata": {
    "a2a": {
      "input_modes": ["text/plain", "application/pdf"],
      "output_modes": ["text/plain", "application/pdf"]
    }
  }
}
```


 这些值同时提供给卡牌的 `defaultInputModes`/`defaultOutputModes` 和生成的技能模式。它们只是广告——仍然接受未声明的模式。替换是按字段进行的，因此如果您希望两者都被覆盖，请发送两者，并注意空列表将被拒绝。


### 文件零件


`FilePart` 双向工作。传入的文件、图像、音频和视频部分成为LangChain内容块。出站内容块映射回任务历史记录和最终流式工件中的 `FilePart`。 MIME 类型、URI 和文件名不变地传递；内联数据被重新编码为标准 base64。


### A2UI v0.9


选择每个助理：


```json
{ "metadata": { "a2a": { "a2ui": true } } }
```


 然后，该卡会通告扩展名并将规范的 MIME 类型附加到两个模式列表中：


```json
"capabilities": {
  "extensions": [
    {
      "uri": "https://a2ui.org/a2a-extension/a2ui/v0.9",
      "description": "Ability to render A2UI v0.9",
      "required": false,
      "params": {
        "v0.9": {
          "supportedCatalogIds": [],
          "acceptsInlineCatalogs": false
        }
      }
    }
  ]
}
```


 客户端通过在 `message.extensions` 中列出 URI 来激活它。有效负载根据 v0.9 模式进行双向验证，A2UI 部分保留在 `message/send`、`tasks/get` 和最终的 `message/stream` 工件中。响应携带`metadata.mimeType: "application/a2ui+json"`。 `application/json+a2ui` 被接受作为输入的别名。


### 过滤工具结果


默认情况下，每个相关工具结果都会发布为 `DataPart`。要仅发布某些工具，请在部署中设置工具名称的允许列表：


```bash
A2A_ALLOWED_TOOL_CALL_RESULTS=generative_ui_tool,another_tool
```


 取消设置意味着发布所有工具结果。该过滤器适用于任务历史记录和流式传输。


## 要求


|特征|最低版本|
| -------------------------------------------- | ------------------------- |
|A2A端点|`langgraph-api >= 0.4.21`|
|入站 `FilePart`|`0.12.0`|
|工具结果 `DataPart`s|`0.12.2`|
|`A2A_ALLOWED_TOOL_CALL_RESULTS`|`0.12.4`|
|出站 `FilePart`，可配置卡模式|`0.13.0`|
|A2UI v0.9|`0.15.0`|
|`historyScope`|`0.15.0`|


```bash
pip install "langgraph-api>=0.13.0"
```


 A2UI v0.9 和 `historyScope` 在 `0.14.0` 候选版本被削减后登陆，因此它们到达了 `0.15.0`。该版本尚未作为稳定版本发布 - 在依赖 `historyScope` 之前检查代理卡上的 `capabilities.extensions`。


您的图表状态必须包含 `messages` 键才能接受 A2A 文本和文件部分。输入架构没有 `messages` 字段的助手将被拒绝并出现解释性错误。


## 创建 A2A 兼容代理


此示例创建一个与 A2A 兼容的代理，该代理使用 OpenAI 的 API 处理传入消息并维护对话状态。代理定义基于消息的状态结构并处理 A2A 协议的消息格式。


为了与 [A2A“文本”部分](https://a2a-protocol.org/dev/specification/#651-textpart-object) 兼容，代理必须具有处于状态的 `messages` 密钥。


A2A 协议使用两个标识符来保持会话的连续性：


* `contextId`：将消息分组到对话线程中（如会话 ID）
* `taskId`：标识该对话中的每个单独请求


在第一条消息中，省略两者 - 代理生成并返回它们。对于对话中的所有后续消息，从先前的响应中发回 `contextId` 并省略 `taskId`，因此每个回合都会在同一对话中打开一个新任务。发送 `taskId` 仅用于添加到仍在运行的任务，例如等待输入的任务。


**LangSmith 跟踪：** Langsmith 部署 A2A 端点会自动将 A2A `contextId` 转换为 `thread_id` 以进行 LangSmith 跟踪，从而将对话中的所有消息分组到单个线程下。


例如：


```python
"""LangGraph A2A conversational agent.

Supports the A2A protocol with messages input for conversational interactions.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, TypedDict

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from openai import AsyncOpenAI


class Context(TypedDict):
    """Context parameters for the agent."""
    my_configurable_param: str


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure for A2A conversational messages.
    """
    messages: List[Dict[str, Any]]


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Process conversational messages and returns output using OpenAI."""
    # Initialize OpenAI client
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Process the incoming messages
    latest_message = state.messages[-1] if state.messages else {}
    user_content = latest_message.get("content", "No message content")

    # Create messages for OpenAI API
    openai_messages = [
        {
            "role": "system",
            "content": "You are a helpful conversational agent. Keep responses brief and engaging."
        },
        {
            "role": "user",
            "content": user_content
        }
    ]

    try:
        # Make OpenAI API call
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=openai_messages,
            max_tokens=100,
            temperature=0.7
        )

        ai_response = response.choices[0].message.content

    except Exception as e:
        ai_response = f"I received your message but had trouble processing it. Error: {str(e)[:50]}..."

    # Create a response message
    response_message = {
        "role": "assistant",
        "content": ai_response
    }

    return {
        "messages": state.messages + [response_message]
    }


# Define the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile()
)
```


## 代理间通信


一旦您的代理通过 `langgraph dev` 或[部署到生产](https://docs.langchain.com/langsmith/deployment) 在本地运行，您就可以使用 A2A 协议促进它们之间的通信。


此示例演示了两个代理如何通过向彼此的 A2A 端点发送 JSON-RPC 消息来进行通信。该脚本模拟多轮对话，其中每个代理处理对方的响应并继续对话。


```python
#!/usr/bin/env python3
"""Agent-to-Agent conversation simulation using the LangGraph A2A endpoint."""

import asyncio
import aiohttp
import os
import uuid


def extract_text(result: dict) -> str:
    """Best-effort extraction of response text from an A2A result."""
    if "error" in result:
        raise RuntimeError(f"A2A error {result['error']['code']}: {result['error']['message']}")

    for art in result.get("result", {}).get("artifacts", []) or []:
        for part in art.get("parts", []) or []:
            if part.get("kind") == "text" and part.get("text"):
                return part["text"]

    msg = (result.get("result", {}).get("status", {}) or {}).get("message", {}) or {}
    for part in msg.get("parts", []) or []:
        if part.get("kind") == "text" and part.get("text"):
            return part["text"]

    return "(no text found)"


async def send_message(session, port, assistant_id, text, context_id=None):
    """Send an A2A message. Returns (response_text, returned_context_id)."""
    url = f"http://127.0.0.1:{port}/a2a/{assistant_id}"

    message = {
        "role": "user",
        "parts": [{"kind": "text", "text": text}],
        "messageId": str(uuid.uuid4()),
    }

    # A2A multi-turn continuity: reuse contextId across turns and agents.
    # Do not reuse taskId — each turn starts a new task within the same context.
    if context_id:
        message["contextId"] = context_id

    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {"message": message},
    }

    headers = {"Accept": "application/json"}
    async with session.post(url, json=payload, headers=headers) as response:
        result = await response.json()

    text = extract_text(result)
    returned_context_id = result.get("result", {}).get("contextId") or context_id
    return text, returned_context_id


async def simulate_conversation():
    """Simulate a conversation between two agents."""

    #Assistant IDs
    agent_a_id = os.getenv("AGENT_A_ID")
    agent_b_id = os.getenv("AGENT_B_ID")

    if not agent_a_id or not agent_b_id:
        print("Set AGENT_A_ID and AGENT_B_ID environment variables")
        return

    message = "Hello! Let's have a conversation."
    context_id = None

    async with aiohttp.ClientSession() as session:
        for i in range(3):
            print(f"--- Round {i + 1} ---")

            message, context_id = await send_message(
                session, 2024, agent_a_id, message, context_id=context_id
            )
            print(f"🔵 Agent A: {message}")

            message, context_id = await send_message(
                session, 2025, agent_b_id, message, context_id=context_id
            )
            print(f"🔴 Agent B: {message}\n")


if __name__ == "__main__":
    asyncio.run(simulate_conversation())
```


 有关完整的工作示例，请参阅：


* [两个 LangGraph 代理进行通信](https://github.com/langchain-samples/A2A-langgraph) - 使用 A2A 协议的两个 LangGraph 代理示例
* [Google ADK 代理与 LangChain 代理](https://github.com/langchain-samples/A2A-google-adk) - Google ADK 代理使用 A2A 协议与 LangChain 代理交互的示例


## 分布式追踪


当多个代理通过 A2A 进行通信时，LangSmith 可以将其所有[痕迹](https://docs.langchain.com/langsmith/observability-concepts#traces) 分组到单个[线程](https://docs.langchain.com/langsmith/observability-concepts#threads) 中，从而为您提供整个多代理对话的统一视图。


### contextId 如何映射到 thread\_id


代理服务器 A2A 端点会自动将 A2A `contextId` 转换为 `thread_id` 以进行 LangSmith 跟踪。这意味着对话中所有参与代理的每条消息都被分组在 LangSmith 中的同一线程下，而无需您进行任何额外的配置。


该流程的工作原理如下：


1. 在第一条消息中，客户端省略了 `contextId`。服务器生成一个并在响应中返回它。
2. 客户端在所有后续消息中传递 `contextId` 以保持会话连续性。
3. 代理服务器将`contextId`映射到LangSmith [元数据](https://docs.langchain.com/langsmith/add-metadata-tags)中的`thread_id`，因此所有回合都出现在同一线程中。


`contextId` 直接用作 LangGraph `thread_id`，因此它必须是 UUID。回显服务器返回的标识符，而不是创建您自己的标识符。 `contextId`（例如 `session-42`）会被拒绝，并显示 `-32602` 和消息 `Failed to create run: Invalid thread ID`。


### 跨多个代理进行追踪


当来自不同框架的代理通过 A2A 进行通信时，`contextId` 可以统一它们的踪迹。将第一个代理在以后的每个请求中返回的 `contextId` 重复使用给该代理和其他代理。


代理服务器不会读取 JSON-RPC 负载上的顶级 `metadata` 字段。客户端无法直接设置 LangGraph `thread_id` — 它始终是 `contextId`。将 `metadata.thread_id` 发送到代理服务器部署没有任何效果。


以下代码片段演示了关键概念。有关两个代理的完整可运行实现，请参阅[Google ADK + LangChain 示例](https://github.com/langchain-samples/A2A-google-adk/blob/main/test_agent_conversation.py)。


```python
import asyncio
import aiohttp
import uuid


async def send_message(session, url, text, context_id=None):
    """Send an A2A message and return (response_text, context_id)."""

    # --- 1. Build the message ---
    # On follow-up turns, include contextId inside the message object so the server
    # associates them with the ongoing conversation. Do not resend taskId: each turn
    # opens a new task within that conversation.
    message = {
        "role": "user",
        "parts": [{"kind": "text", "text": text}],
        "messageId": str(uuid.uuid4()),
    }
    if context_id:
        message["contextId"] = context_id

    # --- 2. Send it ---
    # contextId travels inside the message. Agent Server turns it into the
    # LangGraph thread_id, so no separate tracing field is needed.
    payload = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {"message": message},
    }

    async with session.post(url, json=payload, headers={"Accept": "application/json"}) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}: {await response.text()}")
        result = await response.json()

    if "error" in result:
        raise RuntimeError(result["error"].get("message", "Unknown error"))

    result_obj = result.get("result", {})
    returned_context_id = result_obj.get("contextId") or context_id
    text_out = next(
        (
            part.get("text", "")
            for art in result_obj.get("artifacts", []) or []
            for part in art.get("parts", []) or []
            if part.get("kind") == "text"
        ),
        "(no text)",
    )
    return text_out, returned_context_id


async def run_conversation(agent_a_url, agent_b_url):
    # --- 3. Share the context across agents ---
    # The first response carries a contextId. Pass it to every agent from then
    # on, and all their traces land in one LangSmith thread.
    context_id = None
    message = "Hello! Let's collaborate."

    async with aiohttp.ClientSession() as session:
        for _ in range(3):
            message, context_id = await send_message(
                session, agent_a_url, message, context_id=context_id
            )

            message, context_id = await send_message(
                session, agent_b_url, message, context_id=context_id
            )


asyncio.run(run_conversation(
    "http://localhost:2024/a2a/<agent_a_assistant_id>",
    "http://localhost:2025/a2a/<agent_b_assistant_id>",
))
```


 **1.构建消息**：在后续轮次中将 `contextId` 包含在 `message` 对象内，以便服务器可以将它们与正在进行的对话关联起来。在第一条消息中省略它，因为服务器会生成 `contextId` 并在响应中返回它。请勿在完成回合后重新发送 `taskId`。


**2.发送**：`contextId` 在 `params.message` 内运行。代理服务器将其用作 LangGraph `thread_id`，因此无需设置单独的跟踪字段。


**3.跨代理共享上下文**：让第一个代理创建 `contextId`，然后将相同的值传递给对话其余部分的每个代理。这就是将他们的踪迹分组到一个线程中的原因。


### 在非 LangGraph 代理中接收 thread\_id


[上一节](#tracing-across-multiple-agents)涵盖了客户端——发送消息时传播`contextId`。如果您的代理之一不是基于 LangGraph 构建的，它还需要在接收端读取 `contextId` 并将其附加为线程标识符，以便其跟踪落在同一个 LangSmith 线程中。使用 `langsmith.integrations.otel.configure()` 设置自动跟踪，并从传入的 A2A 请求中读取 `params.message.contextId`。


```python
from fastapi import FastAPI, Request
from langsmith.integrations.otel import configure as configure_otel
from opentelemetry import trace
import json

# --- 1. Configure OTel ---
# Set up automatic tracing to LangSmith for your non-LangGraph agent.
configure_otel(project_name="my-a2a-project")
tracer = trace.get_tracer(__name__)

app = FastAPI()

@app.middleware("http")
async def set_thread_id_middleware(request: Request, call_next):
    thread_id = None
    if request.method == "POST":
        body_bytes = await request.body()
        if body_bytes:
            # --- 2. Extract contextId from the incoming A2A message ---
            try:
                body = json.loads(body_bytes)
                thread_id = body["params"]["message"].get("contextId")
            except (ValueError, KeyError, TypeError):
                pass
            # Re-inject the body so downstream handlers can still read it
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive

    # --- 3. Attach thread_id to the trace ---
    # langsmith.metadata.thread_id groups this trace with others in the same thread.
    with tracer.start_as_current_span("agent") as span:
        if thread_id:
            span.set_attribute("langsmith.metadata.thread_id", thread_id)
        return await call_next(request)
```


 在此中间件之后，在 `app` 上注册您的代理路由。


在您的环境中设置 `LANGSMITH_API_KEY` 和可选的 `LANGSMITH_PROJECT` 以启用跟踪。对话中的所有代理应使用同一项目，以便他们的痕迹一起可见。


### 在 LangSmith 中查看痕迹


运行多代理对话后，打开 [LangSmith UI](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=langsmith-server-a2a) 并导航到 **Threads**。所有参与代理的所有回合都将出现在单个线程下，由共享 `thread_id` 标识。


## 测试您的集成


### 针对您自己的部署


获取卡，然后发送消息：


```bash
curl "https://your-deployment/a2a/{assistant_id}/.well-known/agent-card.json"
```


```bash
curl -X POST "https://your-deployment/a2a/{assistant_id}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "SendMessage",
    "params": {
      "message": {
        "role": "ROLE_USER",
        "parts": [{"text": "hello"}],
        "messageId": "test-1"
      }
    }
  }'
```


 响应包含`result.task.id`和`result.task.contextId`。在下一条消息中重复使用 `contextId` 以继续对话。


对于流式传输，发送 `Accept: text/event-stream` 并使用 `SendStreamingMessage`。第一个事件是 `Task`；状态和工件更新如下。


### 针对官方一致性套件


A2A 在 [a2aproject/a2a-tck](https://github.com/a2aproject/a2a-tck) 上发布了技术兼容性套件。它按 RFC 2119 级别对实施进行分级，并适用于任何 A2A 端点（包括您的端点）。


```bash
./run_tck.py --sut-host https://your-deployment/a2a/{assistant_id} --transport jsonrpc
```


 TCK 通过 `messageId` 前缀驱动某些场景，例如 `tck-input-required`，如 `docs/SUT_REQUIREMENTS.md` 中所述。未实现这些前缀的图表会将这些要求报告为已跳过而不是失败。


### 哪些代理服务器当前出现故障


代理服务器在每个 CI 构建上运行 TCK 作为必需检查，并针对已签入的已知故障列表进行门控。如果出现新的故障，或者列出的要求开始通过，则 CI 会失败，因此列表不会偏离服务器实际执行的操作。


在构建功能之前请阅读以下内容：


|差距|你观察到什么|
| --------------------------------- | ---------------------------------------------------------------------------------------------------- |
|响应线形状仍然是v0.3|任务、消息和部件带有 `kind` 和 `mimeType`，而不是 v1.0 成员存在歧视|
|流媒体事件表现平平|SSE 发出带有 `final` 的 v0.3 对象，而不是 `statusUpdate` / `artifactUpdate` 包装器|
|`tool_results` 是蛇\_case|v1.0 预计为 `toolResults`。故意保留，因为实时 A2UI 客户端会读取此密钥|
|时间戳|序列化为 `+00:00` 而不是 ISO 8601 `Z` 后缀|
|`SubscribeToTask`|返回 `-32601`，其中规范要求 `-32001`|
|推送通知配置|返回 `-32601`，其中规范要求 `-32003`|
|错误不包含 `data`|未附加 `google.rpc.ErrorInfo` 原因或域|
|`A2A-Version` 请求头|未读取，因此处理不受支持的版本而不是返回 `-32009`|
|座席卡缓存|无 `Cache-Control`、`ETag` 或 `Last-Modified` 标头|
|`GetExtendedAgentCard`|已提供服务，但从未通过 `capabilities.extendedAgentCard` 进行广告|


## 禁用 A2A


要禁用 A2A 端点，请在 `langgraph.json` 配置文件中将 `disable_a2a` 设置为 `true`：


```json
{
  "$schema": "https://langgra.ph/schema.json",
  "http": {
    "disable_a2a": true
  }
}
```


 ***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/langsmith/server-a2a.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

