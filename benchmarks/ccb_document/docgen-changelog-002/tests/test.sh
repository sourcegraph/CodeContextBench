#!/bin/bash
# Reward: checklist (0.0-1.0) — weighted pattern matching against ground_truth.json
# Verifier for changelog/release-notes tasks: scores /workspace/documentation.md
# against ground-truth topics using check_any_pattern matching.
#
# Scoring weights (from ground_truth.json):
#   breaking_changes:      0.40
#   deprecation_detection: 0.30
#   new_features:          0.30
#
set -e

# sg_only_env: restore full repo before verification (no-op for regular runs)
[ -f /tmp/.sg_only_mode ] && [ -f /tests/sgonly_verifier_wrapper.sh ] && source /tests/sgonly_verifier_wrapper.sh


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

echo "Scoring release notes documentation ($DOC_SIZE bytes)..."
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
            if re.search(p, text, re.IGNORECASE | re.DOTALL):
                return True
        except re.error:
            if p.lower() in text.lower():
                return True
    return False

sc = gt["scoring_categories"]

# ── Score breaking_changes ─────────────────────────────────────────────
print("=== Breaking Changes ===")
bc_score, bc_total = 0.0, 0.0
for topic in sc["breaking_changes"]["topics"]:
    bc_total += topic["weight"]
    if check_any_pattern(topic["check_any_pattern"], doc):
        bc_score += topic["weight"]
        print(f"  [x] {topic['name']} (weight: {topic['weight']:.3f})")
    else:
        print(f"  [ ] {topic['name']} (weight: {topic['weight']:.3f})")
bc_ratio = bc_score / bc_total if bc_total > 0 else 0
print(f"  Breaking changes score: {bc_score:.3f} / {bc_total:.3f} = {bc_ratio:.2f}")
print()

# ── Score deprecation_detection ────────────────────────────────────────
print("=== Deprecation Detection ===")
dd_score, dd_total = 0.0, 0.0
for topic in sc["deprecation_detection"]["topics"]:
    dd_total += topic["weight"]
    if check_any_pattern(topic["check_any_pattern"], doc):
        dd_score += topic["weight"]
        print(f"  [x] {topic['name']} (weight: {topic['weight']:.3f})")
    else:
        print(f"  [ ] {topic['name']} (weight: {topic['weight']:.3f})")
dd_ratio = dd_score / dd_total if dd_total > 0 else 0
print(f"  Deprecation detection score: {dd_score:.3f} / {dd_total:.3f} = {dd_ratio:.2f}")
print()

# ── Score new_features ─────────────────────────────────────────────────
print("=== New Features ===")
nf_score, nf_total = 0.0, 0.0
for topic in sc["new_features"]["topics"]:
    nf_total += topic["weight"]
    if check_any_pattern(topic["check_any_pattern"], doc):
        nf_score += topic["weight"]
        print(f"  [x] {topic['name']} (weight: {topic['weight']:.3f})")
    else:
        print(f"  [ ] {topic['name']} (weight: {topic['weight']:.3f})")
nf_ratio = nf_score / nf_total if nf_total > 0 else 0
print(f"  New features score: {nf_score:.3f} / {nf_total:.3f} = {nf_ratio:.2f}")
print()

# ── Compute weighted total ─────────────────────────────────────────────
w_breaking = sc["breaking_changes"]["weight"]
w_deprecation = sc["deprecation_detection"]["weight"]
w_features = sc["new_features"]["weight"]

total = (bc_ratio * w_breaking +
         dd_ratio * w_deprecation +
         nf_ratio * w_features)

print("=== Final Score ===")
print(f"  Breaking changes:     {bc_ratio:.2f} * {w_breaking} = {bc_ratio * w_breaking:.3f}")
print(f"  Deprecation detection:{dd_ratio:.2f} * {w_deprecation} = {dd_ratio * w_deprecation:.3f}")
print(f"  New features:         {nf_ratio:.2f} * {w_features} = {nf_ratio * w_features:.3f}")
print(f"  TOTAL:                {total:.2f}")

with open(REWARD_PATH, "w") as f:
    f.write(f"{total:.2f}\n")

print()
print(f"Tests completed - Score: {total:.2f}")
PYEOF
