#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted correctness checks
# Verifies function signature propagation: NewResource() + ctx parameter

set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh
# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tmp/.artifact_only_mode ] && [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi


TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

TASK_OUTPUT="${TASK_OUTPUT:-/workspace/answer.json}"
PASS_THRESHOLD="0.6"
OUTPUT_CONTRACT_MODE="answer_json_bridge"
OUTPUT_PRIMARY_PATH="$TASK_OUTPUT"
ARTIFACT_REQUIRED=false
if [ "$OUTPUT_CONTRACT_MODE" = "repo_state" ]; then
    OUTPUT_PRIMARY_PATH=""
elif [ "${ARTIFACT_ONLY:-false}" = "true" ]; then
    ARTIFACT_REQUIRED=true
fi

write_invalid_output() {
    local code="$1"
    local message="$2"
    python3 - "$code" "$message" "$OUTPUT_CONTRACT_MODE" "$OUTPUT_PRIMARY_PATH" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import sys

code, message, mode, primary_path, required_artifact, pass_threshold = sys.argv[1:7]
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "invalid_output",
    "scorable": False,
    "scorer_family": "repo_state_heuristic",
    "reward": 0.0,
    "pass_threshold": float(pass_threshold),
    "passed": False,
    "output_contract": {
        "mode": mode,
        "primary_path": primary_path or None,
        "required_artifact": required_artifact == "true",
    },
    "sub_scores": {},
    "failure": {
        "code": code,
        "message": message,
        "stage": "output_validation",
    },
}
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
    echo "0.0" > /logs/verifier/reward.txt
}

write_scored_result() {
    local score="$1"
    local reason="${2:-}"
    local passed_checks="${3:-}"
    local total_checks="${4:-}"
    env         VALIDATION_SCORE="$score"         VALIDATION_REASON="$reason"         VALIDATION_PASSED_CHECKS="$passed_checks"         VALIDATION_TOTAL_CHECKS="$total_checks"         CHANGE_UNSTAGED="${UNSTAGED_COUNT:-${UNSTAGED:-0}}"         CHANGE_STAGED="${STAGED_COUNT:-${STAGED:-0}}"         CHANGE_UNTRACKED="${UNTRACKED_COUNT:-${UNTRACKED:-0}}"         CHANGE_COMMITS="${COMMIT_COUNT:-${COMMITS:-0}}"         VALIDATION_OUTPUT_PATH="${VALIDATION_OUTPUT_PATH:-}"         python3 - "$OUTPUT_CONTRACT_MODE" "$OUTPUT_PRIMARY_PATH" "$ARTIFACT_REQUIRED" "$PASS_THRESHOLD" <<'PYEOF'
import json
import os
import sys

mode, primary_path, required_artifact, pass_threshold = sys.argv[1:5]
reward = float(os.environ.get("VALIDATION_SCORE", "0.0") or 0.0)
threshold = float(pass_threshold)
checks = {"heuristic_score": reward}
details = {}
reason = os.environ.get("VALIDATION_REASON")
if reason:
    details["reason"] = reason
passed_checks_raw = os.environ.get("VALIDATION_PASSED_CHECKS", "")
total_checks_raw = os.environ.get("VALIDATION_TOTAL_CHECKS", "")
if passed_checks_raw and total_checks_raw:
    try:
        passed_checks = float(passed_checks_raw)
        total_checks = float(total_checks_raw)
    except ValueError:
        passed_checks = None
        total_checks = None
    if passed_checks is not None and total_checks and total_checks > 0:
        checks["passed_checks_ratio"] = round(passed_checks / total_checks, 4)
        details["passed_checks"] = int(passed_checks) if passed_checks.is_integer() else passed_checks
        details["total_checks"] = int(total_checks) if total_checks.is_integer() else total_checks
change_detection = {
    "unstaged": int(os.environ.get("CHANGE_UNSTAGED", "0") or 0),
    "staged": int(os.environ.get("CHANGE_STAGED", "0") or 0),
    "untracked": int(os.environ.get("CHANGE_UNTRACKED", "0") or 0),
    "commits": int(os.environ.get("CHANGE_COMMITS", "0") or 0),
}
if any(change_detection.values()):
    checks["change_detected"] = 1.0
    details["change_detection"] = change_detection
output_path = os.environ.get("VALIDATION_OUTPUT_PATH")
if output_path:
    details["output_path"] = output_path
payload = {
    "schema_version": "validation_result.v1alpha1",
    "status": "scored",
    "scorable": True,
    "scorer_family": "repo_state_heuristic",
    "reward": reward,
    "pass_threshold": threshold,
    "passed": reward >= threshold,
    "output_contract": {
        "mode": mode,
        "primary_path": primary_path or None,
        "required_artifact": required_artifact == "true",
    },
    "sub_scores": {"checks": checks},
    "failure": None,
}
if details:
    payload["details"] = details
with open("/logs/verifier/validation_result.json", "w") as f:
    json.dump(payload, f, indent=2)
PYEOF
    echo "$score" > /logs/verifier/reward.txt
}


cd "$TASK_REPO_ROOT"

mkdir -p /logs/verifier

git config --global --add safe.directory "$TASK_REPO_ROOT" 2>/dev/null || true

if [ "${ARTIFACT_ONLY:-false}" = "true" ] && [ ! -f "${ANSWER_JSON:-$TASK_OUTPUT}" ]; then
    write_invalid_output "missing_required_output" \
        "answer.json not found at ${ANSWER_JSON:-$TASK_OUTPUT}"
    exit 0
fi


# Guard: check for code changes
UNSTAGED_COUNT=$(git diff --stat 2>/dev/null | wc -l)
STAGED_COUNT=$(git diff --cached --stat 2>/dev/null | wc -l)
UNTRACKED_COUNT=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
COMMIT_COUNT=0
ORIGIN_REF=""
for ref in origin/master origin/main origin/HEAD; do
    if git rev-parse "$ref" >/dev/null 2>&1; then
        ORIGIN_REF="$ref"
        break
    fi
done
if [ -n "$ORIGIN_REF" ]; then
    COMMIT_COUNT=$(git log --oneline "$ORIGIN_REF..HEAD" 2>/dev/null | wc -l)
fi
echo "Change detection: unstaged=$UNSTAGED_COUNT staged=$STAGED_COUNT untracked=$UNTRACKED_COUNT commits=$COMMIT_COUNT"
if [ "$UNSTAGED_COUNT" -eq 0 ] && [ "$STAGED_COUNT" -eq 0 ] && [ "$UNTRACKED_COUNT" -eq 0 ] && [ "$COMMIT_COUNT" -eq 0 ]; then
    echo "No code changes detected"
    write_scored_result "0.0" "no_code_changes"
    exit 0
fi

echo "Running dep-refactor-001 verification..."

SCORE_NUMERATOR=0

# Check 1 (0.20): NewResource function signature has context.Context parameter
if grep -qE 'func NewResource\(ctx context\.Context' internal/storage/resource.go 2>/dev/null; then
    echo "[x] NewResource signature has ctx context.Context parameter"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 20))
elif grep -qE 'func NewResource\(.*context\.Context' internal/storage/resource.go 2>/dev/null; then
    echo "[~] NewResource has context.Context but not as 'ctx' first param"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 10))
else
    echo "[ ] NewResource signature not updated with context.Context"
fi

# Check 2 (0.25): Call sites updated (check for context argument in NewResource calls)
CALL_SITES_WITH_CTX=0
CALL_SITES_TOTAL=0
while IFS= read -r file; do
    count=$(grep -c 'NewResource(' "$file" 2>/dev/null || echo 0)
    ctx_count=$(grep -c 'NewResource(ctx\|NewResource(context\.' "$file" 2>/dev/null || echo 0)
    CALL_SITES_TOTAL=$((CALL_SITES_TOTAL + count))
    CALL_SITES_WITH_CTX=$((CALL_SITES_WITH_CTX + ctx_count))
done < <(grep -rl 'NewResource(' internal/ 2>/dev/null | grep -v resource.go || true)

if [ "$CALL_SITES_TOTAL" -gt 0 ]; then
    if [ "$CALL_SITES_WITH_CTX" -ge "$CALL_SITES_TOTAL" ]; then
        echo "[x] All $CALL_SITES_TOTAL call sites pass context ($CALL_SITES_WITH_CTX/$CALL_SITES_TOTAL)"
        SCORE_NUMERATOR=$((SCORE_NUMERATOR + 25))
    elif [ "$CALL_SITES_WITH_CTX" -gt 0 ]; then
        PARTIAL=$((25 * CALL_SITES_WITH_CTX / CALL_SITES_TOTAL))
        echo "[~] $CALL_SITES_WITH_CTX/$CALL_SITES_TOTAL call sites updated"
        SCORE_NUMERATOR=$((SCORE_NUMERATOR + PARTIAL))
    else
        echo "[ ] No call sites pass context"
    fi
else
    echo "[ ] No NewResource call sites found outside resource.go"
fi

# Check 3 (0.15): Multiple files modified (expect 8+)
FILES_CHANGED=0
if [ -n "$ORIGIN_REF" ]; then
    FILES_CHANGED=$(git diff --name-only "$ORIGIN_REF..HEAD" -- internal/ 2>/dev/null | wc -l)
fi
if [ "$FILES_CHANGED" -eq 0 ]; then
    FILES_CHANGED=$(git diff --name-only -- internal/ 2>/dev/null | wc -l)
fi

if [ "$FILES_CHANGED" -ge 8 ]; then
    echo "[x] $FILES_CHANGED files changed in internal/ (expected 8+)"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 15))
elif [ "$FILES_CHANGED" -ge 4 ]; then
    echo "[~] $FILES_CHANGED files changed (expected 8+, partial credit)"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 8))
elif [ "$FILES_CHANGED" -ge 1 ]; then
    echo "[~] Only $FILES_CHANGED files changed (expected 8+)"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 4))
else
    echo "[ ] No files changed in internal/"
fi

# Check 4 (0.10): Changes scoped to internal/ only
ALL_CHANGED=""
if [ -n "$ORIGIN_REF" ]; then
    ALL_CHANGED=$(git diff --name-only "$ORIGIN_REF..HEAD" 2>/dev/null)
fi
ALL_CHANGED="$ALL_CHANGED
$(git diff --name-only 2>/dev/null)
$(git diff --cached --name-only 2>/dev/null)
$(git ls-files --others --exclude-standard 2>/dev/null)"
ALL_CHANGED=$(echo "$ALL_CHANGED" | sort -u | grep -v '^$' || true)

OUTSIDE_SCOPE=0
if [ -n "$ALL_CHANGED" ]; then
    while IFS= read -r f; do
        case "$f" in
            internal/*) ;;
            *) OUTSIDE_SCOPE=1; echo "WARNING: change outside internal/: $f" ;;
        esac
    done <<< "$ALL_CHANGED"
fi
if [ "$OUTSIDE_SCOPE" -eq 0 ]; then
    echo "[x] All changes within internal/"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 10))
else
    echo "[!] Changes outside internal/"
fi

# Check 5 (0.30): Go compilation succeeds
echo "Running Go compilation check..."
if go build ./internal/... 2>/logs/verifier/build_errors.txt; then
    echo "[x] Go compilation passed"
    SCORE_NUMERATOR=$((SCORE_NUMERATOR + 30))
else
    echo "[ ] Go compilation failed"
    head -20 /logs/verifier/build_errors.txt 2>/dev/null
fi

SCORE=$(awk "BEGIN {printf \"%.2f\", $SCORE_NUMERATOR / 100}")
write_scored_result "$SCORE"
echo ""
echo "[x] Tests completed - Score: $SCORE"
