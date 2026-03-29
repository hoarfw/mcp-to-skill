# PROJECT KNOWLEDGE BASE

**Generated:** 2026-03-28
**Commit:** da632d7
**Branch:** main

## OVERVIEW

将 MCP 服务器配置转换为 Claude Skill 的工具。Python SDK + CLI + Bun/TypeScript 转换脚本，支持 stdio/SSE/HTTP 三种传输协议。核心思路：通过 "渐进式披露" 模式节省上下文消耗（96%+）。

## STRUCTURE

```
mcp-to-skill/
├── converter/          # Python SDK 核心（convert/validate/test/status）
│   ├── converter.py    # 所有业务逻辑：转换、校验、测试、状态查询
│   └── __init__.py     # 公开 API 导出，version = "2.0.0"
├── templates/          # 运行时模板（转换时复制到生成的 skill 目录）
│   ├── executor.py     # MCP 工具调用执行器，支持 stdio/SSE
│   ├── stats_manager.py # 工具调用统计与日志追踪
│   └── pyproject.toml  # 生成 skill 的 uv 依赖声明
├── cli.py              # Python CLI 入口（argparse，子命令：convert/validate/test/status/reset-stats）
├── lib.ts              # Bun 侧转换脚本（实际执行转换、模板复制、SKILL.md 生成）
├── SKILL.md            # 本工具自身的技能描述文件
├── setup.py            # setuptools 兼容构建（入口：mcp-to-skill=cli:main）
├── pyproject.toml      # hatch 构建，Python 3.10+
├── package.json        # npm scripts 委托给 hatch/pytest/ruff/black
└── README.md           # 用户文档（含 API Reference）
```

## WHERE TO LOOK

| 任务 | 位置 | 说明 |
|------|------|------|
| 修改转换逻辑 | `lib.ts` → `convert()` | Bun 侧才是实际转换引擎 |
| 修改 Python SDK API | `converter/converter.py` | Python SDK 封装层，内部调 Bun |
| 修改 CLI 命令 | `cli.py` | argparse 子命令定义 |
| 修改生成 skill 的执行器 | `templates/executor.py` | 运行时 MCP 工具调用 |
| 修改统计/日志功能 | `templates/stats_manager.py` | JSONL 日志 + 统计 |
| 修改生成 skill 的依赖 | `templates/pyproject.toml` + `lib.ts` `generatePyprojectToml()` | 两处需同步 |
| 修改 SKILL.md 生成模板 | `lib.ts` → `generateSkillMD()` | 生成的 skill 文档模板 |
| 修改包元数据 | `pyproject.toml` + `setup.py` + `package.json` | 三处版本号需同步 |

## CODE MAP

| Symbol | Type | Location | Role |
|--------|------|----------|------|
| `Transport` | Enum | `converter/converter.py:16` | stdio/sse/http 传输类型 |
| `MCPConfig` | Dataclass | `converter/converter.py:24` | MCP 服务器配置（name, transport, command, args, endpoint, env, keep_alive） |
| `SkillConfig` | Dataclass | `converter/converter.py:42` | 生成选项（output_dir, install, verbose） |
| `SkillInfo` | Dataclass | `converter/converter.py:50` | 生成结果（name, path, tools, context_saved, transport） |
| `MCPConverterError` | Exception | `converter/converter.py:59` | 基础异常 |
| `ConversionError` | Exception | `converter/converter.py:64` | 转换失败 |
| `ValidationError` | Exception | `converter/converter.py:69` | 验证失败 |
| `convert_to_skill()` | Function | `converter/converter.py:74` | SDK 主入口 → subprocess 调 Bun |
| `validate_skill()` | Function | `converter/converter.py:158` | 检查 executor.py/mcp-config.json/SKILL.md 存在 + 运行 --list |
| `test_skill()` | Function | `converter/converter.py:227` | list/describe/call 三模式测试 |
| `get_skill_status()` | Function | `converter/converter.py:300` | 统计查询 |
| `reset_skill_stats()` | Function | `converter/converter.py:336` | 重置统计 |
| `convert()` | Function | `lib.ts:334` | Bun 侧实际转换逻辑 |
| `introspectMCP()` | Function | `lib.ts:279` | 临时目录启动 MCP 获取工具列表 |
| `copyTemplateFiles()` | Function | `lib.ts:240` | 复制模板到 skill 目录 |
| `generateSkillMD()` | Function | `lib.ts:48` | 生成 SKILL.md 内容 |
| `MCPStatsManager` | Class | `templates/stats_manager.py:15` | 统计管理器（JSONL 日志 + JSON 统计） |

## CONVENTIONS

### 双实现架构
Python SDK（`converter/`）是 **封装层**，内部通过 `subprocess.run(["bun", ...])` 调用 `lib.ts` 执行实际转换。修改转换逻辑时改 `lib.ts`，不是 `converter.py`。

### 版本号三处同步
`pyproject.toml` version、`setup.py` version、`package.json` version 必须保持一致。当前均为 `2.0.0`。`converter/__init__.py` 的 `__version__` 也需同步。

### 模板字段名一致性
修改 `templates/` 中模板时，生成文件与源码中的字段名必须一致（如 `transport`、`endpoint`、`command`）。

### 生成物不提交
`build/`、`*.egg-info/`、`.venv/`、`__pycache__/`、`.mcp.*`、日志文件、`/tmp/` 产物属于生成物。

## ANTI-PATTERNS

- **禁止提交** 真实 API Token、MCP 凭据或密钥；示例配置中统一用占位符或环境变量
- **禁止** 在 `converter.py` 中实现实际转换逻辑——它只是 subprocess 封装，实际逻辑在 `lib.ts`
- **禁止** 裸 `except:` 忽略异常（虽然现有代码有几处 `except:`，新代码不应继续此模式）
- **禁止** 让 Python 和 TypeScript 侧的 MCPConfig 字段定义产生分歧
- SSE executor 的 `list_tools_sse()` 和 `call_tool_sse()` 当前返回 mock 数据，不要当作已实现

## COMMANDS

```bash
# 开发环境
uv sync --extra dev

# 静态检查 & 格式化
ruff check converter/ cli.py
black converter/ cli.py

# 测试（当前无 tests/ 目录，新增时用 pytest）
pytest

# 构建
hatch build

# 冒烟验证（Bun 侧转换链路）
bun lib.ts convert example.json

# npm 委托（build/test/lint/format → hatch/pytest/ruff/black）
npm run build && npm test && npm run lint && npm run format
```

## NOTES

- Python SDK 3.10+，依赖仅 `httpx>=0.25.0`
- 生成的 skill 依赖 `mcp>=1.0.0`（通过 `templates/pyproject.toml`）
- `cli.py` 中 `cmd_test` 使用 `eval(args.args)` 解析参数——有安全隐患，但当前保持现状
- `validate_skill()` 检查三个必需文件：`executor.py`、`mcp-config.json`、`SKILL.md`
- 提交风格：`Feature: ...` / `Fix: ...` 前缀式摘要
- 代理协作统一中文沟通，代码标识/命令名/API 名称保持英文原样
