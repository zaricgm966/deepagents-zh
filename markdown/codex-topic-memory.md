# 专题 · 长期记忆的独立流程

> **本节问题：** 跨任务的经验与当前轮次压缩有什么区别？

**承接：** 先阅读上下文压缩与会话记录专题。

## 启动条件先于记忆生成

记忆流程有自己的启动入口。临时会话、功能关闭或非根 Agent 会直接跳过；缺少状态数据库也会退出。不能把所有会话都描述成必然写入长期记忆。

源码：`codex-rs/memories/write/src/start.rs` · L24–52

<!-- source: memory-gate -->

```rust
pub fn start_memories_startup_task(
    thread_manager: Arc<ThreadManager>,
    auth_manager: Arc<AuthManager>,
    thread_id: ThreadId,
    thread: Arc<CodexThread>,
    config: Arc<Config>,
    parent_permission_profile: PermissionProfile,
    source: &SessionSource,
) {
    if config.ephemeral
        || !config.features.enabled(Feature::MemoryTool)
        || source.is_non_root_agent()
    {
        return;
    }

    let context = Arc::new(MemoryStartupContext::new(
        thread_manager,
        Arc::clone(&auth_manager),
        thread_id,
        thread,
        config.as_ref(),
        source.clone(),
    ));

    if context.state_db().is_none() {
        warn!("state db unavailable for memories startup pipeline; skipping");
        return;
    }
```

**为什么看这些行：**

- [L33](#memory-gate-L33)、[L34](#memory-gate-L34)、[L35](#memory-gate-L35)

    **代码作用：** 临时会话、功能开关和 Agent 来源共同决定是否跳过，这些条件界定记忆流程的适用范围。

    **讲解衔接：** 本专题先判断是否会进入记忆流程。这组条件是第一道适用范围检查，通过后还要继续核对下面的存储前提。

- [L49](#memory-gate-L49)

    **代码作用：** 没有状态数据库时也退出；通过前一组条件后仍需满足实际存储前提。

    **讲解衔接：** 这一行补齐启动前需要具备的状态数据库条件。通过这些检查后，下一段才进入被安排的异步任务体，解释阶段如何推进。


通过会话来源、功能开关和数据库检查后，启动函数会安排异步工作。下面进入这个任务体的后半段，继续检查清理、额度和两阶段工作如何排序。

源码：`codex-rs/memories/write/src/start.rs` · L64–81

<!-- source: memory-pipeline -->

```rust
        // Clean memories to make preserve DB size. This does not consume tokens so can be
        // done before the quota check.
        phase1::prune(context.as_ref(), &config).await;

        if !guard::rate_limits_ok(&auth_manager, &config).await {
            context.counter(
                MEMORY_STARTUP,
                /*inc*/ 1,
                &[("status", "skipped_rate_limit")],
            );
            return;
        }

        // Run phase 1.
        phase1::run(Arc::clone(&context), Arc::clone(&config)).await;
        // Run phase 2.
        phase2::run(context, config, parent_permission_profile).await;
    });
```

**为什么看这些行：**

- [L66](#memory-pipeline-L66)、[L68](#memory-pipeline-L68)

    **代码作用：** 先做清理，再检查额度，说明进入函数与真正开始模型相关工作之间还有条件。

    **讲解衔接：** 上一段通过了启动门槛，这里切到异步任务体的准备阶段。先完成清理与额度检查，再沿后面的调用看记忆处理的两个阶段。

- [L78](#memory-pipeline-L78)、[L80](#memory-pipeline-L80)

    **代码作用：** 依次等待 phase1 与 phase2，下一阶段接在前一阶段之后；这就是本专题比较独立流水线与主任务循环的依据。

    **讲解衔接：** 这两行是阶段之间的实际交接点，完成本专题从“是否启动”到“按什么顺序运行”的主线。若继续深入，就分别进入 phase1 与 phase2，看提取和整合的具体结果。

## 它为什么不是上下文压缩

这里从启动上下文进入独立流水线，按顺序运行 phase1 和 phase2；当前请求的历史压缩则在另一条路径替换会话历史。两者操作对象和时间尺度不同。

继续阅读 `codex-rs/memories/write/src/phase1.rs` 看候选信息如何提取，再读 `phase2.rs` 的整合流程。后者还涉及整合任务、工作目录和结果检查，不能认为运行函数返回就等于所有经验都已可靠存储。

对于教学任务，“仓库使用哪条测试命令”可能是可复用信息，“某次测试失败的临时输出”则未必适合长期保留。是否被选择应以实际提取和整合结果为证据，而不是用这个例子推断实现一定如此选择。

存储经验并不修改模型权重；后续是否使用，还要追记忆内容被加载进入上下文的路径。


## 按启动条件推演一次记忆流程

本专题先读启动门槛，再读异步任务的两个阶段。下面按同样顺序判断，避免跳过启动条件直接讨论整合。

**检查问题：** 非根 Agent 会话是否进入这条启动流程？通过所有前置条件后，phase1 与 phase2 的执行顺序是什么？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：不会启动这条记忆流水线：非根 Agent 会话会在启动函数的前置检查处提前返回。**

`source.is_non_root_agent()` 为真时满足跳过条件，执行 `return`，不会继续安排后面的异步记忆任务。

**依据：** [非根来源条件 L35](#memory-gate-L35)与[提前返回 L37](#memory-gate-L37)。

**第二问：先等待 phase1::run 完成，再调用并等待 phase2::run。**

两行都带 `await`，所以这里是依次推进的两阶段调用，而不是同时启动两项工作。

**依据：** [第一阶段 L78](#memory-pipeline-L78)与[第二阶段 L80](#memory-pipeline-L80)。

</details>

## 为什么这么设计，好处是什么？

**为什么长期记忆有独立的启动条件和阶段？** [启动检查](#source-memory-gate)限定适用会话并检查存储前提，[异步流程](#source-memory-pipeline)再依次推进清理、额度检查及两个阶段。这样，记忆工作有自己的运行范围和处理顺序，可以与当前 Turn 中用于继续请求的历史压缩分别管理。

**放回案例，好处是什么？** 完成筛选任务后，仓库测试约定等可复用信息有机会进入专门的提取与整合流程，无需把每次任务的全部日志都当作长期经验。独立流程也便于分别检查“是否启动、提取了什么、如何整合”。是否最终保存并被后续任务使用，仍取决于各阶段结果及加载路径，不能仅凭本次任务完成来判断。

## 接下来追什么

回到[上下文压缩专题](codex-topic-compact.md)，比较独立记忆流水线与当前会话历史替换。
