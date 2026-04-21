from __future__ import annotations

import os
import re
import shutil
from pathlib import Path


DATA_COLLECTION_ROOT = Path(__file__).resolve().parent.parent
REPO_ROOT = DATA_COLLECTION_ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
README_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


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


def unique_copy_path(root: Path, source_name: str) -> Path:
    base = f"{source_name}_copy"
    candidate = root / base
    counter = 1
    while candidate.exists():
        candidate = root / f"{base}_{counter}"
        counter += 1
    return candidate


def prompt_for_folder_name(root: Path) -> str:
    while True:
        try:
            name = input("New folder name: ").strip()
        except (EOFError, KeyboardInterrupt):
            raise
        if not name:
            print("Name cannot be empty.")
            continue
        if name in {".", ".."}:
            print("Name cannot be '.' or '..'.")
            continue
        if os.sep in name or (os.altsep and os.altsep in name):
            print("Name cannot include path separators.")
            continue
        if (root / name).exists():
            print("A folder or file with that name already exists.")
            continue
        return name


def remove_unwanted_files(folder: Path) -> None:
    for path in folder.rglob("*"):
        if not path.is_file():
            continue
        name_lower = path.name.lower()
        if name_lower.startswith("image") or path.suffix.lower() == ".csv":
            try:
                path.unlink()
            except OSError as exc:
                print(f"Warning: failed to delete {path.name} ({exc})")


def clean_readme_link(folder: Path) -> bool:
    readme_path = folder / "README.md"
    if not readme_path.exists():
        return False
    try:
        text = readme_path.read_text(encoding="utf-8")
    except OSError:
        return False
    lines = text.splitlines()
    in_observations = False
    changed = False
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## "):
            in_observations = "Observations" in stripped
            continue
        if not in_observations:
            continue
        if stripped.startswith("Link:"):
            after = stripped[len("Link:") :].strip()
            if after and README_URL_RE.search(after):
                prefix = line[: len(line) - len(line.lstrip(" \t"))]
                lines[index] = f"{prefix}Link:"
                changed = True
    if changed:
        readme_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return changed


def main() -> int:
    root = EXPERIMENTS_ROOT
    try:
        newest_dir = find_newest_directory(root)
    except FileNotFoundError as exc:
        print(str(exc))
        return 1

    copy_path = unique_copy_path(root, newest_dir.name)
    print(f"Copying '{newest_dir.name}' to '{copy_path.name}'...")
    shutil.copytree(newest_dir, copy_path)
    remove_unwanted_files(copy_path)
    print("Deleted image and csv files")

    try:
        new_name = prompt_for_folder_name(root)
    except (EOFError, KeyboardInterrupt):
        print(f"\nCanceled. Copy kept at '{copy_path.name}'.")
        return 1

    final_path = root / new_name
    copy_path.rename(final_path)
    print(f"Renamed copy to '{final_path.name}'.")
    if clean_readme_link(final_path):
        print("Cleaned README link URL.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
