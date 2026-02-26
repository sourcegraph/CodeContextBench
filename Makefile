.PHONY: agent-nav agent-nav-check docs-consistency repo-health-quick

agent-nav:
	python3 scripts/refresh_agent_navigation.py

agent-nav-check:
	python3 scripts/refresh_agent_navigation.py --check

docs-consistency:
	python3 scripts/docs_consistency_check.py

repo-health-quick:
	python3 scripts/repo_health.py --quick
