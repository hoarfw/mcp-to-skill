#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# mcp-to-skill Installer
# ============================================================
# Usage:
#   ./install.sh              # Install to current project (./.claude/skills/mcp-to-skill)
#   ./install.sh --global     # Install to user home (~/.claude/skills/mcp-to-skill)
#   ./install.sh --local      # Install to current project (./.claude/skills/mcp-to-skill)
#   ./install.sh --uninstall  # Remove installed skill
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="mcp-to-skill"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }

# --- Determine target directory ---
MODE="local"
UNINSTALL=false

for arg in "$@"; do
  case "$arg" in
    --global) MODE="global" ;;
    --local)  MODE="local" ;;
    --uninstall) UNINSTALL=true ;;
    -h|--help)
      sed -n '2,7p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    *)
      error "Unknown argument: $arg"
      ;;
  esac
done

if [ "$MODE" = "global" ]; then
  TARGET_DIR="$HOME/.claude/skills/$SKILL_NAME"
else
  TARGET_DIR="$SCRIPT_DIR/.claude/skills/$SKILL_NAME"
fi

# --- Uninstall ---
if [ "$UNINSTALL" = true ]; then
  if [ -d "$TARGET_DIR" ]; then
    rm -rf "$TARGET_DIR"
    info "Removed: $TARGET_DIR"
  else
    warn "Not found: $TARGET_DIR (nothing to remove)"
  fi
  exit 0
fi

# --- Files to install ---
SKILL_FILES=(
  SKILL.md
  lib.ts
  skill_executor.py
  cli.py
  pyproject.toml
)

SKILL_DIRS=(
  converter
  templates
)

# --- Install ---
info "Installing mcp-to-skill ($MODE mode)"
info "Target: $TARGET_DIR"

mkdir -p "$TARGET_DIR"

# Copy files
for file in "${SKILL_FILES[@]}"; do
  src="$SCRIPT_DIR/$file"
  if [ ! -f "$src" ]; then
    error "Missing source file: $file"
  fi
  cp "$src" "$TARGET_DIR/"
  info "  $file"
done

# Copy directories
for dir in "${SKILL_DIRS[@]}"; do
  src="$SCRIPT_DIR/$dir"
  if [ ! -d "$src" ]; then
    error "Missing source directory: $dir/"
  fi
  cp -r "$src" "$TARGET_DIR/"
  info "  $dir/"
done

# Verify
MISSING=0
for file in "${SKILL_FILES[@]}"; do
  [ ! -f "$TARGET_DIR/$file" ] && MISSING=1
done
for dir in "${SKILL_DIRS[@]}"; do
  [ ! -d "$TARGET_DIR/$dir" ] && MISSING=1
done

if [ "$MISSING" = 1 ]; then
  error "Installation verification failed"
fi

echo ""
info "Installation complete!"
info "Claude will auto-discover this skill from: $TARGET_DIR"
