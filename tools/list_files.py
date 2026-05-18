"""List files in a directory inside the workspace."""

from pathlib import Path

NAME = "list_files"
DESCRIPTION = "List files and directories at a given path inside the workspace."
PARAMETERS = {
    "type": "object",
    "properties": {
        "path": {
            "type": "string",
            "description": "Relative directory path to list (default: workspace root)",
            "default": ".",
        }
    },
    "required": [],
}


def execute(path: str = ".") -> str:
    target = Path("workspace") / path
    if not target.exists():
        return f"Directory not found: {path}"
    if not target.is_dir():
        return f"Not a directory: {path}"

    entries = []
    for item in sorted(target.iterdir()):
        prefix = "d" if item.is_dir() else "f"
        size = item.stat().st_size if item.is_file() else 0
        entries.append(f"  [{prefix}] {item.name}  ({size} bytes)" if size else f"  [{prefix}] {item.name}/")

    if not entries:
        return f"Directory is empty: {path}"
    return f"Contents of {path}/:\n" + "\n".join(entries)
