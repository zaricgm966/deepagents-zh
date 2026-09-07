# 代理客户端协议 (ACP)


> 通过代理客户端协议 (ACP) 公开深度智能体，以与代码编辑器和 IDE 集成。


[代理客户端协议 (ACP)](https://agentclientprotocol.com/get-started/introduction) 标准化编程智能体与代码编辑器或 IDE 之间的通信。通过 ACP 协议，您可以将自定义深度智能体与任何 ACP 兼容的客户端结合使用，从而允许您的代码编辑器提供项目上下文并接收丰富的更新。


ACP 专为代理编辑器集成而设计。如果您希望代理调用外部服务器托管的工具，请参阅[模型上下文协议 (MCP)](https://docs.langchain.com/oss/python/langchain/mcp/)。


## 快速入门


安装ACP集成包：


```bash
pip install deepagents-acp
```


```bash
uv add deepagents-acp
```


 然后通过 ACP 暴露深度智能体。


这会在 stdio 模式下启动 ACP 服务器（它从 stdin 读取请求并将响应写入 stdout）。在实践中，您通常将其作为 ACP 客户端（例如您的编辑器）启动的命令运行，然后通过 stdio 与服务器进行通信。


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="google_genai:gemini-3.6-flash",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="openai:gpt-5.5",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="openrouter:z-ai/glm-5.2",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="fireworks:accounts/fireworks/models/glm-5p2",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="baseten:zai-org/GLM-5.2",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


```python
import asyncio

from acp import run_agent
from deepagents import create_deep_agent
from langgraph.checkpoint.memory import MemorySaver

from deepagents_acp.server import AgentServerACP


async def main() -> None:
    agent = create_deep_agent(
        model="ollama:north-mini-code-1.0",
        # You can customize your deep agent here: set a custom prompt,
        # add your own tools, attach middleware, or compose subagents.
        system_prompt="You are a helpful coding assistant",
        checkpointer=MemorySaver(),
    )

    server = AgentServerACP(agent)
    await run_agent(server)

if __name__ == "__main__":
    asyncio.run(main())
```


 **编程智能体示例**


[查看相关页面](https://github.com/langchain-ai/deepagents/blob/main/libs/acp/examples/demo_agent.py)


`deepagents-acp` 软件包包含一个带有文件系统和 shell 的示例编程智能体，您可以开箱即用。


## 客户


深度智能体可以在任何可以运行 ACP 代理服务器的地方工作。一些著名的 ACP 客户包括：


* [Zed](https://zed.dev/docs/ai/external-agents)
* [JetBrains IDE](https://www.jetbrains.com/help/ai-assistant/acp.html)
* Visual Studio Code（通过 [vscode-acp](https://github.com/formulahendry/vscode-acp)）
* Neovim（通过 ACP 兼容插件）


### 泽德


`deepagents` 存储库包含 [演示 ACP 入口点](https://github.com/langchain-ai/deepagents/blob/main/libs/acp/run_demo_agent.sh)，您可以通过 [Zed](https://zed.dev/docs/ai/external-agents) 注册：


1. 克隆 `deepagents` 存储库并安装依赖项：


```bash
git clone https://github.com/langchain-ai/deepagents.git
cd deepagents/libs/acp
uv sync --all-groups
chmod +x run_demo_agent.sh
```


2. 配置演示代理的凭据：


```bash
cp .env.example .env
```


 然后将`ANTHROPIC_API_KEY`设置为`.env`。


3. 在 Zed 的 `settings.json` 中配置 ACP 代理服务器命令：


```json
{
  "agent_servers": {
    "DeepAgents": {
      "type": "custom",
      "command": "/your/absolute/path/to/deepagents/libs/acp/run_demo_agent.sh"
    }
  }
}
```


4. 打开 Zed 的 Agents 面板并启动 Deep Agents 线程。


### 蟾蜍


如果您想将 ACP 代理服务器作为本地开发工具运行，可以使用 [Toad](https://github.com/batrachianai/toad) 来管理该进程。


```bash
uv tool install -U batrachian-toad

toad acp "python path/to/your_server.py" .
# or
toad acp "uv run python path/to/your_server.py" .
```


 有关协议详细信息和编辑器支持，请参阅上游 ACP 文档：


  * 简介：【https://agentclientprotocol.com/get-started/introduction](https://agentclientprotocol.com/get-started/introduction）
  * 客户/编辑：[https://agentclientprotocol.com/get-started/clients](https://agentclientprotocol.com/get-started/clients)


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/acp.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

