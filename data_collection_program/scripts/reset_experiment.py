from __future__ import annotations

from pathlib import Path


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"


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


def list_html_files(folder: Path) -> list[Path]:
    return sorted(folder.glob("*.html"))


def confirm_deletion() -> bool:
    while True:
        try:
            choice = input(
                "Proceed to empty these HTML files and clear README sections? (y/n): "
            ).strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise
        if choice in {"y", "n"}:
            return choice == "y"
        print("Please enter 'y' or 'n'.")


def empty_files(files: list[Path]) -> None:
    for path in files:
        path.write_text("", encoding="utf-8")


def clear_readme_section(lines: list[str], header_keyword: str) -> bool:
    header_idx = None
    for idx, line in enumerate(lines):
        if line.strip().startswith("## ") and header_keyword in line:
            header_idx = idx
            break
    if header_idx is None:
        return False

    end_idx = None
    for idx in range(header_idx + 1, len(lines)):
        stripped = lines[idx].strip()
        if stripped.startswith("## ") or stripped == "---":
            end_idx = idx
            break
    if end_idx is None:
        end_idx = len(lines)

    lines[header_idx + 1 : end_idx] = [""]
    return True


def clear_readme_sections(readme_path: Path) -> None:
    readme_text = readme_path.read_text(encoding="utf-8")
    ends_with_newline = readme_text.endswith("\n")
    lines = readme_text.splitlines()

    cleared_summary = clear_readme_section(lines, "Per-Model Output Summary")
    cleared_observations = clear_readme_section(lines, "Observations")

    if not cleared_summary:
        print("Warning: Per-Model Output Summary section not found.")
    if not cleared_observations:
        print("Warning: Observations section not found.")

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

    html_files = list_html_files(newest_dir)
    print(f"Latest folder: '{newest_dir.name}'")
    if html_files:
        print("HTML files:")
        for file_path in html_files:
            print(f"- {file_path.name}")
    else:
        print("No .html files found.")

    try:
        should_delete = confirm_deletion()
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1

    if not should_delete:
        print("No changes made.")
        return 0

    if html_files:
        empty_files(html_files)
        print("HTML files emptied.")
    else:
        print("Skipping HTML cleanup (no .html files).")

    readme_path = newest_dir / "README.md"
    if readme_path.exists():
        clear_readme_sections(readme_path)
        print("README sections cleared.")
    else:
        print("README.md not found; skipping README cleanup.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
