#!/bin/bash
set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh

# Artifact mode: parse answer.json, extract analysis text, apply diffs
if [ -f /tests/answer_json_verifier_lib.sh ]; then
    source /tests/answer_json_verifier_lib.sh
fi


TASK_WORKDIR="${TASK_WORKDIR:-/workspace}"
TASK_REPO_ROOT="${TASK_REPO_ROOT:-${VERIFY_REPO:-$TASK_WORKDIR}}"
VERIFY_REPO="${VERIFY_REPO:-$TASK_REPO_ROOT}"

TASK_OUTPUT="${TASK_OUTPUT:-/workspace/answer.json}"
PASS_THRESHOLD="0.6"
OUTPUT_CONTRACT_MODE="repo_state"
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

UNSTAGED=$(git diff --stat 2>/dev/null | wc -l)
STAGED=$(git diff --cached --stat 2>/dev/null | wc -l)
UNTRACKED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l)
COMMITS=0
for ref in origin/master origin/main origin/HEAD; do
    if git rev-parse "$ref" >/dev/null 2>&1; then
        COMMITS=$(git log --oneline "$ref..HEAD" 2>/dev/null | wc -l)
        COMMITS=$((COMMITS - 1))
        [ "$COMMITS" -lt 0 ] && COMMITS=0
        break
    fi
done
if [ "$UNSTAGED" -eq 0 ] && [ "$STAGED" -eq 0 ] && [ "$UNTRACKED" -eq 0 ] && [ "$COMMITS" -eq 0 ]; then
    echo "No code changes detected"
    write_scored_result "0.0" "no_code_changes"
    exit 0
fi

DIFF=$(git diff HEAD~1..HEAD -- django/template/ 2>/dev/null || git diff -- django/template/ 2>/dev/null)
ALL_CHANGED=$(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null)

SCORE=0

# Check 1 (30): Changes in template block resolution code
if echo "$DIFF" | grep -qE "(block|Block|BlockNode|ExtendsNode|render_block|block_context)"; then
    echo "[x] Block-related changes found in django/template/"
    SCORE=$((SCORE + 30))
elif [ -n "$DIFF" ]; then
    echo "[~] Changes in django/template/ but not in block resolution"
    SCORE=$((SCORE + 10))
else
    echo "[ ] No changes in django/template/"
fi

# Check 2 (25): Fix targets nested/multi-level inheritance
MULTI_LEVEL=0
if echo "$DIFF" | grep -qE "(parent|super|inherit|extends|depth|level|nested)"; then
    MULTI_LEVEL=$((MULTI_LEVEL + 1))
fi
if echo "$DIFF" | grep -qE "(push|pop|stack|context|blocks\[|block_stack)"; then
    MULTI_LEVEL=$((MULTI_LEVEL + 1))
fi
if echo "$DIFF" | grep -qE "(render|resolve|compile|nodelist)"; then
    MULTI_LEVEL=$((MULTI_LEVEL + 1))
fi
case $MULTI_LEVEL in
    3) echo "[x] Fix addresses multi-level block resolution"; SCORE=$((SCORE + 25)) ;;
    2) echo "[~] Partial multi-level fix ($MULTI_LEVEL/3)"; SCORE=$((SCORE + 15)) ;;
    1) echo "[~] Minimal multi-level fix ($MULTI_LEVEL/3)"; SCORE=$((SCORE + 10)) ;;
    *) echo "[ ] Multi-level inheritance not addressed" ;;
esac

# Check 3 (20): Changes scoped to django/template/
SCOPE_OK=true
if [ -n "$ALL_CHANGED" ]; then
    while IFS= read -r f; do
        case "$f" in
            django/template/*) ;;
            HISTORY.md) ;;
            "") ;;
            *) SCOPE_OK=false; echo "WARNING: change outside scope: $f" ;;
        esac
    done <<< "$(echo "$ALL_CHANGED" | sort -u)"
fi
if [ "$SCOPE_OK" = true ]; then
    echo "[x] Changes scoped to django/template/"
    SCORE=$((SCORE + 20))
else
    echo "[!] Changes outside django/template/"
fi

# Check 4 (25): Syntax valid
SYNTAX_OK=true
while IFS= read -r f; do
    case "$f" in
        django/template/*.py)
            if [ -f "$f" ]; then
                if ! python3 -c "import ast; ast.parse(open('$f').read())" 2>/dev/null; then
                    SYNTAX_OK=false
                    echo "[ ] Syntax error in $f"
                fi
            fi ;;
    esac
done <<< "$(echo "$ALL_CHANGED" | sort -u)"
if [ "$SYNTAX_OK" = true ]; then
    echo "[x] Python syntax valid"
    SCORE=$((SCORE + 25))
fi

REWARD=$(awk "BEGIN {printf \"%.2f\", $SCORE / 100}")
write_scored_result "$REWARD"
echo "Score: $REWARD"

# Dual-score: independently score both direct edits and answer.json
[ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
