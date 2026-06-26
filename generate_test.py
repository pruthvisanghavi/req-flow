"""
generate_test.py
----------------
For each requirement:
  1. Generate test
  2. Traceability check — if it fails, regenerate (up to 3 attempts)
  3. Human approval — show the test and ask y/n before saving
"""

import os
import re
import sys
import requests
from pathlib import Path

OLLAMA_URL  = "http://ollama:11434/api/chat"
MODEL       = os.environ.get("OLLAMA_MODEL", "qwen3:8b")
MAX_RETRIES = 3

# Prepended to every generation call — never dropped on retries
FORMAT_RULE = (
    "IMPORTANT: Output ONLY a valid Python code block inside triple backticks. "
    "No prose, no headers, no explanation before or after the code block. "
    "Start with ```python and end with ```.\n\n"
)


# ── LLM ─────────────────────────────────────────────────────────

def ask(prompt: str) -> str:
    response = requests.post(OLLAMA_URL, json={
        "model":    MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream":   False,
        "options":  {"temperature": 0.1},
    }, timeout=300)
    response.raise_for_status()
    return response.json()["message"]["content"]


def extract_code(raw: str) -> str:
    """Pull out the first ```python ... ``` block. Fall back to stripping think tags."""
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL)
    block = re.search(r"```(?:python)?\s*\n(.*?)```", raw, flags=re.DOTALL | re.IGNORECASE)
    if block:
        return block.group(1).strip()
    return raw.strip()


# ── Loaders ──────────────────────────────────────────────────────

def load_requirements(path="requirements/requirements.txt"):
    reqs = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) != 3:
            print(f"⚠  Skipping malformed line: {line}")
            continue
        reqs.append(tuple(parts))
    return reqs


# ── Generation ───────────────────────────────────────────────────

def build_prompt(prompt_template, class_name, class_title, source_code, requirement, gaps=""):
    """Always includes FORMAT_RULE. Appends gap feedback when retrying."""
    base = FORMAT_RULE + prompt_template.format(
        requirement=requirement,
        source_code=source_code,
        class_name=class_name,
        class_title=class_title,
    )
    if gaps:
        base += (
            f"\n\nA previous attempt failed the traceability check. Gaps identified:\n{gaps}\n"
            "Fix these gaps. Output ONLY the corrected Python code block — no prose."
        )
    return base


def traceability_check(requirement, code):
    """Returns (passed: bool, verdict: str)."""
    prompt = (
        "You are reviewing a Python unit test against a simulation class. "
        "This is a unit test — NOT a hardware or integration test. "
        "Assume the class faithfully simulates the real behaviour.\n\n"
        f"Requirement: {requirement}\n\n"
        f"Test code:\n{code}\n\n"
        "Does this unit test verify the requirement against the class? "
        "Only flag gaps fixable in a unit test (missing assertions, wrong values, "
        "untested states, missing imports, syntax errors). "
        "Do NOT flag absence of real hardware or integration infrastructure. "
        "Start your answer with YES or NO, then explain in 2-3 sentences."
    )
    raw     = ask(prompt)
    verdict = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
    passed  = verdict.upper().startswith("YES")
    return passed, verdict


# ── Per-requirement pipeline ─────────────────────────────────────

def process(req_id, class_name, description, prompt_template):
    src_path = Path(f"src/{class_name}.py")
    if not src_path.exists():
        print(f"  ⚠  {src_path} not found — skipping {req_id}")
        return

    source_code = src_path.read_text()
    class_title = class_name.capitalize()
    gaps        = ""
    code        = ""

    # ── Step 1 & 2: Generate + traceability loop ─────────────
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n  ⏳ Generating test (attempt {attempt}/{MAX_RETRIES})...")
        prompt = build_prompt(prompt_template, class_name, class_title,
                              source_code, description, gaps)
        raw  = ask(prompt)
        code = extract_code(raw)

        print(f"\n  {'─'*54}")
        print(f"  GENERATED TEST — {req_id}")
        print(f"  {'─'*54}")
        print(code)

        print(f"\n  ⏳ Running traceability check...")
        passed, verdict = traceability_check(description, code)

        print(f"\n  {'─'*54}")
        print(f"  TRACEABILITY — {req_id} — {'✅ PASS' if passed else '❌ FAIL'}")
        print(f"  {'─'*54}")
        print(verdict)

        if passed:
            break

        if attempt < MAX_RETRIES:
            print(f"\n  ⚠  Traceability failed — regenerating with gaps as feedback...")
            gaps = verdict
        else:
            print(f"\n  ⚠  Max retries reached. Proceeding with best attempt.")

    # ── Step 3: Human approval (skipped in CI) ──────────────
    print(f"\n  {'─'*54}")
    if os.environ.get("CI", "false").lower() == "true":
        print(f"  ℹ  CI mode — auto-approving {req_id}")
        answer = "y"
    else:
        sys.stdout.write(f"  Save test for {req_id}? [y/n]: ")
        sys.stdout.flush()
        answer = sys.stdin.readline().strip().lower()

    if answer != "y":
        print(f"  ❌ Rejected — skipping {req_id}")
        return

    out_path = Path(f"tests/test_{class_name}.py")
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        f"# Auto-generated by req-flow\n"
        f"# {req_id}: {description}\n\n"
        f"{code}\n"
    )
    print(f"  ✅ Saved → {out_path}")


# ── Main ─────────────────────────────────────────────────────────

def main():
    prompt_template = open("prompt.txt").read().strip()
    requirements    = load_requirements()

    print("=" * 60)
    print(f"req-flow — {len(requirements)} requirement(s) found")
    print("=" * 60)

    for req_id, class_name, description in requirements:
        print(f"\n{'='*60}")
        print(f"{req_id} | {class_name}")
        print(f"{description}")
        print(f"{'='*60}")
        process(req_id, class_name, description, prompt_template)

    print(f"\n{'='*60}")
    print("Done. Run: pytest tests/ -v")
    print("=" * 60)


if __name__ == "__main__":
    main()