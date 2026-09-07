# 工具


> 将 Deep Agent 连接到自定义函数、API、数据库和任何 MCP 服务器


深度智能体可以调用​​您定义的任何工具、任何[LangChain工具](https://python.langchain.com/docs/concepts/tools/)以及来自任何[MCP服务器](#mcp-tools)的工具。通过 `tools=` 参数以及[内置线束工具](overview.md#execution-environment) 将它们传递给 `create_deep_agent`，以进行文件管理和子智能体生成。


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="openai:gpt-5.5",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    tools=[search, fetch_url, run_query],
)
```


```python
from deepagents import create_deep_agent


agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    tools=[search, fetch_url, run_query],
)
```


## 定制工具


将任何可调用的（例如普通函数、LangChain `@tool` 修饰的函数或工具字典）直接传递给 `tools=`。 Deep Agents 从函数签名和文档字符串推断工具架构，因此在大多数情况下您不需要定义单独的架构。


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="openai:gpt-5.5",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    tools=[internet_search],
)
```


```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])


def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    tools=[internet_search],
)
```


 有关定义和使用 LangChain 工具（工具字典、`StructuredTool`、返回类型、错误处理等）的完整详细信息，请参阅[工具](https://docs.langchain.com/oss/python/langchain/tools)。


## MCP工具


Deep Agents 完全支持 [模型上下文协议 (MCP)](https://docs.langchain.com/oss/python/langchain/mcp)，这是用于将代理连接到外部服务的开放标准。从任何 MCP 服务器加载工具并将其直接传递到 `create_deep_agent`。


MCP 是一种开放协议，允许代理通过标准接口连接到不断增长的服务器生态系统（数据库、API、文件系统、浏览器等）。您无需为每个服务编写自定义集成代码，而是将深度智能体指向 MCP 服务器，它会获取服务器公开的所有工具。


安装 LangChain 并附加 `mcp` 以连接到 MCP 服务器：


```bash
pip install "langchain[mcp]"
```


```bash
uv add "langchain[mcp]"
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="google_genai:gemini-3.6-flash",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="openai:gpt-5.5",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="anthropic:claude-sonnet-5",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="openrouter:z-ai/glm-5.2",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="fireworks:accounts/fireworks/models/glm-5p2",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="baseten:zai-org/GLM-5.2",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


```python
import asyncio

from deepagents import create_deep_agent
from langchain.mcp import MCPAdapter


async def main():
    config = {"mcpServers": {"my_server": {"url": "http://localhost:8000/mcp"}}}
    async with MCPAdapter(config) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model="ollama:north-mini-code-1.0",
            tools=tools,
        )
        await agent.ainvoke(
            {
                "messages": [
                    {"role": "user", "content": "Use the MCP server to help me."}
                ]
            },
            config={"configurable": {"thread_id": "1"}},
        )
```


 有关详细的配置选项（包括 stdio 服务器、OAuth 身份验证、工具过滤和有状态会话），请参阅完整的 [MCP 指南](https://docs.langchain.com/oss/python/langchain/mcp)。


## 内置线束工具


除了您提供的工具之外，每个 Deep Agent 还附带来自线束的一组内置工具：


|工具|描述|
| ------------ | --------------------------------------------------------------------------------------------------------- |
|`ls`|列出目录中的文件。|
|`read_file`|读取文件内容（具有分页和多模式支持）。|
|`write_file`|创建一个新文件，或覆盖现有文件。|
|`edit_file`|在文件中执行精确的字符串替换。|
|`delete`|递归删除文件或目录及其内容。 `delete` 工具需要 `deepagents>=0.7`。|
|`glob`|查找与 glob 模式匹配的文件。|
|`grep`|搜索文件内容。|
|`execute`|运行 shell 命令（仅限沙箱后端）。|
|`task`|生成一个子智能体来处理委托的任务。|


要使用 `write_todos` 添加结构化任务计划，请选择使用 [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware)。参见[任务规划](overview.md#task-planning)。


有关每个内置工具功能的完整详细信息，请参阅[线束概述](overview.md#execution-environment)。


## 多模式工具输出


当所选模型支持多模式工具结果时，自定义工具可以返回纯文本或[标准内容块](https://docs.langchain.com/oss/python/langchain/messages#standard-content-blocks)（文本、图像、音频、视频和文件）。内置 `read_file` 工具还返回支持的非文本文件类型的多模式块。


返回纯文本结果的字符串，或文本加媒体或交错多模式输出的内容块的有序列表。有关示例和上下文压缩注意事项，请参阅[多模式](multimodal.md) 和[工具返回值](https://docs.langchain.com/oss/python/langchain/tools#return-multimodal-content)。


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/tools.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

