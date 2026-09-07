# 待办事项列表


> 通过从座席状态同步的实时待办事项列表来跟踪座席进度


并非每个代理交互都是聊天。有时，代理正在执行多步骤计划，显示进度的最佳方式是实时更新的**待办事项列表**。深度智能体待办事项列表模式直接从代理的状态读取 `todos` 数组，在代理执行其计划时呈现每个项目及其当前状态。它是一个进度仪表板，构建在您用于聊天的同一个 `useStream` 挂钩上。它表明代理状态可以为任何 UI 提供支持，而不仅仅是消息气泡。


## 它是如何运作的


当您选择加入 [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware) 时，深度智能体可以公开 **`todos` 状态**通道。该中间件添加了 `write_todos` 工具，并在代理执行其计划时保留任务进度。当代理执行时，它会将每个待办事项的状态从 `"pending"` 更新到 `"in_progress"` 到 `"completed"`。 [`useStream`](https://reference.langchain.com/javascript/langchain-react/index/useStream) 挂钩通过 `stream.values.todos` 公开此状态，并且您的 UI 会以反应方式呈现它。


任务计划是可选择的。如果没有 [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware)，则 `stream.values.todos` 不存在。参见[任务规划](overview.md#task-planning)。


流程如下所示：


1. 用户提交请求
2. 代理创建计划并在其状态中填充 `todos`
3. 代理开始通过 `pending` 执行每个待办事项转换 →
`in_progress` → `completed`4. `stream.values.todos` 随着代理进度实时更新
5. 您的 UI 重新呈现具有当前状态的待办事项列表


## 设置 `useStream`


在代理上启用 [`TodoListMiddleware`](https://reference.langchain.com/python/langchain/agents/middleware/todo/TodoListMiddleware)。


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="google_genai:gemini-3.6-flash",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="openai:gpt-5.5",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-6",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="openrouter:z-ai/glm-5.2",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="fireworks:accounts/fireworks/models/glm-5p2",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="baseten:zai-org/GLM-5.2",
    middleware=[TodoListMiddleware()],
)
```


```python
from deepagents import create_deep_agent
from langchain.agents.middleware import TodoListMiddleware

agent = create_deep_agent(
    model="ollama:north-mini-code-1.0",
    middleware=[TodoListMiddleware()],
)
```


 然后将 [`useStream`](https://reference.langchain.com/javascript/langchain-react/index/useStream) 指向该代理并从 `stream.values` 读取 `todos`。


代码示例使用 `useStream<typeof myAgent>` 来实现类型安全的流状态。请参阅 [Python](https://docs.langchain.com/oss/python/langchain/frontend/overview#type-inference) 或 [JavaScript](https://docs.langchain.com/oss/javascript/langchain/frontend/overview#type-inference) 后端的类型推断。


```tsx
import { useStream } from "@langchain/react";

const AGENT_URL = "http://localhost:2024";

export function TodoAgent() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_todo_list",
  });

  const todos = stream.values?.todos ?? [];

  return (
    <div>
      <TodoList todos={todos} />
      {stream.messages.map((msg) => (
        <Message key={msg.id} message={msg} />
      ))}
    </div>
  );
}
```


```vue
<script setup lang="ts">
import { useStream } from "@langchain/vue";
import { computed } from "vue";

const AGENT_URL = "http://localhost:2024";

const stream = useStream<typeof myAgent>({
  apiUrl: AGENT_URL,
  assistantId: "deep_agent_todo_list",
});

const todos = computed(() => stream.values.value?.todos ?? []);
</script>

<template>
  <div>
    <TodoList :todos="todos" />
    <Message
      v-for="msg in stream.messages.value"
      :key="msg.id"
      :message="msg"
    />
  </div>
</template>
```


```svelte
<script lang="ts">
  import { useStream } from "@langchain/svelte";

  const AGENT_URL = "http://localhost:2024";

  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_todo_list",
  });

  const todos = $derived(stream.values?.todos ?? []);
</script>

<div>
  <TodoList {todos} />
  {#each stream.messages as msg (msg.id)}
    <Message message={msg} />
  {/each}
</div>
```


```ts
import { Component, computed } from "@angular/core";
import { injectStream } from "@langchain/angular";

const AGENT_URL = "http://localhost:2024";

@Component({
  selector: "app-todo-agent",
  template: `
    <div>
      <app-todo-list [todos]="todos()" />
      @for (msg of stream.messages(); track msg.id) {
        <app-message [message]="msg" />
      }
    </div>
  `,
})
export class TodoAgentComponent {
  stream = injectStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_todo_list",
  });

  todos = computed(() => this.stream.values()?.todos ?? []);
}
```


## 构建 TodoList 组件


待办事项列表使用状态图标、颜色编码和反映当前状态的视觉样式呈现每个项目：


```tsx
function TodoList({ todos }: { todos: Todo[] }) {
  const completed = todos.filter((t) => t.status === "completed").length;
  const percentage = todos.length
    ? Math.round((completed / todos.length) * 100)
    : 0;

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Agent Progress</h2>
        <span className="text-sm text-gray-500">
          {completed}/{todos.length} tasks
        </span>
      </div>

      <ProgressBar percentage={percentage} />

      <ul className="mt-4 space-y-2">
        {todos.map((todo, i) => (
          <TodoItem key={i} todo={todo} />
        ))}
      </ul>
    </div>
  );
}
```


## 进度条


可视化进度条让用户可以一目了然地了解总体完成情况：


```tsx
function ProgressBar({ percentage }: { percentage: number }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Progress</span>
        <span>{percentage}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-green-500 transition-all duration-500"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
```


## 个人待办事项


每个项目都有一个状态图标、颜色编码文本和已完成任务的删除线样式：


```tsx
function TodoItem({ todo }: { todo: Todo }) {
  const config = {
    pending: {
      icon: "○",
      textClass: "text-gray-600",
      bgClass: "bg-gray-50",
      iconClass: "text-gray-400",
    },
    in_progress: {
      icon: "◉",
      textClass: "text-amber-800",
      bgClass: "bg-amber-50 border-amber-200",
      iconClass: "text-amber-500 animate-pulse",
    },
    completed: {
      icon: "✓",
      textClass: "text-green-800 line-through",
      bgClass: "bg-green-50 border-green-200",
      iconClass: "text-green-500",
    },
  };

  const style = config[todo.status];

  return (
    <li
      className={`flex items-start gap-3 rounded-md border px-3 py-2 ${style.bgClass}`}
    >
      <span className={`mt-0.5 text-lg leading-none ${style.iconClass}`}>
        {style.icon}
      </span>
      <span className={`text-sm ${style.textClass}`}>{todo.content}</span>
    </li>
  );
}
```


 `in_progress` 图标使用 `animate-pulse` 来引起对当前活动任务的注意。


## 计算进度


直接从 todos 数组导出进度指标：


```ts
const todos = stream.values?.todos ?? [];

const completed = todos.filter((t) => t.status === "completed").length;
const inProgress = todos.filter((t) => t.status === "in_progress").length;
const pending = todos.filter((t) => t.status === "pending").length;
const percentage = todos.length
  ? Math.round((completed / todos.length) * 100)
  : 0;
```


 当代理修改其状态时，这些值会进行反应性更新，从而保持进度条和计数器同步。


## 与聊天消息结合


待办事项列表与常规聊天界面一起使用。实用的布局将待办事项列表显示为持久侧边栏或标题面板，并在下面显示聊天消息：


```tsx
function TodoAgentLayout() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_todo_list",
  });

  const todos = stream.values?.todos ?? [];

  return (
    <div className="flex h-screen flex-col">
      {todos.length > 0 && (
        <div className="border-b bg-gray-50 p-4">
          <TodoList todos={todos} />
        </div>
      )}

      <main className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-2xl space-y-4">
          {stream.messages.map((msg) => (
            <Message key={msg.id} message={msg} />
          ))}
        </div>
      </main>

      <ChatInput
        onSubmit={(text) =>
          stream.submit({ messages: [{ type: "human", content: text }] })
        }
        isLoading={stream.isLoading}
      />
    </div>
  );
}
```


 仅当 `todos.length > 0` 时才显示待办事项列表。在代理创建其计划之前，没有任何内容可显示。显示空组件会浪费空间。


## 使用案例


待办事项列表模式适合代理执行结构化计划的任何场景：


* **项目规划**：代理将项目分解为任务并完成
他们依次* **研究工作流程**：每个研究问题都成为代理的待办事项
调查并完成* **数据处理**：摄取、验证、转换等步骤
导出每个人都有自己的待办事项* **入职流程**：代理逐步完成设置步骤，检查每一个步骤
当它配置服务时* **报告生成**：报告的各个部分成为待办事项：收集数据，
分析趋势、撰写摘要、格式化输出


## 处理空载状态


在代理创建其计划之前处理初始状态：


```tsx
function TodoList({ todos, isLoading }: { todos: Todo[]; isLoading: boolean }) {
  if (todos.length === 0 && !isLoading) {
    return null;
  }

  if (todos.length === 0 && isLoading) {
    return (
      <div className="rounded-lg border bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="animate-spin">⟳</span>
          Agent is creating a plan...
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      {/* ... full todo list rendering */}
    </div>
  );
}
```


## 最佳实践


* **突出显示待办事项列表**。这是主要进度指标
基于计划的代理。不要把它埋在折叠下面。* **动画状态转换**。平滑的过渡让座席感觉更轻松
反应灵敏。在背景颜色、文本装饰和不透明度上使用 CSS 过渡。* **仅突出显示一项 `in_progress` 项目**。代理通常只执行一项任务
一次。如果多个项目显示为 `in_progress`，则 UI 会变得嘈杂。考虑只脉冲第一个。* **折叠或变暗已完成的项目**。随着列表的增长，已完成的项目
变得不那么相关。减少视觉重量，以便用户专注于仍在发生的事情。* **显示进度百分比**。像“67% 完成”这样的单一数字是
即使从房间的另一边也能立即理解。* **保持待办事项列表同步**。因为 `stream.values` 是反应性更新的，
待办事项列表自动保持最新状态。不要添加手动轮询或刷新逻辑。


## 相关 LangChain 指南


待办事项列表模式是更广泛的 LangChain 渲染结构化代理状态方法的专业化。这些指南涵盖了与基于计划的代理完美配合的相关技术：


  
**结构化输出**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/structured-output)


使用自定义 UI 组件而不是纯文本呈现任何结构化代理状态（而不仅仅是待办事项）。

  


  
**加入和重新加入流**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/join-rejoin)


页面重新加载或选项卡切换后重新连接到正在运行的计划，而不会丢失进度。

  


  
**消息队列**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/message-queues)


在代理仍在执行当前计划的同时对后续任务进行排队。

  


  
**人在环**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop)


当代理需要用户批准或输入时暂停和恢复计划执行。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/frontend/todo-list.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

