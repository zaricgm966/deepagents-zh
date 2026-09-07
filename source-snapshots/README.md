# 源码阅读快照

本目录保存两个源码阅读章节引用的官方文件，并非完整仓库镜像。快照版本固定，不执行源文件中的代码或说明。

## openai/codex

GitHub：https://github.com/openai/codex

固定提交：`121f91fd5d9dc66017866ce9bdc49f1e182721df`

[Apache-2.0 许可](codex/LICENSE) · [NOTICE](codex/NOTICE)

- [LICENSE](codex/LICENSE)
- [NOTICE](codex/NOTICE)
- [codex-rs/apply-patch/src/lib.rs](codex/codex-rs/apply-patch/src/lib.rs)
- [codex-rs/apply-patch/src/seek_sequence.rs](codex/codex-rs/apply-patch/src/seek_sequence.rs)
- [codex-rs/cli/src/main.rs](codex/codex-rs/cli/src/main.rs)
- [codex-rs/codex-mcp/src/lib.rs](codex/codex-rs/codex-mcp/src/lib.rs)
- [codex-rs/core/README.md](codex/codex-rs/core/README.md)
- [codex-rs/core/src/agent/control.rs](codex/codex-rs/core/src/agent/control.rs)
- [codex-rs/core/src/agents_md.rs](codex/codex-rs/core/src/agents_md.rs)
- [codex-rs/core/src/agents_md_manager.rs](codex/codex-rs/core/src/agents_md_manager.rs)
- [codex-rs/core/src/compact.rs](codex/codex-rs/core/src/compact.rs)
- [codex-rs/core/src/compact_remote.rs](codex/codex-rs/core/src/compact_remote.rs)
- [codex-rs/core/src/context/mod.rs](codex/codex-rs/core/src/context/mod.rs)
- [codex-rs/core/src/guardian/mod.rs](codex/codex-rs/core/src/guardian/mod.rs)
- [codex-rs/core/src/guardian/review.rs](codex/codex-rs/core/src/guardian/review.rs)
- [codex-rs/core/src/image_preparation.rs](codex/codex-rs/core/src/image_preparation.rs)
- [codex-rs/core/src/mcp.rs](codex/codex-rs/core/src/mcp.rs)
- [codex-rs/core/src/mcp_tool_call.rs](codex/codex-rs/core/src/mcp_tool_call.rs)
- [codex-rs/core/src/responses_retry.rs](codex/codex-rs/core/src/responses_retry.rs)
- [codex-rs/core/src/rollout.rs](codex/codex-rs/core/src/rollout.rs)
- [codex-rs/core/src/session/handlers.rs](codex/codex-rs/core/src/session/handlers.rs)
- [codex-rs/core/src/session/mod.rs](codex/codex-rs/core/src/session/mod.rs)
- [codex-rs/core/src/session/turn.rs](codex/codex-rs/core/src/session/turn.rs)
- [codex-rs/core/src/session/turn_input.rs](codex/codex-rs/core/src/session/turn_input.rs)
- [codex-rs/core/src/stream_events_utils.rs](codex/codex-rs/core/src/stream_events_utils.rs)
- [codex-rs/core/src/thread_rollout_truncation.rs](codex/codex-rs/core/src/thread_rollout_truncation.rs)
- [codex-rs/core/src/tools/handlers/apply_patch.rs](codex/codex-rs/core/src/tools/handlers/apply_patch.rs)
- [codex-rs/core/src/tools/handlers/multi_agents.rs](codex/codex-rs/core/src/tools/handlers/multi_agents.rs)
- [codex-rs/core/src/tools/handlers/multi_agents/spawn.rs](codex/codex-rs/core/src/tools/handlers/multi_agents/spawn.rs)
- [codex-rs/core/src/tools/handlers/multi_agents/wait.rs](codex/codex-rs/core/src/tools/handlers/multi_agents/wait.rs)
- [codex-rs/core/src/tools/handlers/plan.rs](codex/codex-rs/core/src/tools/handlers/plan.rs)
- [codex-rs/core/src/tools/handlers/plan_spec.rs](codex/codex-rs/core/src/tools/handlers/plan_spec.rs)
- [codex-rs/core/src/tools/handlers/request_user_input.rs](codex/codex-rs/core/src/tools/handlers/request_user_input.rs)
- [codex-rs/core/src/tools/handlers/unified_exec.rs](codex/codex-rs/core/src/tools/handlers/unified_exec.rs)
- [codex-rs/core/src/tools/handlers/view_image.rs](codex/codex-rs/core/src/tools/handlers/view_image.rs)
- [codex-rs/core/src/tools/orchestrator.rs](codex/codex-rs/core/src/tools/orchestrator.rs)
- [codex-rs/core/src/tools/parallel.rs](codex/codex-rs/core/src/tools/parallel.rs)
- [codex-rs/core/src/unified_exec/process_manager.rs](codex/codex-rs/core/src/unified_exec/process_manager.rs)
- [codex-rs/ext/guardian-v2/src/lib.rs](codex/codex-rs/ext/guardian-v2/src/lib.rs)
- [codex-rs/ext/memories/src/lib.rs](codex/codex-rs/ext/memories/src/lib.rs)
- [codex-rs/memories/write/src/phase1.rs](codex/codex-rs/memories/write/src/phase1.rs)
- [codex-rs/memories/write/src/phase2.rs](codex/codex-rs/memories/write/src/phase2.rs)
- [codex-rs/memories/write/src/start.rs](codex/codex-rs/memories/write/src/start.rs)
- [codex-rs/protocol/src/request_user_input.rs](codex/codex-rs/protocol/src/request_user_input.rs)
- [codex-rs/protocol/src/user_input.rs](codex/codex-rs/protocol/src/user_input.rs)
- [codex-rs/rollout/src/recorder.rs](codex/codex-rs/rollout/src/recorder.rs)
- [codex-rs/tui/src/bottom_pane/chat_composer.rs](codex/codex-rs/tui/src/bottom_pane/chat_composer.rs)
- [codex-rs/tui/src/chatwidget/slash_dispatch.rs](codex/codex-rs/tui/src/chatwidget/slash_dispatch.rs)
- [codex-rs/tui/src/chatwidget/streaming.rs](codex/codex-rs/tui/src/chatwidget/streaming.rs)
- [codex-rs/tui/src/slash_command.rs](codex/codex-rs/tui/src/slash_command.rs)
## anthropics/claude-agent-sdk-python

GitHub：https://github.com/anthropics/claude-agent-sdk-python

固定提交：`efd4d865ef1795daffee3cd24cce45307aed8a51`

[MIT 许可](claude-agent-sdk-python/LICENSE)

Claude Code CLI 的完整引擎不在这个 Python SDK 快照内，不能把 SDK 接口当成 CLI 私有算法的实现。

- [LICENSE](claude-agent-sdk-python/LICENSE)
- [examples/agents.py](claude-agent-sdk-python/examples/agents.py)
- [examples/filesystem_agents.py](claude-agent-sdk-python/examples/filesystem_agents.py)
- [examples/hooks.py](claude-agent-sdk-python/examples/hooks.py)
- [examples/setting_sources.py](claude-agent-sdk-python/examples/setting_sources.py)
- [src/claude_agent_sdk/__init__.py](claude-agent-sdk-python/src/claude_agent_sdk/__init__.py)
- [src/claude_agent_sdk/_errors.py](claude-agent-sdk-python/src/claude_agent_sdk/_errors.py)
- [src/claude_agent_sdk/_internal/message_parser.py](claude-agent-sdk-python/src/claude_agent_sdk/_internal/message_parser.py)
- [src/claude_agent_sdk/_internal/query.py](claude-agent-sdk-python/src/claude_agent_sdk/_internal/query.py)
- [src/claude_agent_sdk/_internal/session_resume.py](claude-agent-sdk-python/src/claude_agent_sdk/_internal/session_resume.py)
- [src/claude_agent_sdk/_internal/session_store.py](claude-agent-sdk-python/src/claude_agent_sdk/_internal/session_store.py)
- [src/claude_agent_sdk/_internal/transport/subprocess_cli.py](claude-agent-sdk-python/src/claude_agent_sdk/_internal/transport/subprocess_cli.py)
- [src/claude_agent_sdk/client.py](claude-agent-sdk-python/src/claude_agent_sdk/client.py)
- [src/claude_agent_sdk/query.py](claude-agent-sdk-python/src/claude_agent_sdk/query.py)
- [src/claude_agent_sdk/types.py](claude-agent-sdk-python/src/claude_agent_sdk/types.py)
- [tests/test_option_warnings.py](claude-agent-sdk-python/tests/test_option_warnings.py)
- [tests/test_sdk_mcp_integration.py](claude-agent-sdk-python/tests/test_sdk_mcp_integration.py)
- [tests/test_tool_callbacks.py](claude-agent-sdk-python/tests/test_tool_callbacks.py)

每个文件的 SHA-256 与固定提交记录见 [manifest.json](manifest.json)。章节内容为独立中文源码分析，功能主题参考用户提供的阅读方向，不复制第三方教程正文。
