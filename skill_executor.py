#!/usr/bin/env python3
"""
MCP to Skill Converter - Skill Executor
========================================
Converts any MCP server configuration into a Claude Skill.
"""

import json
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any


def find_skill_dir() -> Path:
    """Find the skill directory containing this executor."""
    return Path(__file__).parent.absolute()


def find_lib_ts() -> Optional[Path]:
    """Find the lib.ts converter script."""
    skill_dir = find_skill_dir()
    lib_path = skill_dir / "lib.ts"

    if lib_path.exists():
        return lib_path

    # Try parent directory if not found
    parent_lib = skill_dir.parent / "lib.ts"
    if parent_lib.exists():
        return parent_lib

    return None


def check_bun() -> bool:
    """Check if bun is available."""
    try:
        result = subprocess.run(
            ["bun", "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def cmd_convert(args):
    """Convert MCP config to skill."""
    lib_path = find_lib_ts()

    if not lib_path:
        print("Error: lib.ts not found. Please ensure this skill is properly installed.", file=sys.stderr)
        sys.exit(1)

    if not check_bun():
        print("Error: bun runtime not found. Install with: curl -fsSL https://bun.sh/install | bash", file=sys.stderr)
        sys.exit(1)

    # Validate config file
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {args.config}", file=sys.stderr)
        sys.exit(1)

    # Build command
    cmd = ["bun", str(lib_path), "convert", str(config_path)]

    if args.output:
        cmd.append(f"--output={args.output}")

    if args.no_install:
        cmd.append("--no-install")

    # Execute
    print(f"Converting MCP config: {args.config}")
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error: Conversion failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("Error: bun runtime not found. Install with: curl -fsSL https://bun.sh/install | bash", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args):
    """Validate a generated skill."""
    lib_path = find_lib_ts()

    if not lib_path:
        print("Error: lib.ts not found.", file=sys.stderr)
        sys.exit(1)

    if not check_bun():
        print("Error: bun runtime not found.", file=sys.stderr)
        sys.exit(1)

    skill_path = Path(args.path)
    if not skill_path.exists():
        print(f"Error: Skill path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    cmd = ["bun", str(lib_path), "validate", str(skill_path)]

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error: Validation failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)


def cmd_test(args):
    """Test a skill."""
    lib_path = find_lib_ts()

    if not lib_path:
        print("Error: lib.ts not found.", file=sys.stderr)
        sys.exit(1)

    if not check_bun():
        print("Error: bun runtime not found.", file=sys.stderr)
        sys.exit(1)

    skill_path = Path(args.path)
    if not skill_path.exists():
        print(f"Error: Skill path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    cmd = ["bun", str(lib_path), "test", str(skill_path)]

    if args.mode == "list":
        cmd.append("--list")
    elif args.mode == "describe":
        if not args.tool:
            print("Error: --describe requires --tool argument", file=sys.stderr)
            sys.exit(1)
        cmd.extend(["--describe", args.tool])
    else:
        print(f"Error: Invalid mode: {args.mode}", file=sys.stderr)
        sys.exit(1)

    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"Error: Test failed with exit code {e.returncode}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args):
    """Get skill status using the skill's executor."""
    skill_path = Path(args.path)
    if not skill_path.exists():
        print(f"Error: Skill path not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    executor = skill_path / "executor.py"
    if not executor.exists():
        print(f"Error: executor.py not found in skill directory", file=sys.stderr)
        sys.exit(1)

    cmd = ["uv", "run", "python", "executor.py", "--status"]
    try:
        result = subprocess.run(cmd, cwd=skill_path, capture_output=True, text=True, check=True)
        print(result.stdout)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="MCP to Skill Converter - Convert any MCP server to a Claude Skill",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert MCP config to skill
  uv run skill_executor.py convert my-mcp.json

  # Convert with custom output
  uv run skill_executor.py convert my-mcp.json --output=/custom/path

  # Validate generated skill
  uv run skill_executor.py validate ~/.claude/skills/my-mcp

  # Test skill tools
  uv run skill_executor.py test ~/.claude/skills/my-mcp --list
  uv run skill_executor.py test ~/.claude/skills/my-mcp --describe tool_name

  # Get skill status
  uv run skill_executor.py status ~/.claude/skills/my-mcp

MCP Config Format (JSON):
  {
    "name": "my-mcp",
    "transport": "stdio|sse|http",
    "command": "npx",           // for stdio
    "args": ["@example/mcp"],   // for stdio
    "endpoint": "https://...",  // for sse/http
    "env": {"API_KEY": "..."}
  }
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert MCP config to skill')
    convert_parser.add_argument('config', help='Path to MCP configuration JSON file')
    convert_parser.add_argument('--output', '-o', help='Custom output directory (default: ~/.claude/skills/{name})')
    convert_parser.add_argument('--no-install', action='store_true', help='Skip dependency installation')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a generated skill')
    validate_parser.add_argument('path', help='Path to skill directory')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test a skill')
    test_parser.add_argument('path', help='Path to skill directory')
    test_parser.add_argument('--mode', choices=['list', 'describe'], default='list',
                             help='Test mode: list tools or describe a tool')
    test_parser.add_argument('--tool', help='Tool name (required for describe mode)')

    # Status command
    status_parser = subparsers.add_parser('status', help='Get skill status and statistics')
    status_parser.add_argument('path', help='Path to skill directory')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'convert':
        cmd_convert(args)
    elif args.command == 'validate':
        cmd_validate(args)
    elif args.command == 'test':
        cmd_test(args)
    elif args.command == 'status':
        cmd_status(args)


if __name__ == '__main__':
    main()
