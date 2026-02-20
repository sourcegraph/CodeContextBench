#!/usr/bin/env python3
"""Verify that sg-benchmarks mirrors are indexed in Sourcegraph.

Run periodically after creating mirrors until all are indexed.
Uses the Sourcegraph GraphQL API via the `src` CLI or direct HTTP.

Usage:
    python3 scripts/verify_sg_indexing.py [--update]

    --update: Update configs/sg_mirror_revisions.json indexed field
"""
import json
import subprocess
import sys
from pathlib import Path

REVISIONS_FILE = Path(__file__).parent.parent / "configs" / "sg_mirror_revisions.json"


def check_repo_indexed(mirror_repo: str) -> bool:
    """Check if a repo is indexed in Sourcegraph using keyword_search."""
    # Use src CLI if available, otherwise use gh + SG API
    # For now, check if repo appears in SG search results
    try:
        # Try a simple search for any file in the repo
        result = subprocess.run(
            ["src", "search", "-json", f"repo:^github.com/{mirror_repo}$ count:1 file:."],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return len(data.get("Results", [])) > 0
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    # Fallback: check via GitHub API if SG has cloned the repo
    # (This is a heuristic - repo existence on GH doesn't mean SG indexed it)
    print(f"  Note: `src` CLI not available. Cannot verify SG indexing for {mirror_repo}.")
    print(f"  Manually verify: search 'repo:^github.com/{mirror_repo}$' on Sourcegraph.")
    return False


def main():
    update = "--update" in sys.argv

    if not REVISIONS_FILE.exists():
        print(f"ERROR: {REVISIONS_FILE} not found")
        sys.exit(1)

    data = json.loads(REVISIONS_FILE.read_text())
    mirrors = data["mirrors"]

    all_indexed = True
    results = []

    for mirror in mirrors:
        repo = mirror["mirror_repo"]
        was_indexed = mirror.get("indexed", False)

        if was_indexed:
            status = "INDEXED (previously verified)"
            indexed = True
        else:
            indexed = check_repo_indexed(repo)
            status = "INDEXED" if indexed else "NOT YET INDEXED"

        if not indexed:
            all_indexed = False

        results.append((repo, status, indexed))
        print(f"  {repo}: {status}")

        if update and indexed and not was_indexed:
            mirror["indexed"] = True

    if update:
        REVISIONS_FILE.write_text(json.dumps(data, indent=2) + "\n")
        print(f"\nUpdated {REVISIONS_FILE}")

    print(f"\n{'ALL INDEXED' if all_indexed else 'SOME NOT YET INDEXED'}")
    print(f"Indexed: {sum(1 for _, _, i in results if i)}/{len(results)}")

    sys.exit(0 if all_indexed else 1)


if __name__ == "__main__":
    main()
