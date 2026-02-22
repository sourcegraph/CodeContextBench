#!/usr/bin/env python3
"""
Inject SOURCEGRAPH_REPO_NAME (or SOURCEGRAPH_REPOS for multi-repo tasks)
into Dockerfile.sg_only files that are missing the env var.

Usage:
    python3 scripts/inject_sg_repo_env.py [--dry-run] [--task TASK_ID]
"""

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# Tasks that already have SOURCEGRAPH_REPO_NAME set — skip these
ALREADY_SET = {
    "curl-cve-triage-001",
    "curl-vuln-reachability-001",
    "kafka-vuln-reachability-001",
    "envoy-code-review-001",
    "vscode-code-review-001",
}

# Multi-repo tasks: use SOURCEGRAPH_REPOS (comma-separated list)
MULTI_REPO_TASKS = {
    "envoy-grpc-server-impl-001": "github.com/envoyproxy/go-control-plane,github.com/istio/istio,github.com/emissary-ingress/emissary",
    "k8s-runtime-object-impl-001": "github.com/kubernetes/api,github.com/kubernetes/apimachinery",
    "envoy-routeconfig-dep-chain-001": "github.com/istio/istio,github.com/envoyproxy/go-control-plane,github.com/envoyproxy/data-plane-api",
    "envoy-stream-aggregated-sym-001": "github.com/envoyproxy/envoy,github.com/grpc/grpc-go",
    "k8s-sharedinformer-sym-001": "github.com/kubernetes/kubernetes,github.com/kubernetes/autoscaler",
    "k8s-typemeta-dep-chain-001": "github.com/kubernetes/kubernetes,github.com/kubernetes/api,github.com/kubernetes/apimachinery",
    "kafka-flink-streaming-arch-001": "github.com/apache/kafka,github.com/apache/flink",
    "terraform-provider-iface-sym-001": "github.com/hashicorp/terraform,github.com/hashicorp/terraform-provider-aws",
    "envoy-migration-doc-gen-001": "sg-benchmarks/envoy--50ea83e6,sg-benchmarks/envoy--7b8baff1",
    "terraform-arch-doc-gen-001": "sg-benchmarks/terraform--7637a921,sg-benchmarks/terraform--24236f4f",
    "terraform-migration-doc-gen-001": "sg-benchmarks/terraform--7637a921,sg-benchmarks/terraform--24236f4f",
    "grpcurl-transitive-vuln-001": "github.com/fullstorydev/grpcurl,github.com/grpc/grpc-go",
    "wish-transitive-vuln-001": "github.com/charmbracelet/wish,github.com/gliderlabs/ssh",
    "numpy-dtype-localize-001": "sg-benchmarks/numpy--a639fbf5,sg-benchmarks/scikit-learn--cb7e82dd,sg-benchmarks/pandas--41968da5",
    "k8s-cri-containerd-reason-001": "sg-benchmarks/containerd--317286ac,github.com/kubernetes/kubernetes",
    "python-http-class-naming-refac-001": "github.com/django/django,github.com/pallets/flask,github.com/psf/requests",
    "etcd-grpc-api-upgrade-001": "sg-benchmarks/etcd--d89978e8,github.com/kubernetes/kubernetes,sg-benchmarks/containerd--317286ac",
}

# Single-repo tasks: task_id -> SOURCEGRAPH_REPO_NAME value
SINGLE_REPO_TASKS = {
    "ansible-abc-imports-fix-001": "sg-benchmarks/ansible--379058e1",
    "ansible-module-respawn-fix-001": "sg-benchmarks/ansible--4c5ce5a1",
    "ansible-galaxy-tar-regression-prove-001": "sg-benchmarks/ansible--b2a289dc",
    "argocd-arch-orient-001": "github.com/argoproj/argo-cd",
    "argocd-sync-reconcile-qa-001": "github.com/argoproj/argo-cd",
    "aspnetcore-code-review-001": "sg-benchmarks/aspnetcore--87525573",
    "bustub-hyperloglog-impl-001": "sg-benchmarks/bustub--d5f79431",
    "calcom-code-review-001": "sg-benchmarks/cal.com--4b99072b",
    "camel-fix-protocol-feat-001": "github.com/apache/camel",
    "camel-routing-arch-001": "github.com/apache/camel",
    "cgen-deps-install-001": "sg-benchmarks/cgen--dibench",
    "cilium-api-doc-gen-001": "github.com/cilium/cilium",
    "cilium-ebpf-datapath-handoff-001": "github.com/cilium/cilium",
    "cilium-ebpf-fault-qa-001": "github.com/cilium/cilium",
    "cilium-project-orient-001": "github.com/cilium/cilium",
    "codecoverage-deps-install-001": "sg-benchmarks/CodeCoverageSummary--dibench",
    "curl-security-review-001": "sg-benchmarks/curl--09e25b9d",
    "django-admins-migration-audit-001": "github.com/django/django",
    "django-audit-trail-implement-001": "github.com/django/django",
    "django-composite-field-recover-001": "github.com/django/django",
    "django-cross-team-boundary-001": "github.com/django/django",
    "django-csrf-session-audit-001": "github.com/django/django",
    "flipt-flagexists-refactor-001": "sg-benchmarks/flipt--3d5a345f",
    "django-legacy-dep-vuln-001": "github.com/django/django",
    "django-modeladmin-impact-001": "github.com/django/django",
    "django-modelchoice-fk-fix-001": "github.com/django/django",
    "django-orm-query-arch-001": "github.com/django/django",
    "django-policy-enforcement-001": "github.com/django/django",
    "django-pre-validate-signal-design-001": "github.com/django/django",
    "django-rate-limit-design-001": "github.com/django/django",
    "django-repo-scoped-access-001": "github.com/django/django",
    "django-role-based-access-001": "github.com/django/django",
    "django-select-for-update-fix-001": "github.com/django/django",
    "django-sensitive-file-exclusion-001": "github.com/django/django",
    "django-template-inherit-recall-001": "github.com/django/django",
    "docgen-changelog-001": "github.com/hashicorp/terraform",
    "docgen-changelog-002": "sg-benchmarks/flipt--3d5a345f",
    "docgen-inline-001": "github.com/django/django",
    "docgen-inline-002": "github.com/apache/kafka",
    "docgen-onboard-001": "github.com/istio/istio",
    "docgen-runbook-001": "github.com/prometheus/prometheus",
    "docgen-runbook-002": "github.com/envoyproxy/envoy",
    "dotenv-expand-deps-install-001": "sg-benchmarks/dotenv-expand--dibench",
    "dotnetkoans-deps-install-001": "sg-benchmarks/DotNetKoans--dibench",
    "envoy-arch-doc-gen-001": "github.com/envoyproxy/envoy",
    "envoy-contributor-workflow-001": "github.com/envoyproxy/envoy",
    "envoy-cve-triage-001": "github.com/envoyproxy/envoy",
    "envoy-duplicate-headers-debug-001": "github.com/envoyproxy/envoy",
    "envoy-ext-authz-handoff-001": "github.com/envoyproxy/envoy",
    "envoy-filter-chain-qa-001": "github.com/envoyproxy/envoy",
    "envoy-request-routing-qa-001": "github.com/envoyproxy/envoy",
    "envoy-vuln-reachability-001": "github.com/envoyproxy/envoy",
    "eslint-markdown-deps-install-001": "sg-benchmarks/markdown--dibench",
    "flink-checkpoint-arch-001": "github.com/apache/flink",
    "flink-pricing-window-feat-001": "github.com/apache/flink",
    "flipt-auth-cookie-regression-prove-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-cockroachdb-backend-fix-001": "sg-benchmarks/flipt--9f8127f2",
    "flipt-degraded-context-fix-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-dep-refactor-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-ecr-auth-oci-fix-001": "sg-benchmarks/flipt--c188284f",
    "flipt-eval-latency-fix-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-otlp-exporter-fix-001": "sg-benchmarks/flipt--b433bd05",
    "flipt-protobuf-metadata-design-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-repo-scoped-access-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-trace-sampling-fix-001": "sg-benchmarks/flipt--3d5a345f",
    "flipt-transitive-deps-001": "sg-benchmarks/flipt--3d5a345f",
    "ghost-code-review-001": "sg-benchmarks/Ghost--b43bfc85",
    "golang-net-cve-triage-001": "github.com/golang/net",
    "grafana-table-panel-regression-001": "github.com/grafana/grafana",
    "iamactionhunter-deps-install-001": "sg-benchmarks/IAMActionHunter--dibench",
    "istio-arch-doc-gen-001": "github.com/istio/istio",
    "istio-xds-destrul-debug-001": "github.com/istio/istio",
    "istio-xds-serving-qa-001": "github.com/istio/istio",
    "k8s-apiserver-doc-gen-001": "sg-benchmarks/kubernetes--stripped",
    "k8s-applyconfig-doc-gen-001": "sg-benchmarks/kubernetes--stripped",
    "k8s-clientgo-doc-gen-001": "sg-benchmarks/kubernetes--stripped",
    "k8s-kubelet-cm-doc-gen-001": "sg-benchmarks/kubernetes--stripped",
    "k8s-crd-lifecycle-arch-001": "github.com/kubernetes/kubernetes",
    "k8s-dra-allocation-impact-001": "github.com/kubernetes/kubernetes",
    "k8s-dra-scheduler-event-fix-001": "github.com/kubernetes/kubernetes",
    "k8s-fairqueuing-doc-gen-001": "sg-benchmarks/kubernetes--stripped",
    "k8s-noschedule-taint-feat-001": "github.com/kubernetes/kubernetes",
    "k8s-scheduler-arch-001": "github.com/kubernetes/kubernetes",
    "k8s-score-normalizer-refac-001": "github.com/kubernetes/kubernetes",
    "k8s-sharedinformer-sym-001": "github.com/kubernetes/kubernetes",
    "kafka-api-doc-gen-001": "github.com/apache/kafka",
    "kafka-batch-accumulator-refac-001": "github.com/apache/kafka",
    "kafka-build-orient-001": "github.com/apache/kafka",
    "kafka-contributor-workflow-001": "github.com/apache/kafka",
    "kafka-message-lifecycle-qa-001": "github.com/apache/kafka",
    "kafka-producer-bufpool-fix-001": "github.com/apache/kafka",
    "kafka-sasl-auth-audit-001": "github.com/apache/kafka",
    "kafka-security-review-001": "github.com/apache/kafka",
    "linux-acpi-backlight-fault-001": "sg-benchmarks/linux--55b2af1c",
    "linux-hda-intel-suspend-fault-001": "sg-benchmarks/linux--07c4ee00",
    "linux-iwlwifi-subdevice-fault-001": "sg-benchmarks/linux--11a48a5a",
    "linux-nfs-inode-revalidate-fault-001": "sg-benchmarks/linux--07cc49f6",
    "linux-ssd-trim-timeout-fault-001": "sg-benchmarks/linux--fa5941f4",
    "llamacpp-context-window-search-001": "sg-benchmarks/llama.cpp--56399714",
    "llamacpp-file-modify-search-001": "sg-benchmarks/llama.cpp--56399714",
    "navidrome-windows-log-fix-001": "sg-benchmarks/navidrome--9c3b4561",
    "nodebb-notif-dropdown-fix-001": "github.com/NodeBB/NodeBB",
    "nodebb-plugin-validate-fix-001": "sg-benchmarks/nodebb--76c6e302",
    "numpy-array-sum-perf-001": "sg-benchmarks/numpy--a639fbf5",
    "openhands-search-file-test-001": "sg-benchmarks/OpenHands--latest",
    "openlibrary-fntocli-adapter-fix-001": "sg-benchmarks/openlibrary--c506c1b0",
    "openlibrary-search-query-fix-001": "sg-benchmarks/openlibrary--7f6b722a",
    "openlibrary-solr-boolean-fix-001": "sg-benchmarks/openlibrary--92db3454",
    "pandas-groupby-perf-001": "sg-benchmarks/pandas--41968da5",
    "pcap-parser-deps-install-001": "sg-benchmarks/pcap-parser--dibench",
    "postgres-client-auth-audit-001": "github.com/postgres/postgres",
    "postgres-query-exec-arch-001": "github.com/postgres/postgres",
    "prometheus-queue-reshard-debug-001": "github.com/prometheus/prometheus",
    "protonmail-conv-testhooks-fix-001": "sg-benchmarks/webclients--c6f65d20",
    "protonmail-dropdown-sizing-fix-001": "sg-benchmarks/webclients--8be4f6cb",
    "protonmail-holiday-calendar-fix-001": "sg-benchmarks/webclients--369fd37d",
    "pytorch-cudnn-version-fix-001": "github.com/pytorch/pytorch",
    "pytorch-dynamo-keyerror-fix-001": "github.com/pytorch/pytorch",
    "pytorch-release-210-fix-001": "github.com/pytorch/pytorch",
    "pytorch-relu-gelu-fusion-fix-001": "github.com/pytorch/pytorch",
    "pytorch-tracer-graph-cleanup-fix-001": "github.com/pytorch/pytorch",
    "quantlib-barrier-pricing-arch-001": "github.com/lballabio/QuantLib",
    "qutebrowser-hsv-color-regression-prove-001": "github.com/qutebrowser/qutebrowser",
    "qutebrowser-adblock-cache-regression-prove-001": "github.com/qutebrowser/qutebrowser",
    "qutebrowser-darkmode-threshold-regression-prove-001": "github.com/qutebrowser/qutebrowser",
    "qutebrowser-url-regression-prove-001": "github.com/qutebrowser/qutebrowser",
    "rust-subtype-relation-refac-001": "github.com/rust-lang/rust",
    "servo-scrollend-event-feat-001": "github.com/servo/servo",
    "similar-asserts-deps-install-001": "sg-benchmarks/similar-asserts--dibench",
    "sklearn-kmeans-perf-001": "sg-benchmarks/scikit-learn--cb7e82dd",
    "strata-cds-tranche-feat-001": "github.com/OpenGamma/Strata",
    "strata-fx-european-refac-001": "github.com/OpenGamma/Strata",
    "teleport-ssh-regression-prove-001": "github.com/gravitational/teleport",
    "tensorrt-mxfp4-quant-feat-001": "github.com/NVIDIA/TensorRT-LLM",
    "terraform-code-review-001": "github.com/hashicorp/terraform",
    "terraform-phantom-update-debug-001": "github.com/hashicorp/terraform",
    "terraform-plan-pipeline-qa-001": "github.com/hashicorp/terraform",
    "terraform-state-backend-handoff-001": "github.com/hashicorp/terraform",
    "test-coverage-gap-001": "github.com/envoyproxy/envoy",
    "test-coverage-gap-002": "github.com/apache/kafka",
    "test-integration-001": "sg-benchmarks/flipt--3d5a345f",
    "test-integration-002": "sg-benchmarks/navidrome--9c3b4561",
    "test-unitgen-go-001": "github.com/kubernetes/kubernetes",
    "test-unitgen-py-001": "github.com/django/django",
    "tutanota-search-regression-prove-001": "github.com/tutao/tutanota",
    "vscode-api-doc-gen-001": "github.com/microsoft/vscode",
    "vscode-ext-host-qa-001": "github.com/microsoft/vscode",
    "vscode-stale-diagnostics-feat-001": "github.com/microsoft/vscode",
    "vuls-oval-regression-prove-001": "github.com/future-architect/vuls",
}

# Note: k8s-sharedinformer-sym-001 appears in both dicts (as single in SINGLE_REPO_TASKS
# and as multi in MULTI_REPO_TASKS). MULTI_REPO_TASKS takes precedence.
# Also: envoy-grpc-server-impl-001, k8s-runtime-object-impl-001 are multi-repo only.


def inject_env_var(dockerfile_path: Path, task_id: str, dry_run: bool = False) -> bool:
    """
    Inject SOURCEGRAPH_REPO_NAME or SOURCEGRAPH_REPOS env var into a Dockerfile.sg_only.
    Returns True if the file was (or would be) modified.
    """
    content = dockerfile_path.read_text()

    # Check if already has either env var
    if "SOURCEGRAPH_REPO_NAME" in content or "SOURCEGRAPH_REPOS" in content:
        print(f"  SKIP {task_id}: already has SOURCEGRAPH_REPO_NAME or SOURCEGRAPH_REPOS")
        return False

    # Determine env var name and value
    if task_id in MULTI_REPO_TASKS:
        env_var = "SOURCEGRAPH_REPOS"
        env_val = MULTI_REPO_TASKS[task_id]
    elif task_id in SINGLE_REPO_TASKS:
        env_var = "SOURCEGRAPH_REPO_NAME"
        env_val = SINGLE_REPO_TASKS[task_id]
    else:
        print(f"  WARN {task_id}: no mapping found, skipping")
        return False

    # Find the FROM line and insert after it
    lines = content.splitlines(keepends=True)

    # Find last FROM line (in case of multi-stage builds, though we don't have them)
    from_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("FROM "):
            from_idx = i

    if from_idx is None:
        print(f"  ERROR {task_id}: no FROM line found in {dockerfile_path}")
        return False

    # Build the ENV line to insert
    env_line = f"\nENV {env_var}={env_val}\n"

    # Insert after FROM line
    new_lines = lines[: from_idx + 1] + [env_line] + lines[from_idx + 1 :]
    new_content = "".join(new_lines)

    if dry_run:
        print(f"  DRY-RUN {task_id}: would add ENV {env_var}={env_val}")
        return True

    dockerfile_path.write_text(new_content)
    print(f"  OK {task_id}: added ENV {env_var}={env_val}")
    return True


def find_all_sg_only_dockerfiles():
    """Find all Dockerfile.sg_only files across SDLC suites."""
    suites = [
        "ccb_build",
        "ccb_debug",
        "ccb_design",
        "ccb_document",
        "ccb_fix",
        "ccb_secure",
        "ccb_test",
        "ccb_understand",
    ]
    results = []
    for suite in suites:
        suite_dir = REPO_ROOT / "benchmarks" / suite
        if not suite_dir.exists():
            continue
        for df in sorted(suite_dir.glob("*/environment/Dockerfile.sg_only")):
            task_id = df.parent.parent.name
            results.append((task_id, df))
    return results


def main():
    parser = argparse.ArgumentParser(description="Inject SOURCEGRAPH_REPO_NAME into Dockerfile.sg_only files")
    parser.add_argument("--dry-run", action="store_true", help="Print changes without writing files")
    parser.add_argument("--task", help="Process only this specific task ID")
    args = parser.parse_args()

    all_files = find_all_sg_only_dockerfiles()
    print(f"Found {len(all_files)} Dockerfile.sg_only files across SDLC suites")

    if args.task:
        all_files = [(tid, df) for tid, df in all_files if tid == args.task]
        if not all_files:
            print(f"ERROR: task {args.task} not found")
            sys.exit(1)

    modified = 0
    skipped_already_set = 0
    skipped_no_mapping = 0
    errors = 0

    for task_id, dockerfile_path in all_files:
        if task_id in ALREADY_SET:
            print(f"  SKIP {task_id}: in ALREADY_SET list")
            skipped_already_set += 1
            continue

        try:
            changed = inject_env_var(dockerfile_path, task_id, dry_run=args.dry_run)
            if changed:
                modified += 1
            else:
                content = dockerfile_path.read_text()
                if "SOURCEGRAPH_REPO_NAME" in content or "SOURCEGRAPH_REPOS" in content:
                    skipped_already_set += 1
                else:
                    skipped_no_mapping += 1
        except Exception as e:
            print(f"  ERROR {task_id}: {e}")
            errors += 1

    print()
    print(f"Summary:")
    print(f"  Modified: {modified}")
    print(f"  Skipped (already set): {skipped_already_set}")
    print(f"  Skipped (no mapping): {skipped_no_mapping}")
    print(f"  Errors: {errors}")
    print(f"  Total: {len(all_files)}")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
