#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/chroma_view.py" "$@"
status=$?
if [[ -t 0 ]]; then
  read -r -p "Press Enter to exit..." _
fi
if [[ "${BASH_SOURCE[0]}" != "$0" ]]; then
  return "$status"
fi
exit "$status"
