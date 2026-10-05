# Vigil

A minimal CLI tool for observing agents and workflows running in your tmux panes. Vigil doesn't start or control anything — it just watches.

```
AGENT            STATUS       STARTED       DURATION
──────────────────────────────────────────────────────
coding-agent     ● RUNNING    10:32 AM      18m
research-agent   ✓ FINISHED   09:15 AM      42m
data-agent       ✗ FAILED     08:47 AM      7m
```

## Installation

```bash
pipx install vigil-tracker   # or: pip install vigil-tracker
```

This installs the `vigil` command.

For development:

```bash
git clone https://github.com/Yared-betsega/vigil-tracker.git && cd vigil-tracker
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Usage

### Attach to a tmux pane

```bash
vigil attach <name> --pane <pane-id>
```

The pane ID is whatever tmux uses — `0`, `mywindow:0`, `mywindow:0.1`, etc.

```bash
vigil attach claude-code  --pane 0
vigil attach api-agent    --pane work:1   --task "Refactor auth"
vigil attach model-train  --pane gpu:0    --workspace ~/ml
```

Vigil finds the process in that pane automatically. No need to look up PIDs or tty paths.

---

### Check status

```bash
# All agents
vigil status

# One agent — shows status + AI summary
vigil status claude-code

# Include raw pane output lines
vigil status claude-code --output
```

```
╭─── claude-code ──────────────────────────────────────────╮
│ Status:          ● RUNNING                                │
│ Started:         10:32 AM                                 │
│ Duration:        18m 24s                                  │
│ Task:            Refactor auth                            │
│ Pane:            work:1                                   │
│                                                           │
│ What's happening: Running the test suite, 42/45 passing. │
╰───────────────────────────────────────────────────────────╯
```

The **What's happening** line is a one-sentence AI summary of what the process is currently doing, generated from the last 20 lines of pane output. Pass `--output` (`-o`) to also show the raw pane lines.

---

### Live dashboard

```bash
# All agents — live status table
vigil watch

# One agent — live detail panel, refreshes every second
vigil watch <name>

# Include raw pane output lines in the live view
vigil watch <name> --output
```

Press `Ctrl+C` to exit.

---

### Mark done manually

```bash
vigil done <name>           # FINISHED
vigil done <name> --failed  # FAILED
```

Use this when a process finished but Vigil didn't catch the exit (e.g. you detached from tmux).

---

### Remove an agent

```bash
vigil rm <name>
```

---

## AI Summarization

Vigil uses a local LLM to summarize what each process is doing. It tries **Ollama first**, then falls back to the **Anthropic API** if available.

### Ollama — local (no API key needed)

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3.2
```

Ollama runs locally and starts automatically. No API key or account needed.

### Ollama — cloud (no local GPU needed)

Sign up at [ollama.com](https://ollama.com), generate an API key in account settings, then:

```bash
export OLLAMA_API_KEY=your_key_here
```

When `OLLAMA_API_KEY` is set, Vigil automatically uses Ollama's cloud API instead of the local instance. Same models, no local Ollama installation required.

To use a different model (default: `llama3.2`), set `VIGIL_OLLAMA_MODEL`:

```bash
export VIGIL_OLLAMA_MODEL=qwen2.5:3b
```

### Setting API keys

Create `~/.vigil/.env` and add your keys there — Vigil loads it automatically on startup:

```bash
OLLAMA_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
VIGIL_OLLAMA_MODEL=llama3.2
```

You only need the keys for the services you want to use.

### Anthropic API (fallback)

Install vigil with the Anthropic extra, then set `ANTHROPIC_API_KEY`:

```bash
pipx install 'vigil-tracker[anthropic]'   # or: pip install 'vigil-tracker[anthropic]'
```

Vigil uses `claude-haiku-4-5`, which costs a fraction of a cent per summary call.

If neither is available, Vigil still works — it just shows the raw pane output without the summary line.

---

## Other ways to attach

If you're not in tmux, you can still attach by tty or PID:

```bash
vigil attach my-agent --tty pts/3   # run `tty` in the target terminal
vigil attach my-agent 18423          # raw PID
```

These work the same but won't show pane output in `vigil status`.
