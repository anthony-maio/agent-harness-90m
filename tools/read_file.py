"""Read the contents of a file inside the workspace."""

from pathlib import Path

NAME = "read_file"
DESCRIPTION = "Read the contents of a file. Path must be relative to the workspace root."
PARAMETERS = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative path to the file to read",
        }
    },
    "required": ["path"],
}


def execute(path: str) -> str:
    target = Path("workspace") / path
    if not target.exists():
        return f"File not found: {path}"
    try:
        content = target.read_text(encoding="utf-8")
        if len(content) > 8000:
            return content[:8000] + f"\n\n[truncated -- file is {len(content)} chars]"
        return content
    except Exception as e:
        return f"Error reading {path}: {e}"
