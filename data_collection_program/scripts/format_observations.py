from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import re

from llm_text_helper import (
    describe_text_mode,
    request_openai_text,
    resolve_text_mode,
)


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
SCORES_FILENAME = "model_scores.json"


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
    return max(directories, key=newest_timestamp)


def confirm_prompt(message: str) -> bool:
    while True:
        try:
            choice = input(message).strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise
        if choice in {"y", "n"}:
            return choice == "y"
        print("Please enter 'y' or 'n'.")


@dataclass(frozen=True)
class ModelObservation:
    model_id: str
    observation: str


def compact_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def model_id_from_name(model_name: str) -> str:
    base_name = Path(model_name.strip()).name
    if base_name.lower().endswith(".html"):
        return base_name[:-5]
    return base_name


def load_observations_from_scores(scores_path: Path) -> list[ModelObservation]:
    if not scores_path.exists():
        raise FileNotFoundError(f"{SCORES_FILENAME} not found in {scores_path.parent}.")
    try:
        data = json.loads(scores_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {scores_path.name}.") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Invalid {scores_path.name} format.")
    models = data.get("models")
    if not isinstance(models, list):
        raise ValueError(f"{scores_path.name} must contain a 'models' array.")

    entries: list[ModelObservation] = []
    for entry in models:
        if not isinstance(entry, dict):
            continue
        model_name = str(entry.get("model_name", "")).strip()
        if not model_name:
            continue
        observation = str(entry.get("observations", "")).strip()
        entries.append(
            ModelObservation(
                model_id=model_id_from_name(model_name),
                observation=compact_whitespace(observation),
            )
        )

    if not entries:
        raise ValueError(f"No model observations found in {scores_path.name}.")
    return entries


def normalize_observation_text(text: str) -> str:
    clean = compact_whitespace(text)
    if not clean:
        return "No observation recorded."
    clean = clean[0].upper() + clean[1:] if clean else clean
    if clean[-1] not in ".!?":
        clean += "."
    return clean


def build_observation_bullets(entries: list[ModelObservation]) -> str:
    lines = []
    for entry in entries:
        lines.append(f"• {entry.model_id}: {normalize_observation_text(entry.observation)}")
    return "\n".join(lines)


def rewrite_observation_via_llm(entry: ModelObservation) -> str:
    system_prompt = (
        "You clean up experiment observation notes for a GitHub README. "
        "Rewrite the observation into one concise polished sentence. "
        "Do not invent facts, do not add scores, keep the meaning faithful, and keep the tone factual."
    )
    user_prompt = (
        f"Model id: {entry.model_id}\n"
        f"Raw observation: {entry.observation}\n\n"
        "Return only the rewritten sentence."
    )
    response_text, _ = request_openai_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        model_env_var="OPENAI_STEP13A_MODEL",
        temperature=0.2,
        max_output_tokens=120,
    )
    return normalize_observation_text(response_text)


def build_observation_bullets_with_mode(
    entries: list[ModelObservation],
) -> tuple[str, str]:
    mode = resolve_text_mode(model_env_var="OPENAI_STEP13A_MODEL")
    if mode.is_api:
        try:
            lines = []
            for entry in entries:
                rewritten = rewrite_observation_via_llm(entry)
                lines.append(f"• {entry.model_id}: {rewritten}")
            return "\n".join(lines), describe_text_mode(mode)
        except Exception as exc:
            if mode.requested == "api":
                raise
            print(
                f"Warning: API observation formatting failed ({exc}). Falling back to local formatter."
            )
    return build_observation_bullets(entries), "Local fallback"


def update_observations_section(readme_path: Path, observations: str) -> None:
    readme_text = readme_path.read_text(encoding="utf-8")
    ends_with_newline = readme_text.endswith("\n")
    lines = readme_text.splitlines()

    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("## ") and "Observations" in line:
            header_idx = idx
            break
    if header_idx is None:
        print("Warning: Observations section not found.")
        return

    end_idx = None
    for idx in range(header_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped == "---":
            end_idx = idx
            break
    if end_idx is None:
        end_idx = len(lines)

    obs_lines = observations.strip().splitlines() if observations.strip() else [""]
    replacement = [""] + obs_lines + [""]
    lines[header_idx + 1 : end_idx] = replacement

    updated_text = "\n".join(lines)
    if ends_with_newline:
        updated_text += "\n"
    readme_path.write_text(updated_text, encoding="utf-8")


def main() -> int:
    root = EXPERIMENTS_ROOT
    try:
        newest_dir = find_newest_directory(root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    print(f"Latest folder found: '{newest_dir.name}'")
    try:
        if not confirm_prompt(f"Use {newest_dir.name}? (y/n): "):
            print("Canceled.")
            return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1

    readme_path = newest_dir / "README.md"
    if not readme_path.exists():
        print(f"README.md not found in {newest_dir.name}.")
        return 1

    scores_path = newest_dir / SCORES_FILENAME
    try:
        entries = load_observations_from_scores(scores_path)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc))
        return 1

    try:
        formatted_observations, mode_label = build_observation_bullets_with_mode(entries)
    except Exception as exc:
        print(f"Step 13a failed: {exc}")
        return 1
    update_observations_section(readme_path, formatted_observations)

    print("======")
    print(f"Mode: {mode_label}")
    print(f"Updated observations in {newest_dir.name}/README.md")
    print(f"README path: {readme_path}")
    print()
    print(formatted_observations)
    print("======")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
