# 构建内容生成器代理


> 建立一个具有品牌记忆、技能、子智能体和图像生成的内容写作代理


## 概述


本指南演示如何使用 [Deep Agents](overview.md) 从头开始​​构建内容编写代理。


您构建的代理将：


1. 从 `AGENTS.md` 和技能文件夹加载语音和工作流程规则
2. 使用 `web_search` 将网络研究委托给专门的子智能体
3. 根据加载的技能起草博客或社交内容
4. 使用 Gemini 生成封面或社交图像并将文件保存在项目目录下


本教程中的代码连接到图像生成工具和文件系统后端，以便代理可以在项目目录下读取和写入帖子、研究笔记和图像。有关完整的可运行项目，请参阅 [content-builder-agent](https://github.com/langchain-ai/deepagents/tree/main/examples/content-builder-agent) 示例。


### 关键概念


本教程涵盖：


* [长期记忆](memory.md) TODO
* [技能](skills.md) TODO
* [子智能体](subagents.md) TODO
* [文件系统后端](backends.md) 用于文件读写
* 用于搜索和图像生成的自定义[工具](https://docs.langchain.com/oss/python/langchain/tools)


## 先决条件


API 密钥：


* Anthropic (Claude) 或其他提供商 API 密钥
* Google (Gemini) 使用 `gemini-2.5-flash-image` 生成图像
* [Tavily](https://www.tavily.com/) 用于网络搜索（免费套餐）
* [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-deepagents-content-builder) 用于跟踪（可选）


Python 3.11 或更高版本。


## 设置


  
**创建项目目录**


```bash
mkdir content-builder-agent
cd content-builder-agent
```


  


  

 **安装依赖项**


    


```bash
pip install deepagents google-genai pillow pyyaml rich tavily-python langchain
```


```bash
uv init
uv add deepagents google-genai pillow pyyaml rich tavily-python langchain
uv sync
```


    


 将 `deepagents` 固定到您自己的项目中支持的范围（例如 `>=0.3.5,<0.4.0`）以匹配上游示例。

  


  
**设置 API 密钥**


```bash
export ANTHROPIC_API_KEY="your_anthropic_api_key"
export GOOGLE_API_KEY="your_google_api_key"
export TAVILY_API_KEY="your_tavily_api_key"           # Optional
export LANGSMITH_API_KEY="your_langsmith_api_key"     # Optional
```


  


## 添加配置文件


该示例将行为保存在三种文件中：内存、技能和子智能体定义。


  
**添加代理.md**


在项目根目录中创建`AGENTS.md`。当您稍后创建代理并将此文件指定为 [内存](memory.md) 参数的一部分时，它会将此文件加载到系统提示符中，以便品牌声音和研究期望适用于每次运行。


```markdown
# Content Writer Agent

You are a content writer for a technology company. Your job is to create engaging, informative content that educates readers about AI, software development, and emerging technologies.

## Brand Voice

- **Professional but approachable**: Write like a knowledgeable colleague, not a textbook
- **Clear and direct**: Avoid jargon unless necessary; explain technical concepts simply
- **Confident but not arrogant**: Share expertise without being condescending
- **Engaging**: Use concrete examples, analogies, and stories to illustrate points

## Writing Standards

1. **Use active voice**: "The agent processes requests" not "Requests are processed by the agent"
2. **Lead with value**: Start with what matters to the reader, not background
3. **One idea per paragraph**: Keep paragraphs focused and scannable
4. **Concrete over abstract**: Use specific examples, numbers, and case studies
5. **End with action**: Every piece should leave the reader knowing what to do next

## Content Pillars

Our content focuses on:
- AI agents and automation
- Developer tools and productivity
- Software architecture and best practices
- Emerging technologies and trends

## Formatting Guidelines

- Use headers (H2, H3) to break up long content
- Include code examples where relevant (with syntax highlighting)
- Add bullet points for lists of 3+ items
- Keep sentences under 25 words when possible
- Include a clear call-to-action at the end

## Research Requirements

Before writing on any topic:
1. Use the `researcher` subagent for in-depth topic research
2. Gather at least 3 credible sources
3. Identify the key points readers need to understand
4. Find concrete examples or case studies to illustrate concepts
```


 要使此代理符合您自己的语气、支柱和格式规则，请更新 `AGENTS.md` 中的文本。

  


  
**添加子智能体.yaml**


创建一个名为 `subagents.yaml` 的文件。然后添加以下文本，其中描述了 `researcher` 子智能体以及 Tavily 支持的 `web_search` 工具、Haiku 模型 ID 以及将结果保存到从主代理委派时指定的路径的说明：


```yaml
# Subagent definitions
# These are loaded by content_writer.py and wired up with tools

researcher:
  description: >
    ALWAYS use this first to research any topic before writing content.
    Searches the web for current information, statistics, and sources.
    When delegating, tell it the topic AND the file path to save results
    (e.g., 'Research renewable energy and save to research/renewable-energy.md').
  model: anthropic:claude-haiku-4-5-20251001
  system_prompt: |
    You are a research assistant. You have access to web_search and write_file tools.

    ## Your Tools
    - web_search(query, max_results=5, topic="general") - Search the web
    - write_file(file_path, content) - Save your findings

    ## Your Process
    1. Use web_search to find information on the topic
    2. Make 2-3 targeted searches with specific queries
    3. Gather key statistics, quotes, and examples
    4. Save findings to the file path specified in your task

    ## Important
    - The user will tell you WHERE to save the file - use that exact path
    - Always include source URLs in your findings
    - Keep findings concise but informative
  tools:
    - web_search
```


 稍后在创建深度智能体时，该文件将作为参数传递。

  


  
**添加技能**


创建 `skills/` 目录。每个技能都是一个文件夹，其中包含 `SKILL.md` 文件，其中包含 YAML frontmatter（`name`、`description`）和技能说明。


创建 `skills/blog-post/SKILL.md` 并将以下文本复制到其中，其中包含有关创建长篇帖子、优化 SEO 内容和生成封面图像的信息。


````md
---
name: blog-post
description: Writes and structures long-form blog posts, creates tutorial outlines, and optimizes content for SEO with cover image generation. Use when the user asks to write a blog post, article, how-to guide, tutorial, technical writeup, thought leadership piece, or long-form content.
---

# Blog Post Writing Skill

## Research First (Required)

**Before writing any blog post, you MUST delegate research:**

1. Use the `task` tool with `subagent_type: "researcher"`
2. In the description, specify BOTH the topic AND where to save:

```


 任务（ subagent_type =“researcher”，description =“研究[主题]。将结果保存到研究/[slug].md”）


```

Example:
```


 任务（subagent_type =“researcher”，description =“研究2025年人工智能代理的现状。将研究结果保存到research/ai-agents-2025.md”）


```

3. After research completes, read the findings file before writing

## Output Structure (Required)

**Every blog post MUST have both a post AND a cover image:**

```


 blogs/ └── <slug>/ ├── post.md # 博文内容 └── Hero.png # 必需：生成的封面图片


```

Example: A post about "AI Agents in 2025" → `blogs/ai-agents-2025/`

**You MUST complete both steps:**
1. Write the post to `blogs/<slug>/post.md`
2. Generate a cover image using `generate_image` and save to `blogs/<slug>/hero.png`

**A blog post is NOT complete without its cover image.**

## Blog Post Structure

Every blog post should follow this structure:

### 1. Hook (Opening)
- Start with a compelling question, statistic, or statement
- Make the reader want to continue
- Keep it to 2-3 sentences

### 2. Context (The Problem)
- Explain why this topic matters
- Describe the problem or opportunity
- Connect to the reader's experience

### 3. Main Content (The Solution)
- Break into 3-5 main sections with H2 headers
- Each section covers one key point
- Include code examples, diagrams, or screenshots where helpful
- Use bullet points for lists

### 4. Practical Application
- Show how to apply the concepts
- Include step-by-step instructions if applicable
- Provide code snippets or templates

### 5. Conclusion & CTA
- Summarize key takeaways (3 bullets max)
- End with a clear call-to-action
- Link to related resources

## Cover Image Generation

After writing the post, generate a cover image using the `generate_cover` tool:

```


 generate_cover(prompt="图像的详细描述...", slug="your-blog-slug")


```

The tool saves the image to `blogs/<slug>/hero.png`.

### Writing Effective Image Prompts

Structure your prompt with these elements:

1. **Subject**: What is the main focus? Be specific and concrete.
2. **Style**: Art direction (minimalist, isometric, flat design, 3D render, watercolor, etc.)
3. **Composition**: How elements are arranged (centered, rule of thirds, symmetrical)
4. **Color palette**: Specific colors or mood (warm earth tones, cool blues and purples, high contrast)
5. **Lighting/Atmosphere**: Soft diffused light, dramatic shadows, golden hour, neon glow
6. **Technical details**: Aspect ratio considerations, negative space for text overlay

### Example Prompts

**For a technical blog post:**
```


 代表 AI 代理的互连发光立方体的等距 3D 插图，每个立方体都有微妙的电路图案。通过发光数据流连接的立方体。深海军蓝背景 (#0a192f) 带有电蓝色 (#64ffda) 和柔和的紫色 (#c792ea) 口音。干净简约的风格，顶部有很多负空间作为标题。专业科技美学。


```

**For a tutorial/how-to:**
```


 干净的平面插图显示手在键盘上打字，抽象代码符号向上浮动，变成灯泡和齿轮。从软珊瑚到浅桃色的温暖渐变背景。风格友善、平易近人。居中构图，带有文本叠加空间。


```

**For thought leadership:**
```


 与几何神经网络模式合并的人体轮廓轮廓的抽象可视化。分割构图-左侧的有机水彩纹理过渡到右侧的干净矢量线。柔和的鼠尾草绿色和温暖的赤土色配色方案。沉思、前瞻性的心情。


```

## SEO Considerations

- Include the main keyword in the title and first paragraph
- Use the keyword naturally 3-5 times throughout
- Keep the title under 60 characters
- Write a meta description (150-160 characters)

## Quality Checklist

Before finishing:
- [ ] Post saved to `blogs/<slug>/post.md`
- [ ] Hero image generated at `blogs/<slug>/hero.png`
- [ ] Hook grabs attention in first 2 sentences
- [ ] Each section has a clear purpose
- [ ] Conclusion summarizes key points
- [ ] CTA tells reader what to do next
````

Next, create `skills/social-media/SKILL.md` and copy the following text into it which contains information on drafting social media posts and generating accompanying imagery:

````md expandable wrap theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
---
name: social-media
description: Drafts engaging social media posts, writes hooks, suggests hashtags, creates thread structures, and generates companion images. Use when the user asks to write a LinkedIn post, tweet, Twitter/X thread, social media caption, social post, or repurpose content for social platforms.
---

# Social Media Content Skill

## Research First (Required)

**Before writing any social media content, you MUST delegate research:**

1. Use the `task` tool with `subagent_type: "researcher"`
2. In the description, specify BOTH the topic AND where to save:

```


 任务（ subagent_type =“researcher”，description =“研究[主题]。将结果保存到研究/[slug].md”）


```

Example:
```


 任务（subagent_type =“researcher”，description =“研究2025年可再生能源趋势。将研究结果保存到research/renewable-energy.md”）


```

3. After research completes, read the findings file before writing

## Output Structure (Required)

**Every social media post MUST have both content AND an image:**

**LinkedIn posts:**
```


 linkedin/ └── <slug>/ ├── post.md # 帖子内容 └── image.png # 必需：生成的视觉效果


```

**Twitter/X threads:**
```


 tweets/ └── <slug>/ ├── thread.md # 话题内容 └── image.png # 必需：生成的视觉效果


```

Example: A LinkedIn post about "prompt engineering" → `linkedin/prompt-engineering/`

**You MUST complete both steps:**
1. Write the content to the appropriate path
2. Generate an image using `generate_image` and save alongside the post

**A social media post is NOT complete without its image.**

## Platform Guidelines

### LinkedIn

**Format:**
- 1,300 character limit (show more after ~210 chars)
- First line is crucial - make it hook
- Use line breaks for readability
- 3-5 hashtags at the end

**Tone:**
- Professional but personal
- Share insights and learnings
- Ask questions to drive engagement
- Use "I" and share experiences

**Structure:**
```


 [钩子 - 1 条引人注目的线]


[空行]


[背景 - 为什么这很重要]


[空行]


[主要见解 - 2-3 个短段落]


[空行]


[号召性用语或问题]


#hashtag1 #hashtag2 #hashtag3


```

### Twitter/X

**Format:**
- 280 character limit per tweet
- Threads for longer content (use 1/🧵 format)
- No more than 2 hashtags per tweet

**Thread Structure:**
```


 1/🧵【Hook——主要洞察】


2/【支撑点1】


3/【支撑点2】


4/ [示例或证据]


5/【结论+CTA】


```

## Image Generation

Every social media post needs an eye-catching image. Use the `generate_social_image` tool:

```


 generate_social_image(prompt="详细描述...", platform="linkedin", slug="your-post-slug")


```

The tool saves the image to `<platform>/<slug>/image.png`.

### Social Image Best Practices

Social images need to work at small sizes in crowded feeds:
- **Bold, simple compositions** - one clear focal point
- **High contrast** - stands out when scrolling
- **No text in image** - too small to read, platforms add their own
- **Square or 4:5 ratio** - works across platforms

### Writing Effective Prompts

Include these elements:

1. **Single focal point**: One clear subject, not a busy scene
2. **Bold style**: Vibrant colors, strong shapes, high contrast
3. **Simple background**: Solid color, gradient, or subtle texture
4. **Mood/energy**: Match the post tone (inspiring, urgent, thoughtful)

### Example Prompts

**For an insight/tip post:**
```


 单个发光灯泡漂浮在深紫色渐变背景上，灯泡由互连的金色几何线条制成，柔和的光线向外散发。最小、引人注目、高对比度。方形构图。


```

**For announcements/news:**
```


 抽象火箭船由彩色几何形状制成，带有粒子尾迹向上发射。明亮的珊瑚色和青色配色方案与干净的白色背景相对应。充满活力、喜庆的气氛。大胆的平面插画风格。


```

**For thought-provoking content:**
```


 两个重叠的半透明圆圈，一个蓝色一个橙色，在中心形成一个发光的交叉点。代表协作或想法的交集。深色木炭背景，柔和空灵的光芒。极简主义和沉思。


```

## Content Types

### Announcement Posts
- Lead with the news
- Explain the impact
- Include link or next step

### Insight Posts
- Share one specific learning
- Explain the context briefly
- Make it actionable

### Question Posts
- Ask a genuine question
- Provide your take first
- Keep it focused on one topic

## Quality Checklist

Before finishing:
- [ ] Post saved to `linkedin/<slug>/post.md` or `tweets/<slug>/thread.md`
- [ ] Image generated alongside the post
- [ ] First line hooks attention
- [ ] Content fits platform limits
- [ ] Tone matches platform norms
- [ ] Has clear CTA or question
- [ ] Hashtags are relevant (not generic)
````

They instruct the agent to call the `researcher` subagent first, write markdown under `blogs/`, `linkedin/`, or `tweets/`, and call `generate_cover` or `generate_social_image` for images.

When you later create the agent and specify the skills folder(s), then the frontmatter of the `SKILLS.md` files from those skill folders get loaded this into the system prompt so the agent can use the skill when a task matches a skill description.
  </Step>
</Steps>

## Build the script

Create `content_writer.py` in the project root. The following sections belong in one file, in order.

<Steps>
  <Step title="Add tools">
The researcher subagent uses Tavily search.
Blog and social workflows use Gemini image generation.
When creating the agent later, the `load_subagents` function reads `subagents.yaml` and resolves tool names to these decorated functions.

```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
import os
from pathlib import Path
from typing import Literal

import yaml
from langchain.tools import tool

EXAMPLE_DIR = Path(__file__).parent


@tool
def web_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news"] = "general",
) -> dict:
    """Search the web for current information.

    Args:
        query: The search query (be specific and detailed)
        max_results: Number of results to return (default: 5)
        topic: "general" for most queries, "news" for current events

    Returns:
        Search results with titles, URLs, and content excerpts.
    """
    try:
        from tavily import TavilyClient

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return {"error": "TAVILY_API_KEY not set"}

        client = TavilyClient(api_key=api_key)
        return client.search(query, max_results=max_results, topic=topic)
    except Exception as e:
        return {"error": f"Search failed: {e}"}


@tool
def generate_cover(prompt: str, slug: str) -> str:
    """Generate a cover image for a blog post.

    Args:
        prompt: Detailed description of the image to generate.
        slug: Blog post slug. Image saves to blogs/<slug>/hero.png
    """
    try:
        from google import genai

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                output_path = EXAMPLE_DIR / "blogs" / slug / "hero.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(str(output_path))
                return f"Image saved to {output_path}"

        return "No image generated"
    except Exception as e:
        return f"Error: {e}"


@tool
def generate_social_image(prompt: str, platform: str, slug: str) -> str:
    """Generate an image for a social media post.

    Args:
        prompt: Detailed description of the image to generate.
        platform: Either "linkedin" or "tweets"
        slug: Post slug. Image saves to <platform>/<slug>/image.png
    """
    try:
        from google import genai

        client = genai.Client()
        response = client.models.generate_content(
            model="gemini-2.5-flash-image",
            contents=[prompt],
        )

        for part in response.parts:
            if part.inline_data is not None:
                image = part.as_image()
                output_path = EXAMPLE_DIR / platform / slug / "image.png"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                image.save(str(output_path))
                return f"Image saved to {output_path}"

        return "No image generated"
    except Exception as e:
        return f"Error: {e}"


def load_subagents(config_path: Path) -> list:
    """Load subagent definitions from YAML and wire up tools.

    Unlike `memory` and `skills`, deep agents do not load subagents from files by default.
    This helper externalizes configuration so you can edit YAML without changing Python code.
    """
    available_tools = {
        "web_search": web_search,
    }

    with open(config_path) as f:
        config = yaml.safe_load(f)

    subagents = []
    for name, spec in config.items():
        subagent = {
            "name": name,
            "description": spec["description"],
            "system_prompt": spec["system_prompt"],
        }
        if "model" in spec:
            subagent["model"] = spec["model"]
        if "tools" in spec:
            subagent["tools"] = [available_tools[t] for t in spec["tools"]]
        subagents.append(subagent)

    return subagents
```


  


  

 **创建代理**


使用 [create\_deep\_agent](https://reference.langchain.com/python/deepagents/graph/create_deep_agent) 创建深度智能体时，传递内存路径、技能目录、图像工具、来自 YAML 的子智能体以及根植于示例目录的 [FilesystemBackend](backends.md)，以便正确解析 `./AGENTS.md` 和 `./skills/` 等路径。


    


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="google_genai:gemini-3.6-flash",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="openai:gpt-5.5",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="anthropic:claude-sonnet-4-6",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="openrouter:z-ai/glm-5.2",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="fireworks:accounts/fireworks/models/glm-5p2",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="baseten:zai-org/GLM-5.2",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


```python
from deepagents import create_deep_agent
from deepagents.backends import FilesystemBackend


def create_content_writer():
    """Create a content writer agent configured by filesystem files."""
    return create_deep_agent(
        model="ollama:north-mini-code-1.0",
        memory=["./AGENTS.md"],
        skills=["./skills/"],
        tools=[generate_cover, generate_social_image],
        subagents=load_subagents(EXAMPLE_DIR / "subagents.yaml"),
        backend=FilesystemBackend(root_dir=EXAMPLE_DIR),
    )
```


    

  


  

 **添加入口点**


使用用户消息调用代理以验证代理是否正常工作：


```python
import sys

from langchain.messages import HumanMessage

if __name__ == "__main__":
    task = (
        " ".join(sys.argv[1:])
        if len(sys.argv) > 1
        else "Write a blog post about how AI agents are transforming software development"
    )

    agent = create_content_writer()
    result = agent.invoke(
        {"messages": [HumanMessage(content=task)]},
        config={"configurable": {"thread_id": "content-builder-demo"}},
    )

    for msg in result.get("messages", []):
        if hasattr(msg, "content") and msg.content:
            print(msg.content)
```


  


## 运行代理


文件系统后端可以读取、写入和删除`root_dir`下的文件。仅在专用目录中运行并在发布之前检查生成的内容。


从项目目录中，您可以调用代理而不传递参数或将提示作为参数传递：


```bash
python content_writer.py
```


```bash
python content_writer.py Write a blog post about prompt engineering
```


 设置 `LANGSMITH_API_KEY` 后，您可以检查 [LangSmith](https://docs.langchain.com/langsmith/observability) 中的运行。


## 输出


成功后，生成的工件将写入系统临时目录（在 macOS 和 Linux 上，通常位于 `/tmp/` 下），而不是项目文件旁边。


```text
blogs/
└── prompt-engineering/
    ├── post.md
    └── hero.png
research/
└── prompt-engineering.md
```


 路径遵循`SKILL.md`中的技能说明。


## 完整代码


在 GitHub 上浏览完整的 [content-builder-agent 示例](https://github.com/langchain-ai/deepagents/tree/main/examples/content-builder-agent)，包括基于 Rich 的流式 UI。


## 后续步骤


* 编辑`AGENTS.md`以改变品牌声音和研究要求
* 在 `skills/<name>/SKILL.md` 下添加新内容类型的技能
* 在`subagents.yaml`中添加子智能体并在`load_subagents`中注册工具
* 阅读[子智能体](subagents.md)、[技能](skills.md)和[自定义](customization.md)进行更深入的配置


***


<div className="source-links">


  

[将这些文档](https://docs.langchain.com/use-these-docs) 通过 MCP 连接到 Claude、VSCode 等以获得实时答案。

  


  

[在 GitHub 上编辑此页面](https://github.com/langchain-ai/docs/edit/main/src/oss/deepagents/content-builder.mdx) 或 [提交问题](https://github.com/langchain-ai/docs/issues/new/choose)。

  

</div>

