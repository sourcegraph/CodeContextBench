"""Copilot harness agent that runs the GitHub Copilot CLI with our baseline guidance."""

import os
import re
import shlex
from pathlib import Path

from harbor.agents.installed.base import BaseInstalledAgent, ExecInput
from harbor.models.agent.context import AgentContext
from harbor.models.trial.paths import EnvironmentPaths

from ..base import BaselineHarnessMixin


class CopilotCliAgent(BaseInstalledAgent):
    """Minimal Copilot CLI wrapper that surfaces the CLI output path."""

    SUPPORTS_ATIF = False
    _OUTPUT_FILENAME = "copilot.log"

    @staticmethod
    def name() -> str:
        return "copilot-cli"

    def version(self) -> str | None:
        return os.environ.get("COPILOT_CLI_VERSION") or "custom"

    @property
    def _install_agent_template_path(self) -> Path:
        return Path(__file__).parent / "install-copilot.sh.j2"

    def create_run_agent_commands(self, instruction: str) -> list[ExecInput]:
        token = self._resolve_token()
        if not token:
            raise RuntimeError(
                "Copilot CLI requires COPILOT_GITHUB_TOKEN, GH_TOKEN, GITHUB_TOKEN, "
                "or a token stored in ~/.config/gh/hosts.yml"
            )

        env = {
            "COPILOT_GITHUB_TOKEN": token,
            "GH_TOKEN": token,
            "GITHUB_TOKEN": token,
        }
        env.update(
            {
                k: v
                for k, v in os.environ.items()
                if k.startswith("COPILOT_") and k not in env
            }
        )

        if model := os.environ.get("COPILOT_MODEL"):
            model_flag = f"--model {shlex.quote(model)} "
        else:
            model_flag = ""

        escaped_instruction = shlex.quote(instruction.strip())
        log_path = EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME

        command = (
            f"set -euo pipefail && "
            f"copilot --prompt {escaped_instruction} "
            f"{model_flag}"
            f"--format markdown "
            f"--log-level info "
            f"--log {log_path} "
            "| tee "
            f"{log_path}"
        )

        return [ExecInput(command=command, env=env)]

    def _resolve_token(self) -> str | None:
        for var in ("COPILOT_GITHUB_TOKEN", "GH_TOKEN", "GITHUB_TOKEN"):
            value = os.environ.get(var)
            if value:
                return value

        cfg = Path.home() / ".config/gh/hosts.yml"
        if not cfg.exists():
            return None

        pattern = re.compile(r"^\s*oauth_token:\s*(\S+)")
        with cfg.open() as fh:
            for line in fh:
                match = pattern.match(line)
                if match:
                    return match.group(1).strip()
        return None

    def populate_context_post_run(self, context: AgentContext) -> None:
        log_path = EnvironmentPaths.agent_dir / self._OUTPUT_FILENAME
        if log_path.exists():
            context.metadata.setdefault("copilot", {})["log_path"] = str(log_path)


class CopilotHarnessAgent(BaselineHarnessMixin, CopilotCliAgent):
    """Copilot CLI agent wired to the baseline MCP and evaluation guidance."""
