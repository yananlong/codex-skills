# Engine Usage

This skill keeps the research-stack integration local while delegating the heavy lifting to the upstream `openaireview` package.

## Bootstrap

Install the engine once:

```bash
python3 scripts/install_engine.py
```

Install optional OCR extras:

```bash
python3 scripts/install_engine.py --with mistral
python3 scripts/install_engine.py --with deepseek
```

Useful flags:

- `--source github|pypi`
- `--ref <branch-or-sha>` when using GitHub
- `--reinstall`
- `--venv <path>`

Default virtualenv:

- `OPENAIREVIEW_VENV` if set
- otherwise `./.openaireview-venv` inside this skill directory

## Mirror CLI

The wrapper keeps the upstream CLI surface:

```bash
python3 scripts/run_openaireview.py review <paper-or-url> [flags]
python3 scripts/run_openaireview.py extract <paper> [flags]
python3 scripts/run_openaireview.py serve --results-dir ./review_results --port 8080
```

### `review` flags

- `--method zero_shot|local|progressive|progressive_full`
- `--model <provider/model>`
- `--provider openrouter|openai|anthropic|gemini|mistral`
- `--reasoning-effort none|low|medium|high`
- `--ocr mistral|deepseek|marker|pymupdf`
- `--max-pages <N>`
- `--max-tokens <N>`
- `--output-dir <dir>`
- `--name <slug>`

### `extract` flags

- `-o, --output <markdown-path>`
- `--ocr mistral|deepseek|marker|pymupdf`

### `serve` flags

- `--results-dir <dir>`
- `--port <port>`

## Environment variables

Set one or more provider keys before LLM review:

- `OPENROUTER_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GEMINI_API_KEY`
- `MISTRAL_API_KEY`

Optional overrides:

- `MODEL`
- `REVIEW_PROVIDER`
- `OPENAIREVIEW_VENV`

## Packaged deep-review helpers

These local wrappers call the upstream packaged skill scripts after installation:

- `python3 scripts/prepare_workspace.py ...`
- `python3 scripts/consolidate_comments.py ...`
- `python3 scripts/save_viz_json.py ...`

The upstream `install-skill` command is intentionally not mirrored here because this research skill already replaces that Claude-specific install surface.
