from pathlib import Path


def count_lines_in_file(path: Path) -> int:
    """Return the number of lines in the given file."""
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def update_readme(root: Path, model_line_counts: dict) -> None:
    readme_path = root / "README.md"
    if not readme_path.exists():
        print(f"README.md not found at {readme_path}, skipping README update.")
        return

    text = readme_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    header_index = None
    for i, line in enumerate(lines):
        if line.strip() == "## 🤖 Per-Model Output Summary":
            header_index = i
            break

    if header_index is None:
        print(
            "Section '## 🤖 Per-Model Output Summary' not found in README, "
            "skipping README update."
        )
        return

    table_start = None
    for j in range(header_index + 1, len(lines)):
        if lines[j].lstrip().startswith("|"):
            table_start = j
            break

    if table_start is None:
        print("Table under 'Per-Model Output Summary' not found, skipping README update.")
        return

    table_end = len(lines)
    for k in range(table_start + 1, len(lines)):
        if not lines[k].lstrip().startswith("|"):
            table_end = k
            break

    updated_models = set()

    for idx in range(table_start + 2, table_end):
        line = lines[idx]
        stripped = line.strip()
        if not stripped or "|" not in stripped:
            continue

        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 2:
            continue

        model_name = cells[0]
        if model_name in model_line_counts:
            cells[1] = str(model_line_counts[model_name])
            lines[idx] = "| " + " | ".join(cells) + " |"
            updated_models.add(model_name)

    if not updated_models:
        print("No matching models found in README table to update.")
        return

    readme_path.write_text(
        "\n".join(lines) + ("\n" if text.endswith("\n") else ""),
        encoding="utf-8",
    )
    print(f"Updated README.md for models: {', '.join(sorted(updated_models))}")


def main() -> None:
    # Use the directory where this script lives as the root
    root = Path(__file__).resolve().parent

    html_files = sorted(root.rglob("*.html"))

    if not html_files:
        print(f"No HTML files found under: {root}")
        return

    print(f"Scanning HTML files under: {root}\n")

    total_lines = 0
    model_line_counts = {}
    for html_file in html_files:
        line_count = count_lines_in_file(html_file)
        total_lines += line_count
        rel_path = html_file.relative_to(root)
        print(f"{rel_path}: {line_count} lines")

        model_name = html_file.stem
        model_line_counts[model_name] = line_count

    print(f"\nTotal lines across all HTML files: {total_lines}")

    update_readme(root, model_line_counts)


# 
if __name__ == "__main__":
    main()
