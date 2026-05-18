# agent-harness-90m

A minimal agent harness in Python. Task intake, tool registry, policy gate, budget enforcement, structured logging, and post-run reports -- everything an LLM agent needs to run safely except the model itself.

Built as the companion repo for [Build Your First Agent Harness in 90 Minutes](https://anthonymaio.substack.com).

## Quickstart

```bash
git clone https://github.com/anthony-maio/agent-harness-90m.git
cd agent-harness-90m
pip install -e .
cp .env.example .env
# add your API key to .env (OpenAI, Anthropic, OpenRouter, etc.)
```

Run the example task:

```bash
python agent.py run tasks/example_research.md
```

Dry run (no LLM calls, just parse and validate):

```bash
python agent.py run tasks/example_research.md --dry-run
```

Auto-approve all policy prompts (for trusted tasks):

```bash
python agent.py run tasks/example_research.md --yes
```

## How it works

```
task.md -> runner -> LLM -> tool calls -> policy gate -> executor -> log
                      ^                        |
                      |                        v
                   memory <--------------- evaluator
```

1. You write a task in Markdown (what to do, which tools, what's blocked, when it's done)
2. The runner hands it to an LLM with tool definitions from the registry
3. Every tool call passes through the policy gate before execution
4. The budget tracker kills the run if limits are hit
5. Everything gets logged as structured JSONL
6. A Markdown report is generated when the run ends

## Project structure

```
agent-harness-90m/
  agent.py              # CLI entry point
  harness.yaml          # Main config (model, tools, policy, budget)
  harness/
    runner.py           # Main agent loop
    task.py             # Task file parser
    tools.py            # Tool registry and execution
    policy.py           # Policy gate and approval prompts
    budget.py           # Budget enforcement
    logger.py           # Structured JSONL logging
    memory.py           # File-based memory layer
    report.py           # Post-run report generation
  tools/
    read_file.py        # Read files from workspace
    write_file.py       # Write files to workspace
    list_files.py       # List workspace directory contents
    web_search.py       # Search stub (replace with real API)
    summarize.py        # LLM-based text summarization
  tasks/
    example_research.md # Example: research brief
    example_digest.md   # Example: weekly digest
  policies/
    default.yaml        # Default policy rules
  logs/                 # JSONL logs (gitignored)
  reports/              # Run reports (gitignored)
  memory.md             # Persistent memory file
```

## Writing tasks

Tasks are Markdown files with four sections:

```markdown
# Task
What the agent should do.

# Allowed tools
- tool_name_1
- tool_name_2

# Cannot do
- blocked_action_1

# Done means
- completion criterion 1
- completion criterion 2
```

See `tasks/example_research.md` for a working example.

## Adding tools

1. Create a Python file in `tools/` with `NAME`, `DESCRIPTION`, `PARAMETERS`, and `execute()`
2. Add the tool to `harness.yaml` under `tools:` with a risk level
3. The registry auto-discovers it on the next run

## Configuration

Everything lives in `harness.yaml`:

- **model** -- provider, model name, temperature, max tokens
- **budget** -- max LLM calls, tool calls, wall-clock seconds
- **tools** -- tool names, descriptions, risk levels
- **policy** -- approval requirements, blocked tools, workspace boundary
- **logging** -- log file paths
- **memory** -- memory file path

### Local models

For Ollama or other local providers, change the model config:

```yaml
model:
  provider: "ollama"
  name: "llama3.2"
```

No API key needed. The harness uses litellm, so any supported provider works.

## Dependencies

- [litellm](https://github.com/BerriAI/litellm) -- unified LLM API (supports OpenAI, Anthropic, Ollama, OpenRouter, Azure, and 100+ others)
- [pyyaml](https://pyyaml.org/) -- config parsing
- [python-dotenv](https://github.com/theskumar/python-dotenv) -- env file loading

## License

MIT
