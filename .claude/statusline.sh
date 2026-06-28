#!/usr/bin/env bash
# Claude Code statusline with a context-window "compact?" warning.
#
# Claude Code pipes a JSON blob to this script on stdin before each render; it
# includes the live token count for the current context window. We surface that
# count and, once it crosses 100K (and again as a soft warning at 80K), show a
# coloured "COMPACT?" nudge so you know to run /compact.
#
# Why a statusline and not a CLAUDE.md rule: the model never sees its own live
# token count, so a memory-file instruction can't reliably fire at a threshold.
# The statusline DOES get the real number on stdin, so it's accurate and free.
#
# Install globally (all projects): copy this file to ~/.claude/statusline.sh,
# chmod +x it, and point ~/.claude/settings.json "statusLine.command" at it.

set -euo pipefail

# Slurp the stdin blob, then hand it to python via an env var. (We can't pipe it
# to `python3 -` here because the program itself arrives on python's stdin.)
input="$(cat)"

# python3 parses the JSON and prints "tokens<TAB>max<TAB>model<TAB>dir".
parsed="$(
  CC_JSON="$input" python3 - <<'PY'
import json, os
try:
    d = json.loads(os.environ.get("CC_JSON", "") or "{}")
except Exception:
    d = {}

cw = d.get("context_window") or {}
# Be tolerant of key-name drift across Claude Code versions.
tokens = (cw.get("total_input_tokens")
          or cw.get("used_tokens")
          or d.get("total_input_tokens")
          or 0)
mx = (cw.get("context_window_size")
      or cw.get("max_tokens")
      or d.get("context_window_size")
      or 200000)

model = ((d.get("model") or {}).get("display_name")) or "claude"
wd = (d.get("workspace") or {}).get("current_dir") or d.get("cwd") or os.getcwd()
dir_short = os.path.basename(wd.rstrip("/")) or wd

# Tabs separate fields; the bash `read` below splits on tab only so a model
# name like "Opus 4.8" (with a space) survives intact.
print(f"{int(tokens)}\t{int(mx)}\t{model}\t{dir_short}".replace("\n", " "))
PY
)"

IFS=$'\t' read -r tokens max model dir <<<"$parsed"

# Fall back if anything came through empty.
tokens="${tokens:-0}"; max="${max:-200000}"; model="${model:-claude}"; dir="${dir:-?}"
[ "$max" -gt 0 ] 2>/dev/null || max=200000

pct=$(( tokens * 100 / max ))

# ANSI colours.
GREEN='\033[32m'; YELLOW='\033[33m'; RED='\033[31m'; DIM='\033[2m'; RESET='\033[0m'

# Format the token count compactly (e.g. 104k).
if [ "$tokens" -ge 1000 ]; then ktok="$(( tokens / 1000 ))k"; else ktok="$tokens"; fi
kmax="$(( max / 1000 ))k"

# Threshold logic: hard warning at 100K, soft warning at 80K.
if [ "$tokens" -ge 100000 ]; then
  ctx_color="$RED"; warn="  ${RED}⚠ COMPACT? (/compact)${RESET}"
elif [ "$tokens" -ge 80000 ]; then
  ctx_color="$YELLOW"; warn="  ${YELLOW}approaching 100K${RESET}"
else
  ctx_color="$GREEN"; warn=""
fi

printf "%b" "${DIM}${model}${RESET} ${DIM}·${RESET} ${dir} ${DIM}·${RESET} ${ctx_color}ctx ${ktok}/${kmax} (${pct}%)${RESET}${warn}"
