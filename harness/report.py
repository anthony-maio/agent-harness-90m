"""
report.py -- Generate a post-run report in Markdown.
"""

import time
from pathlib import Path


def generate_report(
    task_description: str,
    task_source: str,
    tools_used: list[dict],
    files_changed: list[str],
    approvals: list[dict],
    failures: list[dict],
    budget_summary: dict,
    memory_suggestions: list[str],
    final_answer: str,
    output_dir: str,
    task_id: str,
) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    report_file = output_path / f"run_{task_id}.md"

    tool_lines = ""
    for t in tools_used:
        tool_lines += f"- `{t['tool']}` -- called {t['count']} time(s)\n"

    file_lines = ""
    for f in files_changed:
        file_lines += f"- `{f}`\n"

    approval_lines = ""
    for a in approvals:
        status = "approved" if a["approved"] else "denied"
        approval_lines += f"- `{a['tool']}` -- {status}\n"

    failure_lines = ""
    for f in failures:
        failure_lines += f"- Step {f['step']}: {f['error']}\n"

    memory_lines = ""
    for m in memory_suggestions:
        memory_lines += f"- {m}\n"

    report = f"""# Run Report: {task_id}

**Task:** {task_description[:200]}
**Source:** {task_source}
**Completed:** {time.strftime("%Y-%m-%d %H:%M:%S")}

## Budget

| Metric | Used |
|--------|------|
| LLM calls | {budget_summary.get('llm_calls', 'N/A')} |
| Tool calls | {budget_summary.get('tool_calls', 'N/A')} |
| Wall time | {budget_summary.get('wall_seconds', 'N/A')} |

## Tools used

{tool_lines or "None"}

## Files changed

{file_lines or "None"}

## Approvals requested

{approval_lines or "None"}

## Failures

{failure_lines or "None"}

## Memory suggestions

{memory_lines or "None"}

## Final output

{final_answer}
"""

    report_file.write_text(report, encoding="utf-8")
    return report_file
