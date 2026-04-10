#!/usr/bin/env python3
import base64
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple


TARGET_PREFIXES = ("http://127.0.0.1", "http://localhost")
SUCCESS_RESULTS = ("SENT", "FILLED", "SENT_NO_FILE_INPUT", "FILLED_NO_FILE_INPUT")


def js_source(text: str, files: Optional[List[dict]] = None) -> str:
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    file_payload = base64.b64encode(json.dumps(files or [], ensure_ascii=False).encode("utf-8")).decode("ascii")
    return f"""
(() => {{
  const text = decodeURIComponent(escape(atob("{payload}")));
  const fileSpecs = JSON.parse(decodeURIComponent(escape(atob("{file_payload}"))));
  const findComposerTextarea = () =>
    document.querySelector('textarea[placeholder*="Message "]') ||
    document.querySelector('textarea[placeholder*="Message Assistant"]') ||
    document.querySelector('textarea') ||
    document.querySelector('input[placeholder*="Message "]');

  const findSendButton = () => {{
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((button) => {{
      const label = (button.getAttribute("aria-label") || button.textContent || "").trim();
      return /send|发送/i.test(label);
    }}) || null;
  }};

  const findAttachButton = () => {{
    const buttons = Array.from(document.querySelectorAll("button"));
    return buttons.find((button) => {{
      const label = (button.getAttribute("aria-label") || button.getAttribute("title") || button.textContent || "").trim();
      return /attach|file|upload|附件|文件|上传|paperclip|clip/i.test(label);
    }}) || null;
  }};

  const findFileInput = () => document.querySelector('input[type="file"]');

  const base64ToUint8Array = (b64) => {{
    const bin = atob(b64);
    const out = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i += 1) out[i] = bin.charCodeAt(i);
    return out;
  }};

  const attachFiles = (specs) => {{
    if (!Array.isArray(specs) || !specs.length) return "NO_FILES";
    let input = findFileInput();
    if (!input) {{
      const attachButton = findAttachButton();
      if (attachButton) attachButton.click();
      input = findFileInput();
    }}
    if (!input) return "NO_FILE_INPUT";
    const transfer = new DataTransfer();
    for (const spec of specs) {{
      if (!spec || !spec.name || !spec.data) continue;
      const bytes = base64ToUint8Array(spec.data);
      const file = new File([bytes], spec.name, {{ type: spec.mime || "application/octet-stream" }});
      transfer.items.add(file);
    }}
    input.files = transfer.files;
    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
    input.dispatchEvent(new Event("change", {{ bubbles: true }}));
    return transfer.files.length ? "FILES_ATTACHED" : "NO_FILES";
  }};

  const input = findComposerTextarea();
  if (!input) return "NO_INPUT";

  const fileStatus = attachFiles(fileSpecs);

  input.focus();
  if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {{
    input.value = text;
    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
    input.dispatchEvent(new Event("change", {{ bubbles: true }}));
  }} else if (input.isContentEditable) {{
    input.textContent = text;
    input.dispatchEvent(new Event("input", {{ bubbles: true }}));
  }} else {{
    return "BAD_INPUT";
  }}

  const button = findSendButton();
  if (button) {{
    button.click();
    window.setTimeout(() => {{
      if (input instanceof HTMLTextAreaElement || input instanceof HTMLInputElement) {{
        input.value = "";
        input.dispatchEvent(new Event("input", {{ bubbles: true }}));
        input.dispatchEvent(new Event("change", {{ bubbles: true }}));
      }} else if (input.isContentEditable) {{
        input.textContent = "";
        input.dispatchEvent(new Event("input", {{ bubbles: true }}));
      }}
    }}, 40);
    return fileStatus === "NO_FILE_INPUT" ? "SENT_NO_FILE_INPUT" : "SENT";
  }}

  input.dispatchEvent(new KeyboardEvent("keydown", {{ key: "Enter", code: "Enter", bubbles: true }}));
  input.dispatchEvent(new KeyboardEvent("keyup", {{ key: "Enter", code: "Enter", bubbles: true }}));
  return fileStatus === "NO_FILE_INPUT" ? "FILLED_NO_FILE_INPUT" : "FILLED";
}})();
""".strip()


def payload_from_argv(argv: List[str]) -> Tuple[str, List[dict]]:
    if len(argv) >= 3 and argv[1] == "--payload-file":
        data = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
        return str(data.get("text") or "").strip(), list(data.get("files") or [])
    text = (argv[1] if len(argv) > 1 else "").strip()
    return text, []


def run_osascript(script: str, arg: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script, arg],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or result.stderr or "").strip()
    return output or f"EXIT_{result.returncode}"


def safari_script() -> str:
    return r'''
on run argv
  set jsSource to item 1 of argv
  tell application "Safari"
    if not (exists window 1) then return "NO_WINDOW"
    repeat with w in windows
      repeat with t in tabs of w
        set u to URL of t
        if u starts with "http://127.0.0.1" or u starts with "http://localhost" then
          set current tab of w to t
          set index of w to 1
          activate
          delay 0.08
          return (do JavaScript jsSource in t)
        end if
      end repeat
    end repeat
  end tell
  return "NO_TAB"
end run
'''.strip()


def chrome_script() -> str:
    return r'''
on run argv
  set jsSource to item 1 of argv
  tell application "Google Chrome"
    if not (exists window 1) then return "NO_WINDOW"
    repeat with w in windows
      set tabCount to number of tabs in w
      repeat with i from 1 to tabCount
        set t to tab i of w
        set u to URL of t
        if u starts with "http://127.0.0.1" or u starts with "http://localhost" then
          set active tab index of w to i
          set index of w to 1
          activate
          delay 0.08
          return (execute t javascript jsSource)
        end if
      end repeat
    end repeat
  end tell
  return "NO_TAB"
end run
'''.strip()


def send_to_openclaw(text: str, files: Optional[List[dict]] = None) -> str:
    js = js_source(text, files)
    for script in (safari_script(), chrome_script()):
        result = run_osascript(script, js)
        if result not in ("NO_WINDOW", "NO_TAB", ""):
            return result
    return "NO_OPENCLAW_TAB"
