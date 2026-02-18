# Task: Developer Onboarding Guide for Istio Control Plane

**Repository:** istio/istio (cloned at `/workspace`)
**Output:** Write your document to `/workspace/documentation.md`

## Objective

Produce a developer onboarding guide for the Istio control plane, focused on the `pilot/` directory and the Istiod / pilot-discovery component. The target audience is a new developer joining the Istio team who needs to understand how to build, test, and contribute to the control plane.

## Scope

Focus on the developer experience of working on Istio's control plane. Your document must cover build prerequisites, architecture fundamentals, the first-contribution workflow, and key directories and files a new contributor should understand first.

## Content Expectations

Address all of the following in your own structure:

1. **Build prerequisites** -- Go version requirements, protobuf compiler (protoc), Make build system and key targets, Docker for image builds, kubectl and cluster tooling (kind/minikube) for local testing.

2. **Architecture overview** -- Istiod as the unified control plane monolith, the pilot-discovery binary and its role, the xDS protocol (ADS) for pushing configuration to Envoy proxies, sidecar injection via MutatingWebhook, and the config distribution pipeline (PushContext).

3. **First-contribution workflow** -- How to clone the repository, build the project, run unit and integration tests, and submit a pull request (PR process, CLA/DCO requirements, code review expectations).

4. **Key directories and files** -- A map of the most important directories (`pilot/`, `pkg/`, `tests/`, `tools/`, Makefile system) and what a new developer should read first to orient themselves.

## Quality Bar

- Cite specific Makefile targets (e.g., `make build`, `make test`, `make docker`).
- Reference concrete test commands (e.g., `go test ./pilot/...`).
- Include actual file paths from the repository, not generic descriptions.
- Explain what each architectural component does and how they interact.
- Do not fabricate file paths, commands, or internal APIs.

## Anti-Requirements

- Do not document user-facing Istio features (VirtualService, DestinationRule, Gateway CRDs). Focus on developer experience, not user experience.
- Do not provide shallow bullet dumps without explanation.
- Do not rely on external documentation not present in the workspace.
