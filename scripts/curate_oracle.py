#!/usr/bin/env python3
"""Oracle curation tool for MCP-unique benchmark tasks.

Uses the Sourcegraph search API to generate oracle_answer.json files.

Three curation modes:
  keyword   Plain keyword search (original, fastest, most gameable)
  nls       NLS search via patternType:keyword (more semantic, less gameable)
  deep      Multi-query NLS with rev-pinning and min-hits threshold (default)

In "deep" mode:
  - Generates N diverse query formulations from the search_pattern and seed_prompt
  - Pins every query to the fixture's `revision` field via `rev:<ref>`
  - A file must appear in >= min_hits queries to be included in the oracle
  - Reduces tool-affinity bias: an agent can't replay a single query to recover
    the oracle because the oracle requires multi-query intersection

Note: LLM-powered Deep Search (SG Cody deepsearch) is not available over HTTP.
For that capability use the MCP batch agent approach.

Reads:  task_spec.json + repo-set fixture
Writes: oracle_answer.json, oracle_curation_log.json

Environment variables:
    SOURCEGRAPH_URL          SG instance URL (default: https://sourcegraph.sourcegraph.com)
    SOURCEGRAPH_ACCESS_TOKEN SG API token
    SRC_ENDPOINT             Fallback for SOURCEGRAPH_URL
    SRC_ACCESS_TOKEN         Fallback for SOURCEGRAPH_ACCESS_TOKEN

Usage:
    python3 scripts/curate_oracle.py --task-dir benchmarks/ccb_mcp_incident/ccx-incident-142
    python3 scripts/curate_oracle.py --task-dir <dir> --mode deep --num-runs 4 --min-hits 2
    python3 scripts/curate_oracle.py --task-dir <dir> --mode keyword  # legacy behaviour
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Sourcegraph API client (stdlib-only: urllib)
# ---------------------------------------------------------------------------

class SourcegraphClient:
    """Thin wrapper around the Sourcegraph GraphQL search API."""

    DEFAULT_URL = "https://sourcegraph.sourcegraph.com"
    GRAPHQL_PATH = "/.api/graphql"

    def __init__(self, url: str, token: str, verbose: bool = False):
        self.url = url.rstrip("/")
        self.token = token
        self.verbose = verbose
        self.queries_made = 0
        self._request_log: List[Dict] = []
        self._rate_limit_delay = 1.0  # seconds between requests

    def graphql(
        self,
        query: str,
        variables: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Dict:
        """Execute a GraphQL query against the SG API with retry/backoff."""
        endpoint = f"{self.url}{self.GRAPHQL_PATH}"
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"token {self.token}",
        }
        req = urllib.request.Request(endpoint, data=payload, headers=headers, method="POST")

        if self.queries_made > 0:
            time.sleep(self._rate_limit_delay)
        self.queries_made += 1

        log_entry: Dict[str, Any] = {
            "query_index": self.queries_made,
            "variables": variables or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        last_exc: Optional[Exception] = None
        for attempt in range(6):
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read())
                if "errors" in data and data["errors"]:
                    logging.warning("GraphQL errors: %s", data["errors"])
                result = data.get("data", {})
                log_entry["status"] = "ok"
                self._request_log.append(log_entry)
                if self.verbose:
                    logging.debug("SG query #%d: ok", self.queries_made)
                return result
            except urllib.error.HTTPError as exc:
                last_exc = exc
                if exc.code == 429:
                    wait = min(2 ** (attempt + 1), 120)
                    logging.warning("Rate limited (429), waiting %ds", wait)
                    time.sleep(wait)
                else:
                    logging.error("HTTP %d from SG API", exc.code)
                    break
            except urllib.error.URLError as exc:
                last_exc = exc
                logging.warning("URLError (attempt %d): %s", attempt, exc)
                time.sleep(1)

        log_entry["status"] = "error"
        log_entry["error"] = str(last_exc)
        self._request_log.append(log_entry)
        return {}

    def search_files(
        self,
        sg_query: str,
        max_results: int = 200,
        mode: str = "deep",
    ) -> List[Dict]:
        """Return list of {repo, path, line_matches} from a file search.

        mode="deep" or "nls" appends patternType:keyword for semantic matching.
        mode="keyword" uses plain SG keyword search.
        """
        gql = """
        query CurateFiles($query: String!) {
          search(query: $query, version: V2) {
            results {
              results {
                ... on FileMatch {
                  repository { name }
                  file { path }
                  lineMatches { lineNumber preview }
                }
              }
            }
          }
        }
        """
        full_query = f"{sg_query} count:{max_results}"
        if mode in ("deep", "nls"):
            full_query += " patternType:keyword"

        resp = self.graphql(gql, {"query": full_query})
        items = []
        for r in (resp.get("search") or {}).get("results", {}).get("results", []):
            repo = (r.get("repository") or {}).get("name", "")
            path = (r.get("file") or {}).get("path", "")
            if repo and path:
                items.append({
                    "repo": repo,
                    "path": path,
                    "line_matches": r.get("lineMatches", []),
                })
        return items

    def search_symbols(self, sg_query: str, max_results: int = 100) -> List[Dict]:
        """Return list of {repo, path, symbol, kind} from a symbol search."""
        gql = """
        query CurateSymbols($query: String!) {
          search(query: $query, version: V2) {
            results {
              results {
                ... on FileMatch {
                  repository { name }
                  file { path }
                  symbols {
                    name
                    kind
                    location {
                      resource { path }
                      range { start { line character } }
                    }
                  }
                }
              }
            }
          }
        }
        """
        full_query = f"type:symbol {sg_query} count:{max_results}"
        resp = self.graphql(gql, {"query": full_query})
        symbols = []
        for r in (resp.get("search") or {}).get("results", {}).get("results", []):
            repo = (r.get("repository") or {}).get("name", "")
            path = (r.get("file") or {}).get("path", "")
            for sym in r.get("symbols", []):
                symbols.append({
                    "repo": repo,
                    "path": path,
                    "symbol": sym.get("name", ""),
                    "kind": sym.get("kind", ""),
                    "line": (sym.get("location") or {}).get("range", {}).get("start", {}).get("line", 0),
                })
        return symbols

    def get_request_log(self) -> List[Dict]:
        return list(self._request_log)


# ---------------------------------------------------------------------------
# Fixture and spec loading
# ---------------------------------------------------------------------------

def _find_project_root(start: Path) -> Path:
    for root_candidate in [start.resolve(), Path.cwd().resolve()]:
        current = root_candidate
        for _ in range(10):
            if (current / "fixtures").is_dir() or (current / "benchmarks").is_dir():
                return current
            current = current.parent
    return start.resolve()


def load_fixture(repo_set_id: str, project_root: Path) -> Optional[Dict]:
    fixture_path = project_root / "fixtures" / "repo_sets" / f"{repo_set_id}.json"
    if not fixture_path.exists():
        logging.error("Fixture not found: %s", fixture_path)
        return None
    with open(fixture_path) as f:
        return json.load(f)


def get_repos_from_fixture(fixture: Dict) -> List[str]:
    """Extract all repo full names (for metadata / backward compat)."""
    return [r.get("full_name", "") for r in fixture.get("repos", []) if r.get("full_name")]


def get_repos_with_revisions(fixture: Dict) -> List[Tuple[str, str]]:
    """Extract (full_name, revision) pairs for rev-pinned queries.

    revision may be a short hash (e.g. "0753c489"), a tag ("v1.32.0"), or "HEAD".
    """
    result = []
    for r in fixture.get("repos", []):
        name = r.get("full_name", "")
        rev = r.get("revision", "HEAD")
        if name:
            result.append((name, rev))
    return result


def _repo_sg_name(full_name: str) -> str:
    """Convert org/repo to github.com/org/repo for SG queries."""
    if full_name.startswith("github.com/"):
        return full_name
    return f"github.com/{full_name}"


# ---------------------------------------------------------------------------
# Multi-query generation
# ---------------------------------------------------------------------------

def generate_query_variations(
    search_pattern: str,
    seed_prompt: str = "",
    num_runs: int = 3,
) -> List[str]:
    """Generate diverse query formulations for multi-run curation.

    Strategy:
      1. Always include the original search_pattern.
      2. Split on OR/AND and add individual terms as additional queries.
      3. If more runs are needed, extract CamelCase technical terms from
         seed_prompt that are not already covered.

    The goal is that the oracle (intersection across runs) is harder to
    reproduce with a single keyword_search call than the original pattern.
    """
    variations: List[str] = [search_pattern]

    # Split on boolean operators to get sub-terms
    raw_terms = re.split(r"\s+OR\s+|\s+AND\s+", search_pattern, flags=re.IGNORECASE)
    individual = [t.strip().strip('"').strip("'") for t in raw_terms if t.strip()]

    for term in individual:
        if term and term != search_pattern and term not in variations:
            variations.append(term)
        if len(variations) >= num_runs:
            return variations[:num_runs]

    # If still short, mine CamelCase or snake_case identifiers from seed_prompt
    if seed_prompt and len(variations) < num_runs:
        # e.g. "HeartbeatSessionTimeout", "heartbeat_timeout", "sessionTimeout"
        technical = re.findall(r"\b(?:[A-Z][a-z]+(?:[A-Z][a-z]+)+|[a-z]+(?:[A-Z][a-z]+)+)\b", seed_prompt)
        seen_lower = {v.lower() for v in variations}
        for term in technical:
            if term.lower() not in seen_lower:
                variations.append(term)
                seen_lower.add(term.lower())
            if len(variations) >= num_runs:
                break

    return variations[:num_runs]


# ---------------------------------------------------------------------------
# Oracle curation strategies
# ---------------------------------------------------------------------------

def curate_file_set_match(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
    mode: str = "deep",
    num_runs: int = 3,
    min_hits: int = 2,
    seed_prompt: str = "",
    repos_with_revisions: Optional[List[Tuple[str, str]]] = None,
) -> List[Dict]:
    """Search repos for files matching a pattern with multi-query aggregation.

    In "deep" mode:
      - Generates num_runs query variations
      - Pins each query to the repo's revision via `rev:<ref>`
      - Returns only files found in >= min_hits independent queries

    In "keyword" mode (legacy):
      - Single query, no rev-pinning, no aggregation
    """
    search_pattern = check_params.get("search_pattern", "")
    file_filter = check_params.get("file_filter", "")

    if not search_pattern:
        logging.warning("file_set_match: no search_pattern in params — skipping")
        return []

    # Build rev-aware repo list
    rev_map: Dict[str, str] = {}
    if repos_with_revisions:
        rev_map = {name: rev for name, rev in repos_with_revisions}

    if mode == "keyword":
        # Legacy: single query per repo, no rev-pinning
        oracle_files: List[Dict] = []
        seen: set = set()
        for repo in repos:
            sg_repo = _repo_sg_name(repo)
            query = f"repo:^{sg_repo}$ {search_pattern}"
            if file_filter:
                query += f" file:{file_filter}"
            log.append({"type": "file_set_match", "repo": repo, "query": query, "mode": mode})
            results = client.search_files(query, mode=mode)
            logging.info("  %s: %d file matches", repo, len(results))
            for r in results:
                key = (r["repo"], r["path"])
                if key not in seen:
                    seen.add(key)
                    oracle_files.append({"repo": r["repo"], "path": r["path"]})
        return oracle_files

    # Deep / NLS mode: multi-query with rev-pinning and min-hits threshold
    variations = generate_query_variations(search_pattern, seed_prompt, num_runs)
    log.append({
        "event": "query_variations",
        "search_pattern": search_pattern,
        "variations": variations,
        "num_runs": len(variations),
        "min_hits": min_hits,
        "mode": mode,
    })

    # file_hits[(repo, path)] = number of queries that returned it
    file_hits: Dict[Tuple[str, str], int] = {}

    for repo in repos:
        sg_repo = _repo_sg_name(repo)
        rev = rev_map.get(repo, "HEAD")
        rev_clause = "" if rev == "HEAD" else f" rev:{rev}"

        for run_i, variation in enumerate(variations):
            query = f"repo:^{sg_repo}${rev_clause} {variation}"
            if file_filter:
                query += f" file:{file_filter}"
            log.append({
                "type": "file_set_match",
                "repo": repo,
                "revision": rev,
                "query": query,
                "run": run_i,
                "variation": variation,
                "mode": mode,
            })
            results = client.search_files(query, mode=mode)
            logging.info(
                "  %s rev=%s run %d/%d [%s]: %d matches",
                repo, rev, run_i + 1, len(variations), variation[:50], len(results),
            )
            for r in results:
                key = (r["repo"], r["path"])
                file_hits[key] = file_hits.get(key, 0) + 1

    # Apply threshold: only files found in >= min_hits queries
    effective_min = min(min_hits, len(variations))  # can't require more than we ran
    oracle_files = [
        {"repo": repo, "path": path}
        for (repo, path), hits in sorted(file_hits.items())
        if hits >= effective_min
    ]
    log.append({
        "event": "multiquery_complete",
        "total_candidates": len(file_hits),
        "passing_min_hits": len(oracle_files),
        "min_hits_threshold": effective_min,
        "num_variations": len(variations),
        "repos_searched": repos,
    })

    return oracle_files


def curate_symbol_resolution(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
) -> List[Dict]:
    """Search repos for symbol definitions. Returns oracle symbol list."""
    symbol_pattern = check_params.get("symbol_name", check_params.get("search_pattern", ""))
    kind_filter = check_params.get("kind_filter", "")

    if not symbol_pattern:
        logging.warning("symbol_resolution: no symbol_name/search_pattern in params — skipping")
        return []

    oracle_symbols: List[Dict] = []
    seen: set = set()

    for repo in repos:
        sg_repo = _repo_sg_name(repo)
        query = f"repo:^{sg_repo}$ {symbol_pattern}"
        if kind_filter:
            query += " type:symbol"

        log.append({"type": "symbol_resolution", "repo": repo, "query": query})
        results = client.search_symbols(query)
        logging.info("  %s: %d symbol matches", repo, len(results))

        for sym in results:
            key = (sym["repo"], sym["path"], sym["symbol"])
            if key not in seen:
                seen.add(key)
                oracle_symbols.append({
                    "repo": sym["repo"],
                    "path": sym["path"],
                    "symbol": sym["symbol"],
                    "kind": sym.get("kind", ""),
                })

    return oracle_symbols


def curate_dependency_chain(
    client: SourcegraphClient,
    check_params: Dict,
    repos: List[str],
    log: List[Dict],
) -> List[Dict]:
    """Trace an import/call chain across repos. Returns ordered chain steps."""
    chain_steps = check_params.get("chain_steps", [])

    if not chain_steps:
        logging.warning("dependency_chain: no chain_steps in params — skipping")
        return []

    chain: List[Dict] = []

    for step in chain_steps:
        pattern = step.get("search_pattern", "")
        repo_hint = step.get("repo_hint", "")
        symbol_hint = step.get("symbol_hint", "")

        search_repos = [repo_hint] if repo_hint else repos
        for repo in search_repos:
            sg_repo = _repo_sg_name(repo)
            query = f"repo:^{sg_repo}$ {pattern}"

            log.append({"type": "dependency_chain_step", "repo": repo, "query": query, "symbol_hint": symbol_hint})
            results = client.search_files(query)

            if results:
                r = results[0]
                chain.append({
                    "repo": r["repo"],
                    "path": r["path"],
                    "symbol": symbol_hint or pattern,
                })
                break

    return chain


def curate_provenance(
    check_params: Dict,
    repos: List[str],
    oracle_files: List[Dict],
) -> Dict:
    must_cite_paths = check_params.get("must_cite_paths", [])
    must_cite_repos = check_params.get("must_cite_repos", [])

    if not must_cite_paths and oracle_files:
        must_cite_paths = [f["path"] for f in oracle_files[:5]]
    if not must_cite_repos and repos:
        must_cite_repos = repos[:3]

    return {
        "must_cite_paths": must_cite_paths,
        "must_cite_repos": must_cite_repos,
    }


def curate_keyword_presence(check_params: Dict) -> List[str]:
    return check_params.get("required_keywords", [])


# ---------------------------------------------------------------------------
# Main curation orchestrator
# ---------------------------------------------------------------------------

def curate_oracle(
    task_spec: Dict,
    client: SourcegraphClient,
    fixture: Optional[Dict],
    project_root: Path,
    mode: str = "deep",
    num_runs: int = 3,
    min_hits: int = 2,
    verbose: bool = False,
) -> Tuple[Dict, List[Dict]]:
    """Curate oracle_answer.json content by searching SG for each check type."""
    log: List[Dict] = []
    oracle_answer: Dict[str, Any] = {}

    oracle_def = task_spec.get("artifacts", {}).get("oracle", {})
    eval_checks = task_spec.get("evaluation", {}).get("checks", [])
    seed_prompt = task_spec.get("prd", {}).get("seed_prompt", "")

    repos: List[str] = []
    repos_with_revisions: List[Tuple[str, str]] = []
    if fixture:
        repos = get_repos_from_fixture(fixture)
        repos_with_revisions = get_repos_with_revisions(fixture)
        log.append({"event": "repos_from_fixture", "repos": repos, "revisions": dict(repos_with_revisions)})
    else:
        logging.warning("No fixture loaded — using repos from oracle definition if any")

    all_oracle_files: List[Dict] = list(oracle_def.get("required_files", []))
    all_oracle_symbols: List[Dict] = list(oracle_def.get("required_symbols", []))
    all_chains: List[Dict] = list(oracle_def.get("dependency_chains", []))

    for check in eval_checks:
        check_type = check.get("type", "")
        params = check.get("params", {})

        logging.info("Curating check: %s", check_type)

        if check_type == "file_set_match" and repos:
            new_files = curate_file_set_match(
                client=client,
                check_params=params,
                repos=repos,
                log=log,
                mode=mode,
                num_runs=num_runs,
                min_hits=min_hits,
                seed_prompt=seed_prompt,
                repos_with_revisions=repos_with_revisions,
            )
            seen = {(f["repo"], f["path"]) for f in all_oracle_files}
            for f in new_files:
                key = (f["repo"], f["path"])
                if key not in seen:
                    all_oracle_files.append(f)
                    seen.add(key)
            log.append({
                "event": "file_set_match_complete",
                "new_items": len(new_files),
                "total_items": len(all_oracle_files),
            })

        elif check_type == "symbol_resolution" and repos:
            new_syms = curate_symbol_resolution(client, params, repos, log)
            seen_sym = {(s["repo"], s["path"], s["symbol"]) for s in all_oracle_symbols}
            for s in new_syms:
                key = (s["repo"], s["path"], s["symbol"])
                if key not in seen_sym:
                    all_oracle_symbols.append(s)
                    seen_sym.add(key)
            log.append({
                "event": "symbol_resolution_complete",
                "new_items": len(new_syms),
                "total_items": len(all_oracle_symbols),
            })

        elif check_type == "dependency_chain" and repos:
            chain_steps = curate_dependency_chain(client, params, repos, log)
            if chain_steps:
                chain_id = params.get("chain_id", f"chain_{len(all_chains)}")
                all_chains.append({"chain_id": chain_id, "steps": chain_steps})
            log.append({
                "event": "dependency_chain_complete",
                "steps_found": len(chain_steps),
            })

        elif check_type == "provenance":
            prov = curate_provenance(params, repos, all_oracle_files)
            oracle_answer["provenance"] = prov
            log.append({"event": "provenance_oracle", "result": prov})

        elif check_type == "keyword_presence":
            kws = curate_keyword_presence(params)
            oracle_answer["required_keywords"] = kws
            log.append({"event": "keyword_presence_oracle", "keywords": kws})

        elif check_type in ("json_schema_match", "test_ratio"):
            log.append({"event": f"{check_type}_no_curation_needed"})

        else:
            logging.warning("Unknown or uncuratable check type: %s", check_type)

    if all_oracle_files:
        oracle_answer["files"] = all_oracle_files
    if all_oracle_symbols:
        oracle_answer["symbols"] = all_oracle_symbols
    if all_chains:
        oracle_answer["chains"] = all_chains
        if len(all_chains) == 1:
            oracle_answer["chain"] = all_chains[0]["steps"]

    text_parts = []
    for f in all_oracle_files[:10]:
        text_parts.append(f"{f['repo']} at {f['path']}")
    for s in all_oracle_symbols[:5]:
        text_parts.append(f"{s['symbol']} in {s['repo']}/{s['path']}")
    if text_parts:
        oracle_answer["text"] = " | ".join(text_parts)

    oracle_answer["repo_set_id"] = task_spec.get("artifacts", {}).get("repo_set_id", "")
    oracle_answer["symbols"] = oracle_answer.get("symbols", [])

    discovery = "sourcegraph_nls_multiquery" if mode in ("deep", "nls") else "sourcegraph_api"
    oracle_answer["_metadata"] = {
        "discovery_method": discovery,
        "curation_mode": mode,
        "num_runs": num_runs if mode != "keyword" else 1,
        "min_hits": min_hits if mode != "keyword" else 1,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repos_searched": repos,
        "sg_queries_made": client.queries_made,
    }

    return oracle_answer, log


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def find_task_spec(task_dir: Path) -> Optional[Path]:
    for p in [task_dir / "task_spec.json", task_dir / "tests" / "task_spec.json"]:
        if p.exists():
            return p
    return None


def find_oracle_answer(task_dir: Path) -> Optional[Path]:
    for p in [task_dir / "tests" / "oracle_answer.json", task_dir / "oracle_answer.json"]:
        if p.exists():
            return p
    return None


def oracle_answer_path(task_dir: Path) -> Path:
    tests_dir = task_dir / "tests"
    if tests_dir.is_dir():
        return tests_dir / "oracle_answer.json"
    return task_dir / "oracle_answer.json"


def oracle_log_path(task_dir: Path) -> Path:
    tests_dir = task_dir / "tests"
    if tests_dir.is_dir():
        return tests_dir / "oracle_curation_log.json"
    return task_dir / "oracle_curation_log.json"


def merge_oracle_answers(existing: Dict, new: Dict) -> Dict:
    """Merge new oracle findings into existing oracle_answer.json."""
    merged = dict(existing)

    existing_files = {(f["repo"], f["path"]) for f in merged.get("files", [])}
    for f in new.get("files", []):
        key = (f["repo"], f["path"])
        if key not in existing_files:
            merged.setdefault("files", []).append(f)
            existing_files.add(key)

    existing_syms = {(s["repo"], s["path"], s["symbol"]) for s in merged.get("symbols", [])}
    for s in new.get("symbols", []):
        key = (s["repo"], s["path"], s["symbol"])
        if key not in existing_syms:
            merged.setdefault("symbols", []).append(s)
            existing_syms.add(key)

    if "chains" in new:
        merged["chains"] = new["chains"]
    if "chain" in new:
        merged["chain"] = new["chain"]

    for k in ("provenance", "required_keywords"):
        if k in new:
            merged[k] = new[k]

    if "text" in new:
        merged["text"] = new["text"]

    merged["_metadata"] = new.get("_metadata", merged.get("_metadata", {}))

    return merged


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _get_sg_credentials() -> Tuple[str, str]:
    url = (
        os.environ.get("SOURCEGRAPH_URL")
        or os.environ.get("SRC_ENDPOINT")
        or SourcegraphClient.DEFAULT_URL
    )
    token = (
        os.environ.get("SOURCEGRAPH_ACCESS_TOKEN")
        or os.environ.get("SRC_ACCESS_TOKEN")
        or ""
    )
    return url, token


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Curate oracle_answer.json for MCP-unique benchmark tasks using Sourcegraph.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--task-dir", metavar="DIR",
                        help="Task directory (contains task_spec.json or tests/task_spec.json).")
    parser.add_argument("--task-spec", metavar="PATH",
                        help="Direct path to task_spec.json (overrides --task-dir discovery).")
    parser.add_argument(
        "--mode", choices=["deep", "nls", "keyword"], default="deep",
        help=(
            "Curation mode. "
            "deep: multi-query NLS with rev-pinning and min-hits threshold (default). "
            "nls: single NLS query with rev-pinning. "
            "keyword: legacy plain keyword search (most gameable)."
        ),
    )
    parser.add_argument(
        "--num-runs", type=int, default=3,
        help="Number of distinct query formulations to run in deep/nls mode (default: 3).",
    )
    parser.add_argument(
        "--min-hits", type=int, default=2,
        help="Files must appear in this many queries to be included (default: 2). "
             "Ignored in keyword mode.",
    )
    parser.add_argument("--verify", action="store_true",
                        help="After curation, run validate_mcp_task_instance.py.")
    parser.add_argument("--verbose", action="store_true",
                        help="Print detailed progress.")
    parser.add_argument("--max-results", type=int, default=200,
                        help="Maximum results per SG search query (default: 200).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse spec and plan queries without calling SG API.")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    if not args.task_dir and not args.task_spec:
        parser.error("One of --task-dir or --task-spec is required.")

    task_dir: Optional[Path] = Path(args.task_dir).resolve() if args.task_dir else None
    spec_path: Optional[Path] = Path(args.task_spec).resolve() if args.task_spec else None

    if task_dir and not spec_path:
        spec_path = find_task_spec(task_dir)
        if not spec_path:
            logging.error("task_spec.json not found in %s", task_dir)
            return 1

    if not task_dir and spec_path:
        task_dir = spec_path.parent

    assert task_dir is not None and spec_path is not None

    try:
        with open(spec_path) as f:
            task_spec = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        logging.error("Cannot load task_spec.json: %s", exc)
        return 1

    project_root = _find_project_root(task_dir)
    logging.info("Project root: %s", project_root)

    repo_set_id = task_spec.get("artifacts", {}).get("repo_set_id", "")
    fixture = None
    if repo_set_id:
        fixture = load_fixture(repo_set_id, project_root)
        if fixture:
            revisions = {r["full_name"]: r.get("revision", "HEAD") for r in fixture.get("repos", [])}
            logging.info("Loaded fixture: %s (%d repos, revisions: %s)", repo_set_id, len(fixture.get("repos", [])), revisions)
        else:
            logging.warning("Fixture '%s' not found", repo_set_id)
    else:
        logging.warning("No repo_set_id in task_spec")

    existing_oracle_path = find_oracle_answer(task_dir)
    existing_oracle: Dict = {}
    if existing_oracle_path:
        try:
            with open(existing_oracle_path) as f:
                existing_oracle = json.load(f)
            logging.info("Loaded existing oracle_answer.json (%d files)", len(existing_oracle.get("files", [])))
        except (json.JSONDecodeError, OSError):
            logging.warning("Could not load existing oracle_answer.json — starting fresh")

    if args.dry_run:
        checks = task_spec.get("evaluation", {}).get("checks", [])
        repos_with_revisions = get_repos_with_revisions(fixture) if fixture else []
        seed_prompt = task_spec.get("prd", {}).get("seed_prompt", "")
        logging.info("[DRY RUN] mode=%s num_runs=%d min_hits=%d", args.mode, args.num_runs, args.min_hits)
        logging.info("[DRY RUN] Checks: %s", [c.get("type") for c in checks])
        for c in checks:
            if c.get("type") == "file_set_match":
                pattern = c.get("params", {}).get("search_pattern", "")
                variations = generate_query_variations(pattern, seed_prompt, args.num_runs)
                logging.info("[DRY RUN] Variations for %r: %s", pattern, variations)
        for name, rev in repos_with_revisions:
            rev_clause = "" if rev == "HEAD" else f" rev:{rev}"
            logging.info("[DRY RUN] Repo: %s%s", _repo_sg_name(name), rev_clause)
        return 0

    sg_url, sg_token = _get_sg_credentials()
    if not sg_token:
        logging.warning("No SOURCEGRAPH_ACCESS_TOKEN — SG API calls may fail")

    client = SourcegraphClient(sg_url, sg_token, verbose=args.verbose)
    logging.info("Using SG instance: %s  mode=%s  num_runs=%d  min_hits=%d",
                 sg_url, args.mode, args.num_runs, args.min_hits)

    logging.info("Curating oracle for task: %s", task_spec.get("id", spec_path.name))
    oracle_answer, curation_log = curate_oracle(
        task_spec=task_spec,
        client=client,
        fixture=fixture,
        project_root=project_root,
        mode=args.mode,
        num_runs=args.num_runs,
        min_hits=args.min_hits,
        verbose=args.verbose,
    )

    if existing_oracle:
        oracle_answer = merge_oracle_answers(existing_oracle, oracle_answer)
        logging.info("Merged with existing oracle: %d files, %d symbols",
                     len(oracle_answer.get("files", [])), len(oracle_answer.get("symbols", [])))

    out_oracle = oracle_answer_path(task_dir)
    out_oracle.parent.mkdir(parents=True, exist_ok=True)
    with open(out_oracle, "w") as f:
        json.dump(oracle_answer, f, indent=2)
        f.write("\n")
    logging.info("Wrote oracle_answer.json -> %s (%d files, %d symbols)",
                 out_oracle, len(oracle_answer.get("files", [])), len(oracle_answer.get("symbols", [])))

    log_data = {
        "task_id": task_spec.get("id", ""),
        "task_spec_path": str(spec_path),
        "curated_at": datetime.now(timezone.utc).isoformat(),
        "sg_url": sg_url,
        "curation_mode": args.mode,
        "num_runs": args.num_runs,
        "min_hits": args.min_hits,
        "sg_queries_made": client.queries_made,
        "repos_searched": get_repos_from_fixture(fixture) if fixture else [],
        "curation_entries": curation_log,
        "sg_request_log": client.get_request_log(),
    }
    out_log = oracle_log_path(task_dir)
    with open(out_log, "w") as f:
        json.dump(log_data, f, indent=2)
    logging.info("Wrote oracle_curation_log.json -> %s", out_log)

    if args.verify:
        validator = project_root / "scripts" / "validate_mcp_task_instance.py"
        if not validator.exists():
            logging.warning("validate_mcp_task_instance.py not found — skipping verify")
        else:
            logging.info("Running validity gate...")
            result = subprocess.run(
                [sys.executable, str(validator), "--task-dir", str(task_dir), "--verbose"],
                capture_output=True, text=True,
            )
            print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            if result.returncode != 0:
                logging.error("Validity gate FAILED")
                return 1
            logging.info("Validity gate PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
