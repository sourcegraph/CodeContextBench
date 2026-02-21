Configure and launch CodeContextBench benchmark runs.

## Approval Gate (Required)

Before executing any run, confirm with the user:

1. **Model** — e.g. `anthropic/claude-haiku-4-5-20251001` (test) or `anthropic/claude-sonnet-4-6-20250514`
2. **Suite / selection file** — which benchmark suite or `--selection-file`?
3. **Config** — paired (default), `--baseline-only`, or `--full-only`? Which `--full-config`?
4. **Parallel slots** — how many? (default: 1; use 8 for multi-account)
5. **Category** — `staging` (default) or `official`?

Do NOT launch until all five are confirmed.

## Steps

1. Run preflight checks:
```bash
python3 scripts/check_infra.py
```

2. Launch the run with confirmed parameters:
```bash
# MCP-unique tasks (artifact config)
FULL_CONFIG=mcp-remote-artifact bash configs/run_selected_tasks.sh \
  --selection-file configs/selected_mcp_unique_tasks.json \
  --model <MODEL> --parallel <N> --category <CATEGORY>

# SDLC suite
./configs/<suite>_2config.sh --parallel <N>
```

3. Monitor progress:
```bash
python3 scripts/aggregate_status.py --staging
```

## Arguments

$ARGUMENTS — optional: suite name, model, or selection file to pre-fill the approval gate
