# 专题 · 项目说明、文件引用与图片

> **本节问题：** 不同来源的信息怎样成为请求中的上下文？

**承接：** 先完成主线 03，知道 Prompt 的输入与工具规格。

## 项目说明也要通过读取流程

`load_project_instructions` 先从用户说明建立容器，再检查项目是否可信，之后按剩余字节预算读取环境中的项目说明。模型能否使用某段约定，取决于它是否被加载并进入上下文。

源码：`codex-rs/core/src/agents_md.rs` · L55–85

<!-- source: context-agents -->

```rust
pub(crate) async fn load_project_instructions(
    config: &Config,
    user_instructions: Option<Instructions>,
    environments: &TurnEnvironmentSnapshot,
) -> io::Result<Option<LoadedAgentsMd>> {
    let mut loaded = LoadedAgentsMd::from_user_instructions(user_instructions);
    if config.active_project.is_untrusted() {
        return Ok((!loaded.is_empty()).then_some(loaded));
    }

    let mut remaining = config.project_doc_max_bytes;
    for turn_environment in environments.turn_environments() {
        if remaining == 0 {
            break;
        }

        let filesystem = turn_environment.environment.get_filesystem();
        let sandbox = (!turn_environment
            .permission_profile()
            .file_system_sandbox_policy()
            .has_full_disk_read_access())
        .then(|| turn_environment.sandbox_context(/*additional_permissions*/ None));
        match read_agents_md(
            config,
            filesystem.as_ref(),
            &turn_environment.selection.environment_id,
            turn_environment.cwd(),
            remaining,
            sandbox.as_ref(),
        )
        .await
```

**为什么看这些行：**

- [L60](#context-agents-L60)、[L61](#context-agents-L61)

    **代码作用：** 从已有用户说明建立容器，再检查项目信任状态；这决定是否继续读取项目约定。

    **讲解衔接：** 本专题先从程序自动加载说明的路径开始。这组行交代已有说明从哪里接入、项目资料在什么前提下继续读取，下一步再追实际文件读取。

- [L65](#context-agents-L65)、[L77](#context-agents-L77)

    **代码作用：** 设置剩余读取预算并调用 read_agents_md；文件存在并非加载成功的全部条件，还需要通过此处的读取过程。

    **讲解衔接：** 这是“允许读取 → 实际按预算读取”的交接点。读完后再切到用户主动提交截图与文字的路径，对照两种资料进入系统的不同入口。

这段的 `remaining` 以字节预算命名，不能与模型 token 限制混为一谈。跨多个环境时仍在同一剩余预算中读取。

## 把场景扩展为同时提交文字和截图

项目说明来自程序读取，用户还可以在输入框主动提供资料。现在给原案例增加一个条件：用户附上一张按钮截图，同时输入修改要求。为了理解两种资料如何一起提交，我们回到输入代码，比较 LocalImage 与 Text 两种输入项。

源码：`codex-rs/tui/src/chatwidget/input_submission.rs` · L193–212

<!-- source: context-media -->

```rust
        for image_url in &remote_image_urls {
            items.push(UserInput::Image {
                url: image_url.clone(),
                detail: None,
            });
        }

        for image in &local_images {
            items.push(UserInput::LocalImage {
                path: image.path.clone(),
                detail: None,
            });
        }

        if !text.is_empty() {
            items.push(UserInput::Text {
                text: text.clone(),
                text_elements: app_server_text_elements(&text_elements),
            });
        }
```

**为什么看这些行：**

- [L201](#context-media-L201)、[L208](#context-media-L208)

    **代码作用：** 同一个 items 中分别构造 LocalImage 和 Text；要判断发送了什么信息，先看输入项种类，而不是只看界面显示文字。

    **讲解衔接：** 这里从项目说明加载切回用户输入提交，不是 read_agents_md 的后续调用。确认图片与文字如何一起成为 items 后，再回第 03 节检查它们经过后续处理怎样进入请求。

技能和插件需要分开检查两件事：说明是否被加载、工具规格是否暴露给当前请求。它们不是天然自动执行的脚本。继续定位可用 `codex-rs/core/src/session/turn.rs` 中的技能构建与上下文记录调用，再回主线 03 查看最终 Prompt。

教学案例如果改成“按截图调整按钮”，应分别验证图片数据、当前组件源码和用户要求都进入可用信息，不能只加强提示词。


## 检查程序读取与用户输入的区别

本专题比较了程序读取项目说明和用户同时提交文字、截图。现在从已展示的条件和输入类型判断资料如何进入系统。

**检查问题：** 项目说明读取前检查了什么？在文字与截图的案例中，哪个变体携带本地图片？

<details markdown="1" class="answer"><summary>查看答案与代码依据</summary>

**第一问：先检查项目是否可信，再检查剩余读取预算是否允许继续读取。**

项目不可信时，这条加载路径提前返回，不继续读取项目说明；后面的循环在剩余字节预算为零时停止读取。

**依据：** [项目信任检查 L61](#context-agents-L61)、[预算设置 L65](#context-agents-L65)与[零预算判断 L67](#context-agents-L67)。

**第二问：携带本地图片的是 UserInput::LocalImage 变体。**

它用 `path` 字段保存本地图片路径；同一个输入列表中的普通文字则使用 `UserInput::Text`。

**依据：** [LocalImage 构造 L201](#context-media-L201)与[路径字段 L202](#context-media-L202)。

</details>

## 为什么这么设计，好处是什么？

**为什么加载项目说明要检查信任与预算，图片又使用独立类型？** [说明加载代码](#source-context-agents)在读取项目资料前检查信任状态，并在多个环境之间共享剩余读取预算，让自动加载的来源和数量受到明确条件约束。[LocalImage 与 Text](#source-context-media)则把用户主动提供的不同资料分开表达，便于后续按类型处理。

**放回案例，好处是什么？** 仓库中的测试约定可以通过受控的加载流程进入上下文；附带的按钮截图与文字要求也能保留各自的身份。排查模型为何没遵循约定或没看懂截图时，可以分别检查说明是否被加载、图片是否被后续处理。读取预算会限制可加载的内容，因此资料存在于项目中，并不保证它已经完整进入本次请求。

## 接下来追什么

回到[03 · 请求上下文](codex-03-context.md)，继续检查不同来源的信息最终如何进入 Prompt。
