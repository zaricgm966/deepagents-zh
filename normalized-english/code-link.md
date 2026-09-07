
# Deep Agents Code

> Terminal coding agent built on the Deep Agents SDK

Deep Agents Code (`dcode`) is an open source coding agent built on the [Deep Agents SDK](/oss/python/deepagents/quickstart).
It works with any large language model and supports switching providers or models.
Persistent memory carries context across conversations, customizable skills shape behavior, and approval controls gate code execution.

## Get started

Run the following command to install Deep Agents Code and launch an interactive session:


```bash
curl -LsSf https://langch.in/dcode | bash
dcode
```


See the [Quickstart](/oss/deepagents/code/quickstart) to add provider credentials, run your first task, and learn interactive mode.

  <video autoPlay muted loop playsInline className="w-full aspect-video rounded-xl" src="https://mintcdn.com/langchain-5e9cc07a/RVTbVyxmLiI04cgS/oss/images/deepagents/dcode-small.mp4?fit=max&auto=format&n=RVTbVyxmLiI04cgS&q=85&s=0d35e29a34f349183e83bd3d1eceb68b" aria-label="Deep Agents Code terminal demo" data-path="oss/images/deepagents/dcode-small.mp4">
    Your browser does not support the video tag.
  </video>

## Capabilities

  
**Remote sandboxes**

[查看相关页面](/oss/deepagents/code/remote-sandboxes)

    Run agent tools remotely instead of on your local machine.
  


  
**Goals and rubrics**

[查看相关页面](/oss/deepagents/code/goals-and-rubrics)

    Define measurable objectives or grading criteria so the agent can check whether work is done.
  


  
**Subagents**

[查看相关页面](/oss/deepagents/code/subagents)

    Delegate work to task-specific subagents for parallel execution.
  


  
**Memory**

[查看相关页面](/oss/deepagents/code/memory-and-skills#memory)

    Store and retrieve information across sessions, including project conventions and learned patterns.
  


  
**Context compaction**

[查看相关页面](/oss/deepagents/code/quickstart#interactive-mode)

    Summarize older messages and offload originals to storage.
  


  
**Human-in-the-loop**

[查看相关页面](/oss/deepagents/code/quickstart#interactive-mode)

    Require human approval for sensitive tool operations.
  


  
**Skills**

[查看相关页面](/oss/deepagents/code/memory-and-skills#skills)

    Extend agent capabilities with custom expertise and instructions.
  


  
**MCP tools**

[查看相关页面](/oss/deepagents/code/mcp-tools)

    Load external tools from Model Context Protocol servers.
  


  
**Tracing**

[查看相关页面](/oss/deepagents/code/quickstart#trace-with-langsmith)

    Trace agent operations in LangSmith for observability and debugging.
  

## Next steps

  
**Quickstart**

[查看相关页面](/oss/deepagents/code/quickstart)

    Install Deep Agents Code, run your first task, and use interactive or non-interactive modes.
  


  
**Configuration**

[查看相关页面](/oss/deepagents/code/configuration)

    Set up credentials, `config.toml`, environment variables, hooks, and CLI flags.
  

***

<div className="source-links">
  

    [Connect these docs](/use-these-docs) to Claude, VSCode, and more via MCP for real-time answers.
  


  

    [Edit this page on GitHub](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/code/overview.mdx) or [file an issue](https://github.com/langchain-ai/docs/issues/new/choose).
  

</div>
