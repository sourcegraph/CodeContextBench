#!/bin/bash
if [ ! -f /tmp/.sg_only_mode ]; then
    return 0 2>/dev/null || exit 0
fi
echo "[sg_only_verifier] Detected sg_only mode, restoring full repo..."
WORKDIR="$(cat /tmp/.sg_only_workdir 2>/dev/null || echo '/app')"
echo "[sg_only_verifier] Working directory: $WORKDIR"
if [ ! -d /repo_full ]; then
    echo "[sg_only_verifier] WARNING: /repo_full not found, cannot restore"
    return 0 2>/dev/null || exit 0
fi
cd "$WORKDIR"
mkdir -p /tmp/agent_work
find . -type f -size +0 ! -path './.git/*' ! -path './tests/*' ! -path './.claude/*' \
    -print0 | while IFS= read -r -d '' f; do
    mkdir -p "/tmp/agent_work/$(dirname "$f")"
    cp "$f" "/tmp/agent_work/$f"
done
echo "[sg_only_verifier] Backed up agent-written files"
rsync -a --delete /repo_full/ "$WORKDIR/"
echo "[sg_only_verifier] Restored full repo from /repo_full/"
cd /tmp/agent_work
find . -type f -print0 | while IFS= read -r -d '' f; do
    target="${WORKDIR}/${f#./}"
    mkdir -p "$(dirname "$target")"
    cp "$f" "$target"
done
echo "[sg_only_verifier] Overlaid agent changes"
cd "$WORKDIR"
echo "[sg_only_verifier] Restore complete, proceeding with tests"
