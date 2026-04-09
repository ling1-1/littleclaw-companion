#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import re
import signal
import subprocess
import threading
import time
import traceback
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
LEARNING_REQ_DIR = STATE_DIR.parent / "learning-lab" / "requests"
LEARNING_SHOT_DIR = STATE_DIR.parent / "learning-lab" / "screenshots"
LEARNING_RESULT_DIR = STATE_DIR.parent / "learning-lab" / "results"
SESSION_DIR = RUNTIME["openclaw_home"] / "agents" / "main" / "sessions"
UI_DIR = RUNTIME["ui_root"]

C_COLLAPSED_W = 188
C_COLLAPSED_H = 116
COLLAPSED_W = C_COLLAPSED_W
COLLAPSED_H = C_COLLAPSED_H
EXPANDED_W = 420
EXPANDED_W = 468
EXPANDED_H = 780


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
        if not path:
            continue
        file_path = Path(path)
        if not file_path.exists() or not file_path.is_file():
            continue
        try:
            raw = file_path.read_bytes()
        except Exception:
            continue
        mime, _ = mimetypes.guess_type(file_path.name)
        normalized.append(
            {
                "name": item.get("name") or file_path.name,
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
        "这是来自 LittleClaw Companion 的真实请求，请直接按当前会话任务处理。"
        if kind == "learn"
        else "这是来自 LittleClaw Companion 的截图协作请求，请直接按当前会话任务处理。"
    )
    return (
        f"{header}\n\n"
        f"请求文件：{request_path}\n"
        f"主题：{topic}\n"
        f"目标：{goal}\n\n"
        f"请求正文如下：\n\n{body}\n\n"
        "请先基于这份请求继续处理，不要只重复它。"
    )


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
    try:
        if PID_FILE.exists():
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if old_pid and old_pid != os.getpid():
                try:
                    os.kill(old_pid, 0)
                    os.kill(old_pid, signal.SIGTERM)
                except OSError:
                    pass
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
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
        self.pageReady = False
        self.pet = {}
        self.hoverTicks = 0
        self.leaveTicks = 0
        self.expanded = False
        self.queueSummary = "学习队列还很安静。"
        self.latestReply = ""
        self.pendingReply = False
        self.pendingAction = ""
        self.stagedScreenshots = []
        LEARNING_RESULT_DIR.mkdir(parents=True, exist_ok=True)
        return self

    def applicationDidFinishLaunching_(self, notification):
        log("applicationDidFinishLaunching")
        self.buildStatusItem()
        self.buildWindow()
        self.loadPage()
        self.refresh_(None)
        self.showWindow_()
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(10.0, self, "refresh:", None, True)
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.28, self, "hoverTick:", None, True)

    @objc.python_method
    def buildStatusItem(self):
        self.statusItem = NSStatusBar.systemStatusBar().statusItemWithLength_(NSVariableStatusItemLength)
        button = self.statusItem.button()
        if button is not None:
            button.setTitle_("🦞 小钳")
            button.setToolTip_("LittleClaw Companion")
            button.setTarget_(self)
            button.setAction_("toggleWindow:")

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
    def loadPage(self):
        html = (UI_DIR / "index.html").read_text(encoding="utf-8")
        base = NSURL.fileURLWithPath_(str(UI_DIR) + "/")
        self.webView.mainFrame().loadHTMLString_baseURL_(html, base)

    def webView_didFinishLoadForFrame_(self, webView, frame):
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
                    "message": "初次相遇已经记住了，之后小钳会直接进入正常陪伴模式。",
                },
            )
            self.pushState()
            return
        if action == "expand":
            self.setExpanded_(True)
            return
        if action == "collapse":
            self.setExpanded_(False)
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
                    {
                        "topic": topic or "桌面 Companion 学习主题",
                        "goal": goal or "持续学习、沉淀方案并整理 skill 草稿",
                        "sent": False,
                        "pending_reply": False,
                        "blocked": True,
                        "message": gate.get("reason") or "小钳现在太累了，先休息一下。",
                    },
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
            staged_count = len(self.stagedScreenshots)
            if request_path:
                request_body = read_text(request_path)
                if self.stagedScreenshots:
                    request_body = self.append_screenshot_context(
                        request_body,
                        topic or "桌面 Companion 学习主题",
                        goal or "持续学习、沉淀方案并整理 skill 草稿",
                    )
                agent_prompt = build_agent_prompt(
                    "learn",
                    request_path,
                    topic or "桌面 Companion 学习主题",
                    goal or "持续学习、沉淀方案并整理 skill 草稿",
                    request_body,
                )
                send_result = run_direct_send(agent_prompt, assets)
                sent_ok = send_result.returncode == 0
                if sent_ok:
                    self.stagedScreenshots = []
                    self.pendingReply = True
                    self.pendingAction = "learn"
                    self.capture_agent_result_async("learn", request_path, topic or "桌面 Companion 学习主题", started_at)
            self.queueSummary = self.build_queue_summary(force_refresh=True)
            self.notify_action_result(
                "learn",
                {
                    "topic": topic or "桌面 Companion 学习主题",
                    "goal": goal or "持续学习、沉淀方案并整理 skill 草稿",
                    "request_path": request_path,
                    "staged_shots": staged_count,
                    "sent": sent_ok,
                    "pending_reply": sent_ok,
                    "message": (
                        "学习请求已真正发到当前 OpenClaw 会话，正在等待真实回复回执。"
                        if sent_ok
                        else "学习请求已落盘入队，但当前没有可直发的 OpenClaw 会话。"
                    ),
                },
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
                    {
                        "topic": topic or "",
                        "goal": goal or "",
                        "ok": False,
                        "pending_reply": False,
                        "blocked": True,
                        "message": gate.get("reason") or "小钳现在不想工作。",
                    },
                )
                self.pushState()
                return
            started_at = utc_now()
            staged_count = len(self.stagedScreenshots)
            message_text = topic or goal or ""
            if self.stagedScreenshots:
                message_text = self.build_screenshot_message(message_text)
            result = run_direct_send(message_text, assets)
            ok = result.returncode == 0
            if ok:
                self.stagedScreenshots = []
                self.pendingReply = True
                self.pendingAction = "send"
                self.capture_agent_result_async("send", "", topic or goal or "桌面 Companion 直发消息", started_at)
            message = "已经直发到当前 OpenClaw 会话，正在等待真实回复回执。" if ok else "没找到当前 OpenClaw 聊天页，暂时没法直发。"
            self.notify_action_result(
                "send",
                {
                    "topic": topic or "",
                    "goal": goal or "",
                    "message": message,
                    "ok": ok,
                    "staged_shots": staged_count,
                    "pending_reply": ok,
                    "detail": (result.stdout or result.stderr or "").strip(),
                },
            )
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
                        {
                            "topic": topic or "桌面 Companion 截图协作",
                            "goal": goal or "请结合截图理解当前界面并给出下一步建议",
                            "image": str(latest_image) if latest_image else "",
                            "request_path": request_path,
                            "sent": False,
                            "pending_reply": False,
                            "blocked": True,
                            "message": gate.get("reason") or "小钳现在不想继续处理截图。",
                        },
                    )
                    self.pushState()
                    return
            self.notify_action_result(
                "screenshot",
                {
                    "topic": topic or "桌面 Companion 截图协作",
                    "goal": goal or "请结合截图理解当前界面并给出下一步建议",
                    "image": str(latest_image) if latest_image else "",
                    "request_path": request_path,
                    "sent": False,
                    "pending_reply": False,
                    "staged_shots": len(self.stagedScreenshots),
                    "message": "截图已暂存，你可以继续多截几张，最后再点发送或学习统一提交。",
                },
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
                if self.is_input_active():
                    self.leaveTicks = 0
                    return
                self.leaveTicks += 1
                if self.leaveTicks >= 8:
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
        pet = self.pet or {
            "name": "小钳",
            "level": 1,
            "stage_title": "陪伴助手",
            "stage_presence": "开始理解你的节奏，会主动给陪伴反馈。",
            "affinity": 0,
            "energy": 0,
            "hunger": 0,
            "xp": 0,
        }
        if pet.get("onboarding_pending") and not self.expanded:
            self.setExpanded_(True)
            return
        pet_json = json.dumps(pet, ensure_ascii=False)
        queue_json = json.dumps(self.queueSummary, ensure_ascii=False)
        reply_json = json.dumps(self.latestReply, ensure_ascii=False)
        pending_json = "true" if self.pendingReply else "false"
        action_json = json.dumps(self.pendingAction, ensure_ascii=False)
        script = f"window.updatePet({pet_json}, {queue_json}, {reply_json}, {pending_json}, {action_json});"
        self.webView.stringByEvaluatingJavaScriptFromString_(script)

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
                self.notify_action_result("pick_files", {"files": files, "ok": bool(files)})
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
        self.save_position()
        try:
            if PID_FILE.exists():
                PID_FILE.unlink()
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
