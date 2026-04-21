# This script builds the post template from the latest experiment data and updates the README table.

from __future__ import annotations

from pathlib import Path
import json
import csv
import re
import shutil
import subprocess
import sys


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
SCORES_FILENAME = "model_scores.json"

POST_TEMPLATE = """{tldr}

Output Lines:

{output_lines}

Model Details:
{model_details}

*All experiments use the model's very first, unrefined output, without retries or additional guidance.

Code: Github with the original code and more stats: https://github.com/diegocp01/html_ai_battle/tree/main/experiments/{directory_name}

* None of the models have custom instructions, chatgpt's personality is 'default'

* The reasoning time was measured manually starting when the return key was pressed. In the images, the timer starts only when the model begins inferencing, and there is a short delay between these two events. This is why the times may not exactly match.
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


def extract_tldr_summary(text: str) -> str:
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        if "**TLDR:**" not in line:
            continue
        inline = line.split("**TLDR:**", 1)[1].strip()
        candidates = [inline] if inline else []
        candidates.extend(lines[idx + 1 :])
        for candidate in candidates:
            stripped = candidate.strip()
            if not stripped:
                continue
            match = re.match(r"^4\s+Models\s+try\s+to:\s*(.+)$", stripped, re.IGNORECASE)
            if match:
                return match.group(1).strip()
            return stripped
    raise ValueError("TLDR section not found in README.")


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


def rename_downloaded_csv(folder: Path) -> Path:
    downloaded_path = folder / "downloaded_data.csv"
    target_path = folder / f"{folder.name}.csv"
    if downloaded_path.exists():
        if target_path.exists():
            print(
                f"Warning: {target_path.name} already exists. "
                "Using it and leaving downloaded_data.csv unchanged."
            )
            return target_path
        downloaded_path.rename(target_path)
        return target_path
    if target_path.exists():
        return target_path
    raise FileNotFoundError("downloaded_data.csv not found in the target folder.")


def normalize_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def resolve_columns(columns: list[str]) -> dict[str, str]:
    column_lookup = {normalize_header(column): column for column in columns if column}
    aliases = {
        "model": ["llm model", "model"],
        "reasoning_time": [
            "llm reasoning time (s)",
            "llm reasoning time s",
            "reasoning time (s)",
            "reasoning time s",
        ],
        "response_time": [
            "llm response time (s)",
            "llm response time s",
            "response time (s)",
            "response time s",
        ],
        "reasoning_words": ["reasoning total words", "total reasoning words"],
        "lines_html": ["lines of html", "html lines"],
        "performance_score": ["performance score (0-10)", "performance score", "score"],
    }
    resolved: dict[str, str] = {}
    for key, candidates in aliases.items():
        found = None
        for candidate in candidates:
            normalized = normalize_header(candidate)
            if normalized in column_lookup:
                found = column_lookup[normalized]
                break
        if not found:
            raise KeyError(f"Missing column for {key}.")
        resolved[key] = found
    return resolved


def load_csv_rows(csv_path: Path) -> tuple[list[dict[str, str]], list[str]]:
    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    return rows, columns


def is_numeric(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    try:
        float(stripped)
        return True
    except ValueError:
        return False


def format_numeric(value: str) -> str:
    try:
        return f"{float(value):g}"
    except ValueError:
        return value


def to_markdown_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    if not columns:
        return ""
    numeric_columns = {}
    for column in columns:
        values = []
        for row in rows:
            value = row.get(column, "")
            if value is None:
                value = ""
            values.append(str(value).strip())
        numeric_columns[column] = all(is_numeric(value) for value in values)

    formatted_rows: list[dict[str, str]] = []
    for row in rows:
        formatted = {}
        for column in columns:
            value = "" if row.get(column) is None else str(row.get(column))
            if numeric_columns[column]:
                formatted[column] = format_numeric(value)
            else:
                formatted[column] = value
        formatted_rows.append(formatted)

    widths: dict[str, int] = {}
    for column in columns:
        width = len(column)
        for row in formatted_rows:
            width = max(width, len(str(row.get(column, ""))))
        widths[column] = max(width, 3)

    def align_cell(text: str, column: str) -> str:
        width = widths[column]
        if numeric_columns[column]:
            return text.rjust(width)
        return text.ljust(width)

    header_cells = [align_cell(column, column) for column in columns]
    header_line = "| " + " | ".join(header_cells) + " |"

    alignment_cells = []
    for column in columns:
        width = widths[column]
        if numeric_columns[column]:
            alignment_cells.append("-" * (width - 1) + ":")
        else:
            alignment_cells.append(":" + "-" * (width - 1))
    alignment_line = "|" + "|".join(alignment_cells) + "|"

    data_lines = []
    for row in formatted_rows:
        cells = [align_cell(str(row.get(column, "")), column) for column in columns]
        data_lines.append("| " + " | ".join(cells) + " |")

    return "\n".join([header_line, alignment_line, *data_lines])


class SimpleDataFrame:
    def __init__(self, rows: list[dict[str, object]], columns: list[str]) -> None:
        self._rows = rows
        self.columns = columns

    def to_markdown(self, index: bool = False) -> str:
        _ = index
        return to_markdown_table(self._rows, self.columns)


def load_dataframe(csv_path: Path) -> tuple[object, list[dict[str, object]], list[str]]:
    try:
        import pandas as pd
    except Exception:
        rows, columns = load_csv_rows(csv_path)
        return SimpleDataFrame(rows, columns), rows, columns
    df = pd.read_csv(csv_path)
    rows = df.to_dict(orient="records")
    columns = list(df.columns)
    return df, rows, columns


def parse_int(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0
    try:
        return int(float(text))
    except ValueError:
        return 0


def parse_float(value: object) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    if not text:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def normalize_model_key(name: str) -> str:
    return name.strip().lower()


def add_score_aliases(scores: dict[str, float], name: str, score: float) -> None:
    key = normalize_model_key(name)
    if not key:
        return
    scores[key] = score
    if key.endswith(".html"):
        scores[key[:-5]] = score
    else:
        scores[f"{key}.html"] = score


def load_step8_scores(folder: Path) -> tuple[dict[str, float], str | None]:
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

    scores: dict[str, float] = {}
    for entry in models:
        if not isinstance(entry, dict):
            continue
        model_name = str(entry.get("model_name", "")).strip()
        if not model_name:
            continue
        try:
            score = float(entry.get("performance_score", ""))
        except (TypeError, ValueError):
            continue
        add_score_aliases(scores, model_name, score)
    return scores, None


def build_row_lookup(
    rows: list[dict[str, object]], model_column: str
) -> dict[str, dict[str, object]]:
    lookup: dict[str, dict[str, object]] = {}
    for row in rows:
        model_value = str(row.get(model_column, "")).strip()
        if not model_value:
            continue
        lookup[model_value.lower()] = row
    return lookup


def find_row_for_model(
    model_name: str, row_lookup: dict[str, dict[str, object]]
) -> dict[str, object] | None:
    key = model_name.lower()
    if key in row_lookup:
        return row_lookup[key]
    stripped = re.sub(r"^claude-", "", key)
    if stripped in row_lookup:
        return row_lookup[stripped]
    for candidate, row in row_lookup.items():
        if candidate in key or key in candidate:
            return row
    return None


def update_readme_summary(readme_path: Path, markdown_table: str) -> None:
    readme_text = readme_path.read_text(encoding="utf-8")
    ends_with_newline = readme_text.endswith("\n")
    lines = readme_text.splitlines()

    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("## ") and "Per-Model Output Summary" in line:
            header_idx = idx
            break
    if header_idx is None:
        print("Warning: Per-Model Output Summary section not found.")
        return

    end_idx = None
    for idx in range(header_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped == "---":
            end_idx = idx
            break
    if end_idx is None:
        end_idx = len(lines)

    table_lines = markdown_table.strip().splitlines() if markdown_table.strip() else [""]
    replacement = [""] + table_lines + [""]
    lines[header_idx + 1 : end_idx] = replacement

    updated_text = "\n".join(lines)
    if ends_with_newline:
        updated_text += "\n"
    readme_path.write_text(updated_text, encoding="utf-8")


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
        tldr_summary = extract_tldr_summary(readme_text)
    except ValueError as exc:
        print(str(exc))
        return 1

    try:
        csv_path = rename_downloaded_csv(newest_dir)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    df, rows, columns = load_dataframe(csv_path)
    try:
        column_map = resolve_columns(columns)
    except KeyError as exc:
        print(str(exc))
        return 1

    try:
        markdown_table = df.to_markdown(index=False)
    except Exception:
        markdown_table = to_markdown_table(rows, columns)

    row_lookup = build_row_lookup(rows, column_map["model"])
    html_files = ordered_html_files(newest_dir)
    if len(html_files) < 4:
        print("Expected at least 4 HTML files in the latest folder.")
        return 1
    model_names = [path.stem for path in html_files[:4]]

    score_lookup, score_error = load_step8_scores(newest_dir)
    if score_error:
        print(f"Warning: {score_error}")

    output_lines = []
    model_details = []
    missing_scores: list[str] = []
    for model in model_names:
        row = find_row_for_model(model, row_lookup)
        if not row:
            print(f"Missing CSV row for model: {model}")
            return 1
        lines_html = parse_int(row.get(column_map["lines_html"]))
        output_lines.append(f"{lines_html} lines of HTML ({model})")

        score = score_lookup.get(normalize_model_key(model))
        if score is None:
            score = parse_float(row.get(column_map["performance_score"]))
            if score_error is None:
                missing_scores.append(model)
        reasoning_time = parse_int(row.get(column_map["reasoning_time"]))
        response_time = parse_int(row.get(column_map["response_time"]))
        reasoning_words = parse_int(row.get(column_map["reasoning_words"]))
        model_details.append(
            f"{model}: Score {score:.1f}/10. Reasoning Time: {reasoning_time} s, "
            f"Total Response Time: {response_time} s, Total Reasoning Words: {reasoning_words}"
        )

    if missing_scores:
        missing_list = ", ".join(missing_scores)
        print(f"Warning: Missing JSON scores for {missing_list}. Using CSV values.")

    output_lines_text = "\n".join(output_lines)
    model_details_text = "\n\n".join(model_details)
    post_text = POST_TEMPLATE.format(
        tldr=tldr_summary,
        output_lines=output_lines_text,
        model_details=model_details_text,
        directory_name=newest_dir.name,
    )

    try:
        display_path = readme_path.relative_to(root)
    except ValueError:
        display_path = readme_path

    print("=======")
    print(f"TLDR text in {display_path} is ")
    print(tldr_summary)
    print("=======")
    print()
    print(markdown_table)
    print()
    print("Post template:")
    print(post_text)
    print()
    print("=======")

    update_readme_summary(readme_path, markdown_table)

    copied = copy_to_clipboard(post_text)
    if copied:
        print("\033[1m\033[32mPROMPT COPIED TO CLIPBOARD\033[0m")
    else:
        print("\033[1m\033[31mCLIPBOARD COPY FAILED\033[0m")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
