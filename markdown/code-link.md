# 深度智能体代码


> 基于 Deep Agents SDK 构建的终端编程智能体


Deep Agents Code (`dcode`) 是一个基于 [Deep Agents SDK](quickstart.md) 构建的开源编程智能体。它适用于任何大型语言模型，并支持切换提供者或模型。持久记忆在对话中承载上下文，可定制的技能塑造行为，批准控制门代码执行。


## 开始使用


运行以下命令来安装 Deep Agents Code 并启动交互式会话：


```bash
curl -LsSf https://langch.in/dcode | bash
dcode
```


 请参阅[快速入门](https://docs.langchain.com/oss/deepagents/code/quickstart) 以添加提供商凭据、运行第一个任务并学习交互模式。


  <video autoPlay muted loop playsInline className="w-full aspect-video rounded-xl" src="../assets/d8284da4da7058dd.mp4" aria-label="Deep Agents Code terminal demo" data-path="oss/images/deepagents/dcode-small.mp4">
您的浏览器不支持视频标签。  </video>


## 能力


  
**远程沙箱**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/remote-sandboxes)


远程运行代理工具，而不是在本地计算机上。

  


  
**目标和准则**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/goals-and-rubrics)


定义可衡量的目标或评分标准，以便代理可以检查工作是否完成。

  


  
**子智能体**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/subagents)


将工作委托给特定于任务的子智能体以并行执行。

  


  
**记忆**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/memory-and-skills#memory)


跨会话存储和检索信息，包括项目约定和学习模式。

  


  
**上下文压缩**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/quickstart#interactive-mode)


总结较旧的消息并将原始消息卸载到存储中。

  


  
**人在回路**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/quickstart#interactive-mode)


敏感工具操作需要人工批准。

  


  
**技能**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/memory-and-skills#skills)


通过定制专业知识和说明扩展代理的能力。

  


  
**MCP 工具**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/mcp-tools)


从模型上下文协议服务器加载外部工具。

  


  
**追踪**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/quickstart#trace-with-langsmith)


跟踪 LangSmith 中的代理操作以实现可观察性和调试。

  

## 后续步骤


  
**快速入门**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/quickstart)


安装 Deep Agents Code，运行您的第一个任务，并使用交互或非交互模式。

  


  
**配置**


[查看相关页面](https://docs.langchain.com/oss/deepagents/code/configuration)


设置凭据、`config.toml`、环境变量、挂钩和 CLI 标志。

  

***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/code/overview.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

