"""Capture immutable PaperSignal engine source/config fingerprints.

This is a source-fingerprint tool, NOT a full-pipeline performance benchmark.
It deliberately reads only non-secret model-name environment variables and
never reads, hashes, prints, or stores provider/API credentials.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import platform
import re
from typing import Any


SAFE_ENV_DEFAULTS = {
    "AI_PROVIDER": "gemini",
    "GEMINI_MODEL": "gemini-3.5-flash-lite",
    "GEMINI_FALLBACK_MODEL": "gemini-3.6-flash",
    "OPENAI_MODEL": "gpt-5.6-terra",
}
EXTRACTION_CONSTANTS = (
    "MAX_BYTES", "MAX_PAGES", "MAX_PAGES_TO_SCAN",
    "MAX_PAGE_CHARS", "MAX_LLM_CHARS",
)
SCHEMA_START = "EVIDENCE_SCHEMA ="
SCHEMA_END = "\n\n_EVIDENCE_TRANSLATION"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _function_source(source: str, name: str) -> str:
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            segment = ast.get_source_segment(source, node)
            if segment:
                return segment
    raise ValueError(f"Could not locate function {name}")


def _module_constants(source: str) -> dict[str, Any]:
    tree = ast.parse(source)
    constants: dict[str, Any] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            try:
                constants[name] = ast.literal_eval(node.value)
            except (ValueError, TypeError):
                continue
    return constants


def _env_default(source: str, env_name: str, fallback: str) -> str:
    """Read the source default and a safe model-name override only."""
    tree = ast.parse(source)
    source_default = fallback
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "getenv" or len(node.args) < 1:
            continue
        try:
            key = ast.literal_eval(node.args[0])
            default = ast.literal_eval(node.args[1]) if len(node.args) > 1 else fallback
        except (ValueError, TypeError):
            continue
        if key == env_name and isinstance(default, str):
            source_default = default
            break
    # Only the four allowlisted, non-secret settings are ever read.
    value = os.environ.get(env_name, source_default)
    return value if isinstance(value, str) and value.strip() else source_default


def capture(root: Path, *, production_commit: str) -> dict[str, Any]:
    root = root.resolve()
    paths = {
        "main": root / "backend/app/main.py",
        "worker": root / "backend/app/worker.py",
        "requirements": root / "backend/requirements.txt",
        "dockerfile": root / "backend/Dockerfile",
    }
    for label, path in paths.items():
        if not path.is_file():
            raise FileNotFoundError(f"{label} source missing: {path}")

    sources = {label: path.read_text(encoding="utf-8") for label, path in paths.items()}
    main = sources["main"]
    constants = _module_constants(main)

    extraction_function = _function_source(main, "extract_pages")
    prompt_function = _function_source(main, "build_analysis_prompt")
    gemini_function = _function_source(main, "_generate_gemini")
    if SCHEMA_START not in main or SCHEMA_END not in main:
        raise ValueError("Could not locate analysis schema block")
    schema_block = main[main.index(SCHEMA_START):main.index(SCHEMA_END)]

    extraction_config = {
        name: constants.get(name) for name in EXTRACTION_CONSTANTS
    }
    extraction_config["pymupdf_requirement"] = next(
        (line.strip() for line in sources["requirements"].splitlines()
         if line.strip().lower().startswith("pymupdf==")),
        None,
    )
    extraction_config["extract_pages_source_sha256"] = sha256_text(extraction_function)

    provider = _env_default(main, "AI_PROVIDER", SAFE_ENV_DEFAULTS["AI_PROVIDER"]).lower()
    model_config = {
        "provider": provider,
        "gemini_primary_model": _env_default(main, "GEMINI_MODEL", SAFE_ENV_DEFAULTS["GEMINI_MODEL"]),
        "gemini_fallback_model": _env_default(main, "GEMINI_FALLBACK_MODEL", SAFE_ENV_DEFAULTS["GEMINI_FALLBACK_MODEL"]),
        "openai_model": _env_default(main, "OPENAI_MODEL", SAFE_ENV_DEFAULTS["OPENAI_MODEL"]),
        "analysis_version": constants.get("ANALYSIS_VERSION"),
        "secret_values_included": False,
        "secret_environment_variables_read": [],
        "source_defaults_only_unless_safe_override_present": True,
    }
    return {
        "record_type": "SOURCE_FINGERPRINT_ONLY_NOT_FULL_PIPELINE_BASELINE",
        "production_commit": production_commit,
        "runtime": {
            "python": platform.python_version(),
            "pymupdf_runtime": _pymupdf_version(),
            "platform": platform.platform(),
        },
        "files": {
            label: {"path": str(path.relative_to(root)), "sha256": sha256_text(sources[label])}
            for label, path in paths.items()
        },
        "segments": {
            "prompt_sha256": sha256_text(prompt_function),
            "schema_sha256": sha256_text(schema_block),
            "extraction_sha256": sha256_text(json.dumps(extraction_config, sort_keys=True, separators=(",", ":"))),
            "gemini_transport_sha256": sha256_text(gemini_function),
        },
        "model_config": model_config,
        "extraction_config": extraction_config,
        "warning": (
            "Source/config fingerprints do not measure Gemini latency, provider billable cost, "
            "peak RSS, factual accuracy or end-to-end reliability. Do not mark Q0/Q1/Q2 PASS."
        ),
    }


def _pymupdf_version() -> str | None:
    try:
        import fitz
        return str(fitz.VersionBind)
    except Exception:
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Capture non-secret PaperSignal engine fingerprints")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--production-commit", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    report = capture(args.root, production_commit=args.production_commit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "record_type": report["record_type"],
        "production_commit": report["production_commit"],
        "files": report["files"],
        "segments": report["segments"],
        "secret_values_included": False,
        "out": str(args.out),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
