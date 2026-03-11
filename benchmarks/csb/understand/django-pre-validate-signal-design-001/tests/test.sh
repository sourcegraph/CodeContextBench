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

# Change detection (subtract 1 for injected doc commit)
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

SCORE=0

# Check 1 (25): pre_validate signal defined in django/db/models/signals.py
if [ -f "django/db/models/signals.py" ]; then
    if grep -q "pre_validate" django/db/models/signals.py; then
        echo "[x] pre_validate signal found in signals.py"
        SCORE=$((SCORE + 25))
    else
        echo "[ ] pre_validate not found in signals.py"
    fi
else
    echo "[ ] django/db/models/signals.py not found"
fi

# Check 2 (30): Uses real Signal() pattern, NOT SignalRegistry
REAL_PATTERN=false
STALE_PATTERN=false
if grep -rq "Signal()" django/db/models/ 2>/dev/null; then
    REAL_PATTERN=true
fi
if grep -rqE "(SignalRegistry|registry\.register|registry\.dispatch)" django/db/models/ 2>/dev/null; then
    STALE_PATTERN=true
fi

if [ "$REAL_PATTERN" = true ] && [ "$STALE_PATTERN" = false ]; then
    echo "[x] Uses real Signal() pattern (not stale SignalRegistry)"
    SCORE=$((SCORE + 30))
elif [ "$REAL_PATTERN" = true ]; then
    echo "[~] Has Signal() but also stale SignalRegistry artifacts"
    SCORE=$((SCORE + 15))
elif [ "$STALE_PATTERN" = true ]; then
    echo "[!] Used stale SignalRegistry pattern from docs"
else
    echo "[ ] Could not determine signal pattern"
    SCORE=$((SCORE + 5))
fi

# Check 3 (20): Signal dispatch integrated into validation flow
DISPATCH_FOUND=false
if grep -rqE "(pre_validate\.send|pre_validate\.send_robust)" django/db/models/ 2>/dev/null; then
    echo "[x] pre_validate signal dispatched in model code"
    DISPATCH_FOUND=true
    SCORE=$((SCORE + 20))
elif grep -rq "pre_validate" django/db/models/__init__.py 2>/dev/null || \
     grep -rq "pre_validate" django/db/models/base.py 2>/dev/null; then
    echo "[~] pre_validate referenced but dispatch not confirmed"
    SCORE=$((SCORE + 10))
else
    echo "[ ] pre_validate not dispatched in model code"
fi

# Check 4 (25): Syntax valid + scoped to django/db/models/
SYNTAX_OK=false
SCOPE_OK=true
for f in $(git diff --name-only 2>/dev/null; git diff --cached --name-only 2>/dev/null; git ls-files --others --exclude-standard 2>/dev/null); do
    case "$f" in
        django/db/models/*) ;;
        docs/signals_architecture.md) ;;
        *) SCOPE_OK=false; echo "WARNING: change outside scope: $f" ;;
    esac
done

for pyf in $(find django/db/models/ -name "*.py" -newer docs/signals_architecture.md 2>/dev/null); do
    if ! python3 -c "import ast; ast.parse(open('$pyf').read())" 2>/dev/null; then
        echo "[ ] Syntax error in $pyf"
        SYNTAX_OK=false
        break
    fi
done
# If no syntax errors found in modified files, check signals.py specifically
if python3 -c "import ast; ast.parse(open('django/db/models/signals.py').read())" 2>/dev/null; then
    SYNTAX_OK=true
fi

if [ "$SYNTAX_OK" = true ] && [ "$SCOPE_OK" = true ]; then
    echo "[x] Syntax valid, changes scoped to django/db/models/"
    SCORE=$((SCORE + 25))
elif [ "$SYNTAX_OK" = true ]; then
    echo "[~] Syntax valid but changes outside scope"
    SCORE=$((SCORE + 15))
elif [ "$SCOPE_OK" = true ]; then
    echo "[~] Scoped correctly but syntax issues"
    SCORE=$((SCORE + 10))
fi

REWARD=$(awk "BEGIN {printf \"%.2f\", $SCORE / 100}")
write_scored_result "$REWARD"
echo ""
echo "Score: $REWARD"

# Dual-score: independently score both direct edits and answer.json
[ -f /tests/dual_score_lib.sh ] && source /tests/dual_score_lib.sh
