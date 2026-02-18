#!/bin/bash
# Reward: continuous (0.0-1.0) — hybrid: compile check (0.3) + structural checklist (0.7)
set -e

GROUND_TRUTH="/tests/ground_truth.json"
REWARD_FILE="/logs/verifier/reward.txt"

# Source sg_only wrapper if needed
if [ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ]; then
    source /tests/sgonly_verifier_wrapper.sh
fi

mkdir -p /logs/verifier

# Find test file (agent may place it in various locations)
TEST_FILE=""
for f in /workspace/test_json_serializer.py /workspace/test_serializer.py /workspace/tests/test_json_serializer.py /workspace/tests/serializers/test_json.py; do
    if [ -f "$f" ]; then
        TEST_FILE="$f"
        break
    fi
done

# Search more broadly
if [ -z "$TEST_FILE" ]; then
    TEST_FILE=$(find /workspace -maxdepth 3 -name "test_*serial*.py" -type f 2>/dev/null | head -1)
fi

if [ -z "$TEST_FILE" ]; then
    echo "No test file found."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

echo "Found test file: $TEST_FILE"
FILE_SIZE=$(wc -c < "$TEST_FILE")
echo "Test file size: $FILE_SIZE bytes"

if [ "$FILE_SIZE" -lt 200 ]; then
    echo "Test file too short ($FILE_SIZE bytes)"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

# ── Phase 1: Compile check (0.3 weight) ──
COMPILE_SCORE=0.0

echo ""
echo "=== Compile Check ==="
if python3 -m py_compile "$TEST_FILE" 2>/tmp/pycompile_output.txt; then
    echo "  [PASS] py_compile succeeded"
    COMPILE_SCORE=1.0
else
    echo "  [FAIL] py_compile failed:"
    cat /tmp/pycompile_output.txt 2>/dev/null || true
    COMPILE_SCORE=0.0
fi

# ── Phase 2: Structural checklist (0.7 weight) ──
echo ""
echo "=== Structural Checklist ==="

python3 << PYEOF
import json, re

TEST_PATH = "$TEST_FILE"
GT_PATH = "/tests/ground_truth.json"
REWARD_PATH = "/logs/verifier/reward.txt"
COMPILE_SCORE = $COMPILE_SCORE

with open(TEST_PATH) as f:
    doc = f.read()
with open(GT_PATH) as f:
    gt = json.load(f)

def check_any_pattern(patterns, text):
    for p in patterns:
        try:
            if re.search(p, text, re.IGNORECASE):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False

sc = gt["scoring_categories"]
scores = {}

for cat_name, cat_data in sc.items():
    print(f"--- {cat_name} ---")
    s, t = 0.0, 0.0
    for item in cat_data["topics"]:
        t += item["weight"]
        if check_any_pattern(item["check_any_pattern"], doc):
            s += item["weight"]
            print(f"  [x] {item['name']} ({item['weight']})")
        else:
            print(f"  [ ] {item['name']} ({item['weight']})")
    ratio = s / t if t > 0 else 0
    scores[cat_name] = (ratio, cat_data["weight"])
    print(f"  Score: {s:.2f}/{t:.2f} = {ratio:.2f}\n")

checklist_total = sum(r * w for r, w in scores.values())
final = 0.3 * COMPILE_SCORE + 0.7 * checklist_total

print("=== Final Score ===")
print(f"  Compile: {COMPILE_SCORE:.2f} * 0.3 = {0.3 * COMPILE_SCORE:.3f}")
print(f"  Checklist: {checklist_total:.2f} * 0.7 = {0.7 * checklist_total:.3f}")
print(f"  TOTAL: {final:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{final:.2f}\n")
PYEOF
