# This script lists line counts for html files in the newest experiment folder.

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


def confirm_prompt(message: str) -> bool:
    while True:
        try:
            choice = input(message).strip().lower()
        except (EOFError, KeyboardInterrupt):
            raise
        if choice in {"y", "n"}:
            return choice == "y"
        print("Please enter 'y' or 'n'.")


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle)


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


def main() -> int:
    root = EXPERIMENTS_ROOT
    try:
        newest_dir = find_newest_directory(root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    print(f"Latest folder found: '{newest_dir.name}'")
    try:
        if not confirm_prompt("Is this correct? (y/n): "):
            print("Canceled.")
            return 1
    except (EOFError, KeyboardInterrupt):
        print("\nCanceled.")
        return 1

    html_files = sorted(
        [path for path in newest_dir.glob("*.html") if path.is_file()],
        key=lambda path: (file_category(path.name), path.name.lower()),
    )
    if not html_files:
        print("No .html files found in the latest folder.")
        return 1

    print("HTML line counts:")
    for path in html_files:
        try:
            line_count = count_lines(path)
        except OSError as exc:
            print(f"{path.name}: error reading file ({exc})")
            continue
        line_label = "line" if line_count == 1 else "lines"
        print(f"{line_count} {line_label} -> {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
