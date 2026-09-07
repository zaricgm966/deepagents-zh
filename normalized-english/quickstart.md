
# Quickstart

> Build your first deep agent in minutes

This guide walks you through creating your first deep agent with file system tools and subagent capabilities. You will build a research agent that can conduct research and write reports.

  **Using an AI coding assistant?**

  * Install the [LangChain Docs MCP server](/use-these-docs) to give your agent access to up-to-date LangChain documentation and examples.
  * Install [LangChain Skills](https://github.com/langchain-ai/langchain-skills) to improve your agent's performance on LangChain ecosystem tasks.

## Prerequisites

Before you begin, make sure you have an API key from a model provider (e.g., Gemini, Anthropic, OpenAI).

  Deep Agents require a model that supports [tool calling](/oss/python/langchain/models#tool-calling). See [customization](/oss/python/deepagents/customization#model) for how to configure your model.

## Step 1: Install dependencies

```bash
pip install deepagents
```

```bash
uv init
uv add deepagents
uv sync
```

  Google, OpenAI, and Anthropic all provide built-in web search tools: no extra package or API key required. If you use a different provider or prefer [Tavily](https://tavily.com/) for search, install the Tavily package as well:


```bash
pip install tavily-python
```

## Step 2: Set up your API keys

  
**Google**

```bash
export GOOGLE_API_KEY="your-api-key"
```


  


  
**OpenAI**

```bash
export OPENAI_API_KEY="your-api-key"
```


  


  
**Anthropic**

```bash
export ANTHROPIC_API_KEY="your-api-key"
```


  


  
**OpenRouter**

```bash
export OPENROUTER_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  
**Fireworks**

```bash
export FIREWORKS_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  
**Baseten**

```bash
export BASETEN_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  
**Ollama**

```bash
# Local: Ollama must be running on your machine
# Cloud: Set your Ollama API key for hosted inference
export OLLAMA_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


  


  
**Other**

```bash
# Set the API key for your provider
export <PROVIDER>_API_KEY="your-api-key"
export TAVILY_API_KEY="your-tavily-api-key"
```


    Deep Agents work with any [LangChain chat model](/oss/python/deepagents/models#supported-models). Set the API key for your provider.
  

  **Using LangSmith Gateway**

  The [LangSmith Gateway](/langsmith/llm-gateway) routes most major providers through LangSmith. You can [bring your own provider keys](/langsmith/llm-gateway-quickstart#2-make-a-call), or use [Gateway Credits](/langsmith/llm-gateway-credits) to access models without a provider key.

## Step 3: Create a search tool

Google, OpenAI, and Anthropic offer built-in web search tools that run server-side: no extra package or API key needed. Pass a provider tool dict directly to `create_deep_agent`.

  
**Provider search (recommended)**

    

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


    

  


  
**Tavily (any provider)**

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


  

## Step 4: Create a deep agent

Pass your search tool and model to `create_deep_agent`. Pass a `model` string in `provider:model` format, or an [initialized model instance](/oss/python/deepagents/models#configure-model-parameters). See [supported models](/oss/python/deepagents/models#supported-models) for all providers and [suggested models](/oss/python/deepagents/models#suggested-models) for tested recommendations.

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

## Step 5: Set up LangSmith tracing

[LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-deepagents-quickstart) provides you with visibility into your agent's execution, allowing you to view tool calls, subagent delegation, and LLM responses.

Sign up at [smith.langchain.com](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-deepagents-quickstart), create an API key, and set these environment variables:


```bash
export LANGSMITH_TRACING=true
export LANGSMITH_API_KEY="your-langsmith-api-key"
```


## Step 6: Run the agent


```python
result = agent.invoke({"messages": [{"role": "user", "content": "What is langgraph?"}]})

# Print the agent's response
print(result["messages"][-1].content)
```


## How does it work?

Your deep agent automatically:

1. **Conducts research** by calling the `internet_search` tool to gather information.
2. **Manages context** by using file system tools ([`write_file`](/oss/python/deepagents/overview#virtual-filesystem-access), [`read_file`](/oss/python/deepagents/overview#virtual-filesystem-access)) to offload large search results.
3. **Spawns subagents** as needed to delegate complex subtasks to specialized subagents.
4. **Synthesizes a report** to compile findings into a coherent response.

To add structured task planning with `write_todos`, opt in with [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware). See [Task planning](/oss/python/deepagents/overview#task-planning).

## Examples

For agents, patterns, and applications you can build with Deep Agents, see [Examples](https://github.com/langchain-ai/deepagents/tree/main/examples).

## Streaming

Deep Agents have built-in [streaming](/oss/python/langchain/event-streaming) for real-time updates from agent execution using LangGraph.
This allows you to observe output progressively and review and debug agent and subagent work, such as tool calls, tool results, and LLM responses.

## Next steps

Now that you've built your first deep agent:

* **Customize your agent**: Learn about [customization options](/oss/python/deepagents/customization), including custom system prompts, tools, and subagents.
* **Add long-term memory**: Enable [persistent memory](/oss/python/deepagents/memory) across conversations.
* **Deploy to production**: Use [Managed Deep Agents](/langsmith/python/managed-deep-agents-overview) to create, run, and operate deep agents in LangSmith.
* **Test and evaluate**: Use [LangSmith evaluation](/langsmith/evaluation-quickstart) to run automated tests and measure your agent's performance against a dataset.

***

<div className="source-links">
  

    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  


  

    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/quickstart.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  

</div>
