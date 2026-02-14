---
name: weather
description: Query information for any city using wttr.in
type: knowledge
---

# Weather Query Skill

You can check the weather for any location using the `run_command` tool with `curl`.

## Usage

When the user asks for weather information (e.g., "What's the weather in Beijing?", "Forecast for Tokyo"), use the `run_command` tool to query `wttr.in`.

### Command Template

```bash
curl -s "wttr.in/{location}?format=3"
```
Or for more details:
```bash
curl -s "wttr.in/{location}"
```

### Examples

**User:** "What is the weather in Shanghai?"
**Tool Action:**
```json
{
  "name": "run_command",
  "arguments": {
    "command": "curl -s 'wttr.in/Shanghai?format=3'"
  }
}
```

**User:** "Beijing weather forecast"
**Tool Action:**
```json
{
  "name": "run_command",
  "arguments": {
    "command": "curl -s 'wttr.in/Beijing'"
  }
}
```

## Handling Results

The command will return a text representation of the weather.
- `format=3` returns a one-line summary (e.g., "Shanghai: ⛅️  +25°C").
- Without options, it returns a full ASCII art forecast table.

Present the output nicely to the user.
