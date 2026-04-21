from __future__ import annotations

from pathlib import Path
import json
import html
import os
import re
import shutil
import subprocess
import sys
import urllib.request
import urllib.error

from flask import Flask, Response, jsonify, render_template_string, request

from automation.browser_automation import (
    run_chatgpt_automation,
    run_gemini_automation,
    run_grok_automation,
)


ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent
EXPERIMENTS_ROOT = REPO_ROOT / "experiments"
SCRIPTS_DIR = ROOT / "scripts"
TEMPLATES_DIR = ROOT / "templates"

MODEL_FILES_OVERRIDE: list[str] | None = None
SCORES_FILENAME = "model_scores.json"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mK]")
README_URL_RE = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


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


def load_template(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Template not found: {path}")
    return path.read_text(encoding="utf-8")


def get_latest_info() -> tuple[Path | None, list[Path]]:
    try:
        latest_dir = find_newest_directory(EXPERIMENTS_ROOT)
    except FileNotFoundError:
        return None, []
    return latest_dir, ordered_html_files(latest_dir)


def normalize_model_files(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    for value in values:
        if value is None:
            cleaned.append("")
        else:
            cleaned.append(str(value).strip())
    cleaned = cleaned[:4]
    while len(cleaned) < 4:
        cleaned.append("")
    return cleaned


def get_model_files() -> list[str]:
    if MODEL_FILES_OVERRIDE is not None:
        return list(MODEL_FILES_OVERRIDE)

    latest_dir, html_files = get_latest_info()
    if not latest_dir:
        return ["", "", "", ""]
    model_files = [path.name for path in html_files[:4]]
    while len(model_files) < 4:
        model_files.append("")
    return model_files


def validate_folder_name(root: Path, name: str) -> str | None:
    if not name:
        return "Name cannot be empty."
    if name in {".", ".."}:
        return "Name cannot be '.' or '..'."
    if os.sep in name or (os.altsep and os.altsep in name):
        return "Name cannot include path separators."
    if (root / name).exists():
        return "A folder or file with that name already exists."
    return None


def validate_model_filename(name: str) -> str | None:
    if not name:
        return "Model file name cannot be empty."
    if name in {".", ".."}:
        return "Model file name cannot be '.' or '..'."
    if os.sep in name or (os.altsep and os.altsep in name):
        return "Model file name cannot include path separators."
    return None


def unique_copy_path(root: Path, source_name: str) -> Path:
    base = f"{source_name}_copy"
    candidate = root / base
    counter = 1
    while candidate.exists():
        candidate = root / f"{base}_{counter}"
        counter += 1
    return candidate


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


def run_step1(new_name: str) -> str:
    newest_dir = find_newest_directory(EXPERIMENTS_ROOT)
    copy_path = unique_copy_path(EXPERIMENTS_ROOT, newest_dir.name)
    output_lines = [
        f"Copying '{newest_dir.name}' to '{copy_path.name}'...",
    ]
    shutil.copytree(newest_dir, copy_path)
    remove_unwanted_files(copy_path)
    output_lines.append("Deleted image and csv files")
    if clean_readme_link(copy_path):
        output_lines.append("Cleaned README link URL.")
    final_path = EXPERIMENTS_ROOT / new_name
    copy_path.rename(final_path)
    output_lines.append(f"Renamed copy to '{final_path.name}'.")
    return "\n".join(output_lines)


def run_script(script_name: str, stdin_text: str) -> tuple[int, str]:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        return 1, f"{script_name} not found."
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    result = subprocess.run(
        [sys.executable, str(script_path)],
        input=stdin_text,
        text=True,
        capture_output=True,
        env=env,
    )
    output = result.stdout or ""
    if result.stderr:
        output = f"{output}\n{result.stderr}"
    output = strip_ansi(output).strip()
    if not output:
        output = "(No output)"
    return result.returncode, output


def parse_confirm(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        return value.strip().lower() in {"y", "yes", "true", "1"}
    return False


def load_scores_payload(path: Path) -> dict[str, list[dict[str, object]]]:
    if not path.exists():
        return {"models": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"models": []}
    if not isinstance(data, dict):
        return {"models": []}
    models = data.get("models")
    if not isinstance(models, list):
        models = []
    return {"models": models}


def upsert_score_entry(
    models: list[dict[str, object]],
    model_name: str,
    performance_score: float,
    observations: str,
) -> None:
    for entry in models:
        if str(entry.get("model_name", "")).strip() == model_name:
            entry["performance_score"] = performance_score
            entry["observations"] = observations
            return
    models.append(
        {
            "model_name": model_name,
            "performance_score": performance_score,
            "observations": observations,
        }
    )


app = Flask(__name__)


@app.route("/")
def index() -> str:
    latest_dir, ordered_files = get_latest_info()
    latest_name = latest_dir.name if latest_dir else "None found"
    model_files = get_model_files()
    template = load_template(TEMPLATES_DIR / "dashboard.html")
    return render_template_string(
        template,
        latest_dir_name=latest_name,
        ordered_files=[path.name for path in ordered_files],
        model_files=model_files,
        model_override_active=MODEL_FILES_OVERRIDE is not None,
    )


@app.post("/api/model-files")
def api_model_files() -> Response:
    data = request.get_json(silent=True) or {}
    files = data.get("model_files", [])
    if not isinstance(files, list):
        return jsonify(ok=False, output="model_files must be a list."), 400
    cleaned = normalize_model_files(files)
    global MODEL_FILES_OVERRIDE
    if all(not value for value in cleaned):
        MODEL_FILES_OVERRIDE = None
    else:
        MODEL_FILES_OVERRIDE = cleaned
    return jsonify(
        ok=True,
        model_files=get_model_files(),
        override_active=MODEL_FILES_OVERRIDE is not None,
    )


@app.post("/api/step8-scores")
def api_step8_scores() -> Response:
    data = request.get_json(silent=True) or {}
    model_name = str(data.get("model_name", "")).strip()
    observations = str(data.get("observations", "")).strip()
    if not model_name:
        return jsonify(ok=False, output="model_name is required."), 400
    try:
        performance_score = float(data.get("performance_score", ""))
    except (TypeError, ValueError):
        return jsonify(ok=False, output="performance_score must be a number."), 400
    if performance_score < 0 or performance_score > 10:
        return jsonify(ok=False, output="performance_score must be 0-10."), 400
    performance_score = round(performance_score, 2)

    try:
        latest_dir = find_newest_directory(EXPERIMENTS_ROOT)
    except FileNotFoundError as exc:
        return jsonify(ok=False, output=str(exc)), 400

    scores_path = latest_dir / SCORES_FILENAME
    payload = load_scores_payload(scores_path)
    upsert_score_entry(payload["models"], model_name, performance_score, observations)
    scores_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return jsonify(ok=True, output="Saved.", path=str(scores_path.relative_to(REPO_ROOT)))


@app.post("/api/ingest-htmls")
def api_ingest_htmls() -> Response:
    data = request.get_json(silent=True) or {}
    htmls = data.get("htmls", [])
    if not isinstance(htmls, list):
        return jsonify(ok=False, output="htmls must be a list."), 400
    htmls = ["" if value is None else str(value) for value in htmls]
    if len(htmls) < 4:
        return jsonify(ok=False, output="Expected 4 HTML payloads."), 400
    htmls = htmls[:4]

    try:
        latest_dir = find_newest_directory(EXPERIMENTS_ROOT)
    except FileNotFoundError as exc:
        return jsonify(ok=False, output=str(exc)), 400

    model_files = get_model_files()[:4]
    for name in model_files:
        error = validate_model_filename(name)
        if error:
            return jsonify(ok=False, output=error), 400

    written_paths: list[str] = []
    for name, html_text in zip(model_files, htmls):
        target_path = latest_dir / name
        target_path.write_text(html_text, encoding="utf-8")
        written_paths.append(str(target_path.relative_to(REPO_ROOT)))
    return jsonify(ok=True, output="Saved HTML files.", files=written_paths)


@app.route("/step5")
def step5() -> str:
    template = load_template(TEMPLATES_DIR / "time_tracker.html")
    return render_template_string(template, model_files=get_model_files())


@app.route("/step6")
def step6() -> str:
    template = load_template(TEMPLATES_DIR / "reasoning_counter.html")
    return render_template_string(template, model_files=get_model_files())


@app.route("/step8")
def step8() -> str:
    template = load_template(TEMPLATES_DIR / "scoring.html")
    return render_template_string(template, model_files=get_model_files())


@app.route("/step7")
def step7() -> Response:
    code, output = run_script("count_html_lines.py", "y\n")
    status = 200 if code == 0 else 500
    return Response(
        f"<pre>{html.escape(output)}</pre>",
        status=status,
        mimetype="text/html",
    )


@app.post("/run/step1")
def run_step1_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    new_name = str(data.get("new_name", "")).strip()
    error = validate_folder_name(EXPERIMENTS_ROOT, new_name)
    if error:
        return jsonify(ok=False, output=error, returncode=1)
    try:
        output = run_step1(new_name)
    except Exception as exc:
        return jsonify(ok=False, output=str(exc), returncode=1)
    return jsonify(ok=True, output=output, returncode=0)


@app.post("/run/step2")
def run_step2_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    prompt_text = str(data.get("prompt", "")).strip()
    if not prompt_text:
        return jsonify(
            ok=False,
            output="Prompt cannot be empty.",
            returncode=1,
        )
    input_text = f"{prompt_text}\n\n"
    code, output = run_script("update_readme_prompt.py", input_text)
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step3")
def run_step3_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    code, output = run_script("reset_experiment.py", "y\n")
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step7")
def run_step7_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    code, output = run_script("count_html_lines.py", "y\n")
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step10")
def run_step10_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    code, output = run_script("build_scoring_prompt.py", "y\n")
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step11")
def run_step11_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    code, output = run_script("build_song_prompt.py", "y\n")
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step13")
def run_step13_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    code, output = run_script("build_post_template.py", "y\n")
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step13a")
def run_step13a_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    if not parse_confirm(data.get("confirm")):
        return jsonify(ok=True, output="Canceled.", returncode=0)
    input_text = "y\n"
    code, output = run_script("format_observations.py", input_text)
    return jsonify(ok=code == 0, output=output, returncode=code)


@app.post("/run/step5a")
def run_step5a_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    prompt_text = str(data.get("prompt", "")).strip()
    if not prompt_text:
        return jsonify(ok=False, output="Prompt cannot be empty."), 400
    cdp_url = str(data.get("cdp_url", "http://localhost:9222")).strip()

    def generate():
        for event in run_chatgpt_automation(
            prompt=prompt_text,
            cdp_url=cdp_url,
            model_name="GPT-5.2",
        ):
            yield event

    return Response(generate(), mimetype="text/event-stream")


@app.post("/run/step5a-gemini")
def run_step5a_gemini_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    prompt_text = str(data.get("prompt", "")).strip()
    if not prompt_text:
        return jsonify(ok=False, output="Prompt cannot be empty."), 400
    cdp_url = str(data.get("cdp_url", "http://localhost:9222")).strip()

    def generate():
        for event in run_gemini_automation(
            prompt=prompt_text,
            cdp_url=cdp_url,
        ):
            yield event

    return Response(generate(), mimetype="text/event-stream")


@app.post("/run/step5a-grok")
def run_step5a_grok_endpoint() -> Response:
    data = request.get_json(silent=True) or {}
    prompt_text = str(data.get("prompt", "")).strip()
    if not prompt_text:
        return jsonify(ok=False, output="Prompt cannot be empty."), 400
    cdp_url = str(data.get("cdp_url", "http://localhost:9222")).strip()

    def generate():
        for event in run_grok_automation(
            prompt=prompt_text,
            cdp_url=cdp_url,
        ):
            yield event

    return Response(generate(), mimetype="text/event-stream")


@app.post("/api/launch-chrome")
def api_launch_chrome() -> Response:
    chrome_path = (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    )
    if not Path(chrome_path).exists():
        return jsonify(ok=False, output="Chrome not found at expected path.")
    try:
        subprocess.Popen(
            [chrome_path, "--remote-debugging-port=9222"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        return jsonify(ok=False, output=str(exc))
    return jsonify(ok=True, output="Chrome launched with remote debugging on port 9222.")


@app.get("/api/check-cdp")
def api_check_cdp() -> Response:
    cdp_url = request.args.get("cdp_url", "http://localhost:9222")
    try:
        req = urllib.request.Request(f"{cdp_url}/json/version", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            info = json.loads(resp.read().decode())
            browser = info.get("Browser", "unknown")
            return jsonify(ok=True, output=f"Connected: {browser}")
    except Exception as exc:
        return jsonify(ok=False, output=f"Cannot reach CDP: {exc}")


def main() -> int:
    print("Starting server at http://127.0.0.1:5000")
    app.run(debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
