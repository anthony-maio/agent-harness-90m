"""
tools.py -- Tool registry. Discovers tool modules, validates calls against
the harness config, and executes them.

Each tool module in tools/ must expose:
    NAME: str
    DESCRIPTION: str
    PARAMETERS: dict  (JSON-schema-style description of arguments)
    def execute(**kwargs) -> str
"""

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import tools as tools_package


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    risk: str
    execute: Callable[..., str]


class ToolRegistry:
    def __init__(self, config_tools: dict):
        self._tools: dict[str, Tool] = {}
        self._config = config_tools
        self._discover()

    def _discover(self):
        for importer, modname, ispkg in pkgutil.iter_modules(
            tools_package.__path__
        ):
            if modname.startswith("_"):
                continue
            mod = importlib.import_module(f"tools.{modname}")
            name = getattr(mod, "NAME", modname)
            if name not in self._config:
                continue
            self._tools[name] = Tool(
                name=name,
                description=getattr(mod, "DESCRIPTION", ""),
                parameters=getattr(mod, "PARAMETERS", {}),
                risk=self._config[name].get("risk", "medium"),
                execute=mod.execute,
            )

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
                "risk": t.risk,
            }
            for t in self._tools.values()
        ]

    def available_names(self) -> list[str]:
        return list(self._tools.keys())

    def execute(self, name: str, arguments: dict) -> str:
        tool = self._tools.get(name)
        if not tool:
            return f"Error: unknown tool '{name}'"
        try:
            return tool.execute(**arguments)
        except Exception as e:
            return f"Error executing {name}: {e}"
