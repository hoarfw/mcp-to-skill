---
name: mcp-to-skill
description: 将指定MCP 服务器封装为Skill，支持 stdio/SSE/HTTP 传输协议
---

# MCP to Skill Converter (Multi-transport)

将任何 MCP 服务器封装为 Claude Skill，支持多种传输协议（stdio/SSE/HTTP），使用渐进式加载模式节省上下文消耗。

## Supported Transports

### stdio (默认)

标准输入输出传输，大多数 MCP 服务器使用此协议。

**配置示例：**
```json
{
  "name": "github",
  "transport": "stdio",
  "command": "npx",
  "args": ["@modelcontextprotocol/server-github"],
  "env": {"GITHUB_TOKEN": "your-token"}
}
```

### SSE (Server-Sent Events)

通过 HTTP SSE 连接 MCP 服务器，适用于远程 MCP 服务。

**配置示例：**
```json
{
  "name": "deepwiki",
  "transport": "sse",
  "endpoint": "https://mcp.deepwiki.com/sse",
  "env": {}
}
```

**SSE 协议流程：**
1. 连接到 SSE endpoint
2. 监听 `endpoint` 事件获取 postUrl
3. 发送 JSON-RPC 请求（initialize, tools/call）
4. 接收 SSE 响应消息

### HTTP

HTTP 轮询传输协议（实验性）。

**配置示例：**
```json
{
  "name": "http-mcp",
  "transport": "http",
  "endpoint": "https://api.example.com/mcp",
  "env": {}
}
```

## Available Operations

### `convert`

将 MCP 服务器配置转换为 Skill。

**参数：**
- `mcp_config` (object, required): MCP 服务器配置
  ```json
  {
    "name": "server-name",
    "transport": "stdio|sse|http",
    "command": "npx",  // stdio only
    "args": ["@example/mcp-server"],  // stdio only
    "endpoint": "https://...",  // sse/http only
    "env": {"API_KEY": "your-key"}
  }
  ```
- `output_dir` (string, optional): 输出目录，询问用户是用户级别还是项目级别，如果项目为 `.claude/skills/{name}`,如何是用户级别是`~/.claude/skills/{name}

**返回：**
- 生成的技能路径
- 工具列表
- 上下文节省统计

### `validate`

验证生成的技能是否可用。

**参数：**
- `skill_path` (string, required): 技能目录路径

**返回：**
- 验证结果
- 工具列表
- 传输协议类型

### `test`

测试技能的工具调用。

**参数：**
- `skill_path` (string, required): 技能目录路径
- `tool_name` (string, optional): 要测试的工具名，默认 `--list`
- `args` (object, optional): 工具调用参数

## Usage Pattern

### Step 1: 转换为 Skill

```bash
cd $SKILL_DIR
uv run skill_executor.py convert /path/to/my-mcp.json
```

**注意**: 将 `$SKILL_DIR` 替换为实际的 mcp-to-skill 技能目录路径。

### Step 2: 验证技能

```bash
cd $SKILL_DIR
uv run skill_executor.py validate .claude/skills/my-mcp
```

### Step 3: 测试技能

```bash
cd $SKILL_DIR
uv run skill_executor.py test .claude/skills/my-mcp --list
```

### Step 4: 查看状态和统计

```bash
cd ~/.claude/skills/my-mcp

# 查看状态
uv run executor.py --status

# 查看统计
uv run executor.py --stats

# 查看日志
uv run executor.py --logs 100

# 重置统计
uv run executor.py --reset-stats
```

### Step 5: 更新SKILL的描述

更新生成.claude/skills/{name}/SKILL.md的description的描述，将mcp的功能生成清晰简洁的描述


## Examples

### Example 1: stdio 传输

```bash
cd $SKILL_DIR

# 创建配置文件
cat > github-mcp.json << 'EOF'
{
  "name": "github",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "env": {"GITHUB_TOKEN": "ghp_your_token"}
}
EOF

# 转换为 Skill
uv run skill_executor.py convert github-mcp.json

# 验证
uv run skill_executor.py validate .claude/skills/github
```

### Example 2: SSE 传输

```bash
cd $SKILL_DIR

# 创建配置文件
cat > deepwiki.json << 'EOF'
{
  "name": "deepwiki",
  "transport": "sse",
  "endpoint": "https://mcp.deepwiki.com/sse"
}
EOF

# 转换为 Skill
uv run skill_executor.py convert deepwiki.json

# 验证
uv run skill_executor.py validate .claude/skills/deepwiki
```

### Example 3: 混合配置

```bash
cd $SKILL_DIR

# 指定输出目录
uv run skill_executor.py convert my-mcp.json --output=/custom/path

# 仅生成不安装
uv run skill_executor.py convert my-mcp.json --no-install
```

## Generated Skill Structure

转换后的技能包含以下文件：

```
~/.claude/skills/{name}/
├── SKILL.md              # 技能文档（包含传输协议说明）
├── executor.py           # Python 执行器（支持多协议）
├── pyproject.toml        # uv 项目配置
├── mcp-config.json       # MCP 服务器配置
└── package.json          # 元数据
```

## Context Savings

对比 MCP 和 Skill 的上下文使用：

| 场景 | MCP (预加载) | Skill (动态) | 节省 |
|------|--------------|--------------|------|
| 8 个工具 | 4000 tokens | 150 tokens | 96% |
| 20 个工具 | 10000 tokens | 150 tokens | 98.5% |
| 执行工具调用 | 4000 tokens | 0 tokens | 100% |

## Requirements

- Python 3.10+
- uv (https://astral.sh/uv)

## Error Handling

常见错误及解决方案：

| 错误 | 原因 | 解决方案 |
|------|------|----------|
| `Unsupported transport` | 传输协议不支持 | 检查 transport 字段（stdio/sse/http） |
| `endpoint required` | SSE/HTTP 缺少 endpoint | 添加 endpoint 字段 |
| `mcp package not found` | 未安装 mcp 包 | `uv sync` |
| `Command not found` | MCP 命令不存在 | 检查 command 和 args |
| `API key required` | 缺少环境变量 | 在 config 中添加 env |

## Best Practices

1. **命名规范**：使用 kebab-case，如 `github-mcp`
2. **环境变量**：敏感信息通过 `env` 传递，不要硬编码
3. **传输协议**：默认使用 stdio，远程服务使用 SSE
4. **测试验证**：转换后立即验证和测试
5. **文档更新**：根据实际工具更新 SKILL.md

## Limitations

- 需要 MCP 服务器支持相应传输协议
- SSE 实现需要 httpx 依赖
- 每次工具调用都会重新连接 MCP 服务器

---
