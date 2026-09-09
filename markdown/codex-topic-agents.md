# 专题 · 子 Agent 的创建与等待

> **本节问题：** 分出去的任务怎样有开始，也有可验证的结束？

**承接：** 先完成主线 09，理解一轮任务的生命周期。

## 创建前先检查任务边界

子 Agent 是另一段带上下文的执行，不是一条后台 shell 命令。创建 handler 解析消息与角色，计算下一层深度，并拒绝超过限制的请求。

源码：`codex-rs/core/src/tools/handlers/multi_agents/spawn.rs` · L58–74

<!-- source: agent-spawn -->

```rust
    let arguments = function_arguments(payload)?;
    let args: SpawnAgentArgs = parse_arguments(&arguments)?;
    let role_name = args
        .agent_type
        .as_deref()
        .map(str::trim)
        .filter(|role| !role.is_empty());
    let input_items = parse_collab_input(args.message, args.items)?;
    let prompt = render_input_preview(&input_items);
    let session_source = turn.session_source.clone();
    let child_depth = next_thread_spawn_depth(&session_source);
    let max_depth = turn.config.agent_max_depth;
    if exceeds_thread_spawn_depth_limit(child_depth, max_depth) {
        return Err(FunctionCallError::RespondToModel(
            "Agent depth limit reached. Solve the task yourself.".to_string(),
        ));
    }
```

**为什么看这些行：**

- [L65](#agent-spawn-L65)

    **代码作用：** 将子任务消息变为 input_items；这是将来交给子任务的工作内容。

    **讲解衔接：** 这是子任务创建路径的输入准备步骤：先把分出去的需求变成 input_items。接下来查深度限制，确定这些输入是否有机会继续交给新任务。

- [L68](#agent-spawn-L68)、[L70](#agent-spawn-L70)

    **代码作用：** 计算子层级并检查上限；读此处是为了确定创建请求何时会在启动前被拒绝。

    **讲解衔接：** 这组行标出创建前的限制条件，完成“是否允许启动”的检查。下一段跳到等待工具，讨论创建之后如何判断结束；中间创建与投递过程没有在此展开。

启动事件、创建成功与工作完成同样需要分开。`fork_context` 等参数还会影响配置和上下文准备，不能仅凭共享父任务就假设全部数据自动一致。

## 等待的是状态变化

创建参数检查回答的是“能否开始子任务”。本节省略具体创建和消息投递过程，转到等待工具内部的状态等待函数，回答“怎样判断已经结束”；这两个片段不是相邻函数之间的直接调用。

源码：`codex-rs/core/src/tools/handlers/multi_agents/wait.rs` · L307–327

<!-- source: agent-wait -->

```rust
async fn wait_for_final_status(
    session: Arc<Session>,
    thread_id: ThreadId,
    mut status_rx: Receiver<AgentStatus>,
) -> Option<(ThreadId, AgentStatus)> {
    let mut status = status_rx.borrow().clone();
    if is_final(&status) {
        return Some((thread_id, status));
    }

    loop {
        if status_rx.changed().await.is_err() {
            let latest = session.services.agent_control.get_status(thread_id).await;
            return is_final(&latest).then_some((thread_id, latest));
        }
        status = status_rx.borrow().clone();
        if is_final(&status) {
            return Some((thread_id, status));
        }
    }
}
```

**为什么看这些行：**

- [L313](#agent-wait-L313)、[L318](#agent-wait-L318)

    **代码作用：** 先检查现有状态，未到终态才等待状态变化；已完成的任务不需要再等一次通知。

    **讲解衔接：** 现在切到创建之后的等待逻辑，先回答等待开始时任务是否已经结束。只有尚未终结，才需要继续看状态变化后的处理。

- [L320](#agent-wait-L320)、[L323](#agent-wait-L323)

    **代码作用：** 通道关闭或状态更新后都检查终态，再决定返回；等待完成的依据是状态，而不是固定等待了多久。

    **讲解衔接：** 这组行补齐等待过程的返回条件，完成从“开始等待”到“有状态依据可以返回”的解释。读完后再回主任务生命周期，比较子任务终态与整项工作完成的关系。

如果当前已是终态，立即返回；否则等待订阅状态变化。通道关闭后还会读取一次最新状态。等待动作本身不等于子任务成功，必须看返回的是哪一种最终状态。

在筛选案例里，适合把“调查测试入口”拆成独立任务，再把文件位置与依据交回主任务。父子上下文分开不自动意味着磁盘文件隔离，同时编辑仍需要明确工作区和职责。

完整生命周期继续沿 `codex-rs/core/src/agent/control.rs` 追消息、关闭与清理。子任务结论交回后，主任务仍要决定如何使用和验证，不能只见到 spawn 就认为协作完成。


## 检查创建条件与等待终态

创建前的限制与创建后的状态等待已经分开。下面分别用一处条件解释它们。

**检查问题：** 深度超限会在哪一步拒绝？等待函数发现当前状态已是终态时，还会等待一次 changed 吗？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：计算 child_depth 后，检查 exceeds_thread_spawn_depth_limit(...) 时拒绝超限请求。**

L70 判断深度是否超过配置上限，超限后紧接着返回 `FunctionCallError::RespondToModel(...)`，此时还没有继续创建子任务。

**依据：** [深度计算 L68](#agent-spawn-L68)、[上限检查 L70](#agent-spawn-L70)与[错误返回 L71](#agent-spawn-L71)。

**第二问：不会。如果当前状态已经是终态，函数立即返回。**

`is_final(&status)` 为真时，直接返回 `Some((thread_id, status))`；只有未到终态才进入后面的循环等待 `changed()`。

**依据：** [先检查终态 L313](#agent-wait-L313)、[立即返回 L314](#agent-wait-L314)与[后续等待 L318](#agent-wait-L318)。

</details>

## 为什么这么设计，好处是什么？

**为什么创建前限制深度，等待时先读当前状态？** [创建检查](#source-agent-spawn)在继续创建前拒绝超过配置深度的请求，可以限制任务层层派生。[等待逻辑](#source-agent-wait)先检查是否已到终态，未到终态时再通过已有的订阅通道等待后续状态变化；已完成的任务可以立即返回，未完成的任务则等待真正的变化。

**放回案例，好处是什么？** 主任务可以把“调查测试入口”交给子任务，同时继续其他独立工作，再通过状态与返回内容判断何时接收调查结论。如果调查已结束，也无需再等一次新的变化。深度限制只约束嵌套层数；职责划分、共享文件修改和结果验证仍需单独处理，创建成功也不代表调查已经完成。

## 接下来追什么

回到[09 · 任务结束](codex-09-finish.md)，比较子任务终态与主任务生命周期的关系。
