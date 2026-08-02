"""Master backend test suite runner.

Run the default unit/eval harness suite:
    python3 run_test_suite.py

Run the paid/live API-backed suites too:
    python3 run_test_suite.py --include-live
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parent
REPO_ROOT = BACKEND_ROOT.parent
PLACEHOLDER_VALUES = {"", "replace_me", "replace-me", "your_token_here", "paste_token_here"}
PYTEST_MODULE = "pytest"
INSTALL_HELP = (
    f"Install test dependencies from repo root ({REPO_ROOT}) with: "
    f"{Path(sys.executable).name} -m pip install -r requirements.eval.txt"
)


def read_env_files() -> dict[str, str]:
    values: dict[str, str] = {}
    for path in (BACKEND_ROOT.parent / ".env", BACKEND_ROOT / ".env"):
        if not path.exists():
            continue
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def has_real_env_value(env: dict[str, str], key: str) -> bool:
    value = env.get(key, "").strip()
    return bool(value) and value.lower() not in PLACEHOLDER_VALUES


@dataclass
class Suite:
    name: str
    area: str
    args: list[str]
    env: dict[str, str] = field(default_factory=dict)
    required_env: tuple[str, ...] = ()
    required_modules: tuple[str, ...] = ()


@dataclass
class SuiteResult:
    name: str
    status: str
    duration_seconds: float
    details: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run BluHorizon backend tests grouped by area."
    )
    parser.add_argument(
        "--include-live",
        action="store_true",
        help="Include tests that call Claude and/or require Postgres.",
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first failing suite.",
    )
    return parser.parse_args()


def banner(suite: Suite) -> None:
    command = " ".join([Path(sys.executable).name, *suite.args])
    print("\n" + "=" * 88)
    print(f"AREA: {suite.area}")
    print(f"SUITE: {suite.name}")
    print(f"COMMAND: {command}")
    print("=" * 88, flush=True)


def suite_env(suite: Suite) -> dict[str, str]:
    env = read_env_files()
    env.update(os.environ)
    env.setdefault("PYTHONPATH", str(BACKEND_ROOT))

    # Defaults keep local unit tests from requiring real secrets. Live suites
    # still require ANTHROPIC_API_KEY and/or DATABASE_URL explicitly.
    env.setdefault("TAVILY_API_KEY", "unit-test-placeholder")
    env.setdefault("SECRET_KEY", "unit-test-secret")

    if "ANTHROPIC_API_KEY" not in suite.required_env:
        env.setdefault("ANTHROPIC_API_KEY", "unit-test-placeholder")
    if "DATABASE_URL" not in suite.required_env:
        env.setdefault(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/bluhorizon",
        )

    env.update(suite.env)
    return env


def run_suite(suite: Suite) -> SuiteResult:
    env = suite_env(suite)
    missing = [key for key in suite.required_env if not has_real_env_value(env, key)]
    missing_modules = [
        module
        for module in suite.required_modules
        if importlib.util.find_spec(module) is None
    ]
    banner(suite)

    if missing:
        details = "missing required env: " + ", ".join(missing)
        print(f"FAIL: {details}", flush=True)
        return SuiteResult(suite.name, "FAIL", 0.0, details)

    if missing_modules:
        details = "missing Python modules: " + ", ".join(missing_modules)
        print(f"FAIL: {details}", flush=True)
        print(INSTALL_HELP)
        return SuiteResult(suite.name, "FAIL", 0.0, details)

    start = time.monotonic()
    completed = subprocess.run(
        [sys.executable, *suite.args],
        cwd=BACKEND_ROOT,
        env=env,
        check=False,
    )
    duration = time.monotonic() - start
    status = "PASS" if completed.returncode == 0 else "FAIL"
    print(f"\n{status}: {suite.name} ({duration:.2f}s)", flush=True)
    return SuiteResult(suite.name, status, duration)


def default_suites() -> list[Suite]:
    return [
        Suite(
            name="Service Unit Tests",
            area=(
                "config, embeddings, legacy SQLite/FAISS stores, "
                "vector store orchestration, mocked RAG pipeline"
            ),
            args=["-m", "pytest", "tests/services_unit_test.py", "-v"],
            required_modules=(
                PYTEST_MODULE,
                "anthropic",
                "numpy",
                "pgvector",
                "psycopg2",
                "pydantic_settings",
                "sentence_transformers",
                "tiktoken",
            ),
        ),
        Suite(
            name="RAG Eval Harness And Visible Metrics",
            area=(
                "eval dataset validation, deterministic RAG scoring, "
                "citation/refusal/injection gates"
            ),
            args=[
                "-m",
                "pytest",
                "tests/rag_eval_test.py",
                "-v",
                "-s",
                "-m",
                "not llm_eval",
            ],
            env={"SHOW_RAG_METRICS": "1"},
            required_modules=(PYTEST_MODULE,),
        ),
    ]


def live_suites() -> list[Suite]:
    return [
        Suite(
            name="Claude Client Live Tests",
            area="direct Claude client calls",
            args=["-m", "pytest", "tests/services_unit_test.py::TestClaudeClient", "-v"],
            env={"RUN_LLM_EVALS": "1"},
            required_env=("ANTHROPIC_API_KEY",),
            required_modules=(PYTEST_MODULE, "anthropic", "pydantic_settings"),
        ),
        Suite(
            name="Live RAG Hyde Vs No-Hyde Quality Eval",
            area=(
                "Postgres retrieval, HyDE vs raw-question retrieval, "
                "answer accuracy, speed metrics, LLM judge"
            ),
            args=[
                "-m",
                "pytest",
                "tests/rag_eval_test.py",
                "-v",
                "-s",
                "-m",
                "llm_eval",
            ],
            env={"RUN_LLM_EVALS": "1", "SHOW_RAG_METRICS": "1"},
            required_env=("ANTHROPIC_API_KEY", "DATABASE_URL"),
            required_modules=(
                PYTEST_MODULE,
                "anthropic",
                "numpy",
                "psycopg2",
                "pgvector",
                "passlib",
                "sentence_transformers",
                "pydantic_settings",
                "tiktoken",
            ),
        ),
    ]


def print_summary(results: list[SuiteResult]) -> None:
    print("\n" + "=" * 88)
    print("SUITE SUMMARY")
    print("=" * 88)
    for result in results:
        detail = f" - {result.details}" if result.details else ""
        print(
            f"{result.status:4}  {result.duration_seconds:7.2f}s  "
            f"{result.name}{detail}"
        )


def main() -> int:
    args = parse_args()
    include_live = args.include_live or os.getenv("RUN_LLM_EVALS") == "1"

    suites = default_suites()
    if include_live:
        suites.extend(live_suites())

    results: list[SuiteResult] = []
    for suite in suites:
        result = run_suite(suite)
        results.append(result)
        if args.fail_fast and result.status == "FAIL":
            break

    if not include_live:
        results.extend(
            [
                SuiteResult(
                    "Claude Client Live Tests",
                    "SKIP",
                    0.0,
                    "pass --include-live or set RUN_LLM_EVALS=1",
                ),
                SuiteResult(
                    "Live RAG Hyde Vs No-Hyde Quality Eval",
                    "SKIP",
                    0.0,
                    "pass --include-live or set RUN_LLM_EVALS=1",
                ),
            ]
        )

    print_summary(results)
    return 1 if any(result.status == "FAIL" for result in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
