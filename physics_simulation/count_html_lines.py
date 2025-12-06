from pathlib import Path


def count_lines_in_file(path: Path) -> int:
    """Return the number of lines in the given file."""
    with path.open("r", encoding="utf-8", errors="ignore") as f:
        return sum(1 for _ in f)


def main() -> None:
    # Use the directory where this script lives as the root
    root = Path(__file__).resolve().parent

    html_files = sorted(root.rglob("*.html"))

    if not html_files:
        print(f"No HTML files found under: {root}")
        return

    print(f"Scanning HTML files under: {root}\n")

    total_lines = 0
    for html_file in html_files:
        line_count = count_lines_in_file(html_file)
        total_lines += line_count
        rel_path = html_file.relative_to(root)
        print(f"{rel_path}: {line_count} lines")

    print(f"\nTotal lines across all HTML files: {total_lines}")


if __name__ == "__main__":
    main()
