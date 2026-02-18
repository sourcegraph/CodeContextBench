#!/bin/bash
set -e

# Source the sg_only wrapper (no-op if not in sg_only mode)
if [ -f /tests/sgonly_verifier_wrapper.sh ]; then
    source /tests/sgonly_verifier_wrapper.sh
fi

DOC="/workspace/coverage_analysis.md"
GROUND_TRUTH="/tests/ground_truth.json"
REWARD_FILE="/logs/verifier/reward.txt"

mkdir -p /logs/verifier

if [ ! -f "$GROUND_TRUTH" ]; then
    echo "ERROR: ground_truth.json not found"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

if [ ! -f "$DOC" ]; then
    echo "No coverage analysis found at $DOC"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

DOC_SIZE=$(wc -c < "$DOC")
if [ "$DOC_SIZE" -lt 500 ]; then
    echo "Analysis too short (${DOC_SIZE} bytes)"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

echo "Scoring coverage analysis ($DOC_SIZE bytes)..."

python3 << 'PYEOF'
import json, re

DOC_PATH = "/workspace/coverage_analysis.md"
GT_PATH = "/tests/ground_truth.json"
REWARD_PATH = "/logs/verifier/reward.txt"

with open(DOC_PATH) as f:
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
    print(f"=== {cat_name} ===")
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

total = sum(r * w for r, w in scores.values())
print("=== Final Score ===")
for name, (r, w) in scores.items():
    print(f"  {name}: {r:.2f} * {w} = {r*w:.3f}")
print(f"  TOTAL: {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")
PYEOF
