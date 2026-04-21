"""ChatGPT, Gemini & Grok automation via Playwright CDP.

Connects to the user's Chrome instance (launched with --remote-debugging-port),
opens ChatGPT/Gemini/Grok, selects a model, pastes a prompt, and monitors the DOM for
thinking/response completion. Yields SSE events with timing results.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Generator
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright, Page, Browser

# ---------------------------------------------------------------------------
# DOM selectors -- update these when ChatGPT's UI changes
# ---------------------------------------------------------------------------
PROMPT_TEXTAREA = "#prompt-textarea"
SEND_BUTTON_PRIMARY = '[data-testid="send-button"]'
SEND_BUTTON_FALLBACK = "button[aria-label='Send prompt']"
MODEL_SELECTOR = '[data-testid="model-selector"]'
STOP_BUTTON = '[data-testid="stop-button"]'

# Text patterns
THINKING_TEXT = "Thinking"
THOUGHT_FOR_TEXT = "Thought for"

# Timing
POLL_INTERVAL_MS = 500
CONTENT_STABLE_SECONDS = 3
MAX_WAIT_SECONDS = 600  # 10-minute timeout

ET = ZoneInfo("America/New_York")


def _sse(event: str, data: dict) -> str:
    """Format a single SSE message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _et_now() -> tuple[str, str]:
    """Return (MM/DD/YYYY, HH:MM AM/PM) in ET."""
    now = datetime.now(ET)
    date_str = now.strftime("%m/%d/%Y")
    time_str = now.strftime("%I:%M %p")
    return date_str, time_str


def _select_model(page: Page, model_name: str) -> bool:
    """Click the 'ChatGPT 5.2' dropdown and pick 'thinking'.

    The ChatGPT model selector shows three options: auto, instant, thinking.
    We need to click the selector button, then click the 'thinking' option.
    """
    try:
        # The button text is "ChatGPT 5.2" at the top of the page
        selector_btn = page.query_selector(MODEL_SELECTOR)
        if not selector_btn:
            selector_btn = page.query_selector("button:has-text('ChatGPT')")
        if not selector_btn:
            # Broad fallback: find any button with "5.2" or "gpt" in text
            for candidate in page.query_selector_all("button"):
                text = candidate.inner_text().lower()
                if "chatgpt" in text or "5.2" in text:
                    selector_btn = candidate
                    break
        if not selector_btn:
            return False

        selector_btn.click()
        page.wait_for_timeout(1500)

        # Look for the "thinking" option in the opened dropdown.
        # Try clicking any element whose visible text is exactly "Thinking"
        # (case-insensitive match).
        for sel in [
            "[role='option']",
            "[role='menuitem']",
            "[role='menuitemradio']",
            "li",
            "div[class]",
            "button",
            "span",
        ]:
            elements = page.query_selector_all(sel)
            for el in elements:
                try:
                    text = el.inner_text().strip().lower()
                except Exception:
                    continue
                if text == "thinking":
                    el.click()
                    page.wait_for_timeout(500)
                    return True

        # Close the dropdown if we couldn't find it
        page.keyboard.press("Escape")
        return False
    except Exception:
        return False


def _page_text_contains(page: Page, needle: str) -> bool:
    """Check if any visible text on the page contains *needle* (case-insensitive)."""
    try:
        return page.evaluate(
            "(needle) => document.body.innerText.toLowerCase().includes(needle.toLowerCase())",
            needle,
        )
    except Exception:
        return False


def _wait_for_thinking_start(page: Page, timeout_sec: float) -> bool:
    """Poll until the page contains 'Thinking' text (the spinner label)."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if _page_text_contains(page, THINKING_TEXT):
            return True
        page.wait_for_timeout(POLL_INTERVAL_MS)
    return False


def _wait_for_thinking_done(page: Page, timeout_sec: float) -> bool:
    """Poll until 'Thought for' text appears (replaces 'Thinking...')."""
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        if _page_text_contains(page, THOUGHT_FOR_TEXT):
            return True
        page.wait_for_timeout(POLL_INTERVAL_MS)
    return False


def _get_response_text(page: Page) -> str:
    """Extract the current assistant response text."""
    try:
        # Try multiple selectors for the response content
        for sel in [
            "[data-message-author-role='assistant'] .markdown",
            ".markdown.prose",
            ".agent-turn .markdown",
            ".message-content",
        ]:
            els = page.query_selector_all(sel)
            if els:
                return els[-1].inner_text()
    except Exception:
        pass
    return ""


def _wait_for_response_complete(page: Page, timeout_sec: float) -> bool:
    """Wait for the response to finish generating.

    Primary: wait for stop button to disappear.
    Fallback: content stability (no new content for CONTENT_STABLE_SECONDS).
    """
    deadline = time.monotonic() + timeout_sec

    # First check if stop button exists
    stop_btn = page.query_selector(STOP_BUTTON)
    if stop_btn:
        # Wait for it to disappear
        while time.monotonic() < deadline:
            stop_btn = page.query_selector(STOP_BUTTON)
            if not stop_btn:
                # Give a small buffer for final rendering
                page.wait_for_timeout(500)
                return True
            page.wait_for_timeout(POLL_INTERVAL_MS)

    # Fallback: content stability check
    last_text = _get_response_text(page)
    stable_since = time.monotonic()

    while time.monotonic() < deadline:
        page.wait_for_timeout(POLL_INTERVAL_MS)
        current_text = _get_response_text(page)
        if current_text != last_text:
            last_text = current_text
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= CONTENT_STABLE_SECONDS:
            return True

    return False


_CURSOR_JS = """\
(() => {
  if (document.getElementById('pw-cursor')) return;
  const dot = document.createElement('div');
  dot.id = 'pw-cursor';
  Object.assign(dot.style, {
    position: 'fixed', zIndex: '2147483647', pointerEvents: 'none',
    width: '20px', height: '20px', borderRadius: '50%',
    background: 'rgba(255, 40, 40, 0.7)', border: '2px solid #fff',
    boxShadow: '0 0 8px rgba(255,0,0,0.5)', transform: 'translate(-50%,-50%)',
    transition: 'left 0.05s linear, top 0.05s linear',
    left: '-100px', top: '-100px',
  });
  document.body.appendChild(dot);
  const ring = document.createElement('div');
  ring.id = 'pw-cursor-ring';
  Object.assign(ring.style, {
    position: 'fixed', zIndex: '2147483646', pointerEvents: 'none',
    width: '40px', height: '40px', borderRadius: '50%',
    border: '2px solid rgba(255,40,40,0.6)', transform: 'translate(-50%,-50%)',
    left: '-100px', top: '-100px', opacity: '0',
  });
  document.body.appendChild(ring);
  document.addEventListener('mousemove', e => {
    dot.style.left = e.clientX + 'px';
    dot.style.top = e.clientY + 'px';
  }, true);
  document.addEventListener('mousedown', e => {
    ring.style.left = e.clientX + 'px';
    ring.style.top = e.clientY + 'px';
    ring.style.opacity = '1';
    ring.style.transition = 'none';
    ring.style.width = '20px';
    ring.style.height = '20px';
    requestAnimationFrame(() => {
      ring.style.transition = 'all 0.4s ease-out';
      ring.style.width = '60px';
      ring.style.height = '60px';
      ring.style.opacity = '0';
    });
  }, true);
})();
"""


def _inject_cursor(page: Page) -> None:
    """Inject a visible cursor overlay into the page."""
    try:
        page.evaluate(_CURSOR_JS)
    except Exception:
        pass


def run_chatgpt_automation(
    prompt: str,
    cdp_url: str = "http://localhost:9222",
    model_name: str = "GPT-5.2",
) -> Generator[str, None, None]:
    """Run the full ChatGPT automation, yielding SSE event strings.

    Event types:
      status          - progress updates
      reasoning_done  - reasoning timer result
      inference_done  - total inference timer result
      complete        - final results with all timing data
      error           - something went wrong
    """
    browser: Browser | None = None
    page: Page | None = None

    try:
        yield _sse("status", {"message": "Connecting to Chrome via CDP..."})

        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(cdp_url)

        yield _sse("status", {"message": "Connected. Opening new tab..."})

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto("https://chatgpt.com", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        _inject_cursor(page)

        yield _sse("status", {"message": "ChatGPT loaded. Selecting model..."})

        # Select "thinking" mode — this is required
        model_selected = _select_model(page, model_name)
        if model_selected:
            yield _sse("status", {"message": "Thinking mode selected."})
        else:
            yield _sse("error", {
                "message": "FAILED: Could not select 'thinking' mode from the "
                           "model dropdown. Aborting. Make sure ChatGPT shows "
                           "the model selector at the top of the page."
            })
            return

        yield _sse("status", {"message": "Pasting prompt..."})

        # Focus and type into the prompt textarea
        textarea = page.wait_for_selector(PROMPT_TEXTAREA, timeout=10000)
        if not textarea:
            yield _sse("error", {"message": "Could not find prompt textarea."})
            return

        textarea.click()
        page.wait_for_timeout(300)
        page.keyboard.insert_text(prompt)
        page.wait_for_timeout(500)

        yield _sse("status", {"message": "Sending prompt..."})

        # Click send
        send_btn = page.query_selector(SEND_BUTTON_PRIMARY)
        if not send_btn:
            send_btn = page.query_selector(SEND_BUTTON_FALLBACK)
        if not send_btn:
            yield _sse("error", {"message": "Could not find send button."})
            return

        # Record timing
        date_str, time_str = _et_now()
        send_ts = time.monotonic()
        send_btn.click()

        yield _sse("status", {"message": "Prompt sent. Waiting for thinking to start..."})

        # Wait for thinking to begin
        thinking_started = _wait_for_thinking_start(page, timeout_sec=30)
        if thinking_started:
            yield _sse("status", {"message": "Model is thinking..."})
        else:
            yield _sse("status", {
                "message": "Did not detect thinking indicator. Continuing to wait for response..."
            })

        # Wait for thinking to complete
        reasoning_seconds: float | None = None
        if thinking_started:
            thinking_done = _wait_for_thinking_done(page, timeout_sec=MAX_WAIT_SECONDS)
            if thinking_done:
                reasoning_seconds = round(time.monotonic() - send_ts)
                yield _sse("reasoning_done", {
                    "message": f"Reasoning complete: {reasoning_seconds}s",
                    "reasoning_seconds": reasoning_seconds,
                })
            else:
                yield _sse("status", {
                    "message": "Thinking timeout. Waiting for response to complete..."
                })

        yield _sse("status", {"message": "Waiting for response to complete..."})

        # Wait for full response
        response_done = _wait_for_response_complete(page, timeout_sec=MAX_WAIT_SECONDS)
        total_seconds = round(time.monotonic() - send_ts)

        if response_done:
            yield _sse("inference_done", {
                "message": f"Response complete: {total_seconds}s total",
                "total_seconds": total_seconds,
            })
        else:
            yield _sse("status", {
                "message": f"Response may not be fully complete (timeout). Total so far: {total_seconds}s"
            })

        # Final results
        yield _sse("complete", {
            "message": "Automation complete.",
            "reasoning_seconds": reasoning_seconds,
            "total_seconds": total_seconds,
            "date": date_str,
            "time": time_str,
        })

    except Exception as exc:
        yield _sse("error", {"message": str(exc)})

    finally:
        # Don't close the page or browser - user may want to inspect
        pass


# ---------------------------------------------------------------------------
# Gemini automation
# ---------------------------------------------------------------------------
GEMINI_URL = "https://gemini.google.com/u/0/app?pageId=none"
GEMINI_SHOW_THINKING_TEXT = "show thinking"


def _gemini_select_pro(page: Page) -> bool:
    """Click the model dropdown in the input area and select 'Pro'.

    The model picker lives inside [data-test-id="bard-mode-menu-button"]
    and uses button.input-area-switch.  There is also a DISABLED "PRO"
    pill in the top bar that must NOT be clicked.
    """
    try:
        # Step 1: click the model picker button (inside the input area).
        # Use the specific data-test-id to avoid the disabled top-bar pill.
        dropdown = page.query_selector(
            '[data-test-id="bard-mode-menu-button"] button'
        )
        if not dropdown:
            dropdown = page.query_selector("button.input-area-switch")
        if not dropdown:
            return False

        dropdown.click()
        page.wait_for_timeout(1500)

        # Step 2: find and click the "Pro" option in the opened menu.
        clicked = page.evaluate("""\
        (() => {
            const all = document.querySelectorAll('*');
            for (const el of all) {
                if (el.offsetParent === null && el.style.position !== 'fixed') continue;
                const text = el.innerText || '';
                const firstLine = text.split('\\n')[0].trim().toLowerCase();
                if (firstLine !== 'pro') continue;
                if (text.length > 200) continue;
                // Menu item has subtitle like "Thinks longer..."
                if (text.split('\\n').length >= 2) {
                    el.click();
                    return true;
                }
            }
            // Fallback: small element with just "Pro" text
            for (const el of all) {
                if (el.offsetParent === null && el.style.position !== 'fixed') continue;
                const text = (el.innerText || '').trim();
                if (text.toLowerCase() === 'pro' && text.length < 10
                    && !el.disabled) {
                    el.click();
                    return true;
                }
            }
            return false;
        })()
        """)

        if clicked:
            page.wait_for_timeout(500)
            return True

        page.keyboard.press("Escape")
        return False
    except Exception:
        return False


def _gemini_get_response_text(page: Page) -> str:
    """Extract the current Gemini response text."""
    try:
        # Gemini renders model responses in message-content or model-response areas
        for sel in [
            ".model-response-text",
            ".response-content",
            ".markdown-main-panel",
            "model-response .markdown",
            "message-content",
            ".conversation-container .model-response",
        ]:
            els = page.query_selector_all(sel)
            if els:
                return els[-1].inner_text()
        # Broad fallback: get all text from the response area
        els = page.query_selector_all("[class*='response']")
        if els:
            return els[-1].inner_text()
    except Exception:
        pass
    return ""


def _gemini_wait_for_output_start(page: Page, timeout_sec: float) -> bool:
    """Wait until Gemini starts producing visible output text.

    For Pro model, thinking starts immediately after sending. The reasoning
    phase ends when the model starts printing output text.
    """
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        # Check if "show thinking" text appeared (confirms thinking ended)
        if _page_text_contains(page, GEMINI_SHOW_THINKING_TEXT):
            return True
        # Also check if response text has started appearing
        text = _gemini_get_response_text(page)
        if text.strip():
            return True
        page.wait_for_timeout(POLL_INTERVAL_MS)
    return False


def _gemini_wait_for_response_complete(page: Page, timeout_sec: float) -> bool:
    """Wait for Gemini response to finish via content stability."""
    deadline = time.monotonic() + timeout_sec
    last_text = _gemini_get_response_text(page)
    stable_since = time.monotonic()

    while time.monotonic() < deadline:
        page.wait_for_timeout(POLL_INTERVAL_MS)
        current_text = _gemini_get_response_text(page)
        if current_text != last_text:
            last_text = current_text
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= CONTENT_STABLE_SECONDS:
            return True

    return False


def run_gemini_automation(
    prompt: str,
    cdp_url: str = "http://localhost:9222",
) -> Generator[str, None, None]:
    """Run Gemini Pro automation, yielding SSE event strings.

    Gemini Pro always reasons on send. Reasoning ends when output text starts
    appearing (or "show thinking" text appears). Timer logic:
      - reasoning_seconds = send -> first output text / "show thinking"
      - total_seconds = send -> response fully complete
    """
    try:
        yield _sse("status", {"message": "Connecting to Chrome via CDP..."})

        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(cdp_url)

        yield _sse("status", {"message": "Connected. Opening Gemini..."})

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto(GEMINI_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        _inject_cursor(page)

        yield _sse("status", {"message": "Gemini loaded. Selecting Pro model..."})

        # Select Pro model — required
        pro_selected = _gemini_select_pro(page)
        if pro_selected:
            yield _sse("status", {"message": "Pro model selected."})
        else:
            yield _sse("error", {
                "message": "FAILED: Could not select 'Pro' from the model "
                           "dropdown. Aborting. Make sure you are logged into "
                           "Gemini and the model dropdown is visible."
            })
            return

        yield _sse("status", {"message": "Pasting prompt..."})

        # Find and fill the prompt input
        # Gemini uses a Quill rich-text editor (contenteditable .ql-editor)
        textarea = None
        for sel in [
            "rich-textarea .ql-editor",
            ".ql-editor[contenteditable='true']",
            "[contenteditable='true'][aria-label*='prompt' i]",
            "[contenteditable='true'][aria-label*='Gemini' i]",
            ".ql-editor",
            "[contenteditable='true']",
        ]:
            textarea = page.query_selector(sel)
            if textarea:
                break

        if not textarea:
            yield _sse("error", {"message": "Could not find Gemini prompt input."})
            return

        textarea.click()
        page.wait_for_timeout(300)
        page.keyboard.insert_text(prompt)
        page.wait_for_timeout(500)

        yield _sse("status", {"message": "Sending prompt..."})

        # Find and click the send button
        send_btn = None
        for sel in [
            "button[aria-label*='Send' i]",
            "button[aria-label*='send' i]",
            "button.send-button",
            "[data-mat-icon-name='send']",
        ]:
            send_btn = page.query_selector(sel)
            if send_btn:
                break

        if not send_btn:
            # Fallback: find button with send icon or text
            for candidate in page.query_selector_all("button"):
                try:
                    label = candidate.get_attribute("aria-label") or ""
                    text = candidate.inner_text().strip().lower()
                except Exception:
                    continue
                if "send" in label.lower() or "send" in text:
                    send_btn = candidate
                    break

        if not send_btn:
            yield _sse("error", {"message": "Could not find Gemini send button."})
            return

        # Record timing — reasoning starts immediately for Pro
        date_str, time_str = _et_now()
        send_ts = time.monotonic()
        send_btn.click()

        yield _sse("status", {
            "message": "Prompt sent. Pro model is thinking (reasoning starts now)..."
        })

        # Wait for reasoning to end (output text starts appearing or "show thinking")
        reasoning_seconds: float | None = None
        output_started = _gemini_wait_for_output_start(
            page, timeout_sec=MAX_WAIT_SECONDS
        )
        if output_started:
            reasoning_seconds = round(time.monotonic() - send_ts)
            yield _sse("reasoning_done", {
                "message": f"Reasoning complete: {reasoning_seconds}s",
                "reasoning_seconds": reasoning_seconds,
            })
        else:
            yield _sse("status", {
                "message": "Could not detect reasoning end. Continuing..."
            })

        yield _sse("status", {"message": "Waiting for response to complete..."})

        # Wait for full response
        response_done = _gemini_wait_for_response_complete(
            page, timeout_sec=MAX_WAIT_SECONDS
        )
        total_seconds = round(time.monotonic() - send_ts)

        if response_done:
            yield _sse("inference_done", {
                "message": f"Response complete: {total_seconds}s total",
                "total_seconds": total_seconds,
            })
        else:
            yield _sse("status", {
                "message": f"Response may not be fully complete (timeout). "
                           f"Total so far: {total_seconds}s"
            })

        yield _sse("complete", {
            "message": "Automation complete.",
            "reasoning_seconds": reasoning_seconds,
            "total_seconds": total_seconds,
            "date": date_str,
            "time": time_str,
        })

    except Exception as exc:
        yield _sse("error", {"message": str(exc)})

    finally:
        pass


# ---------------------------------------------------------------------------
# Grok automation
# ---------------------------------------------------------------------------
GROK_URL = "https://grok.com"
GROK_THINKING_TEXT = "thinking"
GROK_THOUGHT_FOR_TEXT = "thought for"


def _grok_select_thinking(page: Page) -> bool:
    """Click the model dropdown near the send button and select 'Grok 4.1 Thinking'.

    Grok has a model picker next to the send button. We need to open it and
    pick the option that says "Grok 4.1 Thinking" (or similar).
    """
    try:
        # Look for the model selector dropdown button.
        # Grok typically shows the current model name in a button near the input.
        dropdown = None
        for sel in [
            "button[data-testid='model-selector']",
            "button[aria-haspopup='listbox']",
            "button[aria-haspopup='menu']",
            "button[aria-haspopup='true']",
        ]:
            candidates = page.query_selector_all(sel)
            for c in candidates:
                try:
                    text = c.inner_text().strip().lower()
                except Exception:
                    continue
                if "grok" in text or "model" in text:
                    dropdown = c
                    break
            if dropdown:
                break

        # Fallback: find any button with "grok" in its text
        if not dropdown:
            for candidate in page.query_selector_all("button"):
                try:
                    text = candidate.inner_text().strip().lower()
                except Exception:
                    continue
                if "grok" in text and len(text) < 50:
                    dropdown = candidate
                    break

        if not dropdown:
            return False

        dropdown.click()
        page.wait_for_timeout(1500)

        # Now find and click the "Grok 4.1 Thinking" option
        clicked = page.evaluate("""\
        (() => {
            const all = document.querySelectorAll('*');
            // First pass: look for element containing "thinking" and "4.1"
            for (const el of all) {
                if (el.offsetParent === null && el.style.position !== 'fixed'
                    && el.style.position !== 'absolute') continue;
                const text = (el.innerText || '').toLowerCase();
                if (text.includes('thinking') && text.includes('4.1') && text.length < 200) {
                    el.click();
                    return true;
                }
            }
            // Second pass: look for just "thinking" in a dropdown-like context
            for (const el of all) {
                if (el.offsetParent === null && el.style.position !== 'fixed'
                    && el.style.position !== 'absolute') continue;
                const text = (el.innerText || '').trim().toLowerCase();
                if (text.includes('thinking') && text.length < 100) {
                    el.click();
                    return true;
                }
            }
            return false;
        })()
        """)

        if clicked:
            page.wait_for_timeout(500)
            return True

        page.keyboard.press("Escape")
        return False
    except Exception:
        return False


def _grok_get_response_text(page: Page) -> str:
    """Extract the current Grok response text."""
    try:
        for sel in [
            "[data-testid='assistant-message']",
            ".message-bubble.assistant",
            "[class*='assistant'] [class*='message']",
            "[class*='response']",
            "[class*='markdown']",
        ]:
            els = page.query_selector_all(sel)
            if els:
                return els[-1].inner_text()
    except Exception:
        pass
    return ""


def _grok_wait_for_response_complete(page: Page, timeout_sec: float) -> bool:
    """Wait for Grok response to finish.

    Primary: check if a stop/cancel button disappears.
    Fallback: content stability (no new text for CONTENT_STABLE_SECONDS).
    """
    deadline = time.monotonic() + timeout_sec

    # Check for a stop button first
    stop_btn = None
    for sel in [
        "button[aria-label*='Stop' i]",
        "button[aria-label*='Cancel' i]",
        "button[data-testid='stop-button']",
    ]:
        stop_btn = page.query_selector(sel)
        if stop_btn:
            break

    if stop_btn:
        while time.monotonic() < deadline:
            still_there = False
            for sel in [
                "button[aria-label*='Stop' i]",
                "button[aria-label*='Cancel' i]",
                "button[data-testid='stop-button']",
            ]:
                if page.query_selector(sel):
                    still_there = True
                    break
            if not still_there:
                page.wait_for_timeout(500)
                return True
            page.wait_for_timeout(POLL_INTERVAL_MS)

    # Fallback: content stability
    last_text = _grok_get_response_text(page)
    stable_since = time.monotonic()

    while time.monotonic() < deadline:
        page.wait_for_timeout(POLL_INTERVAL_MS)
        current_text = _grok_get_response_text(page)
        if current_text != last_text:
            last_text = current_text
            stable_since = time.monotonic()
        elif time.monotonic() - stable_since >= CONTENT_STABLE_SECONDS:
            return True

    return False


def run_grok_automation(
    prompt: str,
    cdp_url: str = "http://localhost:9222",
) -> Generator[str, None, None]:
    """Run Grok 4.1 Thinking automation, yielding SSE event strings.

    Flow:
      1. Open grok.com
      2. Select "Grok 4.1 Thinking" from model dropdown
      3. Paste prompt and send
      4. Wait for "thinking" indicator, then "thought for" to get reasoning time
      5. Wait for response to complete for total time
    """
    try:
        yield _sse("status", {"message": "Connecting to Chrome via CDP..."})

        pw = sync_playwright().start()
        browser = pw.chromium.connect_over_cdp(cdp_url)

        yield _sse("status", {"message": "Connected. Opening Grok..."})

        context = browser.contexts[0] if browser.contexts else browser.new_context()
        page = context.new_page()
        page.goto(GROK_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)
        _inject_cursor(page)

        yield _sse("status", {"message": "Grok loaded. Selecting Grok 4.1 Thinking..."})

        # Select Grok 4.1 Thinking — required
        model_selected = _grok_select_thinking(page)
        if model_selected:
            yield _sse("status", {"message": "Grok 4.1 Thinking selected."})
        else:
            yield _sse("error", {
                "message": "FAILED: Could not select 'Grok 4.1 Thinking' from the "
                           "model dropdown. Aborting. Make sure you are logged into "
                           "Grok and the model dropdown is visible near the send button."
            })
            return

        yield _sse("status", {"message": "Pasting prompt..."})

        # Find and fill the prompt input
        textarea = None
        for sel in [
            "textarea",
            "[contenteditable='true']",
            "[role='textbox']",
            "input[type='text']",
        ]:
            textarea = page.query_selector(sel)
            if textarea:
                break

        if not textarea:
            yield _sse("error", {"message": "Could not find Grok prompt input."})
            return

        textarea.click()
        page.wait_for_timeout(300)
        page.keyboard.insert_text(prompt)
        page.wait_for_timeout(500)

        yield _sse("status", {"message": "Sending prompt..."})

        # Find and click the send button
        send_btn = None
        for sel in [
            "button[aria-label*='Send' i]",
            "button[aria-label*='send' i]",
            "button[data-testid='send-button']",
            "button[type='submit']",
        ]:
            send_btn = page.query_selector(sel)
            if send_btn:
                break

        # Fallback: find button with send-like attributes
        if not send_btn:
            for candidate in page.query_selector_all("button"):
                try:
                    label = candidate.get_attribute("aria-label") or ""
                    text = candidate.inner_text().strip().lower()
                except Exception:
                    continue
                if "send" in label.lower() or "send" in text:
                    send_btn = candidate
                    break

        if not send_btn:
            # Last resort: try pressing Enter to send
            yield _sse("status", {"message": "No send button found, trying Enter key..."})
            date_str, time_str = _et_now()
            send_ts = time.monotonic()
            page.keyboard.press("Enter")
        else:
            date_str, time_str = _et_now()
            send_ts = time.monotonic()
            send_btn.click()

        yield _sse("status", {
            "message": "Prompt sent. Waiting for thinking to start..."
        })

        # Wait for thinking to begin (look for "thinking" text on the page)
        thinking_started = _wait_for_thinking_start(page, timeout_sec=30)
        if thinking_started:
            yield _sse("status", {"message": "Grok is thinking..."})
        else:
            yield _sse("status", {
                "message": "Did not detect thinking indicator. Continuing to wait for response..."
            })

        # Wait for thinking to complete (look for "thought for" text)
        reasoning_seconds: float | None = None
        if thinking_started:
            thinking_done = _wait_for_thinking_done(page, timeout_sec=MAX_WAIT_SECONDS)
            if thinking_done:
                reasoning_seconds = round(time.monotonic() - send_ts)
                yield _sse("reasoning_done", {
                    "message": f"Reasoning complete: {reasoning_seconds}s",
                    "reasoning_seconds": reasoning_seconds,
                })
            else:
                yield _sse("status", {
                    "message": "Thinking timeout. Waiting for response to complete..."
                })

        yield _sse("status", {"message": "Waiting for response to complete..."})

        # Wait for full response
        response_done = _grok_wait_for_response_complete(
            page, timeout_sec=MAX_WAIT_SECONDS
        )
        total_seconds = round(time.monotonic() - send_ts)

        if response_done:
            yield _sse("inference_done", {
                "message": f"Response complete: {total_seconds}s total",
                "total_seconds": total_seconds,
            })
        else:
            yield _sse("status", {
                "message": f"Response may not be fully complete (timeout). "
                           f"Total so far: {total_seconds}s"
            })

        yield _sse("complete", {
            "message": "Automation complete.",
            "reasoning_seconds": reasoning_seconds,
            "total_seconds": total_seconds,
            "date": date_str,
            "time": time_str,
        })

    except Exception as exc:
        yield _sse("error", {"message": str(exc)})

    finally:
        pass
