#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for docgen runbook tasks: scores /workspace/documentation.md
# against ground-truth monitoring indicators, failure modes, recovery procedures,
# and code references.
#
# Scoring weights (from ground_truth.json):
#   monitoring_indicators: 0.30
#   failure_modes:         0.30
#   recovery_procedures:   0.20
#   code_references:       0.20
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

echo "Scoring runbook documentation ($DOC_SIZE bytes)..."
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

# ── Score monitoring_indicators ────────────────────────────────────────
print("=== Monitoring Indicators ===")
mi_score, mi_total = 0.0, 0.0
for item in sc["monitoring_indicators"]["topics"]:
    mi_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        mi_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
mi_ratio = mi_score / mi_total if mi_total > 0 else 0
print(f"  Monitoring indicators score: {mi_score:.2f} / {mi_total:.2f} = {mi_ratio:.2f}")
print()

# ── Score failure_modes ────────────────────────────────────────────────
print("=== Failure Modes ===")
fm_score, fm_total = 0.0, 0.0
for item in sc["failure_modes"]["topics"]:
    fm_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        fm_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
fm_ratio = fm_score / fm_total if fm_total > 0 else 0
print(f"  Failure modes score: {fm_score:.2f} / {fm_total:.2f} = {fm_ratio:.2f}")
print()

# ── Score recovery_procedures ──────────────────────────────────────────
print("=== Recovery Procedures ===")
rp_score, rp_total = 0.0, 0.0
for item in sc["recovery_procedures"]["topics"]:
    rp_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        rp_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
rp_ratio = rp_score / rp_total if rp_total > 0 else 0
print(f"  Recovery procedures score: {rp_score:.2f} / {rp_total:.2f} = {rp_ratio:.2f}")
print()

# ── Score code_references ──────────────────────────────────────────────
print("=== Code References ===")
cr_score, cr_total = 0.0, 0.0
for item in sc["code_references"]["topics"]:
    cr_total += item["weight"]
    if check_any_pattern(item["check_any_pattern"], doc):
        cr_score += item["weight"]
        print(f"  [x] {item['name']} (weight: {item['weight']})")
    else:
        print(f"  [ ] {item['name']} (weight: {item['weight']})")
cr_ratio = cr_score / cr_total if cr_total > 0 else 0
print(f"  Code references score: {cr_score:.2f} / {cr_total:.2f} = {cr_ratio:.2f}")
print()

# ── Compute weighted total ─────────────────────────────────────────────
w_mi = sc["monitoring_indicators"]["weight"]
w_fm = sc["failure_modes"]["weight"]
w_rp = sc["recovery_procedures"]["weight"]
w_cr = sc["code_references"]["weight"]

total = (mi_ratio * w_mi +
         fm_ratio * w_fm +
         rp_ratio * w_rp +
         cr_ratio * w_cr)

print("=== Final Score ===")
print(f"  Monitoring:  {mi_ratio:.2f} * {w_mi} = {mi_ratio * w_mi:.3f}")
print(f"  Failures:    {fm_ratio:.2f} * {w_fm} = {fm_ratio * w_fm:.3f}")
print(f"  Recovery:    {rp_ratio:.2f} * {w_rp} = {rp_ratio * w_rp:.3f}")
print(f"  Code refs:   {cr_ratio:.2f} * {w_cr} = {cr_ratio * w_cr:.3f}")
print(f"  TOTAL:       {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
