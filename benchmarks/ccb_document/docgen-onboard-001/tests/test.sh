#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen onboarding tasks: scores /workspace/documentation.md
# against ground-truth topics across 4 categories.
#
# Scoring weights (from ground_truth.json):
#   prerequisites:    0.30
#   architecture:     0.30
#   workflow:         0.20
#   code_references:  0.20
#
set -e

# Source the sg_only wrapper (no-op if not in sg_only mode)
if [ -f /tests/sgonly_verifier_wrapper.sh ]; then
    source /tests/sgonly_verifier_wrapper.sh
fi

DOC="/workspace/documentation.md"
GROUND_TRUTH="/tests/ground_truth.json"
REWARD_FILE="/logs/verifier/reward.txt"

mkdir -p /logs/verifier

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

echo "Scoring onboarding documentation ($DOC_SIZE bytes)..."
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

# ── Score all categories dynamically ──────────────────────────────────
category_results = {}
for cat_name, cat_data in sc.items():
    print(f"=== {cat_name.replace('_', ' ').title()} ===")
    cat_score, cat_total = 0.0, 0.0
    for item in cat_data["topics"]:
        cat_total += item["weight"]
        if check_any_pattern(item["check_any_pattern"], doc):
            cat_score += item["weight"]
            print(f"  [x] {item['name']} (weight: {item['weight']})")
        else:
            print(f"  [ ] {item['name']} (weight: {item['weight']})")
    ratio = cat_score / cat_total if cat_total > 0 else 0
    print(f"  {cat_name} score: {cat_score:.2f} / {cat_total:.2f} = {ratio:.2f}")
    print()
    category_results[cat_name] = {
        "ratio": ratio,
        "weight": cat_data["weight"],
        "score": cat_score,
        "total": cat_total,
    }

# ── Compute weighted total ─────────────────────────────────────────────
total = 0.0
print("=== Final Score ===")
for cat_name, r in category_results.items():
    contribution = r["ratio"] * r["weight"]
    total += contribution
    label = cat_name.replace("_", " ").title()
    print(f"  {label:20s}: {r['ratio']:.2f} * {r['weight']} = {contribution:.3f}")

print(f"  {'TOTAL':20s}: {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
