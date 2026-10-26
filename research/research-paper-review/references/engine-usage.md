# Engine Usage

This skill keeps the research-stack integration local while delegating the heavy lifting to the upstream `openaireview` package.

## Bootstrap

The engine is pinned to OpenAIReview 0.3.0 (release tag `v0.3.0`, commit `27740f8434cf18bd2d66d228291d9dcc3e046bc2`), which needs Python 3.12 or newer. Install it once:

```bash
python3 scripts/install_engine.py               # the pinned release commit from GitHub
python3 scripts/install_engine.py --source pypi # the same version from PyPI
```

Install optional OCR extras:

```bash
python3 scripts/install_engine.py --with mistral
python3 scripts/install_engine.py --with deepseek
```

Useful flags:

- `--source github|pypi`
- `--ref <branch-or-sha>` when using GitHub. Any ref other than the pinned commit or tag installs an unpinned engine; the installer warns and records the choice, and the wrappers then accept it.
- `--reinstall`
- `--venv <path>`

Default virtualenv, always outside the skill directory so packaging or updating the skill never carries or overwrites it:

- `OPENAIREVIEW_VENV` if set
- otherwise `$XDG_DATA_HOME/codex-skills/openaireview-0.3.0/`, or `~/.local/share/codex-skills/openaireview-0.3.0/` when `XDG_DATA_HOME` is unset

The installer writes `codex-skills-engine.json` into the virtualenv with the version, source, ref, and whether the install is pinned. Every wrapper checks it: an installed version that differs from the pin stops with the reinstall command, unless the marker records a deliberate unpinned install. An older install at `./.openaireview-venv` inside the skill is no longer used and can be deleted.

To move to a newer upstream release, change `ENGINE_VERSION`, `ENGINE_TAG`, and `ENGINE_COMMIT` in `scripts/_engine.py` together, reinstall, and rerun the skill's tests.

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

The upstream `install-skill` command is intentionally not mirrored here because it installs a Claude Code slash command under `~/.claude/commands/openaireview`. Codex should use this skill's own `SKILL.md`, references, and wrappers instead.

`scripts/save_viz_json.py` adds Codex-specific defaults on top of the packaged helper: it passes `openaireview__codex` / `OpenAIReview (Codex)` unless overridden and marks the saved viz method as `codex`. Pass `--derive-severity` only when you explicitly want to export OpenAIReview severity tiers derived from 1-5 `impact_rating` values.
