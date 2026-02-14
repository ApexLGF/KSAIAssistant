# Command Skills 使用指南

Command 类型的 Skill 允许你将 shell 命令包装为 AI 代理可调用的工具。

## 基本格式

```yaml
---
name: tool_name
description: 工具描述
type: command
command: shell命令 {param1} {param2}
parameters:
  type: object
  properties:
    param1:
      type: string
      description: 参数1的说明
    param2:
      type: string
      description: 参数2的说明
  required:
    - param1
---

# 工具文档

这里可以写详细的使用说明...
```

## 参数替换

命令中的 `{param_name}` 会被实际参数值替换：

```yaml
command: echo "Hello, {name}! You are {age} years old."
```

当 LLM 调用时传入：
```json
{
  "name": "张三",
  "age": "25"
}
```

实际执行的命令：
```bash
echo "Hello, 张三! You are 25 years old."
```

**注意**：参数值会自动使用 `shlex.quote()` 转义，防止命令注入。

## 示例

### 1. 简单的问候命令

```yaml
---
name: greet
description: 向指定的人打招呼
type: command
command: echo "你好，{name}！"
parameters:
  type: object
  properties:
    name:
      type: string
      description: 要打招呼的人的名字
  required:
    - name
---
```

### 2. 查询磁盘使用情况

```yaml
---
name: disk_usage
description: 查询指定路径的磁盘使用情况
type: command
command: du -sh {path} 2>/dev/null || echo "路径不存在"
parameters:
  type: object
  properties:
    path:
      type: string
      description: 要查询的目录路径
  required:
    - path
---
```

### 3. 搜索文件内容

```yaml
---
name: search_in_files
description: 在指定目录中搜索包含关键词的文件
type: command
command: grep -r {keyword} {directory} 2>/dev/null || echo "未找到匹配项"
parameters:
  type: object
  properties:
    keyword:
      type: string
      description: 要搜索的关键词
    directory:
      type: string
      description: 搜索的目录路径
  required:
    - keyword
    - directory
---
```

### 4. 带可选参数的命令

```yaml
---
name: list_files
description: 列出目录中的文件
type: command
command: ls {flags} {path}
parameters:
  type: object
  properties:
    path:
      type: string
      description: 目录路径
    flags:
      type: string
      description: ls 命令的标志（如 -la）
      default: "-l"
  required:
    - path
---
```

## 安全注意事项

1. **参数自动转义**：所有参数值都会通过 `shlex.quote()` 转义，防止命令注入
2. **避免危险命令**：不要创建可能删除文件或修改系统的命令
3. **错误处理**：使用 `2>/dev/null` 或 `|| echo "错误信息"` 来处理错误
4. **权限控制**：命令以运行代理的用户权限执行

## 最佳实践

1. **清晰的描述**：写清楚工具的功能和参数说明，帮助 LLM 正确使用
2. **错误处理**：在命令中添加错误处理逻辑
3. **输出格式化**：确保命令输出易于 LLM 理解
4. **参数验证**：在 parameters schema 中明确参数类型和要求
5. **文档完善**：在 SKILL.md 的 markdown 部分写详细的使用说明

## 调试

查看已注册的 command skills：

```bash
python -m agent tools
```

测试 skill 是否正确加载：

```bash
python -m agent skills
```
