# 模型上下文协议 (MCP)


> 使用基于 FastMCP 构建的 MCPAdapter 将 LangChain 代理连接到 MCP 服务器。


[模型上下文协议 (MCP)](https://modelcontextprotocol.io) 是一种开放协议，它标准化了应用程序如何向语言模型提供工具和上下文。 LangChain代理通过[`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter)调用MCP服务器上定义的工具，它会发现服务器的工具并将它们改编成可以直接传递给[`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent)的LangChain工具。


[`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter) 构建于 [FastMCP](https://gofastmcp.com) 之上，处理传输推断、协议协商、连接管理和身份验证。本节介绍 LangChain 特定层并链接到 FastMCP 客户端文档以了解下面的连接详细信息。


`langchain.mcp` 命名空间需要 `langchain[mcp]>=1.4.0` 并且处于测试阶段。从它导入每个进程都会引发一次 `LangChainBetaWarning` 。 API 可能会更改。


如果您在v1.4.0之前使用过MCP，请参阅[从`langchain-mcp-adapters`迁移](https://docs.langchain.com/oss/python/migrate/langchain-mcp-adapters)。


## 安装


安装带有 `mcp` extra 的 LangChain，它会引入 FastMCP：


```bash
pip install "langchain[mcp]"
```


```bash
uv add "langchain[mcp]"
```


## 快速入门


打开 [`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter)，使用 `list_tools()` 发现服务器的工具，并在上下文中构建代理。这些工具保留客户端，因此代理在上下文退出后仍然可用：


```python
from langchain.agents import create_agent
from langchain.mcp import MCPAdapter


async def main():
    async with MCPAdapter("https://example.com/mcp") as adapter:
        tools = await adapter.list_tools()
        agent = create_agent("claude-sonnet-5", tools)
        return await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```


## 交通


[`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter) 从您提供的目标推断传输，因此进程内服务器、stdio 上的本地脚本和远程 URL 之间唯一发生变化的是目标本身：


```python
from pathlib import Path

from langchain.mcp import MCPAdapter

# An in-process FastMCP server: no subprocess, no socket. Ideal for tests.
in_memory = MCPAdapter(server)  # a FastMCP instance

# A script path is launched over stdio, one subprocess per adapter.
stdio = MCPAdapter(Path("weather_server.py"))

# A string must be an http(s) URL, reached over streamable HTTP.
http = MCPAdapter("https://example.com/mcp")
```


 目标可以是以下任意一个：


* **`http`/`https` URL** (`str`)：通过可流传输的 HTTP 到达。
* **脚本路径** (`Path`)：作为 stdio 上的子进程启动。
* **传输对象** (`StreamableTransport`)：预配置的传输对象。请参阅[客户端传输](https://gofastmcp.com/clients/transports)。
* **进程内 `FastMCP` 服务器**：连接在内存中，没有子进程或套接字。
* **`MCPConfig` 字典** (`{"mcpServers": {...}}`)：一个适配器后面有多个服务器。请参见[连接](https://docs.langchain.com/oss/python/langchain/mcp/connections#multiple-servers)。
* **预构建的 `fastmcp.Client`**：用于完全控制传输、[缓存](https://gofastmcp.com/clients/client#response-caching) 和[协议协商](https://gofastmcp.com/clients/client#protocol-negotiation)。


`str` 目标必须是 `http` 或 `https` URL。 FastMCP 通过在将字符串测试为 URL 之前将其测试为文件系统路径来解析字符串，因此命名现有 `.py` 或 `.js` 文件的字符串会将该文件作为子进程启动。由于字符串是目标最常从配置或模型到达的形式，因此 [`MCPAdapter`](https://reference.langchain.com/python/langchain/mcp/adapter/MCPAdapter) 会拒绝与 URL 形状不匹配的字符串。


## 后续步骤


  
**连接**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/mcp/connections)


连接生命周期、多个服务器、协议时代和缓存。

  


  
**验证**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/mcp/auth)


不记名令牌、OAuth 2.1 和每用户服务器身份验证。

  


  
**工具**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/mcp/tools)


将 MCP 工具加载到代理中，控制其执行并处理其输出。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/langchain/mcp/index.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

