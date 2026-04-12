#!/usr/bin/env python3
import base64
import fcntl
import json
import mimetypes
import os
import re
import signal
import subprocess
import shutil
import socket
import threading
import time
import traceback
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Optional
from urllib.error import URLError
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import Request, urlopen

import objc
from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSColor,
    NSEvent,
    NSFloatingWindowLevel,
    NSMakeRect,
    NSScreen,
    NSStatusBar,
    NSVariableStatusItemLength,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowStyleMaskBorderless,
    NSOpenPanel,
    NSPanel,
    NSView,
)
from Foundation import NSObject, NSTimer, NSURL
from WebKit import WebView
from runtime_config import load_runtime_config
from core.pet_core import PetRuntime

RUNTIME = load_runtime_config()
PET_API = f"{RUNTIME['pet_api_base']}/pet"
PET_ACTION_API = f"{RUNTIME['pet_api_base']}/pet/action"
LEARNING_SCRIPT = str(RUNTIME["openclaw_home"] / "scripts" / "openclaw-learning-intake.sh")
SCREENSHOT_SCRIPT = str(RUNTIME["openclaw_home"] / "scripts" / "openclaw-screenshot-intake.sh")
DIRECT_SEND_SCRIPT = str(RUNTIME["direct_send_script"])
STATE_DIR = RUNTIME["openclaw_home"] / "workspace" / "memory"
POSITION_FILE = STATE_DIR / "companion-position.json"
PID_FILE = Path("/tmp/littleclaw-companion.pid")
LOG_FILE = Path("/tmp/littleclaw-webview.log")
DEBUG_TOOL_LOG = Path("/tmp/littleclaw-debug-tool.log")
PID_HANDLE = None
LEARNING_REQ_DIR = STATE_DIR.parent / "learning-lab" / "requests"
LEARNING_SHOT_DIR = STATE_DIR.parent / "learning-lab" / "screenshots"
LEARNING_RESULT_DIR = STATE_DIR.parent / "learning-lab" / "results"
SESSION_DIR = RUNTIME["openclaw_home"] / "agents" / "main" / "sessions"
UI_DIR = RUNTIME["ui_root"]
DEBUG_TOOL = Path(__file__).resolve().parent / "pet_debug_tool.py"
DEBUG_SERVER = Path(__file__).resolve().parent / "pet_debug_server.py"
DEBUG_HOST = "127.0.0.1"
DEBUG_PORT = 18796
DEBUG_URL = f"http://{DEBUG_HOST}:{DEBUG_PORT}/"

C_COLLAPSED_W = 196
C_COLLAPSED_H = 132
COLLAPSED_W = C_COLLAPSED_W
COLLAPSED_H = C_COLLAPSED_H
EXPANDED_W = 500
EXPANDED_H = 560
DEBUG_W = 336
DEBUG_H = 404

PRESET_ROOT = Path(RUNTIME["presets_home"])
FALLBACK_PRESET_ROOT = Path(__file__).resolve().parent / "presets"
PET_STATE_FILE = STATE_DIR / "pet-state.json"
PET_INSTALL_FILE = STATE_DIR / "pet-install-id.txt"
PET_RUNTIME = PetRuntime(
    state_file=PET_STATE_FILE,
    install_seed_file=PET_INSTALL_FILE,
    preset_root=PRESET_ROOT,
    fallback_preset_root=FALLBACK_PRESET_ROOT,
)


def pet_name(pet: Optional[dict], fallback: str = "当前伙伴") -> str:
    return str((pet or {}).get("name") or fallback)


def action_feedback(action: str, phase: str, message: str, **extra):
    title_map = {
        ("learn", "blocked"): "现在先别学习",
        ("learn", "queued"): "学习链路已提交",
        ("learn", "waiting_reply"): "学习链路处理中",
        ("learn", "failed"): "学习暂未送达",
        ("send", "blocked"): "现在先别发送",
        ("send", "queued"): "消息已递送",
        ("send", "waiting_reply"): "正在等回执",
        ("send", "failed"): "消息未送达",
        ("screenshot", "blocked"): "现在先别截图",
        ("screenshot", "staged"): "截图已暂存",
        ("pick_files", "staged"): "附件已接住",
        ("pick_files", "failed"): "没有选择附件",
        ("reply", "replied"): "带回真实回复",
    }
    tone_map = {
        "blocked": "notify",
        "queued": "notify",
        "waiting_reply": "busy",
        "failed": "notify",
        "staged": "notify",
        "replied": "notify",
    }
    icon_map = {
        "learn": "⌘",
        "send": "➜",
        "screenshot": "◉",
        "pick_files": "📎",
        "reply": "↩",
    }
    payload = {
        "phase": phase,
        "headline": title_map.get((action, phase), "处理完成"),
        "tone": tone_map.get(phase, "notify"),
        "icon": icon_map.get(action, "•"),
        "message": message,
    }
    payload.update(extra)
    return payload


def log(message: str):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(message + "\n")
    except Exception:
        pass


def read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def build_send_payload(text: str, files: Optional[List[dict]] = None) -> str:
    normalized = []
    for item in files or []:
        path = str(item.get("path") or "").strip()
        inline_data = str(item.get("data") or "").strip()
        mime = str(item.get("mime") or "").strip()
        if inline_data:
            if inline_data.startswith("data:"):
                try:
                    header, encoded = inline_data.split(",", 1)
                    mime = mime or header.split(";")[0].split(":", 1)[1]
                    raw = base64.b64decode(encoded)
                except Exception:
                    continue
            else:
                try:
                    raw = base64.b64decode(inline_data)
                except Exception:
                    continue
        else:
            if not path:
                continue
            file_path = Path(path)
            if not file_path.exists() or not file_path.is_file():
                continue
            try:
                raw = file_path.read_bytes()
            except Exception:
                continue
            guessed_mime, _ = mimetypes.guess_type(file_path.name)
            mime = mime or guessed_mime or "application/octet-stream"
        normalized.append(
            {
                "name": item.get("name") or (Path(path).name if path else f"clipboard-{len(normalized)+1}.png"),
                "path": path,
                "mime": mime or "application/octet-stream",
                "data": base64.b64encode(raw).decode("ascii"),
            }
        )
    payload = {"text": text, "files": normalized}
    with NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".json") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        return fh.name


def run_direct_send(text: str, files: Optional[List[dict]] = None):
    payload_path = build_send_payload(text, files)
    try:
        return subprocess.run(
            ["/usr/bin/python3", DIRECT_SEND_SCRIPT, "--payload-file", payload_path],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        try:
            Path(payload_path).unlink(missing_ok=True)
        except Exception:
            pass


def build_agent_prompt(kind: str, request_path: str, topic: str, goal: str, body: str) -> str:
    header = (
        "这是来自 LittleClaw Companion 的真实学习请求，请直接继续处理，不要重复转述任务。"
        if kind == "learn"
        else "这是来自 LittleClaw Companion 的截图协作请求，请直接继续处理，不要重复转述任务。"
    )
    deliverables = (
        "请优先给出：\n"
        "1. 关键结论或可用线索\n"
        "2. 可执行的下一步方案 / 实验设计 / 处理建议\n"
        "3. 如果适合，补充可继续迭代的方法或 skill 草稿方向"
        if kind == "learn"
        else "请优先给出：\n"
        "1. 对截图和上下文的关键判断\n"
        "2. 明确的下一步处理建议\n"
        "3. 如果需要，指出还缺哪些信息"
    )
    return (
        f"{header}\n\n"
        f"请求文件：{request_path}\n"
        f"主题：{topic}\n"
        f"目标：{goal}\n\n"
        "请先直接阅读上面的请求文件；如果消息里带了本地文件路径，也请一并读取。\n"
        "在当前会话里直接开始处理，不要只复述请求内容。\n\n"
        f"{deliverables}"
    )


def build_learning_request_doc(topic: str, goal: str, screenshot_context: str = "", asset_context: str = "") -> str:
    lines = [
        "# 学习委托",
        "",
        f"- 主题：{topic}",
        f"- 目标：{goal or '查找资料、形成方案，并整理成后续可持续迭代的研究记录。'}",
        f"- 提交时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## 这次希望你完成",
        "",
        "1. 快速厘清问题背景、关键概念和可查方向",
        "2. 找到高价值资料、文献、案例或现有方案",
        "3. 给出可以直接继续推进的下一步建议",
        "",
        "## 输出优先级",
        "",
        "- 先给结论摘要",
        "- 再给依据、资料线索或实验/实现建议",
        "- 如果合适，再补可继续沉淀的方法、流程或 skill 方向",
    ]
    if screenshot_context:
        lines.extend(["", screenshot_context.strip()])
    if asset_context:
        lines.extend(["", asset_context.strip()])
    return "\n".join(lines).strip() + "\n"


def materialize_asset_refs(files: Optional[List[dict]] = None) -> List[dict]:
    refs = []
    asset_dir = LEARNING_REQ_DIR / "inline-assets"
    asset_dir.mkdir(parents=True, exist_ok=True)
    for index, item in enumerate(files or [], start=1):
        path = str((item or {}).get("path") or "").strip()
        name = str((item or {}).get("name") or "").strip() or f"asset-{index}"
        mime = str((item or {}).get("mime") or "").strip() or "application/octet-stream"
        resolved = ""
        if path:
            file_path = Path(path)
            if file_path.exists() and file_path.is_file():
                resolved = str(file_path)
        elif (item or {}).get("data"):
            inline_data = str(item.get("data") or "").strip()
            try:
                if inline_data.startswith("data:"):
                    header, encoded = inline_data.split(",", 1)
                    mime = mime or header.split(";")[0].split(":", 1)[1]
                    raw = base64.b64decode(encoded)
                else:
                    raw = base64.b64decode(inline_data)
            except Exception:
                continue
            suffix = Path(name).suffix or mimetypes.guess_extension(mime) or ".bin"
            target = asset_dir / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}{suffix}"
            try:
                target.write_bytes(raw)
                resolved = str(target)
            except Exception:
                continue
        if resolved:
            refs.append({"name": name, "path": resolved, "mime": mime})
    return refs


def build_asset_reference_block(files: Optional[List[dict]] = None) -> str:
    refs = materialize_asset_refs(files)
    if not refs:
        return ""
    lines = ["附带参考文件（如果网页附件没有挂上，请直接读取这些本地文件）:"]
    for ref in refs:
        lines.append(f"- {ref['name']}: {ref['path']}")
    return "\n".join(lines)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_ts(value: str):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def extract_assistant_text(message: dict) -> str:
    if not isinstance(message, dict):
        return ""
    payload = message.get("message") or {}
    if payload.get("role") != "assistant":
        return ""
    parts = []
    for item in payload.get("content") or []:
        if item.get("type") == "text":
            text = (item.get("text") or "").strip()
            if text:
                parts.append(text)
    return "\n\n".join(parts).strip()


def fetch_json(url: str):
    try:
        with urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError:
        return None
    except Exception:
        return None


def post_action(action: str, extra: dict | None = None):
    body = {"action": action}
    if extra:
        body.update(extra)
    payload = json.dumps(body).encode("utf-8")
    request = Request(PET_ACTION_API, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception:
        return None


def ensure_single_instance():
    global PID_HANDLE
    try:
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        handle = PID_FILE.open("a+", encoding="utf-8")
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.seek(0)
            holder = handle.read().strip() or "unknown"
            log(f"another companion instance already owns pid lock: {holder}")
            handle.close()
            raise SystemExit(0)
        handle.seek(0)
        handle.truncate()
        handle.write(str(os.getpid()))
        handle.flush()
        PID_HANDLE = handle
    except Exception as exc:
        log(f"ensure_single_instance failed: {exc}")


class DragHandleView(NSView):
    def initWithFrame_controller_(self, frame, controller):
        self = objc.super(DragHandleView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.controller = controller
        self.startWindowOrigin = None
        self.startMouse = None
        self.dragged = False
        return self

    def mouseDown_(self, event):
        window = self.window()
        if window is None:
            return
        frame = window.frame()
        self.startWindowOrigin = (frame.origin.x, frame.origin.y)
        point = NSEvent.mouseLocation()
        self.startMouse = (point.x, point.y)
        self.dragged = False

    def mouseDragged_(self, event):
        window = self.window()
        if window is None or self.startWindowOrigin is None or self.startMouse is None:
            return
        point = NSEvent.mouseLocation()
        dx = point.x - self.startMouse[0]
        dy = point.y - self.startMouse[1]
        if abs(dx) > 3 or abs(dy) > 3:
            self.dragged = True
        new_x = self.startWindowOrigin[0] + dx
        new_y = self.startWindowOrigin[1] + dy
        window.setFrameOrigin_((new_x, new_y))

    def mouseUp_(self, event):
        if self.controller is not None:
            self.controller.save_position()
            if not self.dragged and not self.controller.expanded:
                self.controller.setExpanded_(True)
        self.startWindowOrigin = None
        self.startMouse = None
        self.dragged = False


class KeyablePanel(NSPanel):
    def canBecomeKeyWindow(self):
        return True

    def canBecomeMainWindow(self):
        return True


class CompanionController(NSObject):
    def init(self):
        self = objc.super(CompanionController, self).init()
        if self is None:
            return None
        self.window = None
        self.statusItem = None
        self.webView = None
        self.rootView = None
        self.dragView = None
        self.debugWindow = None
        self.debugWebView = None
        self.pageReady = False
        self.debugPageReady = False
        self.pet = {}
        self.hoverTicks = 0
        self.leaveTicks = 0
        self.expanded = False
        self.queueSummary = "学习队列还很安静。"
        self.latestReply = ""
        self.pendingReply = False
        self.pendingAction = ""
        self.stagedScreenshots = []
        self.debugPinned = False
        self.lastDebugRefreshAt = 0.0
        self.needsDeferredPush = False
        LEARNING_RESULT_DIR.mkdir(parents=True, exist_ok=True)
        return self

    def applicationDidFinishLaunching_(self, notification):
        log("applicationDidFinishLaunching")
        self.buildStatusItem()
        self.buildWindow()
        self.buildDebugWindow()
        self.loadPage()
        self.loadDebugPage()
        self.refresh_(None)
        self.showWindow_()
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(10.0, self, "refresh:", None, True)
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.28, self, "hoverTick:", None, True)

    @objc.python_method
    def buildStatusItem(self):
        self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self.statusItem.button()
        if button is not None:
            button.setTitle_("🦞 LittleClaw")
            button.setToolTip_("LittleClaw Companion")
            button.setTarget_(self)
            button.setAction_("toggleWindow:")

    @objc.python_method
    def display_emoji_for_pet(self, pet):
        species = str((pet or {}).get("species_id") or "lobster")
        explicit = str((pet or {}).get("emoji") or "").strip()
        fallback = {
            "lobster": "🦞",
            "sprite": "✨",
            "mecha": "🤖",
        }.get(species, "🦞")
        if explicit and explicit != "🦞":
            return explicit
        return fallback

    @objc.python_method
    def refresh_window_titles(self):
        pet = self.pet or {}
        name = str(pet.get("name") or "LittleClaw")
        stage = str(pet.get("stage_title") or pet.get("species_title") or "").strip()
        emoji = self.display_emoji_for_pet(pet)
        if self.statusItem and self.statusItem.button() is not None:
            self.statusItem.button().setTitle_(f"{emoji} {name}")
            tooltip = f"{name} · {stage}" if stage else name
            self.statusItem.button().setToolTip_(tooltip)
        if self.window is not None:
            title = f"{name} · {stage}" if stage else name
            self.window.setTitle_(title)

    @objc.python_method
    def buildWindow(self):
        frame = self.default_frame(COLLAPSED_W, COLLAPSED_H)
        self.window = KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        self.window.setTitle_("LittleClaw Companion")
        self.window.setFloatingPanel_(True)
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setHidesOnDeactivate_(False)
        self.window.setReleasedWhenClosed_(False)
        self.window.setBecomesKeyOnlyIfNeeded_(False)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        self.rootView = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, COLLAPSED_W, COLLAPSED_H))
        self.webView = WebView.alloc().initWithFrame_frameName_groupName_(NSMakeRect(0, 0, COLLAPSED_W, COLLAPSED_H), None, None)
        self.webView.setFrameLoadDelegate_(self)
        self.webView.setPolicyDelegate_(self)
        self.webView.setDrawsBackground_(False)
        self.rootView.addSubview_(self.webView)
        self.dragView = DragHandleView.alloc().initWithFrame_controller_(NSMakeRect(0, 0, COLLAPSED_W, COLLAPSED_H), self)
        self.dragView.setWantsLayer_(True)
        self.dragView.layer().setBackgroundColor_(NSColor.clearColor().CGColor())
        self.rootView.addSubview_(self.dragView)
        self.window.setContentView_(self.rootView)

    @objc.python_method
    def buildDebugWindow(self):
        frame = self.default_frame(DEBUG_W, DEBUG_H)
        self.debugWindow = KeyablePanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame, NSWindowStyleMaskBorderless, NSBackingStoreBuffered, False
        )
        self.debugWindow.setTitle_("LittleClaw Debug")
        self.debugWindow.setFloatingPanel_(True)
        self.debugWindow.setLevel_(NSFloatingWindowLevel)
        self.debugWindow.setOpaque_(False)
        self.debugWindow.setBackgroundColor_(NSColor.clearColor())
        self.debugWindow.setHasShadow_(True)
        self.debugWindow.setHidesOnDeactivate_(False)
        self.debugWindow.setReleasedWhenClosed_(False)
        self.debugWindow.setBecomesKeyOnlyIfNeeded_(False)
        self.debugWindow.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        root = NSView.alloc().initWithFrame_(NSMakeRect(0, 0, DEBUG_W, DEBUG_H))
        self.debugWebView = WebView.alloc().initWithFrame_frameName_groupName_(NSMakeRect(0, 0, DEBUG_W, DEBUG_H), None, None)
        self.debugWebView.setFrameLoadDelegate_(self)
        self.debugWebView.setPolicyDelegate_(self)
        self.debugWebView.setDrawsBackground_(False)
        root.addSubview_(self.debugWebView)
        self.debugWindow.setContentView_(root)

    @objc.python_method
    def loadPage(self):
        html = (UI_DIR / "index.html").read_text(encoding="utf-8")
        debug_boot = f"<script>window.LITTLECLAW_DEBUG_ENABLED = {'true' if bool(RUNTIME.get('debug_ui_enabled', True)) else 'false'};</script>"
        if "</head>" in html:
            html = html.replace("</head>", f"{debug_boot}</head>", 1)
        else:
            html = debug_boot + html
        base = NSURL.fileURLWithPath_(str(UI_DIR) + "/")
        self.webView.mainFrame().loadHTMLString_baseURL_(html, base)

    @objc.python_method
    def loadDebugPage(self):
        if self.debugWebView is None:
            return
        html = (UI_DIR / "debug.html").read_text(encoding="utf-8")
        base = NSURL.fileURLWithPath_(str(UI_DIR) + "/")
        self.debugWebView.mainFrame().loadHTMLString_baseURL_(html, base)

    def webView_didFinishLoadForFrame_(self, webView, frame):
        if webView == self.debugWebView:
            self.debugPageReady = True
            self.pushDebugState()
            return
        self.pageReady = True
        self.applyCompactState()
        self.pushState()

    def webView_decidePolicyForNavigationAction_request_frame_decisionListener_(self, webView, actionInfo, request, frame, listener):
        try:
            url = str(request.URL())
            parsed = urlparse(url)
            if parsed.scheme == "littleclaw":
                params = parse_qs(parsed.query)
                action = params.get("action", [""])[0]
                topic = unquote(params.get("topic", [""])[0])
                goal = unquote(params.get("goal", [""])[0])
                assets_raw = unquote(params.get("assets", ["[]"])[0] or "[]")
                try:
                    assets = json.loads(assets_raw)
                except Exception:
                    assets = []
                self.dispatch_action(action, topic, goal, assets)
                listener.ignore()
                return
        except Exception as exc:
            log(f"policy delegate error: {exc}")
        listener.use()

    @objc.python_method
    def dispatch_action(self, action, topic, goal, assets=None):
        if action in ("feed", "play", "nap"):
            result = post_action(action)
            if isinstance(result, dict) and isinstance(result.get("pet"), dict):
                self.pet = result["pet"]
            self.notify_action_result(
                action,
                {
                    "pet": self.pet,
                    "blocked": bool(isinstance(result, dict) and result.get("blocked")),
                    "message": (
                        result.get("reason")
                        if isinstance(result, dict) and result.get("blocked")
                        else "这次照顾已经生效，状态和亲密会按新规则刷新。"
                    ),
                },
            )
            self.pushState()
            return
        if action == "ack_intro":
            result = post_action("acknowledge_intro")
            if isinstance(result, dict) and isinstance(result.get("pet"), dict):
                self.pet = result["pet"]
            self.notify_action_result(
                action,
                {
                    "pet": self.pet,
                    "ok": True,
                    "message": f"初次相遇已经记住了，之后{pet_name(self.pet)}会直接进入正常陪伴模式。",
                },
            )
            self.pushState()
            return
        if action == "expand":
            self.debugPinned = False
            self.setExpanded_(True)
            return
        if action == "collapse":
            self.debugPinned = False
            self.setExpanded_(False)
            return
        if action == "toggle_debug":
            if not bool(RUNTIME.get("debug_ui_enabled", True)):
                self.notify_action_result(
                    "toggle_debug",
                    {
                        "pet": self.pet,
                        "ok": False,
                        "message": "当前构建没有暴露调试入口。",
                    },
                )
                self.pushState()
                return
            self.debugPinned = True
            self.setExpanded_(True)
            self.launch_debug_tool()
            return
        if action == "close_debug":
            if self.debugWindow is not None:
                self.debugWindow.orderOut_(None)
            return
        if action == "debug_pet":
            self.apply_debug_pet(topic or "{}")
            self.pushState()
            return
        if action == "pick_files":
            self.open_file_picker()
            return
        if action == "learn":
            gate = post_action("learn_request", {"topic": topic or "", "goal": goal or ""})
            if isinstance(gate, dict) and isinstance(gate.get("pet"), dict):
                self.pet = gate["pet"]
            if isinstance(gate, dict) and gate.get("blocked"):
                self.notify_action_result(
                    "learn",
                    action_feedback(
                        "learn",
                        "blocked",
                        gate.get("reason") or f"{pet_name(self.pet)}现在太累了，先休息一下。",
                        topic=topic or "桌面 Companion 学习主题",
                        goal=goal or "持续学习、沉淀方案并整理 skill 草稿",
                        sent=False,
                        pending_reply=False,
                        blocked=True,
                    ),
                )
                self.pushState()
                return
            started_at = utc_now()
            result = subprocess.run(
                [LEARNING_SCRIPT, topic or "桌面 Companion 学习主题", goal or "持续学习、沉淀方案并整理 skill 草稿"],
                capture_output=True,
                text=True,
                check=False,
            )
            request_path = (result.stdout or "").strip().splitlines()[-1] if (result.stdout or "").strip() else ""
            sent_ok = False
            attach_warning = False
            staged_count = len(self.stagedScreenshots)
            if request_path:
                screenshot_context = self.screenshot_context_block() if self.stagedScreenshots else ""
                asset_context = build_asset_reference_block(assets)
                request_body = build_learning_request_doc(
                    topic or "桌面 Companion 学习主题",
                    goal or "持续学习、沉淀方案并整理 skill 草稿",
                    screenshot_context=screenshot_context,
                    asset_context=asset_context,
                )
                try:
                    Path(request_path).write_text(request_body, encoding="utf-8")
                except Exception as exc:
                    log(f"rewrite learning request failed: {exc}")
                agent_prompt = build_agent_prompt(
                    "learn",
                    request_path,
                    topic or "桌面 Companion 学习主题",
                    goal or "持续学习、沉淀方案并整理 skill 草稿",
                    request_body,
                )
                send_result = run_direct_send(agent_prompt, assets)
                sent_ok = send_result.returncode == 0
                attach_warning = "NO_FILE_INPUT" in ((send_result.stdout or "") + (send_result.stderr or ""))
                if sent_ok:
                    self.stagedScreenshots = []
                    self.pendingReply = True
                    self.pendingAction = "learn"
                    self.capture_agent_result_async("learn", request_path, topic or "桌面 Companion 学习主题", started_at)
            self.queueSummary = self.build_queue_summary(force_refresh=True)
            self.notify_action_result(
                "learn",
                action_feedback(
                    "learn",
                    "waiting_reply" if sent_ok else "failed",
                    ("学习请求已真正发到当前 OpenClaw 会话，但当前页面没有可用的文件入口；我已经把本地文件路径写进请求里，当前会话仍然可以直接读取。"
                    if attach_warning and assets and sent_ok
                    else "学习请求已真正发到当前 OpenClaw 会话，正在等待真实回复回执。")
                    if sent_ok
                    else "学习请求已落盘入队，但当前没有可直发的 OpenClaw 会话。",
                    topic=topic or "桌面 Companion 学习主题",
                    goal=goal or "持续学习、沉淀方案并整理 skill 草稿",
                    request_path=request_path,
                    staged_shots=staged_count,
                    sent=sent_ok,
                    pending_reply=sent_ok,
                    files_attached=bool(sent_ok and not attach_warning),
                    detail=(send_result.stdout or send_result.stderr or "").strip() if request_path else "",
                ),
            )
            self.pushState()
            return
        if action == "send":
            gate = post_action("send_message", {"text": topic or goal or ""})
            if isinstance(gate, dict) and isinstance(gate.get("pet"), dict):
                self.pet = gate["pet"]
            if isinstance(gate, dict) and gate.get("blocked"):
                self.notify_action_result(
                    "send",
                    action_feedback(
                        "send",
                        "blocked",
                        gate.get("reason") or f"{pet_name(self.pet)}现在不想工作。",
                        topic=topic or "",
                        goal=goal or "",
                        ok=False,
                        pending_reply=False,
                        blocked=True,
                    ),
                )
                self.pushState()
                return
            started_at = utc_now()
            staged_count = len(self.stagedScreenshots)
            message_text = topic or goal or ""
            if self.stagedScreenshots:
                message_text = self.build_screenshot_message(message_text)
            asset_context = build_asset_reference_block(assets)
            if asset_context:
                message_text = f"{message_text.rstrip()}\n\n{asset_context}"
            result = run_direct_send(message_text, assets)
            ok = result.returncode == 0
            attach_warning = "NO_FILE_INPUT" in ((result.stdout or "") + (result.stderr or ""))
            if ok:
                self.stagedScreenshots = []
                self.pendingReply = True
                self.pendingAction = "send"
                self.capture_agent_result_async("send", "", topic or goal or "桌面 Companion 直发消息", started_at)
            message = (
                "已经直发到当前 OpenClaw 会话，但当前页面没有可用的文件入口；我已经把本地文件路径写进消息里，当前会话仍然可以直接读取。"
                if ok and attach_warning and assets
                else "已经直发到当前 OpenClaw 会话，正在等待真实回复回执。"
                if ok
                else "没找到当前 OpenClaw 聊天页，暂时没法直发。"
            )
            self.notify_action_result(
                "send",
                action_feedback(
                    "send",
                    "waiting_reply" if ok else "failed",
                    "已经直发到当前 OpenClaw 会话，但当前页面没有可用的文件入口；我已经把本地文件路径写进消息里，当前会话仍然可以直接读取。"
                    if ok and attach_warning and assets
                    else "已经直发到当前 OpenClaw 会话，正在等待真实回复回执。"
                    if ok
                    else "没找到当前 OpenClaw 聊天页，暂时没法直发。",
                    topic=topic or "",
                    goal=goal or "",
                    ok=ok,
                    staged_shots=staged_count,
                    pending_reply=ok,
                    files_attached=bool(ok and not attach_warning),
                    detail=(result.stdout or result.stderr or "").strip(),
                ),
            )
            self.pushState()
            return
        if action == "screenshot":
            result = subprocess.run(
                [SCREENSHOT_SCRIPT, topic or "桌面 Companion 截图协作", goal or "请结合截图理解当前界面并给出下一步建议"],
                capture_output=True,
                text=True,
                check=False,
            )
            request_path = (result.stdout or "").strip().splitlines()[-1] if (result.stdout or "").strip() else ""
            latest_image = self.extract_screenshot_path(request_path) or (str(self.latest_file(LEARNING_SHOT_DIR, "*.png")) if self.latest_file(LEARNING_SHOT_DIR, "*.png") else "")
            if latest_image and latest_image not in self.stagedScreenshots:
                self.stagedScreenshots.append(latest_image)
            self.queueSummary = self.build_queue_summary(force_refresh=True)
            if request_path:
                gate = post_action("focus_companion")
                if isinstance(gate, dict) and isinstance(gate.get("pet"), dict):
                    self.pet = gate["pet"]
                if isinstance(gate, dict) and gate.get("blocked"):
                    self.notify_action_result(
                        "screenshot",
                        action_feedback(
                            "screenshot",
                            "blocked",
                            gate.get("reason") or f"{pet_name(self.pet)}现在不想继续处理截图。",
                            topic=topic or "桌面 Companion 截图协作",
                            goal=goal or "请结合截图理解当前界面并给出下一步建议",
                            image=str(latest_image) if latest_image else "",
                            request_path=request_path,
                            sent=False,
                            pending_reply=False,
                            blocked=True,
                        ),
                    )
                    self.pushState()
                    return
            self.notify_action_result(
                "screenshot",
                action_feedback(
                    "screenshot",
                    "staged",
                    "截图已暂存，你可以继续多截几张，最后再点发送或学习统一提交。",
                    topic=topic or "桌面 Companion 截图协作",
                    goal=goal or "请结合截图理解当前界面并给出下一步建议",
                    image=str(latest_image) if latest_image else "",
                    request_path=request_path,
                    sent=False,
                    pending_reply=False,
                    staged_shots=len(self.stagedScreenshots),
                ),
            )
            self.pushState()

    @objc.python_method
    def capture_agent_result_async(self, kind: str, request_path: str, topic: str, started_at: datetime):
        thread = threading.Thread(
            target=self.capture_agent_result,
            args=(kind, request_path, topic, started_at),
            daemon=True,
        )
        thread.start()

    @objc.python_method
    def capture_agent_result(self, kind: str, request_path: str, topic: str, started_at: datetime):
        try:
            deadline = time.time() + 180
            last_text = ""
            stable_polls = 0
            while time.time() < deadline:
                reply, reply_ts, event_ts, last_tool_ts = self.find_latest_assistant_reply(started_at)
                if reply and reply != last_text:
                    last_text = reply
                    stable_polls = 0
                elif reply:
                    stable_polls += 1
                if reply and event_ts is not None:
                    quiet_seconds = (utc_now() - event_ts).total_seconds()
                else:
                    quiet_seconds = 0
                assistant_is_final = bool(reply_ts) and (last_tool_ts is None or reply_ts > last_tool_ts)
                if reply and assistant_is_final and quiet_seconds >= 6 and stable_polls >= 2:
                    self.write_result_file(kind, request_path, topic, reply)
                    pet_state = None
                    try:
                        reward = post_action("reply_complete", {"topic": topic, "reply": reply})
                        if isinstance(reward, dict) and isinstance(reward.get("pet"), dict):
                            pet_state = reward["pet"]
                    except Exception as exc:
                        log(f"reply_complete reward failed: {exc}")
                    payload = json.dumps(
                        {
                            "kind": kind,
                            "topic": topic,
                            "phase": "replied",
                            "headline": "带回真实回复",
                            "tone": "notify",
                            "icon": "↩",
                            "reply": reply[:6000],
                            "reply_ts": reply_ts.isoformat() if reply_ts else "",
                            "message": "OpenClaw 已经返回了真实回复。",
                            "pet": pet_state or {},
                        },
                        ensure_ascii=False,
                    )
                    self.performSelectorOnMainThread_withObject_waitUntilDone_("applyCapturedReply:", payload, False)
                    return
                time.sleep(3)
            self.performSelectorOnMainThread_withObject_waitUntilDone_("clearPendingReply:", None, False)
        except Exception as exc:
            log(f"capture_agent_result failed: {exc}\n{traceback.format_exc()}")
            self.performSelectorOnMainThread_withObject_waitUntilDone_("clearPendingReply:", None, False)

    def applyCapturedReply_(self, payload_json):
        try:
            payload = json.loads(payload_json or "{}")
        except Exception:
            payload = {}
        if isinstance(payload.get("pet"), dict) and payload.get("pet"):
            self.pet = payload["pet"]
        self.latestReply = (payload.get("reply") or "")[:12000]
        self.pendingReply = False
        self.pendingAction = ""
        self.queueSummary = self.build_queue_summary(force_refresh=True)
        self.notify_reply_result(payload)
        self.pushState()

    def clearPendingReply_(self, _obj):
        self.pendingReply = False
        self.pendingAction = ""
        self.pushState()

    @objc.python_method
    def find_latest_assistant_reply(self, started_at: datetime):
        try:
            files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
            assistant_entries = []
            newest_event_ts = None
            last_tool_ts = None
            for path in files:
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except Exception:
                    continue
                for line in lines:
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue
                    ts = parse_ts(item.get("timestamp", ""))
                    if ts is None or ts < started_at:
                        continue
                    if newest_event_ts is None or ts >= newest_event_ts:
                        newest_event_ts = ts
                    message = item.get("message") or {}
                    role = message.get("role")
                    if role == "toolResult" and (last_tool_ts is None or ts >= last_tool_ts):
                        last_tool_ts = ts
                    text = extract_assistant_text(item)
                    if text:
                        assistant_entries.append((ts, text))
            if assistant_entries:
                assistant_entries.sort(key=lambda item: item[0])
                chosen_ts = None
                chosen_text = ""
                if last_tool_ts is not None:
                    after_tool = [(ts, text) for ts, text in assistant_entries if ts > last_tool_ts]
                    if after_tool:
                        chosen_ts, chosen_text = after_tool[-1]
                if not chosen_text:
                    chosen_ts, chosen_text = assistant_entries[-1]
                return chosen_text, chosen_ts, newest_event_ts, last_tool_ts
        except Exception as exc:
            log(f"find_latest_assistant_reply failed: {exc}")
        return "", None, None, None

    @objc.python_method
    def write_result_file(self, kind: str, request_path: str, topic: str, reply: str):
        try:
            stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
            slug = "".join(ch if ch.isalnum() else "-" for ch in topic.lower()).strip("-")[:48] or kind
            path = LEARNING_RESULT_DIR / f"{stamp}-{slug}.md"
            path.write_text(
                "\n".join(
                    [
                        "# Companion 真实回执",
                        "",
                        f"- 类型：{kind}",
                        f"- 主题：{topic}",
                        f"- 请求文件：{request_path}",
                        f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                        "",
                        "## OpenClaw 最新真实回复摘录",
                        "",
                        reply.strip(),
                        "",
                    ]
                ),
                encoding="utf-8",
            )
        except Exception as exc:
            log(f"write_result_file failed: {exc}")

    def refresh_(self, _timer):
        pet = fetch_json(PET_API)
        if pet:
            self.pet = pet
        self.queueSummary = self.build_queue_summary()
        self.pushState()

    def hoverTick_(self, _timer):
        if self.window is None:
            return
        if self.needsDeferredPush and self.pageReady and not self.is_input_active():
            self.needsDeferredPush = False
            self.pushState()
        if self.debugPinned and self.expanded:
            now = time.time()
            if now - self.lastDebugRefreshAt >= 1.2:
                self.lastDebugRefreshAt = now
                self.refresh_(None)
            self.leaveTicks = 0
            return
        mouse = NSEvent.mouseLocation()
        frame = self.window.frame()
        inside = (
            frame.origin.x <= mouse.x <= frame.origin.x + frame.size.width
            and frame.origin.y <= mouse.y <= frame.origin.y + frame.size.height
        )
        if inside:
            self.hoverTicks += 1
            self.leaveTicks = 0
        else:
            self.hoverTicks = 0
            if self.expanded:
                if self.is_input_active() or self.is_panel_interactive():
                    self.leaveTicks = 0
                    return
                self.leaveTicks += 1
                if self.leaveTicks >= 18:
                    self.setExpanded_(False)

    @objc.python_method
    def is_input_active(self):
        if not self.pageReady:
            return False
        try:
            value = self.webView.stringByEvaluatingJavaScriptFromString_(
                "window.isPromptActive ? window.isPromptActive() : 'false';"
            )
            return str(value).lower() == "true"
        except Exception:
            return False

    @objc.python_method
    def is_panel_interactive(self):
        if not self.pageReady:
            return False
        try:
            value = self.webView.stringByEvaluatingJavaScriptFromString_(
                "window.isPanelInteractive ? window.isPanelInteractive() : 'false';"
            )
            return str(value).lower() == "true"
        except Exception:
            return False

    @objc.python_method
    def visible_frame(self):
        window = self.window
        if window is not None:
            try:
                screen = window.screen()
                if screen is not None:
                    return screen.visibleFrame()
            except Exception:
                pass
        screen = NSScreen.mainScreen()
        return screen.visibleFrame() if screen is not None else NSMakeRect(120, 120, 1440, 900)

    @objc.python_method
    def compact_chip_origin(self, frame):
        chip_x = frame.origin.x + max(0, (frame.size.width - 128) / 2)
        chip_y = frame.origin.y + max(0, (frame.size.height - 52) / 2)
        return chip_x, chip_y

    @objc.python_method
    def expanded_origin_from_compact(self, compact_frame, width, height):
        visible = self.visible_frame()
        margin = 14
        chip_x, chip_y = self.compact_chip_origin(compact_frame)

        left_space = chip_x - visible.origin.x
        right_space = (visible.origin.x + visible.size.width) - (chip_x + 128)

        if right_space >= left_space:
            x = chip_x
        else:
            x = chip_x + 128 - width

        center_y = chip_y + 26
        y = center_y - height / 2

        min_x = visible.origin.x + margin
        max_x = visible.origin.x + visible.size.width - width - margin
        min_y = visible.origin.y + margin
        max_y = visible.origin.y + visible.size.height - height - margin

        x = max(min_x, min(max_x, x))
        y = max(min_y, min(max_y, y))
        return x, y

    @objc.python_method
    def collapsed_origin_from_frame(self, frame, width, height):
        visible = self.visible_frame()
        margin = 0
        edge_threshold = 42
        x = frame.origin.x
        y = frame.origin.y

        left_edge = visible.origin.x
        right_edge = visible.origin.x + visible.size.width - width
        bottom_edge = visible.origin.y
        top_edge = visible.origin.y + visible.size.height - height

        if abs(frame.origin.x - visible.origin.x) <= edge_threshold:
            x = left_edge
        elif abs((frame.origin.x + frame.size.width) - (visible.origin.x + visible.size.width)) <= edge_threshold:
            x = right_edge
        else:
            x = max(left_edge + margin, min(right_edge - margin, x))

        y = max(bottom_edge, min(top_edge, y))
        return x, y

    @objc.python_method
    def setExpanded_(self, expanded):
        self.expanded = expanded
        if not expanded:
            self.debugPinned = False
        width = EXPANDED_W if expanded else COLLAPSED_W
        height = EXPANDED_H if expanded else COLLAPSED_H
        frame = self.window.frame()
        if expanded:
            x, y = self.expanded_origin_from_compact(frame, width, height)
        else:
            x, y = self.collapsed_origin_from_frame(frame, width, height)

        self.window.setFrame_display_(NSMakeRect(x, y, width, height), True)
        self.rootView.setFrame_(NSMakeRect(0, 0, width, height))
        self.webView.setFrame_(NSMakeRect(0, 0, width, height))
        if expanded:
            drag_width = min(164, max(120, width * 0.26))
            drag_height = 28
            drag_x = max(0, (width - drag_width) / 2)
            drag_y = max(0, height - drag_height - 12)
            self.dragView.setHidden_(False)
            self.dragView.setFrame_(NSMakeRect(drag_x, drag_y, drag_width, drag_height))
        else:
            chip_x = max(0, (width - 128) / 2)
            chip_y = max(0, (height - 52) / 2)
            self.dragView.setHidden_(False)
            self.dragView.setFrame_(NSMakeRect(chip_x, chip_y, 128, 52))
        if expanded:
            NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.16, self, "applyCompactStateTimer:", None, False)
        else:
            self.applyCompactState()

    def applyCompactStateTimer_(self, _timer):
        self.applyCompactState()

    @objc.python_method
    def applyCompactState(self):
        if not self.pageReady:
            return
        compact = "true" if not self.expanded else "false"
        self.webView.stringByEvaluatingJavaScriptFromString_(f"window.setCompact({compact});")

    @objc.python_method
    def pushState(self):
        if not self.pageReady:
            return
        if self.is_input_active():
            self.needsDeferredPush = True
            return
        pet = self.pet or {
            "name": "LittleClaw",
            "level": 1,
            "stage_title": "初始形态",
            "species_id": "lobster",
            "stage_presence": "开始理解你的节奏，会主动给陪伴反馈。",
            "affinity": 0,
            "energy": 0,
            "hunger": 0,
            "xp": 0,
        }
        self.refresh_window_titles()
        if pet.get("onboarding_pending") and not self.expanded:
            self.setExpanded_(True)
            return
        pet_json = json.dumps(pet, ensure_ascii=False)
        queue_json = json.dumps(self.queueSummary, ensure_ascii=False)
        reply_json = json.dumps(self.latestReply, ensure_ascii=False)
        pending_json = "true" if self.pendingReply else "false"
        action_json = json.dumps(self.pendingAction, ensure_ascii=False)
        openclaw_json = json.dumps(self.current_openclaw_status(), ensure_ascii=False)
        script = f"window.updatePet({pet_json}, {queue_json}, {reply_json}, {pending_json}, {action_json}, {openclaw_json});"
        self.webView.stringByEvaluatingJavaScriptFromString_(script)
        self.needsDeferredPush = False
        self.pushDebugState()

    @objc.python_method
    def pushDebugState(self):
        if not self.debugPageReady or self.debugWebView is None:
            return
        pet_json = json.dumps(self.pet or {}, ensure_ascii=False)
        self.debugWebView.stringByEvaluatingJavaScriptFromString_(
            f"window.updateDebugState && window.updateDebugState({pet_json});"
        )

    @objc.python_method
    def build_queue_summary(self, force_refresh=False):
        try:
            requests = sorted(LEARNING_REQ_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            shots = sorted(LEARNING_SHOT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            results = sorted(LEARNING_RESULT_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            latest = results[0].stem[:20] if results else (requests[0].stem[:20] if requests else "无")
            staged = f"，暂存 {len(self.stagedScreenshots)} 张" if self.stagedScreenshots else ""
            return f"学习请求 {len(requests)} 条，截图 {len(shots)} 张{staged}，结果 {len(results)} 条，最近 {latest}"
        except Exception:
            return "学习队列暂时不可读。"

    @objc.python_method
    def current_openclaw_status(self):
        try:
            files = sorted(SESSION_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
            newest = None
            for path in files:
                try:
                    lines = path.read_text(encoding="utf-8").splitlines()
                except Exception:
                    continue
                for line in lines:
                    try:
                        item = json.loads(line)
                    except Exception:
                        continue
                    message = item.get("message") or {}
                    role = str(message.get("role") or "")
                    if not role:
                        continue
                    ts = parse_ts(item.get("timestamp", ""))
                    if ts is None:
                        continue
                    if newest is None or ts >= newest["ts"]:
                        newest = {
                            "ts": ts,
                            "role": role,
                            "stop_reason": str(message.get("stopReason") or ""),
                            "tool_name": str(message.get("toolName") or ""),
                        }
            if newest is None:
                return {
                    "state": "idle",
                    "active": False,
                    "title": "OpenClaw 待命中",
                    "detail": "当前会话没有新的处理动作，伙伴会先在旁边陪着你。",
                    "tone": "notify",
                    "icon": "•",
                    "pill": "待命",
                }
            age = max(0.0, (utc_now() - newest["ts"]).total_seconds())
            role = newest["role"]
            stop_reason = newest["stop_reason"]
            tool_name = newest["tool_name"]
            if role == "assistant" and stop_reason == "toolUse" and age <= 90:
                return {
                    "state": "working",
                    "active": True,
                    "title": "OpenClaw 工作中",
                    "detail": "当前会话正在继续调用工具和处理结果。",
                    "tone": "busy",
                    "icon": "…",
                    "pill": "处理中",
                }
            if role == "toolResult" and age <= 90:
                detail = f"当前工具 {tool_name} 已返回结果，OpenClaw 还在继续处理。" if tool_name else "当前工具已返回结果，OpenClaw 还在继续处理。"
                return {
                    "state": "working",
                    "active": True,
                    "title": "OpenClaw 工作中",
                    "detail": detail,
                    "tone": "busy",
                    "icon": "…",
                    "pill": "处理中",
                }
            if role == "user" and age <= 45:
                return {
                    "state": "queued",
                    "active": True,
                    "title": "OpenClaw 收到请求",
                    "detail": "当前会话刚收到一条新消息，正在准备响应。",
                    "tone": "busy",
                    "icon": "↗",
                    "pill": "新请求",
                }
            if role == "assistant" and age <= 45:
                return {
                    "state": "completed",
                    "active": False,
                    "fresh_reply": True,
                    "title": "OpenClaw 刚回信",
                    "detail": "当前会话刚刚产出了一条新回复。",
                    "tone": "notify",
                    "icon": "✓",
                    "pill": "新回复",
                }
        except Exception as exc:
            log(f"current_openclaw_status failed: {exc}")
        return {
            "state": "idle",
            "active": False,
            "title": "OpenClaw 待命中",
            "detail": "当前会话没有新的处理动作，伙伴会先在旁边陪着你。",
            "tone": "notify",
            "icon": "•",
            "pill": "待命",
        }

    @objc.python_method
    def launch_debug_tool(self):
        candidates = [
            str(RUNTIME.get("python_executable") or ""),
            "/usr/bin/python3",
            shutil.which("python3") or "",
        ]
        if self.debug_server_running():
            subprocess.Popen(["open", DEBUG_URL], start_new_session=True)
            log("launch_debug_tool reused running debug server")
            return
        last_error = None
        for candidate in candidates:
            if not candidate:
                continue
            try:
                probe = subprocess.run(
                    [candidate, "-c", "import json, http.server"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if probe.returncode != 0:
                    last_error = probe.stderr.strip() or probe.stdout.strip() or f"python probe failed: {candidate}"
                    continue
                with DEBUG_TOOL_LOG.open("a", encoding="utf-8") as fh:
                    fh.write(f"launch via {candidate} @ {datetime.now().isoformat()}\n")
                out = DEBUG_TOOL_LOG.open("a", encoding="utf-8")
                subprocess.Popen(
                    [candidate, str(DEBUG_SERVER)],
                    cwd=str(DEBUG_SERVER.parent),
                    stdout=out,
                    stderr=out,
                    start_new_session=True,
                )
                for _ in range(20):
                    if self.debug_server_running():
                        subprocess.Popen(["open", DEBUG_URL], start_new_session=True)
                        log(f"launch_debug_tool ok: {candidate}")
                        return
                    time.sleep(0.12)
                last_error = f"debug server did not start in time: {candidate}"
                break
            except Exception as exc:
                last_error = str(exc)
        log(f"launch_debug_tool failed: {last_error or 'no usable python with tkinter'}")

    @objc.python_method
    def debug_server_running(self):
        try:
            with socket.create_connection((DEBUG_HOST, DEBUG_PORT), timeout=0.35):
                return True
        except Exception:
            return False

    @objc.python_method
    def toggleDebugWindow(self):
        if self.debugWindow is None:
            return
        if self.debugWindow.isVisible():
            self.debugWindow.orderOut_(None)
            return
        frame = self.window.frame() if self.window is not None else self.default_frame(COLLAPSED_W, COLLAPSED_H)
        x = frame.origin.x + frame.size.width + 14
        y = frame.origin.y + max(0, frame.size.height - DEBUG_H)
        visible = self.visible_frame()
        x = max(visible.origin.x + 8, min(x, visible.origin.x + visible.size.width - DEBUG_W - 8))
        y = max(visible.origin.y + 8, min(y, visible.origin.y + visible.size.height - DEBUG_H - 8))
        self.debugWindow.setFrame_display_(NSMakeRect(x, y, DEBUG_W, DEBUG_H), True)
        self.debugWindow.orderFrontRegardless()
        self.debugWindow.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)
        self.pushDebugState()

    @objc.python_method
    def debug_stage_adjustment(self, state: dict, species_id: str, stage_id: str, payload: dict) -> dict:
        stages = PET_RUNTIME.evolution_stages(species_id)
        index = next((idx for idx, item in enumerate(stages) if item["id"] == stage_id), 0)
        target = stages[index]
        nxt = stages[index + 1] if index + 1 < len(stages) else None

        level = max(int(payload.get("level", target["min_level"])), int(target["min_level"]))
        affinity = max(int(payload.get("affinity", target["min_affinity"])), int(target["min_affinity"]))
        streak = max(int(payload.get("reward_streak", target["min_streak"])), int(target["min_streak"]))
        progress = max(int(payload.get("progress", target.get("min_progress", 0))), int(target.get("min_progress", 0)))

        if nxt is not None:
            level = min(level, max(int(target["min_level"]), int(nxt["min_level"]) - 1))
            affinity = min(affinity, max(int(target["min_affinity"]), int(nxt["min_affinity"]) - 1))
            streak = min(streak, max(int(target["min_streak"]), int(nxt["min_streak"]) - 1))
            progress = min(progress, max(int(target.get("min_progress", 0)), int(nxt.get("min_progress", 0)) - 1))

        state["level"] = level
        state["affinity"] = affinity
        state["reward_streak"] = streak
        state["task_score"] = progress
        state["total_actions"] = max(int(state.get("total_actions", 0)), progress * 2)
        state["send_count"] = 0
        state["learn_count"] = 0
        state["reply_count"] = 0
        state["hard_task_count"] = 0
        state["project_count"] = 0
        return state

    @objc.python_method
    def apply_debug_pet(self, payload_json: str):
        try:
            payload = json.loads(payload_json or "{}")
        except Exception:
            payload = {}
        state = PET_RUNTIME.load_state()
        species_id = str(payload.get("species_id") or state.get("species_id") or "lobster")
        species = PET_RUNTIME.species_config(species_id)
        state["species_id"] = species_id
        state["species_title"] = species.get("title", state.get("species_title", "龙虾系"))
        state["species"] = species.get("title", state.get("species", "龙虾系"))
        state["rarity"] = str(payload.get("rarity") or state.get("rarity") or "common").lower()
        state["xp"] = max(0, int(payload.get("xp", state.get("xp", 0))))
        state["energy"] = max(0, min(100, int(payload.get("energy", state.get("energy", 78)))))
        state["hunger"] = max(0, min(100, int(payload.get("hunger", state.get("hunger", 22)))))
        state["onboarding_pending"] = False
        stage_id = str(payload.get("stage_id") or "").strip()
        if stage_id:
            state = self.debug_stage_adjustment(state, species_id, stage_id, payload)
        else:
            if "level" in payload:
                state["level"] = max(1, int(payload.get("level", state.get("level", 1))))
            if "affinity" in payload:
                state["affinity"] = max(0, min(100, int(payload.get("affinity", state.get("affinity", 75)))))
        PET_RUNTIME.save_state(state)
        latest = fetch_json(PET_API)
        self.pet = latest if isinstance(latest, dict) else PET_RUNTIME.load_state()

    @objc.python_method
    def latest_file(self, directory: Path, pattern: str):
        try:
            files = sorted(directory.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
            return files[0] if files else None
        except Exception:
            return None

    @objc.python_method
    def open_file_picker(self):
        try:
            panel = NSOpenPanel.openPanel()
            panel.setCanChooseFiles_(True)
            panel.setCanChooseDirectories_(False)
            panel.setAllowsMultipleSelection_(True)
            panel.setCanCreateDirectories_(False)
            if panel.runModal():
                files = []
                for url in panel.URLs() or []:
                    path = str(url.path())
                    if not path:
                        continue
                    ext = Path(path).suffix.lower()
                    files.append(
                        {
                            "name": Path(path).name,
                            "path": path,
                            "kind": "image" if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"} else "file",
                            "preview": f"file://{path}" if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"} else "",
                        }
                    )
                self.notify_action_result(
                    "pick_files",
                    action_feedback(
                        "pick_files",
                        "staged" if files else "failed",
                        f"已接住 {len(files)} 个附件，你可以继续添加或直接发送。"
                        if files
                        else "没有选择附件，已回到待命状态。",
                        files=files,
                        ok=bool(files),
                    ),
                )
        except Exception as exc:
            log(f"open_file_picker failed: {exc}")

    @objc.python_method
    def extract_screenshot_path(self, request_path: str) -> str:
        body = read_text(request_path)
        match = re.search(r"^- 截图：(.+)$", body, re.MULTILINE)
        return match.group(1).strip() if match else ""

    @objc.python_method
    def screenshot_context_block(self):
        if not self.stagedScreenshots:
            return ""
        lines = ["## 已暂存截图", ""]
        for idx, shot in enumerate(self.stagedScreenshots, start=1):
            lines.append(f"{idx}. {shot}")
        lines.append("")
        lines.append("请结合以上全部截图一起理解当前问题，不要只看最后一张。")
        return "\n".join(lines)

    @objc.python_method
    def append_screenshot_context(self, body: str, topic: str, goal: str):
        context = self.screenshot_context_block()
        if not context:
            return body
        return f"{body.rstrip()}\n\n{context}\n"

    @objc.python_method
    def build_screenshot_message(self, message_text: str):
        context = self.screenshot_context_block()
        lines = [
            "这是来自 LittleClaw Companion 的多截图协作请求，请结合全部暂存截图一起处理。",
            "",
            f"用户要求：{message_text or '请先阅读截图并给出下一步建议'}",
            "",
            context,
        ]
        return "\n".join(lines).strip()

    @objc.python_method
    def notify_action_result(self, action: str, payload: dict):
        if not self.pageReady:
            return
        action_json = json.dumps(action, ensure_ascii=False)
        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        self.webView.stringByEvaluatingJavaScriptFromString_(
            f"window.onActionResult && window.onActionResult({action_json}, {payload_json});"
        )

    @objc.python_method
    def notify_reply_result(self, payload: dict):
        if not self.pageReady:
            return
        payload_json = json.dumps(payload or {}, ensure_ascii=False)
        self.webView.stringByEvaluatingJavaScriptFromString_(
            f"window.onReplyResult && window.onReplyResult({payload_json});"
        )

    def toggleWindow_(self, _sender):
        if self.window is None:
            return
        if self.window.isVisible():
            self.save_position()
            self.window.orderOut_(None)
        else:
            self.showWindow_()

    @objc.python_method
    def showWindow_(self):
        if self.window is None:
            return
        frame = self.default_frame(COLLAPSED_W, COLLAPSED_H)
        self.window.setFrame_display_(frame, True)
        self.setExpanded_(False)
        self.window.orderFrontRegardless()
        self.window.makeKeyAndOrderFront_(None)
        NSApp.activateIgnoringOtherApps_(True)

    @objc.python_method
    def default_frame(self, width, height):
        screen = NSScreen.mainScreen()
        visible = screen.visibleFrame() if screen is not None else NSMakeRect(120, 120, 1440, 900)
        pos = self.load_position()
        x = pos.get("x", visible.origin.x + visible.size.width - width - 48)
        y = pos.get("y", visible.origin.y + (visible.size.height - height) / 2)
        return NSMakeRect(x, y, width, height)

    @objc.python_method
    def load_position(self):
        if POSITION_FILE.exists():
            try:
                return json.loads(POSITION_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        screen = NSScreen.mainScreen()
        visible = screen.visibleFrame() if screen is not None else NSMakeRect(120, 120, 1440, 900)
        return {
            "x": visible.origin.x + visible.size.width - COLLAPSED_W - 56,
            "y": visible.origin.y + (visible.size.height - COLLAPSED_H) / 2,
        }

    @objc.python_method
    def save_position(self):
        if self.window is None:
            return
        try:
            STATE_DIR.mkdir(parents=True, exist_ok=True)
            frame = self.window.frame()
            snapped_x, snapped_y = self.collapsed_origin_from_frame(frame, frame.size.width, frame.size.height)
            self.window.setFrameOrigin_((snapped_x, snapped_y))
            POSITION_FILE.write_text(
                json.dumps({"x": snapped_x, "y": snapped_y}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            log(f"save_position failed: {exc}")

    def applicationWillTerminate_(self, notification):
        global PID_HANDLE
        self.save_position()
        try:
            if PID_FILE.exists() and PID_FILE.read_text(encoding="utf-8").strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass
        try:
            if PID_HANDLE is not None:
                fcntl.flock(PID_HANDLE.fileno(), fcntl.LOCK_UN)
                PID_HANDLE.close()
                PID_HANDLE = None
        except Exception:
            pass


def main():
    try:
        ensure_single_instance()
        app = NSApplication.sharedApplication()
        delegate = CompanionController.alloc().init()
        app.setDelegate_(delegate)
        app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
        globals()["_delegate"] = delegate
        app.run()
    except Exception:
        log(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
