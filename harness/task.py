"""
task.py -- Parse a Markdown task file into a structured Task object.

Task files use H1 headers as section delimiters:

    # Task
    Find three recent papers on small-model reasoning.

    # Allowed tools
    - web_search
    - read_file
    - write_file

    # Cannot do
    - send_email
    - delete_file

    # Done means
    - brief.md exists in workspace/
    - every claim has a source URL
"""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Task:
    description: str
    allowed_tools: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    done_criteria: list[str] = field(default_factory=list)
    raw_text: str = ""
    source_path: str = ""


def parse_task(path: Path) -> Task:
    text = path.read_text(encoding="utf-8")
    sections: dict[str, str] = {}
    current_section = ""
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("# "):
            if current_section:
                sections[current_section] = "\n".join(current_lines).strip()
            current_section = line[2:].strip().lower()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section:
        sections[current_section] = "\n".join(current_lines).strip()

    def extract_list(section_text: str) -> list[str]:
        items = []
        for line in section_text.splitlines():
            line = line.strip()
            if line.startswith("- "):
                items.append(line[2:].strip())
        return items

    return Task(
        description=sections.get("task", ""),
        allowed_tools=extract_list(sections.get("allowed tools", "")),
        blocked_actions=extract_list(sections.get("cannot do", "")),
        done_criteria=extract_list(sections.get("done means", "")),
        raw_text=text,
        source_path=str(path),
    )
