#!/usr/bin/env python3
import json
import os
import subprocess
import tkinter as tk
from pathlib import Path
from tkinter import ttk
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

PET_API = "http://127.0.0.1:18793"
PET_STATE_FILE = Path("/Users/baijingting/.openclaw/workspace/memory/pet-state.json")
POSITION_FILE = Path("/Users/baijingting/.openclaw/workspace/memory/companion-position.json")
LEARNING_SCRIPT = "/Users/baijingting/.openclaw/scripts/openclaw-learning-intake.sh"
SCREENSHOT_SCRIPT = "/Users/baijingting/.openclaw/scripts/openclaw-screenshot-intake.sh"
LEARNING_LAB_DIR = Path("/Users/baijingting/.openclaw/workspace/learning-lab")


class LittleClawCompanion:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#F4F7FB")
        self.root.geometry("278x118+1040+240")
        self.root.title("LittleClaw Companion")
        self.root.resizable(False, False)

        self.drag_start = None
        self.detail_open = False
        self.hovering = False
        self.pet = self.load_local_pet()
        self.status_text = tk.StringVar(value="我会在所有页面上陪着你。")
        self.topic_var = tk.StringVar()
        self.goal_var = tk.StringVar()
        self.position = self.load_position()
        self.queue_items = []

        self.build_ui()
        self.apply_position(self.position["x"], self.position["y"])
        self.refresh_pet()
        self.schedule_refresh()
        self.schedule_idle_nudge()
        self.root.after(120, self.bring_to_front)

    def build_ui(self):
        self.shell = tk.Frame(self.root, bg="#F4F7FB")
        self.shell.pack(fill="both", expand=True, padx=8, pady=8)

        self.card = tk.Frame(self.shell, bg="#F8FBFF", bd=0, highlightthickness=1, highlightbackground="#E7EEF8")
        self.card.pack(fill="both", expand=True)

        self.compact = tk.Frame(self.card, bg="#F8FBFF")
        self.compact.pack(fill="x", padx=10, pady=10)
        self.compact.bind("<Enter>", self.on_enter)
        self.compact.bind("<Leave>", self.on_leave)

        self.avatar = tk.Canvas(self.compact, width=48, height=48, bg="#F8FBFF", highlightthickness=0, cursor="hand2")
        self.avatar.pack(side="left")
        self.avatar.bind("<Button-1>", self.toggle_detail)
        self.avatar.bind("<ButtonPress-1>", self.start_drag)
        self.avatar.bind("<B1-Motion>", self.on_drag)
        self.avatar.bind("<ButtonRelease-1>", self.finish_drag)

        self.info = tk.Frame(self.compact, bg="#F8FBFF")
        self.info.pack(side="left", padx=10)
        self.info.bind("<ButtonPress-1>", self.start_drag)
        self.info.bind("<B1-Motion>", self.on_drag)
        self.info.bind("<ButtonRelease-1>", self.finish_drag)

        self.name_label = tk.Label(self.info, text="小钳", font=("PingFang SC", 14, "bold"), bg="#F8FBFF", fg="#1F2A44")
        self.name_label.pack(anchor="w")
        self.stage_label = tk.Label(self.info, text="Lv.1 · 琥珀幼体", font=("PingFang SC", 10), bg="#F8FBFF", fg="#72809A")
        self.stage_label.pack(anchor="w", pady=(2, 0))

        self.chevron = tk.Label(self.compact, text="▾", font=("SF Pro", 11), bg="#F8FBFF", fg="#94A3B8", cursor="hand2")
        self.chevron.pack(side="right", padx=(8, 0))
        self.chevron.bind("<Button-1>", self.toggle_detail)

        self.quick = tk.Frame(self.card, bg="#F8FBFF")
        self.quick.pack(fill="x", padx=10, pady=(0, 8))
        self.quick.pack_forget()

        self.quick_inner = tk.Frame(self.quick, bg="#F8FBFF")
        self.quick_inner.pack(anchor="e")
        for text, caption, command, color in [
            ("喂", "投喂", lambda: self.pet_action("feed"), "#FFE8D8"),
            ("玩", "互动", lambda: self.pet_action("play"), "#E6F1FF"),
            ("睡", "休息", lambda: self.pet_action("nap"), "#EFE7FF"),
            ("学", "学习", self.open_detail, "#E6F7EC"),
            ("截", "截屏", self.capture_and_queue, "#EEF2F6"),
        ]:
            cell = tk.Frame(self.quick_inner, bg="#F8FBFF")
            cell.pack(side="left", padx=4)
            btn = tk.Label(cell, text=text, bg=color, fg="#334155", width=3, height=1, font=("PingFang SC", 10, "bold"), cursor="hand2", relief="flat")
            btn.pack()
            tip = tk.Label(cell, text=caption, bg="#F8FBFF", fg="#94A3B8", font=("PingFang SC", 8))
            tip.pack(pady=(3, 0))
            btn.bind("<Button-1>", lambda _e, cmd=command: cmd())

        self.detail = tk.Frame(self.card, bg="#FFFFFF")
        self.detail.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.detail.pack_forget()

        self.detail_header = tk.Frame(self.detail, bg="#FFFFFF")
        self.detail_header.pack(fill="x", pady=(6, 8))
        self.detail_header.bind("<ButtonPress-1>", self.start_drag)
        self.detail_header.bind("<B1-Motion>", self.on_drag)
        self.detail_header.bind("<ButtonRelease-1>", self.finish_drag)

        tk.Label(self.detail_header, text="详细面板", font=("PingFang SC", 12, "bold"), bg="#FFFFFF", fg="#22314B").pack(side="left")
        close = tk.Label(self.detail_header, text="×", font=("SF Pro", 16), bg="#FFFFFF", fg="#72809A", cursor="hand2")
        close.pack(side="right")
        close.bind("<Button-1>", self.toggle_detail)

        self.scroll_canvas = tk.Canvas(self.detail, bg="#FFFFFF", highlightthickness=0, width=320, height=410)
        self.scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self.detail, orient="vertical", command=self.scroll_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.configure(yscrollcommand=scrollbar.set)
        self.scroll_body = tk.Frame(self.scroll_canvas, bg="#FFFFFF")
        self.scroll_canvas.create_window((0, 0), window=self.scroll_body, anchor="nw")
        self.scroll_body.bind("<Configure>", lambda _e: self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all")))

        self.build_detail_body()

    def build_detail_body(self):
        self.hero = tk.Frame(self.scroll_body, bg="#FFF4EC")
        self.hero.pack(fill="x", pady=(0, 10))
        self.hero_canvas = tk.Canvas(self.hero, width=292, height=132, bg="#FFF4EC", highlightthickness=0)
        self.hero_canvas.pack(fill="x")

        self.presence_label = tk.Label(self.scroll_body, textvariable=self.status_text, justify="left", wraplength=280, font=("PingFang SC", 11), bg="#FFFFFF", fg="#3A4A66")
        self.presence_label.pack(fill="x", pady=(0, 12))

        self.stat_frame = tk.Frame(self.scroll_body, bg="#FFFFFF")
        self.stat_frame.pack(fill="x", pady=(0, 10))
        self.stat_vars = {}
        for title in ["亲密度", "精力值", "饥饿值"]:
            block = tk.Frame(self.stat_frame, bg="#FFFFFF")
            block.pack(fill="x", pady=4)
            head = tk.Frame(block, bg="#FFFFFF")
            head.pack(fill="x")
            tk.Label(head, text=title, font=("PingFang SC", 10), bg="#FFFFFF", fg="#55657F").pack(side="left")
            value = tk.Label(head, text="0", font=("PingFang SC", 10, "bold"), bg="#FFFFFF", fg="#334155")
            value.pack(side="right")
            bar_bg = tk.Frame(block, bg="#E9EEF5", height=8)
            bar_bg.pack(fill="x", pady=(4, 0))
            bar_bg.pack_propagate(False)
            bar_fg = tk.Frame(bar_bg, bg="#FF9B5A", width=0)
            bar_fg.pack(fill="y", side="left")
            self.stat_vars[title] = (value, bar_fg, bar_bg)

        self.evo_card = tk.Frame(self.scroll_body, bg="#FFF7F0")
        self.evo_card.pack(fill="x", pady=(0, 10))
        tk.Label(self.evo_card, text="进化进度", font=("PingFang SC", 11, "bold"), bg="#FFF7F0", fg="#23314A").pack(anchor="w", padx=12, pady=(10, 4))
        self.evo_text = tk.Label(self.evo_card, text="", justify="left", wraplength=270, font=("PingFang SC", 10), bg="#FFF7F0", fg="#5B677F")
        self.evo_text.pack(fill="x", padx=12, pady=(0, 8))
        evo_bg = tk.Frame(self.evo_card, bg="#E6EAF2", height=8)
        evo_bg.pack(fill="x", padx=12, pady=(0, 10))
        evo_bg.pack_propagate(False)
        self.evo_bar = tk.Frame(evo_bg, bg="#FFB24A", width=0)
        self.evo_bar.pack(fill="y", side="left")
        self.evo_bar_bg = evo_bg

        self.learn_card = tk.Frame(self.scroll_body, bg="#EEF8F2")
        self.learn_card.pack(fill="x", pady=(0, 10))
        tk.Label(self.learn_card, text="外部学习", font=("PingFang SC", 11, "bold"), bg="#EEF8F2", fg="#23314A").pack(anchor="w", padx=12, pady=(10, 4))
        tk.Label(self.learn_card, text="想让它持续学什么，就从这里入队。", font=("PingFang SC", 10), bg="#EEF8F2", fg="#61708A").pack(anchor="w", padx=12, pady=(0, 6))
        topic_entry = tk.Entry(self.learn_card, textvariable=self.topic_var, relief="flat", font=("PingFang SC", 11), bg="#FFFFFF")
        topic_entry.pack(fill="x", padx=12, pady=4, ipady=8)
        goal_entry = tk.Entry(self.learn_card, textvariable=self.goal_var, relief="flat", font=("PingFang SC", 10), bg="#FFFFFF")
        goal_entry.pack(fill="x", padx=12, pady=4, ipady=8)
        actions = tk.Frame(self.learn_card, bg="#EEF8F2")
        actions.pack(fill="x", padx=12, pady=(6, 12))
        self.make_card_button(actions, "入队学习", self.queue_learning, "#1E8E5A", "#FFFFFF").pack(side="left", padx=(0, 6))
        self.make_card_button(actions, "全局截屏", self.capture_and_queue, "#1F2937", "#FFFFFF").pack(side="left")

        self.meta_card = tk.Frame(self.scroll_body, bg="#EEF4FF")
        self.meta_card.pack(fill="x")
        self.meta_text = tk.Label(self.meta_card, text="", justify="left", wraplength=270, font=("PingFang SC", 10), bg="#EEF4FF", fg="#53627C")
        self.meta_text.pack(fill="x", padx=12, pady=12)

        self.queue_card = tk.Frame(self.scroll_body, bg="#F5F7FB")
        self.queue_card.pack(fill="x", pady=(10, 0))
        tk.Label(self.queue_card, text="学习队列 / 最近产物", font=("PingFang SC", 11, "bold"), bg="#F5F7FB", fg="#23314A").pack(anchor="w", padx=12, pady=(10, 4))
        self.queue_text = tk.Label(self.queue_card, text="还没有学习请求。", justify="left", wraplength=270, font=("PingFang SC", 10), bg="#F5F7FB", fg="#61708A")
        self.queue_text.pack(fill="x", padx=12, pady=(0, 12))

    def make_card_button(self, parent, text, command, bg, fg):
        button = tk.Label(parent, text=text, bg=bg, fg=fg, font=("PingFang SC", 10, "bold"), padx=14, pady=8, cursor="hand2")
        button.bind("<Button-1>", lambda _e: command())
        return button

    def toggle_detail(self, _event=None):
        self.detail_open = not self.detail_open
        if self.detail_open:
            self.quick.pack(fill="x", padx=10, pady=(0, 8))
            self.detail.pack(fill="both", expand=True, padx=10, pady=(0, 10))
            self.root.geometry("372x640")
        else:
            self.detail.pack_forget()
            if not self.hovering:
                self.quick.pack_forget()
            self.root.geometry("278x118")

    def open_detail(self, _event=None):
        if not self.detail_open:
            self.toggle_detail()

    def on_enter(self, _event=None):
        self.hovering = True
        if not self.quick.winfo_ismapped():
            self.quick.pack(fill="x", padx=10, pady=(0, 8))
        if not self.detail_open:
            self.root.geometry("278x162")

    def on_leave(self, _event=None):
        self.hovering = False
        if not self.detail_open:
            self.quick.pack_forget()
            self.root.geometry("278x118")

    def start_drag(self, event):
        self.drag_start = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())

    def on_drag(self, event):
        if not self.drag_start:
            return
        sx, sy, wx, wy = self.drag_start
        nx = wx + event.x_root - sx
        ny = wy + event.y_root - sy
        self.root.geometry(f"+{nx}+{ny}")

    def finish_drag(self, _event):
        self.drag_start = None
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        screen_w = self.root.winfo_screenwidth()
        width = self.root.winfo_width()
        snap_x = 18 if x < screen_w / 2 else screen_w - width - 18
        self.apply_position(snap_x, max(18, y))
        self.save_position(snap_x, max(18, y))

    def apply_position(self, x, y):
        self.root.geometry(f"+{int(x)}+{int(y)}")

    def save_position(self, x, y):
        POSITION_FILE.parent.mkdir(parents=True, exist_ok=True)
        POSITION_FILE.write_text(json.dumps({"x": x, "y": y}, ensure_ascii=False), encoding="utf-8")

    def load_position(self):
        if POSITION_FILE.exists():
            try:
                return json.loads(POSITION_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"x": 1040, "y": 240}

    def schedule_refresh(self):
        self.root.after(5000, self.periodic_refresh)

    def periodic_refresh(self):
        self.refresh_pet()
        self.schedule_refresh()

    def schedule_idle_nudge(self):
        self.root.after(45000, self.idle_nudge)

    def idle_nudge(self):
        if not self.drag_start and not self.detail_open:
            x = self.root.winfo_x()
            y = self.root.winfo_y()
            screen_h = self.root.winfo_screenheight()
            ny = y + 10 if y < screen_h / 2 else y - 10
            self.apply_position(x, max(18, min(screen_h - 180, ny)))
            self.save_position(x, max(18, min(screen_h - 180, ny)))
        self.schedule_idle_nudge()

    def bring_to_front(self):
        try:
            self.root.deiconify()
            self.root.lift()
            self.root.focus_force()
            self.root.attributes("-topmost", True)
        except Exception:
            pass

    def pet_action(self, action):
        payload = json.dumps({"action": action}).encode("utf-8")
        request = Request(f"{PET_API}/pet/action", data=payload, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            self.pet = data.get("pet", self.pet)
            self.status_text.set({
                "feed": "刚喂过了，现在它明显更贴近你了。",
                "play": "玩过之后精神了一圈，还想继续陪着你。",
                "nap": "它刚眯了一会，状态稳回来了。",
            }.get(action, "动作完成。"))
            self.render_pet()
        except Exception as exc:
            self.status_text.set(f"动作没接上，但我还在。{exc}")

    def queue_learning(self):
        topic = self.topic_var.get().strip()
        if not topic:
            self.status_text.set("先告诉小钳你想让它学什么。")
            return
        goal = self.goal_var.get().strip()
        self.run_script([LEARNING_SCRIPT, topic, goal], "学习请求已经入队，会慢慢沉淀成方案和经验。")

    def capture_and_queue(self):
        topic = self.topic_var.get().strip() or "截图协作"
        goal = self.goal_var.get().strip() or "请结合截图理解当前界面并给出下一步建议"
        self.run_script([SCREENSHOT_SCRIPT, topic, goal], "截图和说明已经入队给 OpenClaw 继续处理。")

    def run_script(self, args, success_text):
        try:
            output = subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
            self.status_text.set(success_text)
            self.goal_var.set("")
            self.topic_var.set("")
            self.meta_text.configure(text=f"最近结果：\n{output}\n\n上次同步：{self.pet.get('last_updated', '')}")
            self.refresh_queue()
        except subprocess.CalledProcessError as exc:
            self.status_text.set(exc.output.strip() or "执行失败")

    def refresh_pet(self):
        try:
            with urlopen(f"{PET_API}/pet", timeout=3) as response:
                self.pet = json.loads(response.read().decode("utf-8"))
        except URLError:
            self.pet = self.load_local_pet()
        except Exception:
            pass
        self.refresh_queue()
        self.render_pet()

    def load_local_pet(self):
        if PET_STATE_FILE.exists():
            try:
                return json.loads(PET_STATE_FILE.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "name": "小钳",
            "species": "琥珀小龙虾",
            "emoji": "🦞",
            "affinity": 75,
            "energy": 70,
            "hunger": 25,
            "level": 1,
            "xp": 0,
            "stage_title": "琥珀幼体",
            "stage_presence": "刚学会陪伴，会安静跟着你。",
            "last_action": "idle",
            "last_updated": "",
            "reward_streak": 0,
            "total_actions": 0,
        }

    def render_pet(self):
        pet = self.pet
        self.name_label.configure(text=pet.get("name", "小钳"))
        self.stage_label.configure(text=f"Lv.{pet.get('level', 1)} · {pet.get('stage_title', '琥珀幼体')}")
        self.draw_avatar()
        self.status_text.set(pet.get("stage_presence", "我会在你旁边。"))

        stats = {
            "亲密度": pet.get("affinity", 0),
            "精力值": pet.get("energy", 0),
            "饥饿值": pet.get("hunger", 0),
        }
        for title, value in stats.items():
            label, bar_fg, bar_bg = self.stat_vars[title]
            label.configure(text=str(value))
            bar_fg.configure(width=int((bar_bg.winfo_width() or 260) * max(0, min(100, value)) / 100))

        self.evo_text.configure(
            text=f"当前阶段：{pet.get('stage_title', '琥珀幼体')}\nXP {pet.get('xp', 0)}/100 · 累计互动 {pet.get('total_actions', 0)} 次"
        )
        self.evo_bar.configure(width=int((self.evo_bar_bg.winfo_width() or 260) * max(0, min(100, pet.get('xp', 0))) / 100))
        self.meta_text.configure(
            text=(
                f"奖励连击：{pet.get('reward_streak', 0)}\n"
                f"最近动作：{pet.get('last_action', 'idle')}\n"
                f"上次同步：{pet.get('last_updated', '') or '刚刚'}"
            )
        )
        self.render_queue()

    def refresh_queue(self):
        items = []
        req_dir = LEARNING_LAB_DIR / "requests"
        shot_dir = LEARNING_LAB_DIR / "screenshots"
        for path in sorted(req_dir.glob("*.md"), reverse=True)[:6]:
            items.append(("请求", path))
        for path in sorted(shot_dir.glob("*.png"), reverse=True)[:4]:
            items.append(("截图", path))
        items.sort(key=lambda item: item[1].stat().st_mtime if item[1].exists() else 0, reverse=True)
        self.queue_items = items[:6]

    def render_queue(self):
        if not self.queue_items:
            self.queue_text.configure(text="还没有学习请求。\n你可以输入想学习的主题，或者先来一次全局截屏入队。")
            return
        lines = []
        for kind, path in self.queue_items:
            stamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%m-%d %H:%M")
            lines.append(f"[{kind}] {stamp} · {path.name}")
        self.queue_text.configure(text="\n".join(lines))

    def draw_avatar(self):
        self.avatar.delete("all")
        self.avatar.create_oval(2, 2, 46, 46, fill="#FFF1E7", outline="#FFD1B5", width=1)
        self.avatar.create_oval(7, 7, 41, 41, fill="#FFB07D", outline="")
        self.avatar.create_oval(16, 18, 20, 22, fill="#253047", outline="")
        self.avatar.create_oval(28, 18, 32, 22, fill="#253047", outline="")
        self.avatar.create_arc(18, 22, 30, 30, start=200, extent=140, style="arc", outline="#8A4C37", width=2)
        self.avatar.create_arc(4, 14, 14, 24, start=30, extent=180, style="arc", outline="#FF8D65", width=2)
        self.avatar.create_arc(34, 14, 44, 24, start=-30, extent=180, style="arc", outline="#FF8D65", width=2)


if __name__ == "__main__":
    root = tk.Tk()
    app = LittleClawCompanion(root)
    root.mainloop()
