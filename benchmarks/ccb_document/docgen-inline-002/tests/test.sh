#!/bin/bash
# Reward: continuous (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen-inline-002: Kafka record batch Javadoc
set -e

DOC="/workspace/documentation.md"
GROUND_TRUTH="/tests/ground_truth.json"
REWARD_FILE="/logs/verifier/reward.txt"

mkdir -p /logs/verifier

# Source the sg_only wrapper (no-op if not in sg_only mode)
if [ -f /tests/sgonly_verifier_wrapper.sh ]; then
    source /tests/sgonly_verifier_wrapper.sh
fi

# ── Check prerequisites ────────────────────────────────────────────────
if [ ! -f "$GROUND_TRUTH" ]; then
    echo "ERROR: ground_truth.json not found at $GROUND_TRUTH"
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

if [ ! -f "$DOC" ]; then
    echo "No documentation found at $DOC"
    echo "Agent did not produce the required output."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

DOC_SIZE=$(wc -c < "$DOC")
if [ "$DOC_SIZE" -lt 500 ]; then
    echo "Documentation is too short (${DOC_SIZE} bytes). Likely incomplete."
    echo "0.0" > "$REWARD_FILE"
    exit 0
fi

echo "Scoring Kafka record batch Javadoc documentation ($DOC_SIZE bytes)..."
echo "Ground truth: $GROUND_TRUTH"
echo ""

# ── Delegate scoring to Python ────────────────────────────────────────
python3 << 'PYEOF'
import json, re, sys

DOC_PATH = "/workspace/documentation.md"
GT_PATH = "/tests/ground_truth.json"
REWARD_PATH = "/logs/verifier/reward.txt"

with open(DOC_PATH) as f:
    doc = f.read()
with open(GT_PATH) as f:
    gt = json.load(f)

def check_any_pattern(patterns, text):
    """Return True if at least one pattern matches (case-insensitive)."""
    for p in patterns:
        try:
            if re.search(p, text, re.IGNORECASE):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False

sc = gt["scoring_categories"]
category_names = ["javadoc_presence", "thread_safety", "performance_notes", "cross_references"]
category_ratios = {}

for cat_name in category_names:
    cat = sc[cat_name]
    print(f"=== {cat_name} (weight: {cat['weight']}) ===")
    score, total = 0.0, 0.0
    for item in cat["topics"]:
        total += item["weight"]
        if check_any_pattern(item["check_any_pattern"], doc):
            score += item["weight"]
            print(f"  [x] {item['name']} (weight: {item['weight']})")
        else:
            print(f"  [ ] {item['name']} (weight: {item['weight']})")
    ratio = score / total if total > 0 else 0
    category_ratios[cat_name] = ratio
    print(f"  Score: {score:.2f} / {total:.2f} = {ratio:.2f}")
    print()

# ── Compute weighted total ─────────────────────────────────────────────
total_reward = 0.0
print("=== Final Score ===")
for cat_name in category_names:
    w = sc[cat_name]["weight"]
    r = category_ratios[cat_name]
    contribution = r * w
    total_reward += contribution
    print(f"  {cat_name}: {r:.2f} * {w} = {contribution:.3f}")

print(f"  TOTAL: {total_reward:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total_reward:.2f}\n")

print()
print(f"Tests completed - Score: {total_reward:.2f}")
PYEOF
