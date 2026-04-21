from __future__ import annotations

import re
from pathlib import Path

from llm_text_helper import (
    describe_text_mode,
    request_openai_text,
    resolve_text_mode,
)


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"

LEADING_VERBS = {
    "build",
    "create",
    "design",
    "develop",
    "generate",
    "make",
    "produce",
    "write",
}
STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "by",
    "for",
    "from",
    "in",
    "into",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
}
FILLER_WORDS = ["interactive", "prototype", "scene", "visual"]


def newest_timestamp(path: Path) -> float:
    stat = path.stat()
    return getattr(stat, "st_birthtime", stat.st_mtime)


def find_newest_directory(root: Path) -> Path:
    directories = [
        entry
        for entry in root.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    ]
    if not directories:
        raise FileNotFoundError("No directories found in the target folder.")
    directories_with_readme = [
        entry for entry in directories if (entry / "README.md").exists()
    ]
    candidates = directories_with_readme or directories
    return max(candidates, key=newest_timestamp)


def read_prompt_from_user() -> str:
    print("Paste the experiment prompt. End with an empty line (press Enter twice).")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            raise
        if not line.strip():
            if lines:
                break
            print("Prompt cannot be empty. Try again.")
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def extract_original_prompt(lines: list[str]) -> str:
    header_idx = None
    for idx, line in enumerate(lines):
        if "Original Prompt" in line:
            header_idx = idx
            break
    if header_idx is None:
        return ""

    end_idx = None
    for idx in range(header_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped == "---" or stripped.startswith("## "):
            end_idx = idx
            break
    if end_idx is None:
        end_idx = len(lines)

    content_lines = lines[header_idx + 1 : end_idx]
    return "\n".join(content_lines).strip()


def extract_tldr(lines: list[str]) -> str:
    for idx, line in enumerate(lines):
        if line.strip().startswith("**TLDR:**"):
            if idx + 1 < len(lines):
                return lines[idx + 1].strip()
            return ""
    return ""


def tokenize_prompt(prompt: str) -> list[str]:
    collapsed = re.sub(r"\s+", " ", prompt.strip())
    tokens = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", collapsed.lower())
    while tokens and tokens[0] in LEADING_VERBS:
        tokens.pop(0)
    return tokens


def build_summary(prompt: str) -> str:
    tokens = tokenize_prompt(prompt)
    words: list[str] = []
    for token in tokens:
        if token in STOPWORDS:
            continue
        if token == "html":
            continue
        words.append(token)
        if len(words) == 6:
            break

    if not words:
        words = ["interactive", "prompt", "summary"]

    while len(words) < 4:
        filler = FILLER_WORDS[len(words) % len(FILLER_WORDS)]
        if filler not in words:
            words.append(filler)
        else:
            words.append("prototype")

    words = words[:6]
    summary_words = words + ["html"]
    return " ".join(summary_words)


def sanitize_summary(summary: str) -> str:
    clean = re.sub(r"\s+", " ", summary.strip())
    clean = clean.strip("`'\" ")
    clean = re.sub(r"^4\s+models\s+try\s+to:\s*", "", clean, flags=re.IGNORECASE)
    clean = clean.strip(" .,:;!?")
    clean = clean.lower()
    words = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", clean)
    if not words:
        return ""
    if len(words) > 8:
        words = words[:8]
    if words[-1] != "html":
        words.append("html")
    return " ".join(words)


def build_summary_via_llm(prompt: str) -> str:
    system_prompt = (
        "You write short GitHub README TLDR lines for archived coding experiments. "
        "Return only a lowercase summary phrase for the line '4 Models try to: ...'. "
        "Keep it between 4 and 8 words, no quotes, no markdown, no ending punctuation. "
        "Capture the main task, ignore filler like 'using HTML/CSS/JS in a single HTML file' unless essential, "
        "and end with the word 'html'."
    )
    user_prompt = f"Original experiment prompt:\n{prompt}"
    response_text, _ = request_openai_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_env_var="OPENAI_STEP2_MODEL",
        temperature=0.1,
        max_output_tokens=40,
    )
    summary = sanitize_summary(response_text)
    if not summary:
        raise RuntimeError("OpenAI summary sanitization produced an empty TLDR.")
    return summary


def build_summary_with_mode(prompt: str) -> tuple[str, str]:
    mode = resolve_text_mode(model_env_var="OPENAI_STEP2_MODEL")
    if mode.is_api:
        try:
            summary = build_summary_via_llm(prompt)
            return summary, describe_text_mode(mode)
        except Exception as exc:
            if mode.requested == "api":
                raise
            print(f"Warning: API summary failed ({exc}). Falling back to local TLDR builder.")
    return build_summary(prompt), "Local fallback"


def replace_original_prompt(lines: list[str], new_prompt: str) -> None:
    header_idx = None
    for idx, line in enumerate(lines):
        if "Original Prompt" in line:
            header_idx = idx
            break
    if header_idx is None:
        raise ValueError("Could not find the 'Original Prompt' section in README.md.")

    end_idx = None
    for idx in range(header_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped == "---" or stripped.startswith("## "):
            end_idx = idx
            break
    if end_idx is None:
        end_idx = len(lines)

    replacement = [""] + new_prompt.splitlines() + [""]
    lines[header_idx + 1 : end_idx] = replacement


def replace_tldr(lines: list[str], summary: str) -> None:
    tldr_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("**TLDR:**"):
            tldr_idx = idx
            break
    if tldr_idx is None:
        raise ValueError("Could not find the TLDR section in README.md.")

    tldr_line = f"4 Models try to: {summary}"
    if tldr_idx + 1 < len(lines):
        lines[tldr_idx + 1] = tldr_line
    else:
        lines.append(tldr_line)


def main() -> int:
    root = EXPERIMENTS_ROOT
    try:
        newest_dir = find_newest_directory(root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    readme_path = newest_dir / "README.md"
    if not readme_path.exists():
        print(f"README.md not found in {newest_dir.name}.")
        return 1

    print(f"README target: '{newest_dir.name}'.")
    try:
        prompt_text = read_prompt_from_user()
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1

    try:
        summary, mode_label = build_summary_with_mode(prompt_text)
    except Exception as exc:
        print(f"Step 2 failed: {exc}")
        return 1

    readme_text = readme_path.read_text(encoding="utf-8")
    ends_with_newline = readme_text.endswith("\n")
    lines = readme_text.splitlines()

    old_prompt = extract_original_prompt(lines)
    old_tldr = extract_tldr(lines)
    new_tldr_line = f"4 Models try to: {summary}"

    print(f"\nMode: {mode_label}\n")
    print("\nOld prompt:\n")
    print(old_prompt or "(empty)")
    print("\nNew prompt:\n")
    print(prompt_text)
    print("\nOld TLDR line:\n")
    print(old_tldr or "(empty)")
    print("\nNew TLDR line:\n")
    print(new_tldr_line)
    print("")

    try:
        replace_original_prompt(lines, prompt_text)
        replace_tldr(lines, summary)
    except ValueError as exc:
        print(str(exc))
        return 1

    updated_text = "\n".join(lines)
    if ends_with_newline:
        updated_text += "\n"

    readme_path.write_text(updated_text, encoding="utf-8")
    print(f"Updated {readme_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
