"""Configuration model for TestAIAgent."""

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator


class OpenAIConfig(BaseModel):
    """OpenAI API configuration."""

    api_key: str = Field(default="")
    model: str = Field(default="gpt-5.2")
    base_url: str | None = Field(default=None)


class DeepSeekConfig(BaseModel):
    """DeepSeek API configuration."""

    api_key: str = Field(default="")
    model: str = Field(default="deepseek-chat")
    base_url: str = Field(default="https://api.deepseek.com")


class MCPServerConfig(BaseModel):
    """MCP Server configuration."""
    
    name: str
    transport: str = Field(default="stdio")  # stdio or sse
    command: str | None = Field(default=None)
    args: list[str] = Field(default_factory=list)
    url: str | None = Field(default=None)  # For SSE transport


class Config(BaseModel):
    """Main configuration model."""

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    deepseek: DeepSeekConfig = Field(default_factory=DeepSeekConfig)
    mcp_servers: list[MCPServerConfig] = Field(default_factory=list)
    skills_dir: str = Field(default="./skills")
    history_file: str = Field(default="./data/history.json")
    max_history_messages: int = Field(default=500)
    
    @model_validator(mode="before")
    @classmethod
    def expand_env_vars(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Expand environment variables in string values."""
        return _expand_env_vars_recursive(data)


def _expand_env_vars_recursive(obj: Any) -> Any:
    """Recursively expand ${VAR} patterns in strings."""
    if isinstance(obj, str):
        # Match ${VAR_NAME} pattern
        pattern = r"\$\{([^}]+)\}"
        
        def replace(match: re.Match) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, "")
        
        return re.sub(pattern, replace, obj)
    elif isinstance(obj, dict):
        return {k: _expand_env_vars_recursive(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_expand_env_vars_recursive(item) for item in obj]
    return obj


def load_config(config_path: str | Path | None = None) -> Config:
    """Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default config.yaml
        
    Returns:
        Loaded and validated Config object
    """
    if config_path is None:
        config_path = Path("config.yaml")
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        # Return default config if file doesn't exist
        return Config()
    
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    
    return Config.model_validate(data)
