"""
budget.py -- Budget enforcement. Tracks LLM calls, tool calls, and
wall-clock time. Kills the run when any limit is hit.
"""

import time
from dataclasses import dataclass


@dataclass
class BudgetStatus:
    llm_calls: int = 0
    tool_calls: int = 0
    elapsed_seconds: float = 0.0
    exhausted: bool = False
    exhausted_reason: str = ""


class Budget:
    def __init__(self, config: dict):
        self._max_llm = config.get("max_llm_calls", 25)
        self._max_tool = config.get("max_tool_calls", 50)
        self._max_wall = config.get("max_wall_seconds", 300)
        self._warn_pct = config.get("warn_at_percentage", 80) / 100.0
        self._llm_calls = 0
        self._tool_calls = 0
        self._start = time.time()
        self._warned: set[str] = set()

    def record_llm_call(self):
        self._llm_calls += 1
        self._check_warning("llm_calls", self._llm_calls, self._max_llm)

    def record_tool_call(self):
        self._tool_calls += 1
        self._check_warning("tool_calls", self._tool_calls, self._max_tool)

    def check(self) -> BudgetStatus:
        elapsed = time.time() - self._start
        status = BudgetStatus(
            llm_calls=self._llm_calls,
            tool_calls=self._tool_calls,
            elapsed_seconds=elapsed,
        )

        if self._llm_calls >= self._max_llm:
            status.exhausted = True
            status.exhausted_reason = f"LLM call limit reached ({self._max_llm})"
        elif self._tool_calls >= self._max_tool:
            status.exhausted = True
            status.exhausted_reason = f"Tool call limit reached ({self._max_tool})"
        elif elapsed >= self._max_wall:
            status.exhausted = True
            status.exhausted_reason = f"Wall-clock limit reached ({self._max_wall}s)"

        return status

    def _check_warning(self, name: str, current: int, limit: int):
        if name in self._warned:
            return
        if current >= limit * self._warn_pct:
            print(f"  [budget] Warning: {name} at {current}/{limit} ({int(current/limit*100)}%)")
            self._warned.add(name)

    def summary(self) -> dict:
        elapsed = time.time() - self._start
        return {
            "llm_calls": f"{self._llm_calls}/{self._max_llm}",
            "tool_calls": f"{self._tool_calls}/{self._max_tool}",
            "wall_seconds": f"{elapsed:.1f}/{self._max_wall}",
        }
