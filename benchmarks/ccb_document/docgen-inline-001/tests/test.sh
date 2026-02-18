#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen inline tasks: scores /workspace/documentation.md
# against ground-truth docstring presence, parameter docs, examples, and style.
#
# Scoring weights (from ground_truth.json):
#   docstring_presence:  0.30
#   parameter_docs:      0.30
#   examples:            0.20
#   style_compliance:    0.20
#
set -e

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

echo "Scoring inline docstring documentation ($DOC_SIZE bytes)..."
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

# ── Score docstring_presence ─────────────────────────────────────────
print("=== Docstring Presence ===")
dp_score, dp_total = 0.0, 0.0
for item in sc["docstring_presence"]["topics"]:
    dp_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        dp_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
dp_ratio = dp_score / dp_total if dp_total > 0 else 0
print(f"  Docstring presence score: {dp_score:.2f} / {dp_total:.2f} = {dp_ratio:.2f}")
print()

# ── Score parameter_docs ─────────────────────────────────────────────
print("=== Parameter Docs ===")
pd_score, pd_total = 0.0, 0.0
for item in sc["parameter_docs"]["topics"]:
    pd_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        pd_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
pd_ratio = pd_score / pd_total if pd_total > 0 else 0
print(f"  Parameter docs score: {pd_score:.2f} / {pd_total:.2f} = {pd_ratio:.2f}")
print()

# ── Score examples ───────────────────────────────────────────────────
print("=== Examples ===")
ex_score, ex_total = 0.0, 0.0
for item in sc["examples"]["topics"]:
    ex_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        ex_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
ex_ratio = ex_score / ex_total if ex_total > 0 else 0
print(f"  Examples score: {ex_score:.2f} / {ex_total:.2f} = {ex_ratio:.2f}")
print()

# ── Score style_compliance ───────────────────────────────────────────
print("=== Style Compliance ===")
sc_score, sc_total = 0.0, 0.0
for item in sc["style_compliance"]["topics"]:
    sc_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        sc_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
sc_ratio = sc_score / sc_total if sc_total > 0 else 0
print(f"  Style compliance score: {sc_score:.2f} / {sc_total:.2f} = {sc_ratio:.2f}")
print()

# ── Compute weighted total ────────────────────────────────────────────
w_dp = sc["docstring_presence"]["weight"]
w_pd = sc["parameter_docs"]["weight"]
w_ex = sc["examples"]["weight"]
w_sc = sc["style_compliance"]["weight"]

total = (dp_ratio * w_dp +
         pd_ratio * w_pd +
         ex_ratio * w_ex +
         sc_ratio * w_sc)

print("=== Final Score ===")
print(f"  Docstring presence: {dp_ratio:.2f} * {w_dp} = {dp_ratio * w_dp:.3f}")
print(f"  Parameter docs:     {pd_ratio:.2f} * {w_pd} = {pd_ratio * w_pd:.3f}")
print(f"  Examples:           {ex_ratio:.2f} * {w_ex} = {ex_ratio * w_ex:.3f}")
print(f"  Style compliance:   {sc_ratio:.2f} * {w_sc} = {sc_ratio * w_sc:.3f}")
print(f"  TOTAL:              {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
