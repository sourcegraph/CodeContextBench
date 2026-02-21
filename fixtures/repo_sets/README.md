# Repo-Set Fixtures

Repo-set fixtures define the repository set for each MCP-unique benchmark task.
Each fixture specifies:

- **Repos**: The full set of repositories relevant to the task
- **Cross-org flag**: Whether repos span multiple GitHub organizations
- **Sourcegraph indexing**: Whether repos are natively indexed or need mirrors

## Design Principle

**Baseline and MCP-Full agents have access to the same repos.** The only
difference is the *method* of access:

- **Baseline**: All repos cloned locally in `/workspace`. No MCP tools.
- **MCP-Full**: Local code truncated/empty. Agent uses Sourcegraph MCP tools.

This ensures we measure whether MCP tools help the agent work better/faster —
not whether MCP can access repos the baseline can't.

## Schema

All fixtures validate against `schemas/repo_set_fixture.schema.json`.

## Directory Structure

```
fixtures/repo_sets/
  kubernetes-ecosystem.json    # k8s core + client-go + api + etcd
  nodejs-web-stack.json        # node + express + lodash + prisma
  python-ml-stack.json         # scikit-learn + numpy + pandas + scipy
  grafana-observability.json   # grafana + loki + mimir
  multi-org-go.json            # k8s + etcd + grafana (cross-org Go)
```

## Access Mode

All repos should use `access_mode: "local_checkout"`. The `mcp_only` and `both`
values are retained in the schema for potential future use but should not be
used — baseline must always have full local access to every repo in the fixture.

| Mode | Baseline Config | MCP-Full Config |
|------|----------------|-----------------|
| `local_checkout` | Full repo in `/workspace` | Truncated; agent uses MCP |

## Adding a New Fixture

1. Create `fixtures/repo_sets/<name>.json` following the schema
2. Set **all repos** to `access_mode: "local_checkout"`
3. Verify all repos are Sourcegraph-indexed (use `mcp__sourcegraph__keyword_search`)
4. For unindexed repos, create an `sg-benchmarks` mirror and set `sourcegraph_mirror`
5. Pin every repo to a specific `revision` (SHA or tag) for reproducibility
6. Run: `python3 -c "import json; json.load(open('fixtures/repo_sets/<name>.json'))"`
7. Ensure `local_checkout_repos` lists ALL repos; `mcp_only_repos` should be `[]`

## Mirror Conventions

Repos not natively indexed in Sourcegraph use `sg-benchmarks` mirrors:
- Mirror naming: `sg-benchmarks/<org>-<repo>` (e.g. `sg-benchmarks/kubernetes-client-go`)
- Use orphan-commit approach for large repos (>2GB)
