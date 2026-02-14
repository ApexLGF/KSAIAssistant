# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

TestAIAgent 是一个基于 Python 的 AI 代理框架，集成了 OpenAI API、MCP (Model Context Protocol) 服务器和自定义 Skills 系统。支持多轮对话、工具执行和命令解析。

## 开发命令

### 安装
```bash
pip install -e .
```

### 运行代理
```bash
# 启动交互式对话
python -m agent

# 清除历史记录后启动
python -m agent --clear

# 使用指定配置文件
python -m agent -c my_config.yaml

# 列出可用工具
python -m agent tools

# 列出已加载的 Skills
python -m agent skills
```

### 测试
```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest
```

## 架构设计

### 核心组件

**Agent 主流程** ([agent/core/agent.py](agent/core/agent.py)):
- `Agent` 类协调整个对话循环
- 初始化 MCP 连接、加载 skills、管理工具注册表
- 实现流式对话，自动执行工具调用
- 从 LLM 响应中解析 skill 命令并内联执行

**MCP 集成** ([agent/tools/mcp/](agent/tools/mcp/)):
- `MCPManager` 管理 MCP 服务器连接的生命周期（支持 stdio 和 SSE 传输）
- 使用 `AsyncExitStack` 进行正确的异步上下文管理
- `create_mcp_tools()` 将 MCP 工具包装为代理兼容的工具
- 每个 MCP 服务器连接维护自己的 session 和工具列表

**Skills 系统** ([agent/tools/skills/](agent/tools/skills/)):
- Skills 在 `SKILL.md` 文件中定义，包含 YAML frontmatter
- 两种 skill 类型：
  - `knowledge`: 内容注入到系统 prompt
  - `command`: 注册为可执行工具，LLM 可通过 function calling 调用
- `SkillLoader` 递归查找并解析 `skills_dir` 中的���有 `SKILL.md` 文件
- Command skills 通过 `SkillCommandTool` 包装，支持参数替换和 shell 命令执行
- Skills 可以定义特殊命令标签（如 `[CRON_CREATE]...[/CRON_CREATE]`），从 LLM 响应中解析

**工具注册表** ([agent/tools/registry.py](agent/tools/registry.py)):
- 所有工具的中央注册表（内置、MCP 和未来基于 skill 的工具）
- 将工具转换为 OpenAI function calling 格式
- 处理工具执行和 JSON 参数解析

**上下文管理** ([agent/core/context.py](agent/core/context.py)):
- 管理对话历史，支持可配置的消息数量限制
- 处理 OpenAI 消息格式（user、assistant、tool results）
- 通过 `HistoryStorage` 持久化到 JSON 文件

### 配置

配置从 `config.yaml` 加载（参见 [config.py](agent/config.py)）：
- OpenAI API 设置（key、model、base_url）
- MCP 服务器定义（name、transport、command/url、args）
- Skills 目录路径
- 历史文件位置和最大消息数

**重要**: 配置文件可能包含 API 密钥，切勿提交真实密钥。

### Skill 命令系统

代理可以从 LLM 响应中解析特殊命令标签：
- `[CRON_CREATE]...[/CRON_CREATE]`: 创建定时任务
- `[CRON_LIST]`: 列出定时任务
- `[CRON_DELETE: job-id]`: 删除定时任务

检测到这些命令后，会立即执行并将结果注入回对话。

## 关键设计模式

1. **异步优先**: 所有 I/O 操作（LLM 调用、MCP 通信、工具执行）都是异步的
2. **工具抽象**: 所有能力（命令、MCP 工具、未来的 skills）实现相同的 `Tool` 接口
3. **流式处理**: LLM 响应在处理时流式输出到控制台
4. **对话循环**: Agent 持续调用 LLM 直到没有工具调用，然后返回最终响应
5. **优雅降级**: MCP 连接失败记录为警告而非错误

## 添加新功能

### 添加新的内置工具
1. 在 [agent/tools/](agent/tools/) 中创建继承自 `Tool` 的类
2. 实现 `name`、`description`、`parameters` 和 `execute()` 方法
3. 在 `Agent.initialize()` 中通过 `self.registry.register(YourTool())` 注册

### 添加新的 Skill

#### Knowledge 类型 Skill
1. 在 `skills/` 下创建目录
2. 添加带 YAML frontmatter 的 `SKILL.md` 文件：
   ```yaml
   ---
   name: your-skill
   description: 这个 skill 的功能
   type: knowledge
   ---

   你的 skill 内容...
   ```
3. Skill 会在代理启动时自动加载，内容注入到系统 prompt

#### Command 类型 Skill
1. 在 `skills/` 下创建目录
2. 添加带 YAML frontmatter 的 `SKILL.md` 文件：
   ```yaml
   ---
   name: your-command
   description: 这个命令的功能
   type: command
   command: echo "Hello, {name}!"
   parameters:
     type: object
     properties:
       name:
         type: string
         description: 参数说明
     required:
       - name
   ---

   命令说明文档...
   ```
3. Command skill 会被注册为工具，LLM 可以通过 function calling 调用
4. 命令中的 `{param_name}` 会被实际参数值替换（自动转义）

### 添加新的 MCP 服务器
在 `config.yaml` 中添加：
```yaml
mcp_servers:
  - name: your-server
    transport: stdio  # 或 sse
    command: npx
    args: ["-y", "@your/mcp-server"]
```

## 常见问题

- MCP 服务器必须已安装并可通过指定命令访问
- Skills 必须有有效的 YAML frontmatter，否则加载失败
- 工具名称在所有来源（内置、MCP、skills）中必须唯一
- 除非设置 `max_history_messages`，否则历史文件会无限增长
