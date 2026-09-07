# 权限


> 使用深度智能体的声明性权限规则控制文件系统访问


使用声明性权限规则控制代理可以读取或写入哪些文件和目录。将规则列表传递给 `permissions=`，代理的内置文件系统工具会尊重它们。


权限需要 `deepagents>=0.5.2`。


权限仅适用于内置文件系统工具（`ls`、`read_file`、`glob`、`grep`、`write_file`、`edit_file`、`delete`）。不包括访问文件系统的自定义工具和 MCP 工具。权限也不适用于[沙箱后端](sandboxes.md)，它支持通过 `execute` 工具执行任意命令。


当您需要在内置文件系统工具上使用**基于路径的允许/拒绝规则**时，请使用 `permissions`。当您需要自定义验证逻辑（速率限制、审核日志记录、内容检查）或需要控制自定义工具时，请使用[后端策略挂钩](backends.md#add-policy-hooks)。


## 基本用法


将 [`FilesystemPermission`](https://reference.langchain.com/python/deepagents/middleware/permissions/FilesystemPermission) 规则列表传递给 [`create_deep_agent`](https://reference.langchain.com/python/deepagents/graph/create_deep_agent)。规则按声明顺序进行评估。第一个匹配的规则获胜。如果没有规则匹配，则允许该操作。


```python
from deepagents import FilesystemPermission, create_deep_agent


# Read-only agent: deny all writes
agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/**"],
            mode="deny",
        ),
    ],
)
```


## 规则结构


每个 `FilesystemPermission` 具有三个字段：


|场地|类型|描述|
| ------------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|`operations`|`list["read" \| "write"]`|此规则适用于操作。 `"read"` 涵盖 `ls`、`read_file`、`glob`、`grep`。 `"write"` 涵盖 `write_file`、`edit_file`、`delete`。|
|`paths`|`list[str]`|用于匹配文件路径的全局模式（例如，`["/workspace/**"]`）。支持 `**` 递归匹配和 `{a,b}` 交替匹配。|
|`mode`|`"allow" \| "deny" \| "interrupt"`|是否允许、拒绝或暂停匹配操作以供人工批准。默认为 `"allow"`。请参阅[暂停以供人工批准](#pause-for-human-approval)。|


规则使用first-match-wins评估：`operations`和`paths`与当前调用匹配的第一条规则决定结果。如果没有规则匹配，则**允许**（允许的默认值）。


## 暂停以供人工批准


`"interrupt"` 模式需要 `deepagents>=0.6.8`。


将 `mode="interrupt"` 设置为暂停以供人工批准，而不是直接允许或拒绝匹配操作。当代理在与中断模式规则匹配的路径上调用内置写入工具（`write_file`、`edit_file`、`delete`）时，`create_deep_agent` 会引发人机交互中断而不是运行该工具，并且审阅者可以批准、编辑或拒绝该调用。


```python
from deepagents import FilesystemPermission, create_deep_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_deep_agent(
    model=model,
    permissions=[
        # Pause for approval before writing anything under /secrets.
        FilesystemPermission(
            operations=["write"],
            paths=["/secrets/**"],
            mode="interrupt",
        ),
    ],
    # Interrupt mode requires a checkpointer to pause and resume.
    checkpointer=InMemorySaver(),
)
```


 中断模式规则会自动连接到代理的人机循环中间件中，并与您传递的任何 `interrupt_on` 合并，因此您可以像工具调用中断一样处理和恢复它们。请参阅[人机交互](human-in-the-loop.md) 了解恢复流程。


删除目录是全有或全无：`delete` 检查目标和每个后代路径上的 `write` 权限，如果其中任何一个被拒绝，则拒绝整个操作，而不是删除树的一部分。 `delete` 将同样的保守检查应用于现有的空目录，因为它仍然是一个目录而不是已确认的叶目标。


相反，删除纯文件是完全匹配的情况：`delete` 以与 `write_file` 和 `edit_file` 相同的方式解析目标，使用首次匹配获胜评估，因此较早、较窄的 `allow` 规则胜过后来的包罗万象的 `deny`。此精确匹配行为需要 `deepagents>=0.7.3`。


使用文字前导段锚定中断模式（例如，`/secrets/**` 或 `/projects/*/secrets/**`）。批量工具（目录上的 `ls`、`glob`、`grep` 和 `delete`）在其搜索子树可能与规则的锚定前缀重叠时触发中断，因此像 `/**/secrets` 这样的完全非锚定模式会保守地过度触发。


## 示例


### 隔离到工作区目录


仅允许在 `/workspace/` 下进行读写，并拒绝其他所有内容：


```python
agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/workspace/**"],
            mode="allow",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny",
        ),
    ],
)
```


### 保护特定文件


```python
agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/workspace/.env", "/workspace/examples/**"],
            mode="deny",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/workspace/**"],
            mode="allow",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny",
        ),
    ],
)
```


### 只读存储器


允许代理读取内存文件，但阻止其修改它们。这对于仅应由应用程序代码更新的组织范围的策略或共享知识库非常有用。有关更多上下文，请参阅[只读与可写内存](memory.md#read-only-vs-writable-memory)。


```python
from deepagents.backends import CompositeBackend, StateBackend, StoreBackend

agent = create_deep_agent(
    model=model,
    backend=CompositeBackend(
        default=StateBackend(),
        routes={
            "/memories/": StoreBackend(
                namespace=lambda rt: (rt.server_info.user.identity,),
            ),
            "/policies/": StoreBackend(
                namespace=lambda rt: (rt.context.org_id,),
            ),
        },
    ),
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/memories/**", "/policies/**"],
            mode="deny",
        ),
    ],
)
```


### 拒绝所有访问


阻止所有读取和写入。这是一个限制性基线，您可以在其上分层更具体的允许规则：


```python
agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny",
        ),
    ],
)
```


### 规则排序


由于首场比赛获胜，规则顺序很重要。将更具体的规则放在更广泛的规则之前：


```python
# Correct: deny .env, allow workspace, deny everything else
correct_permissions = [
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/workspace/.env"],
        mode="deny",
    ),
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/workspace/**"],
        mode="allow",
    ),
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/**"],
        mode="deny",
    ),
]

# Bug: /workspace/** matches .env first, so the deny never triggers
incorrect_permissions = [
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/workspace/**"],
        mode="allow",
    ),
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/workspace/.env"],
        mode="deny",  # never reached
    ),
    FilesystemPermission(
        operations=["read", "write"],
        paths=["/**"],
        mode="deny",
    ),
]
```


## 子智能体权限


[子智能体](subagents.md)默认继承父代理的权限。要为子智能体提供不同的权限，请在其规范中设置 `permissions` 字段。这完全取代了父母的规则。


```python
agent = create_deep_agent(
    model=model,
    backend=backend,
    permissions=[
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/workspace/**"],
            mode="allow",
        ),
        FilesystemPermission(
            operations=["read", "write"],
            paths=["/**"],
            mode="deny",
        ),
    ],
    subagents=[
        {
            "name": "auditor",
            "description": "Read-only code reviewer",
            "system_prompt": "Review the code for issues.",
            "permissions": [
                FilesystemPermission(
                    operations=["write"],
                    paths=["/**"],
                    mode="deny",
                ),
                FilesystemPermission(
                    operations=["read"],
                    paths=["/workspace/**"],
                    mode="allow",
                ),
                FilesystemPermission(
                    operations=["read"],
                    paths=["/**"],
                    mode="deny",
                ),
            ],
        }
    ],
)
```


## 复合后端


当使用具有沙箱默认值的 [`CompositeBackend`](https://reference.langchain.com/python/deepagents/backends/composite/CompositeBackend) 时，每个权限路径的范围必须位于已知的路由前缀下。沙箱支持任意命令执行，因此仅基于路径的限制无法阻止通过 shell 命令访问文件系统。将权限范围限定为特定于路由的[后端](backends.md) 可避免这种冲突。


```python
from deepagents.backends import CompositeBackend


composite = CompositeBackend(
    default=sandbox,
    routes={"/memories/": memories_backend},
)

# Works: permissions are scoped to the /memories/ route
agent = create_deep_agent(
    model=model,
    backend=composite,
    permissions=[
        FilesystemPermission(
            operations=["write"],
            paths=["/memories/**"],
            mode="deny",
        ),
    ],
)
```


 包含任何路径之外的路径的权限会引发 `NotImplementedError`：


```python
# Raises NotImplementedError: /workspace/** hits the sandbox default
try:
    create_deep_agent(
        model=model,
        backend=composite,
        permissions=[
            FilesystemPermission(
                operations=["write"],
                paths=["/workspace/**"],
                mode="deny",
            ),
        ],
    )
except NotImplementedError:
    pass

# Also raises: /** covers both routes and the default
try:
    create_deep_agent(
        model=model,
        backend=composite,
        permissions=[
            FilesystemPermission(
                operations=["read"],
                paths=["/**"],
                mode="deny",
            ),
        ],
    )
except NotImplementedError:
    pass
```


 ***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/permissions.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

