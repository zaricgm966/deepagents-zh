# 子智能体流式传输


> 显示具有流媒体内容、进度跟踪和可折叠卡片的专家子智能体


当协调器代理生成专业子智能体（研究人员、分析师、作家）时，您需要将协调器的消息与每个子智能体的流输出分开呈现。 v1 SDK 将协调器消息保留在根流上，并将子智能体公开为发现快照。将快照传递给选择器挂钩或可组合项（例如 `useMessages(stream, subagent)`）以呈现专家的范围流。


这就是 LangChain 前端 SDK 超越平面聊天记录的地方：子智能体是一流的流实体，拥有自己的状态、消息、工具调用元数据和结果。您的 UI 可以显示委托、进度、错误和最终综合，而无需要求用户读取每个工作人员的交错令牌。


## 为什么基于选择器的子智能体流


根流始终专注于协调器对话：


* `stream.messages` 仅包含协调者的消息
* `stream.subagents` 包含带有身份、命名空间和状态的发现快照
* 每个子智能体的消息、工具调用和值都使用选择器助手读取
* 用户界面保持干净：协调员的推理与
专家的工作


这种分离使您可以在一个位置呈现协调器的消息，并且仅当用户需要查看专业工作时才安装子智能体卡。


对于大型任务，这还可以保持 UI 可扩展。用户可以浏览协调器的高级计划，仅扩展他们关心的专业工作，并且仍然保留完整的子智能体跟踪以进行调试、审计或重放。


## 设置 `useStream`


不需要额外的流选项。将流指向深度智能体，渲染来自 `stream.messages` 的协调器消息，并使用 `stream.subagents` 为活跃专家挂载卡。在聊天布局中，通过生成子智能体的工具调用 ID 对子智能体进行索引，以便每张卡都显示在协调器下方。将流指向深度智能体，呈现来自 `stream.messages` 的协调器消息，并使用 `stream.subagents` 为活跃专家挂载卡。在聊天布局中，通过生成子智能体的工具调用 ID 对子智能体进行索引，以便每张卡都显示在委派工作的协调员轮次下。


代码示例使用 `useStream<typeof myAgent>` 来实现类型安全的流状态。请参阅 [Python](https://docs.langchain.com/oss/python/langchain/frontend/overview#type-inference) 或 [JavaScript](https://docs.langchain.com/oss/javascript/langchain/frontend/overview#type-inference) 后端的类型推断。


```tsx
import { useStream } from "@langchain/react";
import { AIMessage, HumanMessage } from "langchain";

const AGENT_URL = "http://localhost:2024";

export function DeepAgentChat() {
  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_subagent_cards",
  });
  const subagents = [...stream.subagents.values()];
  const subagentsByCallId = new Map(subagents.map((s) => [s.id, s]));

  return (
    <div>
      {stream.messages.map((msg) => {
        const turnSubagents = AIMessage.isInstance(msg)
          ? (msg.tool_calls ?? [])
              .map((tc) => subagentsByCallId.get(tc.id ?? ""))
              .filter((s): s is NonNullable<typeof s> => !!s)
          : [];

        return (
          <div key={msg.id}>
            {HumanMessage.isInstance(msg) && <HumanBubble>{msg.text}</HumanBubble>}
            {AIMessage.isInstance(msg) && msg.text.trim() && (
              <AIBubble>{msg.text}</AIBubble>
            )}
            {turnSubagents.map((subagent) => (
              <SubagentCard key={subagent.id} stream={stream} subagent={subagent} />
            ))}
          </div>
        );
      })}
    </div>
  );
}
```


```vue
<script setup lang="ts">
import { computed } from "vue";
import { useStream } from "@langchain/vue";
import { AIMessage, HumanMessage } from "langchain";

const AGENT_URL = "http://localhost:2024";

const stream = useStream<typeof myAgent>({
  apiUrl: AGENT_URL,
  assistantId: "deep_agent_subagent_cards",
});

const subagentsByCallId = computed(
  () => new Map([...stream.subagents.value.values()].map((s) => [s.id, s]))
);

function subagentsForMessage(msg: unknown) {
  if (!AIMessage.isInstance(msg)) return [];
  return (msg.tool_calls ?? [])
    .map((tc) => subagentsByCallId.value.get(tc.id ?? ""))
    .filter(Boolean);
}
</script>

<template>
  <div>
    <div
      v-for="msg in stream.messages.value"
      :key="msg.id"
    >
      <HumanBubble v-if="HumanMessage.isInstance(msg)">
        {{ msg.text }}
      </HumanBubble>
      <AIBubble v-else-if="AIMessage.isInstance(msg) && msg.text.trim()">
        {{ msg.text }}
      </AIBubble>
      <SubagentCard
        v-for="subagent in subagentsForMessage(msg)"
        :key="subagent.id"
        :stream="stream"
        :subagent="subagent"
      />
    </div>
  </div>
</template>
```


```svelte
<script lang="ts">
  import { useStream } from "@langchain/svelte";

  const AGENT_URL = "http://localhost:2024";

  const stream = useStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_subagent_cards",
  });
</script>

<div>
  {#each stream.messages as msg (msg.id)}
    <Message {msg} />
  {/each}
  {#each [...stream.subagents.values()] as subagent (subagent.id)}
    <SubagentCard {stream} {subagent} />
  {/each}
</div>
```


```ts
import { Component, computed } from "@angular/core";
import { injectStream } from "@langchain/angular";

const AGENT_URL = "http://localhost:2024";

@Component({
  selector: "app-deep-agent-chat",
  template: `
    @for (msg of stream.messages(); track msg.id) {
      <app-message [message]="msg" />
    }
    @for (subagent of subagents(); track subagent.id) {
      <app-subagent-card [stream]="stream" [subagent]="subagent" />
    }
  `,
})
export class DeepAgentChatComponent {
  stream = injectStream<typeof myAgent>({
    apiUrl: AGENT_URL,
    assistantId: "deep_agent_subagent_cards",
  });

  subagents = computed(() => [...this.stream.subagents().values()]);
}
```


## 提交消息


通过根流提交消息。深度智能体工作流程通常涉及多层嵌套子图，因此如果您的代理可以深度委托，请设置适当的递归限制：


```ts
stream.submit(
  { messages: [{ type: "human", content: text }] },
  { config: { recursion_limit: 100 } }
);
```


 Deep Agents 将默认递归限制设置为 10,000，这对于大多数多专家设置来说已经足够了。如果需要，您可以通过 `config.recursion_limit` 覆盖它。


## 子智能体发现快照


每个 [SubagentDiscoverySnapshot](https://reference.langchain.com/javascript/langchain-react/SubagentDiscoverySnapshot) 都是线程内运行的子智能体的轻量级发现记录。它告诉您的 UI 子智能体存在、它在子智能体树中的位置以及它所处的生命周期状态。


该快照**不**包括子智能体的流式消息或工具调用。相反，请将快照传递给选择器挂钩，例如 `useMessages(stream, subagent)` 或 `useToolCalls(stream, subagent)`。仅当安装了相应的卡或面板时，这些挂钩才使用快照命名空间来订阅子智能体的流原语。


## 构建子智能体卡


每个子智能体卡都会显示专家的姓名、状态、流媒体内容和工具调用。使用选择器挂钩订阅子智能体命名空间：


```tsx
import {
  useMessages,
  useToolCalls,
  type AnyStream,
  type SubagentDiscoverySnapshot,
} from "@langchain/react";

function SubagentCard({
  stream,
  subagent,
}: {
  stream: AnyStream;
  subagent: SubagentDiscoverySnapshot;
}) {
  const [expanded, setExpanded] = useState(true);
  const messages = useMessages(stream, subagent);
  const toolCalls = useToolCalls(stream, subagent);

  const lastAIMessage = messages
    .filter(AIMessage.isInstance)
    .at(-1);

  const displayContent =
    lastAIMessage?.text ?? subagent.output ?? "";

  return (
    <div className="rounded-lg border bg-white shadow-sm">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4"
      >
        <div className="flex items-center gap-3">
          <StatusIcon status={subagent.status} />
          <div>
            <h4 className="font-semibold capitalize">{subagent.name}</h4>
            <p className="text-xs text-gray-500">
              {toolCalls.length} tool call{toolCalls.length === 1 ? "" : "s"}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={subagent.status} />
        </div>
      </button>

      {expanded && displayContent && (
        <div className="border-t px-4 py-3">
          <div className="prose prose-sm max-w-none line-clamp-6">
            {displayContent}
            {subagent.status === "running" && (
              <span className="inline-block h-4 w-1 animate-pulse bg-blue-500" />
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```


## 进度追踪


显示进度条和计数器，以便用户知道有多少子智能体已完成：


```tsx
function SubagentProgress({
  subagents,
}: {
  subagents: SubagentDiscoverySnapshot[];
}) {
  const completed = subagents.filter((s) => s.status === "complete").length;
  const total = subagents.length;
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs text-gray-500">
        <span>Subagent progress</span>
        <span>
          {completed}/{total} complete
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-gray-200">
        <div
          className="h-full rounded-full bg-blue-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
```


## 使用子智能体卡呈现消息


关键的布局模式是从根流渲染协调器消息，并将子智能体卡附加到工具调用生成它们的 AI 消息上：


```tsx
function DeepAgentLayout({ stream }: { stream: AnyStream }) {
  const subagents = [...stream.subagents.values()];
  const subagentsByCallId = new Map(subagents.map((s) => [s.id, s]));

  return (
    <div className="space-y-3">
      {stream.messages.map((message) => {
        const turnSubagents = AIMessage.isInstance(message)
          ? (message.tool_calls ?? [])
              .map((tc) => subagentsByCallId.get(tc.id ?? ""))
              .filter((s): s is SubagentDiscoverySnapshot => !!s)
          : [];

        return (
          <div key={message.id}>
            <Message message={message} />
            {turnSubagents.length > 0 && (
              <div className="ml-4 space-y-3 border-l-2 border-blue-200 pl-4">
                <SubagentProgress subagents={subagents} />
                {turnSubagents.map((subagent) => (
                  <SubagentCard key={subagent.id} stream={stream} subagent={subagent} />
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
```


 您可以将内联卡与全局子智能体视图结合起来：通过为转录卡生成子智能体的协调器工具调用来索引子智能体，并使用 `stream.subagents` 作为总结所有活动工作人员的持久侧边栏。这为用户提供了本地上下文和整个运行的鸟瞰图。


## 最佳实践


* **仅在需要的地方安装选择器**。作用域消息和工具调用流
当卡调用 `useMessages(stream, subagent)` 或 `useToolCalls(stream, subagent)` 时。* **显示专家姓名**。 `subagent.name` 告诉用户哪个工作线程处于活动状态。
* **使用可折叠卡片**。在具有 5 个以上子智能体的工作流程中，自动折叠
完成卡片，以便用户可以专注于积极的工作。* **仅在需要时覆盖递归**。 Deep Agents 设置了较高的默认值
递归限制；仅针对异常深入的自定义工作流程传递 `config.recursion_limit`。* **处理每个子智能体的错误**。一个子智能体失败不应导致系统崩溃
整个用户界面。在该子智能体的卡中显示错误，而其他子智能体继续运行。


## 相关 LangChain 指南


这些 LangChain 前端模式与子智能体卡的工作方式与与单代理流的工作方式相同。深度智能体基于相同的 `useStream` API 构建，因此这些指南直接适用：


  
**工具调用**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/tool-calling)


将每个子智能体的工具调用呈现为丰富的、类型安全的 UI 卡，具有待处理、已完成和失败状态。

  


  
**降价消息**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/markdown-messages)


将协调器和子智能体消息显示为格式化的降价，并具有适当的流支持。

  


  
**人在环**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/human-in-the-loop)


使用相同的中断 API 暂停委托子智能体以供用户批准或输入。

  


  
**推理标记**


[查看相关页面](https://docs.langchain.com/oss/python/langchain/frontend/reasoning-tokens)


使用可折叠推理块在子智能体卡内进行表面模型思考。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/frontend/subagent-streaming.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

