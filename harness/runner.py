"""
runner.py -- The main agent loop. Reads the task, calls the LLM with
tool definitions, enforces policy and budget on every step, logs
everything, and generates a report at the end.
"""

import json
import time
from collections import Counter
from pathlib import Path

import yaml
from litellm import completion

from harness.budget import Budget
from harness.logger import HarnessLogger
from harness.memory import Memory
from harness.policy import PolicyGate
from harness.report import generate_report
from harness.task import Task, parse_task
from harness.tools import ToolRegistry

SYSTEM_PROMPT = """You are a task-execution agent running inside a harness.
You have access to specific tools listed below. Use them to complete the task.

Rules:
- Only use the tools provided. Do not hallucinate tool names.
- Work step by step. Call one or two tools per turn, then assess progress.
- When the task is complete, respond with a final answer (no tool calls).
- If you cannot complete the task, explain what's blocking you.
- Be concise. Tool results are logged automatically.

Available memory context:
{memory}
"""


def run_task(
    task_path: Path,
    config_path: Path,
    dry_run: bool = False,
    auto_approve: bool = False,
):
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    task = parse_task(task_path)
    task_id = time.strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Agent Harness -- Run {task_id}")
    print(f"{'='*60}")
    print(f"  Task:   {task.description[:80]}...")
    print(f"  Source: {task.source_path}")
    print(f"  Tools:  {', '.join(task.allowed_tools) or 'all configured'}")
    print(f"{'='*60}\n")

    registry = ToolRegistry(config.get("tools", {}))
    policy = PolicyGate(
        config.get("policy", {}),
        task.blocked_actions,
        auto_approve=auto_approve,
    )
    budget = Budget(config.get("budget", {}))
    memory = Memory(config.get("memory", {}).get("file", "memory.md"))
    logger = HarnessLogger(
        config["logging"]["tool_calls"],
        config["logging"]["llm_calls"],
        task_id,
    )

    if dry_run:
        _print_dry_run(task, registry, config)
        return

    Path(config.get("policy", {}).get("workspace_root", "./workspace")).mkdir(
        parents=True, exist_ok=True
    )

    tool_defs = _build_tool_definitions(registry, task.allowed_tools)
    memory_context = memory.read()

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT.format(memory=memory_context[:2000]),
        },
        {"role": "user", "content": task.raw_text},
    ]

    tools_used_counter: Counter = Counter()
    files_changed: list[str] = []
    approvals: list[dict] = []
    failures: list[dict] = []
    step = 0

    logger.log_event("run_started", f"Task: {task.source_path}")

    while True:
        status = budget.check()
        if status.exhausted:
            print(f"\n  [budget] {status.exhausted_reason} -- stopping.")
            logger.log_event("budget_exhausted", status.exhausted_reason)
            break

        step += 1
        print(f"  Step {step}...")

        try:
            response = completion(
                model=f"{config['model']['provider']}/{config['model']['name']}",
                messages=messages,
                tools=tool_defs if tool_defs else None,
                temperature=config["model"].get("temperature", 0.2),
                max_tokens=config["model"].get("max_tokens", 4096),
            )
        except Exception as e:
            print(f"  [error] LLM call failed: {e}")
            failures.append({"step": step, "error": str(e)})
            logger.log_event("llm_error", str(e))
            break

        budget.record_llm_call()
        choice = response.choices[0]
        message = choice.message

        logger.log_llm_call(
            step=step,
            prompt_summary=messages[-1].get("content", "")[:200] if messages else "",
            response_summary=(message.content or "")[:300],
            tool_calls_requested=[
                {"name": tc.function.name, "args": tc.function.arguments}
                for tc in (message.tool_calls or [])
            ],
        )

        if not message.tool_calls:
            print(f"  [done] Agent finished at step {step}.")
            final_answer = message.content or ""
            print(f"\n  Final answer:\n  {final_answer[:500]}\n")
            break

        messages.append(message.model_dump())

        for tc in message.tool_calls:
            tool_name = tc.function.name
            try:
                tool_args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                tool_args = {}

            decision = policy.check(tool_name, tool_args)

            if not decision.allowed:
                result = f"BLOCKED: {decision.reason}"
                print(f"    {tool_name} -> BLOCKED ({decision.reason})")
                logger.log_tool_call(tool_name, tool_args, result, approved=False)
                approvals.append({"tool": tool_name, "approved": False})
            elif decision.needs_approval:
                approved = policy.prompt_approval(tool_name, tool_args)
                approvals.append({"tool": tool_name, "approved": approved})
                if not approved:
                    result = "DENIED: User denied approval"
                    print(f"    {tool_name} -> DENIED by user")
                    logger.log_tool_call(tool_name, tool_args, result, approved=False)
                else:
                    result = registry.execute(tool_name, tool_args)
                    print(f"    {tool_name} -> OK (approved)")
                    budget.record_tool_call()
                    tools_used_counter[tool_name] += 1
                    logger.log_tool_call(tool_name, tool_args, result)
                    if tool_name == "write_file":
                        files_changed.append(tool_args.get("path", "unknown"))
            else:
                result = registry.execute(tool_name, tool_args)
                print(f"    {tool_name} -> OK")
                budget.record_tool_call()
                tools_used_counter[tool_name] += 1
                logger.log_tool_call(tool_name, tool_args, result)
                if tool_name == "write_file":
                    files_changed.append(tool_args.get("path", "unknown"))

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result[:4000],
                }
            )
    else:
        final_answer = "Run ended without a final answer."

    memory_suggestions = _extract_memory_suggestions(messages)

    report_path = generate_report(
        task_description=task.description,
        task_source=task.source_path,
        tools_used=[
            {"tool": t, "count": c} for t, c in tools_used_counter.items()
        ],
        files_changed=files_changed,
        approvals=approvals,
        failures=failures,
        budget_summary=budget.summary(),
        memory_suggestions=memory_suggestions,
        final_answer=final_answer if "final_answer" in dir() else "Budget exhausted before completion.",
        output_dir=config.get("reports", {}).get("output_dir", "reports"),
        task_id=task_id,
    )

    print(f"\n{'='*60}")
    print(f"  Run complete. Report: {report_path}")
    print(f"  Budget: {budget.summary()}")
    print(f"{'='*60}\n")

    if memory_suggestions:
        print("  Memory update suggestions:")
        memory.append_if_approved(memory_suggestions)

    logger.log_event("run_completed", f"Report: {report_path}")


def _build_tool_definitions(registry: ToolRegistry, allowed: list[str]) -> list[dict]:
    defs = []
    for tool_info in registry.list_tools():
        if allowed and tool_info["name"] not in allowed:
            continue
        defs.append(
            {
                "type": "function",
                "function": {
                    "name": tool_info["name"],
                    "description": tool_info["description"],
                    "parameters": tool_info["parameters"],
                },
            }
        )
    return defs


def _extract_memory_suggestions(messages: list[dict]) -> list[str]:
    for msg in reversed(messages):
        content = msg.get("content", "")
        if isinstance(content, str) and "MEMORY:" in content:
            suggestions = []
            for line in content.splitlines():
                if line.strip().startswith("MEMORY:"):
                    suggestions.append(line.strip()[7:].strip())
            return suggestions
    return []


def _print_dry_run(task: Task, registry: ToolRegistry, config: dict):
    print("\n  [dry-run] Task parsed successfully.\n")
    print(f"  Description: {task.description[:200]}")
    print(f"  Allowed tools: {task.allowed_tools or 'all configured'}")
    print(f"  Blocked actions: {task.blocked_actions}")
    print(f"  Done criteria: {task.done_criteria}")
    print(f"\n  Available tools in registry: {registry.available_names()}")
    print(f"  Model: {config['model']['provider']}/{config['model']['name']}")
    print(f"  Budget: {config.get('budget', {})}")
    print(f"\n  [dry-run] No LLM calls made.\n")
