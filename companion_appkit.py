#!/usr/bin/env python3
import json
import os
import signal
import subprocess
import traceback
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

import objc
from AppKit import (
    NSApp,
    NSApplication,
    NSApplicationActivationPolicyAccessory,
    NSBackingStoreBuffered,
    NSBezierPath,
    NSButton,
    NSColor,
    NSEvent,
    NSFloatingWindowLevel,
    NSFont,
    NSMakeRect,
    NSMidX,
    NSMidY,
    NSScreen,
    NSStatusBar,
    NSTextField,
    NSVariableStatusItemLength,
    NSView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowStyleMaskBorderless,
    NSPanel,
    NSRoundedBezelStyle,
)
from Foundation import NSObject, NSTimer

PET_API = "http://127.0.0.1:18793/pet"
PET_ACTION_API = "http://127.0.0.1:18793/pet/action"
LEARNING_SCRIPT = "/Users/baijingting/.openclaw/scripts/openclaw-learning-intake.sh"
SCREENSHOT_SCRIPT = "/Users/baijingting/.openclaw/scripts/openclaw-screenshot-intake.sh"
STATE_DIR = Path("/Users/baijingting/.openclaw/workspace/memory")
POSITION_FILE = STATE_DIR / "companion-position.json"
PID_FILE = Path("/tmp/littleclaw-companion.pid")
LOG_FILE = Path("/tmp/littleclaw-appkit-debug.log")
LEARNING_REQ_DIR = STATE_DIR.parent / "learning-lab" / "requests"
LEARNING_SHOT_DIR = STATE_DIR.parent / "learning-lab" / "screenshots"

COLLAPSED_W = 104
COLLAPSED_H = 104
EXPANDED_W = 420
EXPANDED_H = 360


def log(message: str):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(message + "\n")
    except Exception:
        pass


def fetch_json(url: str):
    try:
        with urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError:
        return None
    except Exception:
        return None


def post_action(action: str):
    payload = json.dumps({"action": action}).encode("utf-8")
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
                    log(f"terminated old instance pid={old_pid}")
                except OSError:
                    pass
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    except Exception as exc:
        log(f"ensure_single_instance failed: {exc}")


class BubbleView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(BubbleView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.compact = True
        return self

    def drawRect_(self, rect):
        bounds = self.bounds()
        radius = 28 if self.compact else 26
        fill = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.975, 0.965, 0.988)
        stroke = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.73, 0.58, 0.86)
        shadow = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.94, 0.57, 0.40, 0.10)
        shadow.set()
        shadow_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, radius, radius)
        shadow_path.fill()
        inner = NSMakeRect(bounds.origin.x + 2, bounds.origin.y + 2, bounds.size.width - 4, bounds.size.height - 4)
        fill.set()
        path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(inner, radius, radius)
        path.fill()
        stroke.set()
        path.setLineWidth_(1.4)
        path.stroke()


class AvatarView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(AvatarView, self).initWithFrame_(frame)
        if self is None:
            return None
        self.blink = 0.0
        self.float_offset = 0.0
        self.mood = "calm"
        return self

    def drawRect_(self, rect):
        bounds = self.bounds()
        cx = NSMidX(bounds)
        cy = NSMidY(bounds) + self.float_offset
        body_w = min(bounds.size.width * 0.52, 84)
        body_h = min(bounds.size.height * 0.48, 62)
        body_x = cx - body_w / 2
        body_y = cy - body_h / 2 - 2
        head_size = min(bounds.size.width * 0.42, 58)
        head_x = cx - head_size / 2
        head_y = body_y + body_h * 0.52

        shadow = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.80, 0.48, 0.36, 0.12)
        shadow.set()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx - 28, body_y - 12, 56, 12)).fill()

        glow = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.80, 0.70, 0.22)
        glow.set()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(head_x - 18, body_y - 10, head_size + 36, head_size + body_h * 0.8)).fill()

        shell = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.58, 0.44, 0.98)
        shell.set()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(head_x, head_y, head_size, head_size * 0.9)).fill()

        body = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.66, 0.50, 0.98)
        body.set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(body_x, body_y, body_w, body_h), 18, 18).fill()

        accent = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.84, 0.74, 0.95)
        accent.set()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(head_x + 8, head_y + head_size * 0.16, head_size - 16, head_size * 0.54)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(body_x + 8, body_y + body_h * 0.24, body_w - 16, body_h * 0.44)).fill()

        claw = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.97, 0.60, 0.48, 0.96)
        claw.set()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(body_x - 12, body_y + body_h * 0.36, 16, 10), 6, 6).fill()
        NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(NSMakeRect(body_x + body_w - 4, body_y + body_h * 0.36, 16, 10), 6, 6).fill()

        eye_color = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.20, 0.17, 0.18, 1.0)
        eye_color.set()
        eye_w = 8
        eye_h = 3 if self.blink > 0.72 else 11
        eye_y = head_y + head_size * 0.40
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx - 15, eye_y, eye_w, eye_h)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx + 7, eye_y, eye_w, eye_h)).fill()

        blush = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.96, 0.48, 0.44, 0.25)
        blush.set()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx - 26, head_y + head_size * 0.24, 11, 6)).fill()
        NSBezierPath.bezierPathWithOvalInRect_(NSMakeRect(cx + 15, head_y + head_size * 0.24, 11, 6)).fill()

        mouth = NSBezierPath.bezierPath()
        mouth.moveToPoint_((cx - 8, head_y + head_size * 0.18))
        if self.mood == "happy":
            mouth.curveToPoint_controlPoint1_controlPoint2_((cx + 8, head_y + head_size * 0.18), (cx - 4, head_y + head_size * 0.08), (cx + 4, head_y + head_size * 0.08))
        elif self.mood == "sleepy":
            mouth.curveToPoint_controlPoint1_controlPoint2_((cx + 8, head_y + head_size * 0.18), (cx - 4, head_y + head_size * 0.24), (cx + 4, head_y + head_size * 0.24))
        else:
            mouth.curveToPoint_controlPoint1_controlPoint2_((cx + 8, head_y + head_size * 0.18), (cx - 4, head_y + head_size * 0.13), (cx + 4, head_y + head_size * 0.13))
        eye_color.set()
        mouth.setLineWidth_(2.0)
        mouth.stroke()

        leg = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.85, 0.42, 0.34, 0.85)
        leg.set()
        for x in (body_x + 8, body_x + 20, body_x + body_w - 28, body_x + body_w - 16):
            path = NSBezierPath.bezierPath()
            path.moveToPoint_((x, body_y + 4))
            path.lineToPoint_((x - 2, body_y - 6))
            path.setLineWidth_(1.8)
            path.stroke()


class PresenceBadgeView(NSView):
    def initWithFrame_(self, frame):
        self = objc.super(PresenceBadgeView, self).initWithFrame_(frame)
        if self is None:
            return None
        return self

    def drawRect_(self, rect):
        bounds = self.bounds()
        fill = NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 0.96, 0.90, 0.92)
        stroke = NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.80, 0.66, 0.72)
        fill.set()
        bubble = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bounds, 16, 16)
        bubble.fill()
        stroke.set()
        bubble.setLineWidth_(1.0)
        bubble.stroke()


class CompanionController(NSObject):
    def init(self):
        self = objc.super(CompanionController, self).init()
        if self is None:
            return None
        self.window = None
        self.statusItem = None
        self.pet = {}
        self.hovering = False
        self.expanded = False
        self.lastMouseInside = False
        self.hoverTicks = 0
        self.leaveTicks = 0
        self.lastSummary = ""
        self.avatarPhase = 0
        self.isCompactMode = True
        return self

    def applicationDidFinishLaunching_(self, notification):
        log("applicationDidFinishLaunching")
        self.buildStatusItem()
        self.buildWindow()
        self.refresh_(None)
        self.showWindow_()
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(9.0, self, "refresh:", None, True)
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.28, self, "hoverTick:", None, True)
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(0.22, self, "avatarTick:", None, True)

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
        self.window = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False,
        )
        self.window.setTitle_("LittleClaw Companion")
        self.window.setFloatingPanel_(True)
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setMovableByWindowBackground_(True)
        self.window.setHidesOnDeactivate_(False)
        self.window.setReleasedWhenClosed_(False)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorFullScreenAuxiliary
        )

        self.rootView = BubbleView.alloc().initWithFrame_(NSMakeRect(0, 0, COLLAPSED_W, COLLAPSED_H))
        self.rootView.setWantsLayer_(True)
        self.window.setContentView_(self.rootView)

        self.avatarView = AvatarView.alloc().initWithFrame_(NSMakeRect(12, 16, 80, 72))
        self.rootView.addSubview_(self.avatarView)
        self.nameField = self.makeLabel(NSMakeRect(10, 10, 84, 18), "小钳", 13, True)
        self.rootView.addSubview_(self.nameField)
        self.levelField = self.makeLabel(NSMakeRect(10, -2, 82, 14), "Lv.1", 10, False)
        self.rootView.addSubview_(self.levelField)

        self.heroCard = self.makeCard(NSMakeRect(14, 208, 392, 138))
        self.rootView.addSubview_(self.heroCard)
        self.statsCard = self.makeCard(NSMakeRect(14, 140, 392, 54))
        self.rootView.addSubview_(self.statsCard)
        self.composeCard = self.makeCard(NSMakeRect(14, 14, 392, 114))
        self.rootView.addSubview_(self.composeCard)

        self.detailAvatar = AvatarView.alloc().initWithFrame_(NSMakeRect(274, 228, 114, 96))
        self.rootView.addSubview_(self.detailAvatar)
        self.presenceBadge = PresenceBadgeView.alloc().initWithFrame_(NSMakeRect(24, 220, 230, 42))
        self.rootView.addSubview_(self.presenceBadge)
        self.detailName = self.makeLabel(NSMakeRect(28, 300, 180, 26), "小钳", 22, True)
        self.rootView.addSubview_(self.detailName)
        self.detailStage = self.makeMutedPill(NSMakeRect(28, 270, 150, 22), "Lv.1 · 琥珀幼体")
        self.rootView.addSubview_(self.detailStage)
        self.detailText = self.makeLabel(NSMakeRect(38, 230, 206, 22), "我会跟着你，有事就点我。", 12, False)
        self.rootView.addSubview_(self.detailText)
        self.statsField = self.makeLabel(NSMakeRect(28, 162, 188, 18), "亲密 100 · 精力 66", 11, False)
        self.rootView.addSubview_(self.statsField)
        self.progressField = self.makeLabel(NSMakeRect(28, 144, 188, 18), "饥饿 0 · XP 8/100", 11, False)
        self.rootView.addSubview_(self.progressField)
        self.queueField = self.makeLabel(NSMakeRect(236, 146, 150, 28), "学习队列还很安静。", 10, False)
        self.rootView.addSubview_(self.queueField)
        self.inputField = self.makeInput(NSMakeRect(28, 76, 364, 28), "学习主题 / 截图要求")
        self.rootView.addSubview_(self.inputField)
        self.secondaryField = self.makeInput(NSMakeRect(28, 42, 364, 28), "目标 / 约束 / 想让它沉淀成什么")
        self.rootView.addSubview_(self.secondaryField)

        self.quickFeed = self.makeButton(NSMakeRect(274, 206, 52, 22), "喂食", "feed:", "soft")
        self.quickPlay = self.makeButton(NSMakeRect(336, 206, 52, 22), "玩耍", "play:", "soft")
        self.quickNap = self.makeButton(NSMakeRect(305, 182, 52, 22), "小睡", "nap:", "soft")
        self.quickLearn = self.makeButton(NSMakeRect(278, 12, 52, 24), "学习", "learn:", "accent")
        self.quickShot = self.makeButton(NSMakeRect(340, 12, 52, 24), "截图", "screenshot:", "accent")

        for view in [
            self.detailName,
            self.detailStage,
            self.detailText,
            self.statsField,
            self.progressField,
            self.queueField,
            self.inputField,
            self.secondaryField,
            self.quickFeed,
            self.quickPlay,
            self.quickNap,
            self.quickLearn,
            self.quickShot,
        ]:
            self.rootView.addSubview_(view)

        self.setExpanded_(False)

    @objc.python_method
    def default_frame(self, width, height):
        screen = NSScreen.mainScreen()
        visible = screen.visibleFrame() if screen is not None else NSMakeRect(120, 120, 1440, 900)
        pos = self.load_position()
        x = pos.get("x", visible.origin.x + visible.size.width - width - 48)
        y = pos.get("y", visible.origin.y + (visible.size.height - height) / 2)
        return NSMakeRect(x, y, width, height)

    @objc.python_method
    def makeLabel(self, frame, text, size, bold):
        field = NSTextField.alloc().initWithFrame_(frame)
        field.setStringValue_(text)
        field.setBezeled_(False)
        field.setDrawsBackground_(False)
        field.setEditable_(False)
        field.setSelectable_(False)
        field.setTextColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.18, 0.15, 0.14, 0.96))
        field.setFont_(NSFont.boldSystemFontOfSize_(size) if bold else NSFont.systemFontOfSize_(size))
        field.setLineBreakMode_(4)
        return field

    @objc.python_method
    def makeMutedPill(self, frame, text):
        field = self.makeLabel(frame, text, 11, False)
        field.setAlignment_(1)
        field.setBezeled_(False)
        field.setDrawsBackground_(True)
        field.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.99, 0.92, 0.88, 0.94))
        return field

    @objc.python_method
    def makeCard(self, frame):
        view = NSView.alloc().initWithFrame_(frame)
        view.setWantsLayer_(True)
        view.layer().setCornerRadius_(18)
        view.layer().setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.56).CGColor())
        view.layer().setBorderWidth_(0.8)
        view.layer().setBorderColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.85, 0.76, 0.65).CGColor())
        return view

    @objc.python_method
    def makeButton(self, frame, title, selector, tone):
        button = NSButton.alloc().initWithFrame_(frame)
        button.setTitle_(title)
        button.setTarget_(self)
        button.setAction_(selector)
        button.setBezelStyle_(NSRoundedBezelStyle)
        button.setFont_(NSFont.systemFontOfSize_(11))
        if tone == "accent":
            button.setBezelColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.98, 0.72, 0.56, 0.92))
        else:
            button.setBezelColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(0.97, 0.93, 0.90, 0.94))
        return button

    @objc.python_method
    def makeInput(self, frame, placeholder):
        field = NSTextField.alloc().initWithFrame_(frame)
        field.setBezeled_(True)
        field.setDrawsBackground_(True)
        field.setEditable_(True)
        field.setSelectable_(True)
        field.setFont_(NSFont.systemFontOfSize_(12))
        field.setPlaceholderString_(placeholder)
        field.setBackgroundColor_(NSColor.colorWithCalibratedRed_green_blue_alpha_(1.0, 1.0, 1.0, 0.90))
        field.cell().setUsesSingleLineMode_(True)
        field.setFocusRingType_(1)
        return field

    def refresh_(self, _timer):
        pet = fetch_json(PET_API)
        if not pet:
            return
        self.pet = pet
        self.nameField.setStringValue_(pet.get("name", "小钳"))
        self.levelField.setStringValue_(f"Lv.{pet.get('level', 1)}")
        self.detailName.setStringValue_(pet.get("name", "小钳"))
        self.detailStage.setStringValue_(f"Lv.{pet.get('level', 1)} · {pet.get('stage_title', '琥珀幼体')}")
        self.detailText.setStringValue_(pet.get("stage_presence", "我会跟着你，有事就点我。"))
        self.statsField.setStringValue_(f"亲密 {pet.get('affinity', 0)} · 精力 {pet.get('energy', 0)}")
        self.progressField.setStringValue_(f"饥饿 {pet.get('hunger', 0)} · XP {pet.get('xp', 0)}/100")
        self.queueField.setStringValue_(self.build_queue_summary())
        mood = self.current_mood()
        self.avatarView.mood = mood
        self.detailAvatar.mood = mood
        if self.statusItem and self.statusItem.button() is not None:
            self.statusItem.button().setTitle_(f"{pet.get('emoji', '🦞')} {pet.get('name', '小钳')}")

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
            if not self.expanded and self.hoverTicks >= 2:
                self.setExpanded_(True)
        else:
            self.hoverTicks = 0
            self.leaveTicks += 1
            if self.expanded and self.leaveTicks >= 4:
                self.setExpanded_(False)
        self.lastMouseInside = inside

    def avatarTick_(self, _timer):
        if self.isCompactMode and not self.window.isVisible():
            return
        self.avatarPhase = (self.avatarPhase + 1) % 40
        blink = 1.0 if self.avatarPhase in (18, 19) else 0.0
        offset = -0.8 if self.isCompactMode else (-1.6 if self.avatarPhase < 20 else 1.6)
        self.avatarView.blink = blink
        self.detailAvatar.blink = blink
        self.avatarView.float_offset = offset
        self.detailAvatar.float_offset = offset
        self.avatarView.setNeedsDisplay_(True)
        if self.expanded:
            self.detailAvatar.setNeedsDisplay_(True)

    @objc.python_method
    def setExpanded_(self, expanded):
        self.expanded = expanded
        self.isCompactMode = not expanded
        width = EXPANDED_W if expanded else COLLAPSED_W
        height = EXPANDED_H if expanded else COLLAPSED_H
        frame = self.window.frame()
        new_x = frame.origin.x
        new_y = frame.origin.y
        self.window.setFrame_display_(NSMakeRect(new_x, new_y, width, height), True)
        self.rootView.setFrame_(NSMakeRect(0, 0, width, height))
        self.rootView.compact = not expanded
        self.rootView.setNeedsDisplay_(True)

        compact_hidden = expanded
        self.avatarView.setHidden_(compact_hidden)
        self.nameField.setHidden_(True)
        self.levelField.setHidden_(True)
        self.window.setAlphaValue_(0.99 if expanded else 0.96)

        detail_hidden = not expanded
        for view in [
            self.detailName,
            self.detailStage,
            self.detailText,
            self.statsField,
            self.progressField,
            self.queueField,
            self.inputField,
            self.secondaryField,
            self.quickFeed,
            self.quickPlay,
            self.quickNap,
            self.quickLearn,
            self.quickShot,
            self.detailAvatar,
            self.heroCard,
            self.statsCard,
            self.composeCard,
        ]:
            view.setHidden_(detail_hidden)

    def feed_(self, _sender):
        self.run_action("feed", "小钳吃饱了，贴近了一点。")

    def play_(self, _sender):
        self.run_action("play", "刚陪它玩了一会，状态热起来了。")

    def nap_(self, _sender):
        self.run_action("nap", "它眯了一会，现在精神点了。")

    def learn_(self, _sender):
        topic = self.inputField.stringValue().strip() or "桌面 Companion 学习主题"
        goal = self.secondaryField.stringValue().strip() or "持续学习、沉淀方案并整理 skill 草稿"
        subprocess.Popen([LEARNING_SCRIPT, topic, goal])
        self.detailText.setStringValue_(f"已开始学习：{topic}")
        self.queueField.setStringValue_(self.build_queue_summary(force_refresh=True))

    def screenshot_(self, _sender):
        topic = self.inputField.stringValue().strip() or "桌面 Companion 截图协作"
        goal = self.secondaryField.stringValue().strip() or "请结合截图理解当前界面并给出下一步建议"
        subprocess.Popen([SCREENSHOT_SCRIPT, topic, goal])
        self.detailText.setStringValue_(f"准备截图：{topic}")
        self.queueField.setStringValue_(self.build_queue_summary(force_refresh=True))

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
    def run_action(self, action: str, text: str):
        data = post_action(action)
        if isinstance(data, dict) and isinstance(data.get("pet"), dict):
            self.pet = data["pet"]
            self.refresh_(None)
        self.detailText.setStringValue_(text)

    @objc.python_method
    def current_mood(self):
        energy = int(self.pet.get("energy", 60) or 0)
        hunger = int(self.pet.get("hunger", 0) or 0)
        affinity = int(self.pet.get("affinity", 60) or 0)
        if energy < 25:
            return "sleepy"
        if affinity > 85 and hunger < 35:
            return "happy"
        return "calm"

    @objc.python_method
    def build_queue_summary(self, force_refresh=False):
        try:
            requests = sorted(LEARNING_REQ_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
            shots = sorted(LEARNING_SHOT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            latest_req = requests[0].stem if requests else "无"
            summary = f"学习请求 {len(requests)} 条，截图 {len(shots)} 张，最近：{latest_req[:28]}"
            if force_refresh or summary != self.lastSummary:
                self.lastSummary = summary
            return self.lastSummary
        except Exception:
            return "学习队列暂时不可读，但功能仍可用。"

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
            POSITION_FILE.write_text(
                json.dumps({"x": frame.origin.x, "y": frame.origin.y}, ensure_ascii=False, indent=2),
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
