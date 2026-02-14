---
name: hello
description: 向指定的人打招呼
type: command
command: echo "你好，{name}！今天是 $(date '+%Y-%m-%d')"
parameters:
  type: object
  properties:
    name:
      type: string
      description: 要打招呼的人的名字
  required:
    - name
---

# Hello Command Skill

这是一个简单的 command 类型 skill 示例。

## 功能

向指定的人打招呼，并显示当前日期。

## 参数

- `name`: 要打招呼的人的名字（必填）

## 示例

当 LLM 调用这个工具时：
```json
{
  "name": "张三"
}
```

会执行命令：
```bash
echo "你好，张三！今天是 2024-02-13"
```
