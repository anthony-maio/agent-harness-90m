"""
memory.py -- Simple file-based memory. The agent can read context from
memory.md and suggest new entries. Humans approve what gets remembered.
"""

import time
from pathlib import Path


class Memory:
    def __init__(self, file_path: str):
        self._path = Path(file_path)
        if not self._path.exists():
            self._path.write_text(
                "# Agent Memory\n\nEntries added after task runs.\n\n",
                encoding="utf-8",
            )

    def read(self) -> str:
        return self._path.read_text(encoding="utf-8")

    def suggest_entries(self, entries: list[str]) -> list[str]:
        """Return suggested entries for human review. Does not write automatically."""
        return entries

    def append(self, entry: str):
        timestamp = time.strftime("%Y-%m-%d %H:%M")
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(f"- [{timestamp}] {entry}\n")

    def append_if_approved(self, entries: list[str]) -> list[str]:
        approved = []
        for entry in entries:
            print(f"\n  Memory suggestion: {entry}")
            response = input("  Add to memory? [y/N] ").strip().lower()
            if response in ("y", "yes"):
                self.append(entry)
                approved.append(entry)
        return approved
