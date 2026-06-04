#!/usr/bin/env python3
"""Mirror the upstream openaireview CLI from the local skill.

Provider-backed LLM review is opt-in so ChatGPT/Codex runs can use the active
chat model directly instead of failing on missing external API keys.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _engine import DEFAULT_VENV, run_cli


PROVIDER_KEY_ENVS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "GEMINI_API_KEY",
    "MISTRAL_API_KEY",
)

TRUE_VALUES = {"1", "true", "yes", "on"}


def _truthy_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in TRUE_VALUES


def _has_provider_key() -> bool:
    return any(os.environ.get(name) for name in PROVIDER_KEY_ENVS)


def _is_review_command(remainder: list[str]) -> bool:
    return bool(remainder) and remainder[0] == "review"


def _print_native_review_guidance() -> None:
    print(
        "No external OpenAIReview LLM review was run.\n"
        "\n"
        "Inside ChatGPT/Codex, use the research-paper-review ChatGPT-native "
        "path instead: prepare or extract the paper workspace, then have the "
        "active chat model read full_text.md, write summary.md, generate the "
        "comments/*.json pass outputs, consolidate findings, and write "
        "final_issues.json, review_summary.json, and overall_assessment.txt.\n"
        "\n"
        "To force the upstream provider-backed review CLI outside ChatGPT, pass "
        "--external-llm or set OPENAIREVIEW_USE_EXTERNAL_LLM=1, and configure "
        "one supported provider key: OPENROUTER_API_KEY, OPENAI_API_KEY, "
        "ANTHROPIC_API_KEY, GEMINI_API_KEY, or MISTRAL_API_KEY.",
        file=sys.stderr,
    )


def parse_args() -> tuple[argparse.Namespace, list[str]]:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--venv",
        type=Path,
        default=DEFAULT_VENV,
        help="Virtualenv path created by install_engine.py.",
    )
    parser.add_argument(
        "--external-llm",
        action="store_true",
        help=(
            "Opt in to the upstream provider-backed `review` command. "
            "Without this flag, review should be performed by the active "
            "ChatGPT/Codex model when running inside ChatGPT."
        ),
    )
    args, remainder = parser.parse_known_args()
    if remainder and remainder[0] == "--":
        remainder = remainder[1:]
    if not remainder:
        parser.error("Pass an openaireview subcommand such as review, extract, or serve.")
    return args, remainder


def main() -> int:
    args, remainder = parse_args()

    if _is_review_command(remainder):
        external_llm_requested = args.external_llm or _truthy_env("OPENAIREVIEW_USE_EXTERNAL_LLM")
        if not external_llm_requested:
            _print_native_review_guidance()
            return 2
        if not _has_provider_key():
            print(
                "External OpenAIReview LLM review was requested, but no supported "
                "provider API key is configured.",
                file=sys.stderr,
            )
            return 2

    return run_cli(args.venv, remainder)


if __name__ == "__main__":
    raise SystemExit(main())
