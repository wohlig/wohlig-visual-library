#!/bin/zsh
# Usage: gen1.sh <name> <outdir> "<prompt>"
# Runs one Codex image generation and copies ITS image (found via its own thread id) to <outdir>/<name>.png
name=$1; out=$2; prompt=$3
mkdir -p "$out"
CODEX=$(command -v codex || echo /Applications/Codex.app/Contents/Resources/codex)
tid=$("$CODEX" exec --json --skip-git-repo-check -c model_provider=openai \
  "Use your image generation tool to create exactly one image for this request, then reply with only 'done'. Request: $prompt" </dev/null 2>/dev/null \
  | grep -o '"thread_id":"[^"]*"' | head -1 | cut -d'"' -f4)
f=$(ls -t ~/.codex/generated_images/$tid/* 2>/dev/null | head -1)
if [ -n "$f" ]; then cp "$f" "$out/$name.png"; echo "OK $name $tid"; else echo "FAIL $name $tid"; fi
