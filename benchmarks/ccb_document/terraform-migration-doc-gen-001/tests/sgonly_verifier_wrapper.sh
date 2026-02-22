#!/bin/bash
# SG-only verifier wrapper: restore truncated source files from backup
#
# Source this at the TOP of test.sh for build-requiring tasks that use
# sg_only_env mode. It detects /tmp/.sg_only_mode and restores truncated
# (0-byte) source files from /repo_full/ while preserving agent changes.
#
# Key insight: the sg_only Dockerfile truncates source files to 0 bytes.
# Agent-written files are non-zero. So restoring only 0-byte files from
# /repo_full/ recovers the full codebase without touching agent work.
# This avoids the expensive delete+copy cycle on large repos (e.g. 9GB
# ProtonMail monorepo with 135K node_modules entries).
#
# For non-sg_only runs, this script is a no-op.
#
# Usage in test.sh:
#   #!/bin/bash
#   [ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
#   # ... rest of test.sh as normal ...

if [ ! -f /tmp/.sg_only_mode ]; then
    # Not in sg_only mode — nothing to do
    return 0 2>/dev/null || exit 0
fi

echo "[sg_only_verifier] Detected sg_only mode, restoring full repo..."

# Read the working directory
WORKDIR="$(cat /tmp/.sg_only_workdir 2>/dev/null || echo '/app')"
echo "[sg_only_verifier] Working directory: $WORKDIR"

if [ ! -d /repo_full ]; then
    echo "[sg_only_verifier] WARNING: /repo_full not found, cannot restore"
    return 0 2>/dev/null || exit 0
fi

# Restore truncated files: find 0-byte files and bulk-copy originals from
# backup using tar pipe (orders of magnitude faster than individual cp on
# repos with 100K+ truncated files like ProtonMail's node_modules).
# Agent-written files are non-zero and will not be touched.
cd "$WORKDIR"
find . -type f -size 0 \
    ! -path './.git/*' ! -path './tests/*' ! -path './.claude/*' \
    ! -path './node_modules/*' ! -path './__pycache__/*' ! -path './vendor/*' \
    -print0 | (cd /repo_full && tar --null -T - -cf - 2>/dev/null) \
    | tar xf - -C "$WORKDIR/" 2>/dev/null
echo "[sg_only_verifier] Restored truncated files from /repo_full/"

# Return to working directory
cd "$WORKDIR"
echo "[sg_only_verifier] Restore complete, proceeding with tests"
