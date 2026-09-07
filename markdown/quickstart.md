# 快速入门


> 在几分钟内构建您的第一个深度智能体


本指南将引导您使用文件系统工具和子智能体功能创建第一个深度智能体。您将建立一个可以进行研究和撰写报告的研究代理。


**使用人工智能编码助手？**


  * 安装[LangChain Docs MCP 服务器](https://docs.langchain.com/use-these-docs)，让您的代理能够访问最新的 LangChain 文档和示例。
  * 安装[LangChain技能](https://github.com/langchain-ai/langchain-skills)以提高代理在LangChain生态系统任务上的性能。


## 先决条件


在开始之前，请确保您拥有模型提供商（例如 Gemini、Anthropic、OpenAI）提供的 API 密钥。


深度智能体需要支持[工具调用](https://docs.langchain.com/oss/python/langchain/models#tool-calling)的模型。请参阅[自定义](customization.md#model)了解如何配置您的模型。


## 第1步：安装依赖项


```bash
pip install deepagents
```


```bash
uv init
uv add deepagents
uv sync
```


 Google、OpenAI 和 Anthropic 都提供内置网络搜索工具：无需额外的软件包或 API 密钥。如果您使用不同的提供商或更喜欢 [Tavily](https://tavily.com/) 进行搜索，请同时安装 Tavily 软件包：


```bash
pip install tavily-python
```


## 第 2 步：设置您的 API 密钥


  
**谷歌**


```bash
export GOOGLE_API_KEY="your-api-key"
```


  


  

 **开放人工智能**


```bash
export OPENAI_API_KEY="your-api-key"
```


  


  

 **人择**


```bash
export ANTHROPIC_API_KEY="your-api-key"
```


  


  

 **开放路由器**


```bash
export OPENROUTER_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  

 **烟花**


```bash
export FIREWORKS_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  

 **巴斯坦**


```bash
export BASETEN_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  

 **奥拉马**


```bash
# Local: Ollama must be running on your machine
# Cloud: Set your Ollama API key for hosted inference
export OLLAMA_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  

 **其他**


```bash
# Set the API key for your provider
export <PROVIDER>_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


 深度智能体可与任何 [LangChain 聊天模型](models.md#supported-models) 配合使用。为您的提供商设置 API 密钥。

  

**使用 LangSmith 网关**


[LangSmith 网关](https://docs.langchain.com/langsmith/llm-gateway) 通过 LangSmith 路由大多数主要提供商。您可以[自带提供商密钥](https://docs.langchain.com/langsmith/llm-gateway-quickstart#2-make-a-call)，或使用[网关积分](https://docs.langchain.com/langsmith/llm-gateway-credits)在没有提供商密钥的情况下访问模型。


## 第三步：创建搜索工具


Google、OpenAI 和 Anthropic 提供在服务器端运行的内置网络搜索工具：无需额外的软件包或 API 密钥。将提供程序工具字典直接传递给 `create_deep_agent`。


  
**提供商搜索（推荐）**


    


```python
from deepagents import create_deep_agent

# Google's built-in search — no extra install or API key needed
internet_search = {"google_search": {}}
```


```python
from deepagents import create_deep_agent

# OpenAI's built-in web search — no extra install or API key needed
internet_search = {"type": "web_search"}
```


```python
from deepagents import create_deep_agent

# Anthropic's built-in web search — no extra install or API key needed
internet_search = {"type": "web_search_20260209", "name": "web_search"}
```


    

  


  

 **Tavily（任何提供商）**


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
```


  


## 第 4 步：创建深度智能体


将您的搜索工具和型号传递给 `create_deep_agent`。传递 `provider:model` 格式的 `model` 字符串，或 [初始化的模型实例](models.md#configure-model-parameters)。请参阅[支持的型号](models.md#supported-models) 了解所有提供商，并参阅[建议的型号](models.md#suggested-models) 了解经过测试的建议。


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="openai:gpt-5.5",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


```python
# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    tools=[internet_search],
    system_prompt=research_instructions,
)
```


## 第 5 步：设置 LangSmith 跟踪


[LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-deepagents-quickstart) 为您提供代理执行的可见性，允许您查看工具调用、子智能体委托和 LLM 响应。


在 [smith.langchain.com](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-deepagents-quickstart) 注册，创建 API 密钥，并设置以下环境变量：


```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="your-langsmith-api-key"
```


## 第 6 步：运行代理


```python
result = agent.invoke({"messages": [{"role": "user", "content": "What is langgraph?"}]})

# Print the agent's response
print(result["messages"][-1].content)
```


## 它是如何运作的？


您的深度智能体会自动：


1. **通过调用 `internet_search` 工具收集信息来进行研究**。
2. **通过使用文件系统工具（[`write_file`](overview.md#virtual-filesystem-access)、[`read_file`](overview.md#virtual-filesystem-access)）来卸载大型搜索结果来管理上下文。
3. **根据需要生成子智能体**，将复杂的子任务委托给专门的子智能体。
4. **综合报告**将调查结果汇编成连贯的回应。


要使用 `write_todos` 添加结构化任务计划，请选择使用 [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware)。参见[任务规划](overview.md#task-planning)。


## 示例


有关可以使用深度智能体构建的代理、模式和应用程序，请参阅[示例](https://github.com/langchain-ai/deepagents/tree/main/examples)。


## 流媒体


深度智能体具有内置的[流](https://docs.langchain.com/oss/python/langchain/event-streaming)，用于使用 LangGraph 从代理执行中进行实时更新。这使您可以逐步观察输出并检查和调试代理和子智能体的工作，例如工具调用、工具结果和 LLM 响应。


## 后续步骤


现在您已经构建了第一个深度智能体：


* **自定义您的代理**：了解[自定义选项](customization.md)，包括自定义系统提示、工具和子智能体。
* **添加长期记忆**：跨对话启用[持久记忆](memory.md)。
* **部署到生产**：使用[托管深度智能体](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview) 在 LangSmith 中创建、运行和操作深度智能体。
* **测试和评估**：使用 [LangSmith 评估](https://docs.langchain.com/langsmith/evaluation-quickstart) 运行自动化测试并根据数据集衡量代理的性能。


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/quickstart.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

