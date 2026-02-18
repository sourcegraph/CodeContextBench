#!/bin/bash
# Reward: checklist (0.0-1.0) -- weighted pattern matching against ground_truth.json
# Verifier for changelog generation tasks: scores /workspace/documentation.md
# against ground-truth categories for change classification, completeness,
# and issue/commit references.
#
# Scoring weights (from ground_truth.json):
#   change_categorization: 0.40
#   completeness:          0.30
#   issue_references:      0.30
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

# -- Check prerequisites ---------------------------------------------------
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

echo "Scoring changelog documentation ($DOC_SIZE bytes)..."
echo "Ground truth: $GROUND_TRUTH"
echo ""

# -- Delegate scoring to Python ---------------------------------------------
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

# -- Score change_categorization --------------------------------------------
print("=== Change Categorization ===")
cat_score, cat_total = 0.0, 0.0
for item in sc["change_categorization"]["topics"]:
    cat_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        cat_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
cat_ratio = cat_score / cat_total if cat_total > 0 else 0
print(f"  Categorization score: {cat_score:.2f} / {cat_total:.2f} = {cat_ratio:.2f}")
print()

# -- Score completeness -----------------------------------------------------
print("=== Completeness ===")
comp_score, comp_total = 0.0, 0.0
for item in sc["completeness"]["topics"]:
    comp_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        comp_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
comp_ratio = comp_score / comp_total if comp_total > 0 else 0
print(f"  Completeness score: {comp_score:.2f} / {comp_total:.2f} = {comp_ratio:.2f}")
print()

# -- Score issue_references -------------------------------------------------
print("=== Issue References ===")
ref_score, ref_total = 0.0, 0.0
for item in sc["issue_references"]["topics"]:
    ref_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        ref_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
ref_ratio = ref_score / ref_total if ref_total > 0 else 0
print(f"  References score: {ref_score:.2f} / {ref_total:.2f} = {ref_ratio:.2f}")
print()

# -- Compute weighted total -------------------------------------------------
w_cat = sc["change_categorization"]["weight"]
w_comp = sc["completeness"]["weight"]
w_ref = sc["issue_references"]["weight"]

total = (cat_ratio * w_cat +
         comp_ratio * w_comp +
         ref_ratio * w_ref)

print("=== Final Score ===")
print(f"  Categorization: {cat_ratio:.2f} * {w_cat} = {cat_ratio * w_cat:.3f}")
print(f"  Completeness:   {comp_ratio:.2f} * {w_comp} = {comp_ratio * w_comp:.3f}")
print(f"  References:     {ref_ratio:.2f} * {w_ref} = {ref_ratio * w_ref:.3f}")
print(f"  TOTAL:          {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
