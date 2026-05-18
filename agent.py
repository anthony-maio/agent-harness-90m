"""
agent.py -- CLI entry point for the agent harness.

Usage:
    python agent.py run tasks/example_research.md
    python agent.py run tasks/example_research.md --config harness.yaml
    python agent.py run tasks/example_research.md --dry-run
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from harness.runner import run_task


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Run a task inside the agent harness."
    )
    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", help="Execute a task file")
    run_parser.add_argument("task", type=Path, help="Path to a task .md file")
    run_parser.add_argument(
        "--config",
        type=Path,
        default=Path("harness.yaml"),
        help="Path to harness config (default: harness.yaml)",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse the task and show what would happen, but don't execute",
    )
    run_parser.add_argument(
        "--yes",
        action="store_true",
        help="Auto-approve all policy prompts (use with caution)",
    )

    args = parser.parse_args()

    if args.command != "run":
        parser.print_help()
        sys.exit(1)

    if not args.task.exists():
        print(f"Task file not found: {args.task}")
        sys.exit(1)

    if not args.config.exists():
        print(f"Config file not found: {args.config}")
        sys.exit(1)

    run_task(
        task_path=args.task,
        config_path=args.config,
        dry_run=args.dry_run,
        auto_approve=args.yes,
    )


if __name__ == "__main__":
    main()
