"""Write content to a file inside the workspace."""

from pathlib import Path

NAME = "write_file"
DESCRIPTION = "Write content to a file. Path must be relative to the workspace root. Creates parent directories if needed."
PARAMETERS = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative path for the output file",
        },
        "content": {
            "type": "string",
            "description": "Content to write to the file",
        },
    },
    "required": ["path", "content"],
}


def execute(path: str, content: str) -> str:
    target = Path("workspace") / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content)} chars to {path}"
