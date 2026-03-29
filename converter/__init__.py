"""
mcp-to-skill SDK
=================
Python SDK for converting MCP servers to Claude Skills.
"""

from .converter import (
    MCPConfig,
    SkillConfig,
    SkillInfo,
    Transport,
    MCPConverterError,
    ConversionError,
    ValidationError,
    convert_to_skill,
    validate_skill,
    test_skill,
    get_skill_status,
    reset_skill_stats,
)

__version__ = "2.0.0"

__all__ = [
    "MCPConfig",
    "SkillConfig",
    "SkillInfo",
    "Transport",
    "MCPConverterError",
    "ConversionError",
    "ValidationError",
    "convert_to_skill",
    "validate_skill",
    "test_skill",
    "get_skill_status",
    "reset_skill_stats",
]
