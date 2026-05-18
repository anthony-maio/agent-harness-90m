"""
logger.py -- Structured JSONL logging for tool calls and LLM calls.
Every action the agent takes gets a line in the log. No exceptions.
"""

import json
import time
from pathlib import Path


class HarnessLogger:
    def __init__(self, tool_log_path: str, llm_log_path: str, task_id: str):
        self._tool_path = Path(tool_log_path)
        self._llm_path = Path(llm_log_path)
        self._task_id = task_id
        self._tool_path.parent.mkdir(parents=True, exist_ok=True)
        self._llm_path.parent.mkdir(parents=True, exist_ok=True)

    def log_tool_call(
        self,
        tool: str,
        arguments: dict,
        result_summary: str,
        approved: bool = True,
        error: str | None = None,
    ):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "task_id": self._task_id,
            "type": "tool_call",
            "tool": tool,
            "arguments": arguments,
            "result_summary": result_summary[:500],
            "approved": approved,
            "error": error,
        }
        self._append(self._tool_path, entry)

    def log_llm_call(
        self,
        step: int,
        prompt_summary: str,
        response_summary: str,
        tool_calls_requested: list[dict] | None = None,
    ):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "task_id": self._task_id,
            "type": "llm_call",
            "step": step,
            "prompt_summary": prompt_summary[:300],
            "response_summary": response_summary[:500],
            "tool_calls_requested": tool_calls_requested or [],
        }
        self._append(self._llm_path, entry)

    def log_event(self, event: str, details: str = ""):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "task_id": self._task_id,
            "type": "event",
            "event": event,
            "details": details,
        }
        self._append(self._tool_path, entry)

    def _append(self, path: Path, entry: dict):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
