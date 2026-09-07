# 型号


> 为深度智能体配置模型提供程序和参数


深度智能体可与任何支持[工具调用](https://docs.langchain.com/oss/python/langchain/models#tool-calling)的[LangChain聊天模型](https://docs.langchain.com/oss/python/langchain/models)配合使用。


## 支持机型


以 `provider:model` 格式指定模型（例如，`google_genai:gemini-3.6-flash`、`openai:gpt-5.4` 或 `anthropic:claude-sonnet-4-6`）。提供者前缀选择 LangChain 集成，冒号后面的所有内容都会作为模型标识符传递给该提供者。有关有效的提供程序字符串，请参阅 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 的 `model_provider` 参数。有关特定于提供商的配置，请参阅[聊天模型集成](https://docs.langchain.com/oss/python/integrations/chat)。


模型标识符必须与提供者期望的格式匹配。一些提供商使用简单的名称，例如 `gpt-5.5`；其他人使用命名空间 ID 或部署路径（如 `zai-org/GLM-5.2`），因此完整的 Deep Agents 字符串将为 `baseten:zai-org/GLM-5.2`。检查提供商的模型目录或集成文档以获取当前标识符。


### 推荐型号


这些模型在测试基本代理操作的[深度智能体评估套件](https://github.com/langchain-ai/deepagents/tree/main/libs/evals#readme) 上表现良好。通过这些评估是必要的，但不足以在更长、更复杂的任务中表现出色。


|提供者|型号|
| --------------------------------------------------------- | ------------------------------------------------------- |
|[Google](https://docs.langchain.com/oss/python/integrations/providers/google)|`gemini-3.1-pro-preview`、`gemini-3.6-flash`|
|[OpenAI](https://docs.langchain.com/oss/python/integrations/providers/openai)|`gpt-5.5`、`gpt-5.4`|
|[Anthropic](https://docs.langchain.com/oss/python/integrations/providers/anthropic)|`claude-opus-4-8`、`claude-opus-4-7`、`claude-opus-4-6`|
|自由重量|`GLM-5.2`、`Kimi-K2.7 Code`、`MiniMax-M3`|


开放重量模型可通过 [Baseten](https://docs.langchain.com/oss/python/integrations/providers/baseten)、[Fireworks](https://docs.langchain.com/oss/python/integrations/chat/fireworks)、[OpenRouter](https://docs.langchain.com/oss/python/integrations/providers/openrouter) 和 [Ollama](https://docs.langchain.com/oss/python/integrations/providers/ollama) 等提供商获得。


### 模型评估


[Deep Agents 评估套件](https://github.com/langchain-ai/deepagents/tree/main/libs/evals#readme) 测试流行模型：


<div className="deepagents-eval-category-matrix">
|模型|全面的|文件操作|检索|工具使用|记忆|对话|总结|
  | :----------------------------------------------- | -----------------------------------------------------------------------------: | ------------------------------------------------------------------------------: | ------------------------------------------------------------------------------: | -----------------------------------------------------------------------------: | -----------------------------------------------------------------------------: | -----------------------------------------------------------------------------: | ------------------------------------------------------------------------------: |
|google\_genai:gemini-3.6-flash|[82%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|**[90%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|[54%](https://github.com/langchain-ai/deepagents/actions/runs/25290479270)|[38%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|
|openai:gpt-5.4|[18%](https://github.com/langchain-ai/deepagents/actions/runs/24906955930)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|[18%](https://github.com/langchain-ai/deepagents/actions/runs/24906955930)|[51%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)|[38%](https://github.com/langchain-ai/deepagents/actions/runs/24425363630)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|
|openai:gpt-5.5|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|[92%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|[84%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|[64%](https://github.com/langchain-ai/deepagents/actions/runs/25345307822)|**[52%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|
|anthropic:claude-opus-4-6|[26%](https://github.com/langchain-ai/deepagents/actions/runs/24906955930)|[92%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|[26%](https://github.com/langchain-ai/deepagents/actions/runs/24906955930)|**[69%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|[22%](https://github.com/langchain-ai/deepagents/actions/runs/24363491527)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/24172638583)**|
|anthropic:claude-opus-4-7|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|[82%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|—|[48%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|
|baseten:moonshotai/Kimi-K2.6|[79%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)|[92%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)**|[84%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)|—|[43%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)|[60%](https://github.com/langchain-ai/deepagents/actions/runs/25475600906)|
|baseten:zai-org/GLM-5|[77%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)**|[89%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)|[44%](https://github.com/langchain-ai/deepagents/actions/runs/23872647281)|[24%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)|[60%](https://github.com/langchain-ai/deepagents/actions/runs/25403850424)|
|fireworks:accounts/fireworks/models/glm-5p1|[81%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)**|[87%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)|—|[33%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25461031650)|
|fireworks:accounts/fireworks/models/minimax-m2p7|[79%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)**|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)**|[85%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)|—|[43%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)|[60%](https://github.com/langchain-ai/deepagents/actions/runs/25403894412)|
|ollama:minimax-m2.7:cloud|[73%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|[92%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|[90%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|[82%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|[38%](https://github.com/langchain-ai/deepagents/actions/runs/23872647281)|[29%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|[60%](https://github.com/langchain-ai/deepagents/actions/runs/24106499785)|
|openrouter:deepseek/deepseek-v4-flash|[81%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)**|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)|**[90%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)**|—|[33%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25677815395)|
|openrouter:minimax/minimax-m2.7|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|[92%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)**|[89%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|—|[43%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|[60%](https://github.com/langchain-ai/deepagents/actions/runs/25455998535)|
|openrouter:z-ai/glm-5.1|**[89%](https://github.com/langchain-ai/deepagents/actions/runs/25387853856)**|[92%](https://github.com/langchain-ai/deepagents/actions/runs/25234719085)|**[100%](https://github.com/langchain-ai/deepagents/actions/runs/25234686782)**|[89%](https://github.com/langchain-ai/deepagents/actions/runs/25387853856)|—|[33%](https://github.com/langchain-ai/deepagents/actions/runs/25225620506)|[80%](https://github.com/langchain-ai/deepagents/actions/runs/25235579950)|
</div>


有关详细信息，请参阅[评估运行](https://github.com/langchain-ai/deepagents/actions/workflows/evals.yml)。


## 配置模型参数


以 `provider:model` 格式将模型字符串传递到 [`create_deep_agent`](https://reference.langchain.com/python/deepagents/graph/create_deep_agent)，或传递已配置的模型实例以实现完全控制。在底层，模型字符串通过 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 解析。


要配置特定于模型的参数，请使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 或直接实例化提供程序模型类：


```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

model = init_chat_model(
    model="google_genai:gemini-3.6-flash",
    thinking_level="medium",  # [!code highlight]
)
agent = create_deep_agent(model=model)
```


```python
from langchain_google_genai import ChatGoogleGenerativeAI
from deepagents import create_deep_agent

model = ChatGoogleGenerativeAI(
    model="gemini-3.1-pro-preview",
    thinking_level="medium",  # [!code highlight]
)
agent = create_deep_agent(model=model)
```


 可用参数因提供商而异。有关特定于提供商的配置选项，请参阅[聊天模型集成](https://docs.langchain.com/oss/python/integrations/chat) 页面。


### 提供商简介


[`ProviderProfile`](profiles.md#provider-profiles) 封装初始化参数，当您在创建深度智能体时提供 `provider:model` 字符串时，会应用这些初始化参数。当您通过 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 传递预配置模型时，它不适用。


您可以在两个级别上注册，并且两者可以共存：


* **提供商级别**：像 `"openai"` 这样的裸提供商密钥适用于 `openai` 提供商的每个模型。
* **型号级别**：`provider:model` 密钥（例如 `"openai:gpt-5.4"`）仅适用于该特定型号，并合并在任何匹配的提供商级别配置文件之上。


```python
from deepagents import ProviderProfile, register_provider_profile

# Provider-wide default: every openai model gets temperature=0.
register_provider_profile(
    "openai",
    ProviderProfile(init_kwargs={"temperature": 0}),
)

# Model-level override: gpt-5.5 additionally gets a specific reasoning effort.
# Inherits temperature=0 from the provider-level profile above.
register_provider_profile(
    "openai:gpt-5.5",
    ProviderProfile(init_kwargs={"reasoning_effort": "medium"}),
)
```


 有关完整字段列表、合并语义和插件打包，请参阅[配置文件](profiles.md)。


要确定模型构建后*代理*的行为方式，请使用[线束配置文件](profiles.md#harness-profiles)。


## 在运行时选择模型


如果您的应用程序允许用户选择模型（例如使用 UI 中的下拉菜单），请使用 [中间件](https://docs.langchain.com/oss/python/langchain/middleware) 在运行时交换模型，而无需重建代理。


通过 [运行时上下文](https://docs.langchain.com/oss/python/langchain/models#dynamic-model-selection) 传递用户的模型选择，然后使用 `wrap_model_call` 中间件在每次调用时使用 [`@wrap_model_call`](https://reference.langchain.com/python/langchain/agents/middleware/types/wrap_model_call) 装饰器覆盖模型：


```python
from dataclasses import dataclass
from typing import Callable

from langchain.agents.middleware import ModelRequest, ModelResponse, wrap_model_call
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent


@dataclass
class Context:
    model: str


@wrap_model_call
def configurable_model(
    request: ModelRequest,
    handler: Callable[[ModelRequest], ModelResponse],
) -> ModelResponse:
    model_name = request.runtime.context.model
    model = init_chat_model(model_name)
    return handler(request.override(model=model))


agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    middleware=[configurable_model],
    context_schema=Context,
)

# Invoke with the user's model selection
result = agent.invoke(
    {"messages": [{"role": "user", "content": "Hello!"}]},
    context=Context(model="openai:gpt-5.5"),
)
```


 更多动态模型模式（例如基于会话复杂度或成本优化的路由），请参阅LangChain代理指南中的[动态模型](https://docs.langchain.com/oss/python/langchain/models#dynamic-model-selection)。


## 了解更多


* [LangChain中的模型](https://docs.langchain.com/oss/python/langchain/models)：聊天模型功能包括工具调用、结构化输出和多模态


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/models.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

