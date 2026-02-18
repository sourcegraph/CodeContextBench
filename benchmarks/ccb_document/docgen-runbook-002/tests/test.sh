#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen runbook tasks: scores /workspace/documentation.md
# against ground-truth failure scenarios, diagnostic commands, config fixes,
# and code references.
#
# Scoring weights (from ground_truth.json):
#   failure_scenarios:    0.30
#   diagnostic_commands:  0.30
#   config_fixes:         0.20
#   code_references:      0.20
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

echo "Scoring troubleshooting runbook ($DOC_SIZE bytes)..."
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
category_names = ["failure_scenarios", "diagnostic_commands", "config_fixes", "code_references"]
category_labels = ["Failure Scenarios", "Diagnostic Commands", "Configuration Fixes", "Code References"]

ratios = {}

for cat_name, cat_label in zip(category_names, category_labels):
    print(f"=== {cat_label} ===")
    cat = sc[cat_name]
    score, total = 0.0, 0.0
    for item in cat["topics"]:
        total += item["weight"]
        if check_any_pattern(item["check_any_pattern"], doc):
            score += item["weight"]
            print(f"  [x] {item['name']} (weight: {item['weight']})")
        else:
            print(f"  [ ] {item['name']} (weight: {item['weight']})")
    ratio = score / total if total > 0 else 0
    ratios[cat_name] = ratio
    print(f"  {cat_label} score: {score:.2f} / {total:.2f} = {ratio:.2f}")
    print()

# ── Compute weighted total ─────────────────────────────────────────────
total = 0.0
print("=== Final Score ===")
for cat_name, cat_label in zip(category_names, category_labels):
    w = sc[cat_name]["weight"]
    r = ratios[cat_name]
    contribution = r * w
    total += contribution
    print(f"  {cat_label:25s}: {r:.2f} * {w} = {contribution:.3f}")

print(f"  {'TOTAL':25s}: {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
