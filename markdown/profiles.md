# 型材


> 选择模型时 Deep Agents 应用的按提供商和按模型默认的软件包


**利用配置文件**让您可以打包每当选择给定提供程序或特定模型时 Deep Agents 应用的配置：系统提示调整、工具描述覆盖、排除的工具或中间件、额外的中间件和通用子智能体编辑。它们是在不更改 `create_deep_agent` 调用站点的情况下调整特定模型线束行为方式的主要方法。在Python中构建配置文件时使用`HarnessProfile`； [加载或保存 YAML/JSON 文件](#load-profiles-from-config-files) 时使用 `HarnessProfileConfig`。 Deep Agents 为 OpenAI 和 Anthropic (Claude) 模型提供了内置的线束配置文件。


**提供者配置文件**是*模型构造* kwargs 的较窄配套 API，它不会影响线束。大多数呼叫者不需要它们；当您希望 `init_chat_model` 默认值、凭据检查或运行时派生的 kwargs 作为您选择的提供程序的默认值时（例如，打包提供程序集成时），请选择其中之一。


## 线束型材


`HarnessProfile` 描述了 `create_deep_agent` 在构建聊天模型后应用的提示组装、工具可见性、中间件和默认子智能体调整：


```python
from deepagents import (
    GeneralPurposeSubagentProfile,
    HarnessProfile,
    register_harness_profile,
)

register_harness_profile(
    "openai:gpt-5.5",
    HarnessProfile(
        system_prompt_suffix="Respond in under 100 words.",
        excluded_tools={"execute"},
        excluded_middleware={"SummarizationMiddleware"},
        general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False),
    ),
)
```


 **基本系统提示**


替换基本 Deep Agents 系统提示符（[系统提示符](customization.md#system-prompt) 中的 `base` 密钥）。


**系统提示符后缀**


在调用者的 `suffix` 之后附加文本，放在组装的系统提示符的最后。应用于主代理、声明性子智能体和自动添加的通用子智能体。


**工具描述_覆盖**


覆盖按工具名称键入的各个工具描述。


**排除的工具**


从工具集中删除特定的线束级工具。按工具名称（字符串）匹配，用作注入后过滤器，以便它可以删除用户提供的工具和由线束中间件添加的工具。请参阅[不使用默认文件系统工具运行](overview.md#virtual-filesystem-access) 以获取有效示例。


**排除的中间件**


从[深度智能体堆栈](customization.md#deep-agents-stack) 中剥离特定的中间件类。接受中间件类或字符串名称。


**额外的中间件**


将中间件附加到此配置文件适用的每个堆栈。有关内置排序，请参阅[深度智能体堆栈](customization.md#full-stack)。


**通用子智能体**


禁用、重命名或重新提示通用子智能体。当此字段的 `system_prompt` 与 `base_system_prompt` 一起设置时，通用特定子智能体提示将获胜 - 请参阅[通用子智能体提示](customization.md#general-purpose-subagent-prompt)。


呼叫者提供的 `system_prompt=` 始终位于组合提示符的前面，而 ​​`system_prompt_suffix` 始终位于末尾 — 无论选择哪种型号。相同的覆盖规则适用于子智能体：每个子智能体针对其自己的模型重新运行配置文件解析。请参阅[系统提示](customization.md#system-prompt) 了解每个案例的完整细分（主代理、子智能体和通用子智能体）。


要在不使用 `task` 工具的情况下运行代理，请参阅[在没有子智能体的情况下运行](subagents.md#running-without-subagents) — 设置 `general_purpose_subagent=GeneralPurposeSubagentProfile(enabled=False)` 并通过 `subagents=` 不传递任何同步子智能体。 `SubAgentMiddleware`（和 `task` 工具）仅在至少存在一个同步子智能体时才附加，因此此配置将其完全排除。异步子智能体不受影响。


列出 `FilesystemMiddleware`、`SubAgentMiddleware` 或 `excluded_middleware` 中的内部权限中间件会引发 `ValueError` — 它们是 [深度智能体堆栈](customization.md#deep-agents-stack) 中所需的脚手架。要在模型中隐藏其工具而不删除中间件，请改用 `excluded_tools` — 请参阅[在不使用默认文件系统工具的情况下运行](overview.md#virtual-filesystem-access)。


`excluded_middleware` 中的条目接受两种形式：


* 中间件*类*（按确切类型匹配），或匹配 `AgentMiddleware.name` 的纯字符串。对内置别名和公共别名使用纯字符串，例如 `"SummarizationMiddleware"`。
* `module:Class` 导入引用（例如，`"my_pkg.middleware:TelemetryMiddleware"`）用于从配置文件中定位精确的中间件类。导入引用会延迟解析，因此仅将它们用于受信任的本地配置 - 加载一个导入 Python 代码。


**预配置模型实例的查找顺序**


当您传递预配置的聊天模型实例而不是 `provider:model` 字符串时，该工具会从该实例合成规范的 `provider:identifier` 密钥，并按以下顺序查找它：


  1. 完全匹配 `provider:identifier`
  2. 仅标识符（仅当标识符已包含 `:` 时）
  3. 仅提供者的后备


## 注册码


两种配置文件类型使用相同的密钥格式：


* **提供商级别** - 像 `"openai"` 这样的裸提供商名称适用于该提供商的每个模型。
* **型号级别** — 完全合格的 `provider:model` 密钥（如 `"openai:gpt-5.5"`）仅适用于该特定型号。


当提供程序级别和模型级别配置文件同时存在时，它们会在解析时合并。未设置的模型级字段继承自提供者级配置文件；显式模型级值会覆盖它们。


在现有密钥下重新注册会将新配置文件合并到之前的配置文件之上，但不会替换它。有关每个字段的规则，请参阅[合并语义](#merge-semantics)。


没有与每个提供商匹配的通配符密钥。要在各处应用相同的覆盖（例如，无论选择哪个模型，都删除 `SummarizationMiddleware`），请在您使用的每个提供商密钥下注册配置文件。配置文件用于根据所选模型进行调整。无论型号如何，都应在 `create_deep_agent` 调用站点上进行全局调整。


## 合并语义


|场地|合并行为|
| -------------------------------------------- | ------------------------------------------------------------------------------------ |
|`base_system_prompt`、`system_prompt_suffix`|设置后新值获胜；否则继承|
|`tool_description_overrides`|每个键的映射合并；新价值在共享密钥上获胜|
|`excluded_tools`、`excluded_middleware`|设置并集|
|`extra_middleware`|按名称合并：新实例替换其位置上的现有实例，附加新条目|
|`general_purpose_subagent`|按字段合并（未设置的字段继承）|


\| `init_kwargs`（提供商）|字典按键合并；新价值赢得共享密钥| \| `pre_init`（提供者）| Callables 链：现有的先运行，然后是新的 | \| `init_kwargs_factory`（提供者）|每个 `resolve_model` 调用都会合并其输出的工厂链 |


## 提供商简介


`ProviderProfile` 声明深度智能体应如何为给定提供者或特定模型规范构建聊天模型。仅当您在创建深度智能体时提供 `provider:model` 字符串时才适用，而不是当您使用 [`init_chat_model`](https://reference.langchain.com/python/langchain/chat_models/base/init_chat_model) 传递预配置模型时适用：


```python
from deepagents import ProviderProfile, register_provider_profile

register_provider_profile(
    "openai",
    ProviderProfile(init_kwargs={"temperature": 0}),
)
```


 **init_kwargs**


静态初始化参数转发到 `init_chat_model`。


**预初始化**


在构建之前运行的副作用（例如，凭据验证）。


**init_kwargs_factory**


Kwargs 源自运行时状态（例如，从环境变量中提取的标头）。


## 从配置文件加载配置文件


对于 YAML/JSON 支持的工作流程，请使用 `HarnessProfileConfig`。它镜像 `HarnessProfile` 的声明性子集（提示文本、工具描述覆盖、排除的工具和中间件、通用子智能体编辑）并拥有 `to_dict` / `from_dict`。仅运行时状态（中间件实例、工厂和类形式 `excluded_middleware` 条目）保留在 `HarnessProfile` 上。


`register_harness_profile` 接受任一类型，因此配置支持的调用者不需要手动转换步骤：


```yaml
# openai.yaml
base_system_prompt: You are helpful.
system_prompt_suffix: Respond briefly.
excluded_tools:
  - execute
  - grep
excluded_middleware:
  - SummarizationMiddleware
  - my_pkg.middleware:TelemetryMiddleware
general_purpose_subagent:
  enabled: false
```


```python
import yaml
from deepagents import HarnessProfileConfig, register_harness_profile

with open("openai.yaml") as f:
    register_harness_profile(
        "openai",
        HarnessProfileConfig.from_dict(yaml.safe_load(f)),
    )
```


 要去另一个方向，`HarnessProfileConfig.from_harness_profile(...)`当运行时配置文件仅使用可序列化功能时，将其导出回声明性形状：


* 类形式的 `excluded_middleware` 条目序列化为公共别名（当类通过 `serialized_name: ClassVar[str]` 公开别名时）或 `module:Class` 导入引用。
* 非空 `extra_middleware` 和 `__main__` 中或函数范围内声明的中间件类无法序列化 — 导出引发 `ValueError`。


## 将配置文件作为插件发送


可分发的配置文件可以通过 `importlib.metadata` 入口点自行注册，而不需要调用者手动运行 `register_*_profile`。加载顺序是**首先内置，然后是入口点插件，然后是用户代码中的任何直接 `register_*_profile` 调用**；所有三个路径都通过相同的附加注册，因此后面的注册位于同一密钥下的早期注册之上。


在相应组下的发行版自己的 `pyproject.toml` 中声明一个入口点：


```toml
[project.entry-points."deepagents.harness_profiles"]
my_provider = "my_pkg.profiles:register_harness"

[project.entry-points."deepagents.provider_profiles"]
my_provider = "my_pkg.profiles:register_provider"
```


 每个目标都会解析为一个零参数可调用函数，该可调用函数在导入 `deepagents.profiles` 时执行注册：


```python
from deepagents import (
    HarnessProfile,
    ProviderProfile,
    register_harness_profile,
    register_provider_profile,
)


def register_harness() -> None:
    register_harness_profile(
        "my_provider",
        HarnessProfile(system_prompt_suffix="Batch independent tool calls in parallel."),
    )


def register_provider() -> None:
    register_provider_profile(
        "my_provider",
        ProviderProfile(init_kwargs={"temperature": 0}),
    )
```


## 有关的


* [线束概述](overview.md)—线束功能概述
* [Models](models.md)—配置模型提供者和参数
* [定制](customization.md)—全`create_deep_agent`配置面


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/profiles.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

