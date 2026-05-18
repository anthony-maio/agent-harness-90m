"""
policy.py -- Policy gate. Checks tool calls against the policy config
and the task's own restrictions. Prompts for approval when required.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    needs_approval: bool = False


class PolicyGate:
    def __init__(self, config: dict, task_blocked: list[str], auto_approve: bool = False):
        self._require_approval: set[str] = set(config.get("require_approval", []))
        self._blocked: set[str] = set(config.get("block", []))
        self._blocked.update(task_blocked)
        self._workspace_root = Path(config.get("workspace_root", "./workspace"))
        self._auto_approve = auto_approve

    def check(self, tool_name: str, arguments: dict) -> PolicyDecision:
        if tool_name in self._blocked:
            return PolicyDecision(
                allowed=False,
                reason=f"Tool '{tool_name}' is blocked by policy",
            )

        if tool_name in ("write_file", "read_file"):
            path = arguments.get("path", "")
            if path and not self._is_in_workspace(path):
                return PolicyDecision(
                    allowed=False,
                    reason=f"Path '{path}' is outside the workspace root ({self._workspace_root})",
                )

        if tool_name in self._require_approval:
            if self._auto_approve:
                return PolicyDecision(
                    allowed=True,
                    reason="Auto-approved (--yes flag)",
                    needs_approval=False,
                )
            return PolicyDecision(
                allowed=True,
                reason=f"Tool '{tool_name}' requires approval",
                needs_approval=True,
            )

        return PolicyDecision(allowed=True, reason="Allowed by policy")

    def prompt_approval(self, tool_name: str, arguments: dict) -> bool:
        print(f"\n--- APPROVAL REQUIRED ---")
        print(f"Tool:      {tool_name}")
        print(f"Arguments: {arguments}")
        print(f"---")
        response = input("Approve? [y/N] ").strip().lower()
        return response in ("y", "yes")

    def _is_in_workspace(self, path: str) -> bool:
        try:
            resolved = Path(path).resolve()
            workspace = self._workspace_root.resolve()
            return str(resolved).startswith(str(workspace))
        except (ValueError, OSError):
            return False
