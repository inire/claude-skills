#!/usr/bin/env bash
# Deploy this skill to ~/.claude/skills/ so it loads in fresh Claude sessions.
#
# Run from the skill directory:
#   bash deploy.sh
#
# Mirrors SKILL.md, README.md, and assets/ to the load path. Does NOT copy
# tests/ or this script itself — those are dev-only.

set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST_DIR="$HOME/.claude/skills/dictionary-pipeline"

echo "Deploying $SOURCE_DIR -> $DEST_DIR"

mkdir -p "$DEST_DIR/assets"
cp "$SOURCE_DIR/SKILL.md" "$DEST_DIR/SKILL.md"
cp "$SOURCE_DIR/README.md" "$DEST_DIR/README.md"
cp "$SOURCE_DIR/assets/"* "$DEST_DIR/assets/"

echo "Deployed. Files:"
ls -1 "$DEST_DIR"
echo "Assets:"
ls -1 "$DEST_DIR/assets"
