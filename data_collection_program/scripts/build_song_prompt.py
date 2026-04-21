# This script builds a QA prompt by injecting the README prompt section.

from __future__ import annotations

from pathlib import Path
import json
import re
import shutil
import subprocess
import sys


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
SCORES_FILENAME = "model_scores.json"

PROMPT_TEMPLATE = """
# Context
I have run an experiment comparing 4 LLMs (GPT, Gemini, Grok, and Claude Opus). They were all given the same prompt to generate HTML code. The prompt the models used today was ‘[prompt]’

# Task
Write a song summarizing the results of this week's experiment based on the provided "Observations" and "Scores."

# Critical Constraints
1. **Naming Convention:** Do NOT use the exact commercial names of the models. Instead, write their names **phonetically** or use nicknames that fit the flow and rhyme scheme of the song (e.g., "Gem-in-eye," "Gee-P-Tee," "Grok," "Claw-d").
2. **Content:** The lyrics must reflect the specific observations provided and the exact anime of the model (e.g., if one failed the HTML structure, mock it; if one was perfect, praise it).
3. **Structure:** Verse-Chorus structure.

# Input Data (Observations & Scores)
**Model 1: GPT-5.2 Extended Thinking**
* Observations: [observations]
* Score: [score]/10

**Model 2: Gemini 3 Pro**
* Observations: [observations]
* Score: [score]/10

**Model 3: Grok 4.1 Thinking**
* Observations: [observations]
* Score: [score]/10

**Model 4: Claude Opus 4.5 Thinking (32k)**
* Observations: [observations]
* Score: [score]/10

# Reference Style
See an example of how the models sound good phonetically, in a previously generated song, and the style:
"[Verse 1] Gee-P-Tee Five point Two, Extended Thinking, in the frame, You just came out two days ago, but it’s a shame. You lacking my dog, my boi, what’s wrong with the head? There is no simulation, just parameters instead. You shoulda focused on the motion, not the text input, Score is zero Point three outta ten, yeah you stuck in the soot.

[Verse 2] Gem-in-eye Three Pro, nice intro right there, But what is wrong with the front tires? That’s a scare! Nice Tokyo Drift fam, you sliding with the pace, Score is Eight point eight outta ten, yeah you stayed in the race.

[Verse 3] G-rok Four point One Thinking, well at least you made it render, But the car is floating up like a Space-X sender. Instead of the car drifting, the camera moves away, Score is One outta ten, physics took a holiday.

[Verse 4] Claw-d O-pus Four point Five,  thinking Thirty two -K on the deck, I am completely speechless, gotta give respect. You didn’t just fulfill it, you made it interact, Playing in another dimension, that’s a fact. Compared to these little guys, homie, you the king, Beat the score board, you mastered everything. Score is 10 outta ten. ” 

"""


def newest_timestamp(path: Path) -> float:
    stat = path.stat()
    return getattr(stat, "st_birthtime", stat.st_mtime)


def find_newest_directory(root: Path) -> Path:
    directories = [
        entry
        for entry in root.iterdir()
        if entry.is_dir()
        and not entry.name.startswith(".")
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


def find_readme_file(folder: Path) -> Path:
    readmes = [
        path
        for path in folder.iterdir()
        if path.is_file() and path.name.lower().startswith("readme")
    ]
    if not readmes:
        raise FileNotFoundError("No README file found in the target folder.")
    return sorted(readmes, key=lambda path: path.name.lower())[0]


def extract_prompt_section(text: str) -> str:
    lines = text.splitlines()
    start_index = None
    for idx, line in enumerate(lines):
        if re.match(r"^##\s+.*original prompt", line, re.IGNORECASE):
            start_index = idx + 1
            break

    if start_index is None:
        raise ValueError("Prompt section not found in README.")

    collected: list[str] = []
    for line in lines[start_index:]:
        stripped = line.strip()
        if re.match(r"^##\s+", line) or re.match(r"^#\s+", line) or stripped.startswith("---"):
            break
        collected.append(line)

    while collected and not collected[0].strip():
        collected.pop(0)
    while collected and not collected[-1].strip():
        collected.pop()

    return "\n".join(collected).strip()


def file_category(name: str) -> int:
    lower = name.lower()
    if lower.startswith("gpt"):
        return 0
    if lower.startswith("gemini") and "pro" in lower:
        return 1
    if lower.startswith("grok"):
        return 2
    if lower.startswith("opus"):
        return 3
    return 4


def ordered_html_files(folder: Path) -> list[Path]:
    files = [path for path in folder.glob("*.html") if path.is_file()]
    return sorted(files, key=lambda path: (file_category(path.name), path.name.lower()))


def load_step8_scores(folder: Path) -> tuple[dict[str, dict[str, object]], str | None]:
    scores_path = folder / SCORES_FILENAME
    if not scores_path.exists():
        return {}, f"{SCORES_FILENAME} not found in {folder.name}."
    try:
        data = json.loads(scores_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}, f"Unable to parse {scores_path.name}."
    if not isinstance(data, dict):
        return {}, f"{scores_path.name} is not a JSON object."
    models = data.get("models")
    if not isinstance(models, list):
        return {}, f"{scores_path.name} is missing a models list."

    results: dict[str, dict[str, object]] = {}
    for entry in models:
        if not isinstance(entry, dict):
            continue
        model_name = str(entry.get("model_name", "")).strip()
        if not model_name:
            continue
        results[model_name] = {
            "observations": entry.get("observations", ""),
            "performance_score": entry.get("performance_score"),
        }
    return results, None


def format_performance_score(value: object) -> str | None:
    try:
        return f"{float(value):.1f}"
    except (TypeError, ValueError):
        return None


def build_final_prompt(prompt_text: str, observations: list[str], scores: list[str]) -> str:
    updated = PROMPT_TEMPLATE.replace("[prompt]", prompt_text)
    observation_iter = iter(observations)
    score_iter = iter(scores)

    def replace_match(match: re.Match[str]) -> str:
        if match.group(1) == "observations":
            return next(observation_iter, "[observations]")
        return next(score_iter, "[score]")

    return re.sub(r"\[(observations|score)\]", replace_match, updated)


def copy_to_clipboard(text: str) -> bool:
    if sys.platform == "darwin":
        try:
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
            return True
        except Exception:
            pass

    for command in ("wl-copy", "xclip"):
        if shutil.which(command):
            try:
                if command == "xclip":
                    subprocess.run(
                        ["xclip", "-selection", "clipboard"],
                        input=text,
                        text=True,
                        check=True,
                    )
                else:
                    subprocess.run([command], input=text, text=True, check=True)
                return True
            except Exception:
                pass

    try:
        import tkinter as tk
    except Exception:
        return False

    try:
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
        return True
    except Exception:
        return False


def main() -> int:
    root = EXPERIMENTS_ROOT
    try:
        newest_dir = find_newest_directory(root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    print(f"Latest folder found: '{newest_dir.name}'")
    try:
        if not confirm_prompt("this is the last folder created is this correct? y/n: "):
            print("Canceled.")
            return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1

    try:
        readme_path = find_readme_file(newest_dir)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    readme_text = readme_path.read_text(encoding="utf-8")
    try:
        prompt_text = extract_prompt_section(readme_text)
    except ValueError as exc:
        print(str(exc))
        return 1

    html_files = ordered_html_files(newest_dir)
    model_files = [path.name for path in html_files[:4]]
    while len(model_files) < 4:
        model_files.append("")

    scores_by_model, scores_error = load_step8_scores(newest_dir)
    if scores_error:
        print(f"Warning: {scores_error}")

    observation_values: list[str] = []
    score_values: list[str] = []
    missing_models: list[str] = []
    for model_name in model_files:
        entry = scores_by_model.get(model_name)
        if not entry:
            observation_values.append("[observations]")
            score_values.append("[score]")
            if model_name:
                missing_models.append(model_name)
            continue
        observation = str(entry.get("observations", "")).strip()
        if not observation:
            observation = "No observations provided."
        observation_values.append(observation)
        score_text = format_performance_score(entry.get("performance_score"))
        if score_text is None:
            score_values.append("[score]")
            if model_name:
                missing_models.append(model_name)
        else:
            score_values.append(score_text)

    if missing_models:
        missing_list = ", ".join(missing_models)
        print(f"Warning: Missing scores for {missing_list}.")

    final_prompt = build_final_prompt(prompt_text, observation_values, score_values)
    copied = copy_to_clipboard(final_prompt)
    try:
        display_path = readme_path.relative_to(root)
    except ValueError:
        display_path = readme_path

    print("=======")
    print(f"current prompt in {display_path} is ")
    print(prompt_text)
    print("=======")
    print()
    print("Prompt Template + current README prompt:")
    print(final_prompt)
    print()
    print("=======")
    if copied:
        print("\033[1m\033[32mPROMPT COPIED TO CLIPBOARD\033[0m")
    else:
        print("\033[1m\033[31mCLIPBOARD COPY FAILED\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
