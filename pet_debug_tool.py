#!/usr/bin/env python3
import json
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk
from urllib.error import URLError
from urllib.request import Request, urlopen

from core.pet_core import PetRuntime
from runtime_config import load_runtime_config

RUNTIME = load_runtime_config()
PET_API = f"{RUNTIME['pet_api_base']}/pet"
PET_ACTION_API = f"{RUNTIME['pet_api_base']}/pet/action"
STATE_FILE = RUNTIME["openclaw_home"] / "workspace" / "memory" / "pet-state.json"
INSTALL_FILE = RUNTIME["openclaw_home"] / "workspace" / "memory" / "pet-install-id.txt"
PRESETS_ROOT = Path(__file__).resolve().parent / "presets"
LOG_FILE = Path("/tmp/littleclaw-debug-tool.log")
PET_RUNTIME = PetRuntime(
    state_file=STATE_FILE,
    install_seed_file=INSTALL_FILE,
    preset_root=PRESETS_ROOT,
    fallback_preset_root=PRESETS_ROOT,
)


def log(message: str):
    try:
        with LOG_FILE.open("a", encoding="utf-8") as fh:
            fh.write(message.rstrip() + "\n")
    except Exception:
        pass


def fetch_json(url: str):
    try:
        with urlopen(url, timeout=3) as response:
            return json.loads(response.read().decode("utf-8"))
    except URLError:
        return None
    except Exception:
        log("fetch_json failed:\n" + traceback.format_exc())
        return None


def post_json(url: str, payload: dict):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(url, data=body, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


class PetDebugTool:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("LittleClaw Debug Tool")
        self.root.geometry("820x920")
        self.root.minsize(780, 820)
        self.root.configure(bg="#fff7f2")

        self.current_pet = {}

        self.species_var = tk.StringVar(value="mecha")
        self.stage_var = tk.StringVar(value="seed")
        self.rarity_var = tk.StringVar(value="common")
        self.level_var = tk.StringVar(value="1")
        self.xp_var = tk.StringVar(value="0")
        self.affinity_var = tk.StringVar(value="75")
        self.energy_var = tk.StringVar(value="78")
        self.hunger_var = tk.StringVar(value="22")
        self.streak_var = tk.StringVar(value="0")
        self.progress_var = tk.StringVar(value="0")

        self.send_text_var = tk.StringVar(value="测试一下发送链路")
        self.learn_topic_var = tk.StringVar(value="测试学习请求")
        self.learn_goal_var = tk.StringVar(value="验证学习链路是否会推动成长")
        self.reply_topic_var = tk.StringVar(value="测试真实回执")
        self.reply_text_var = tk.StringVar(value="测试回复完成，验证 XP / 等级 / 进化提示是否联动。")

        self.stage_menu = None
        self.status_var = tk.StringVar(value="正在初始化调试工具…")

        self.build_ui()
        self.refresh_state(initial=True)
        self.root.after(2500, self.periodic_refresh)

    def build_ui(self):
        style = ttk.Style()
        try:
            style.theme_use("aqua")
        except Exception:
            pass

        shell = ttk.Frame(self.root, padding=16)
        shell.pack(fill="both", expand=True)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(2, weight=1)

        top = ttk.Frame(shell)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(0, weight=1)
        ttk.Label(top, text="LittleClaw 调试工具", font=("PingFang SC", 18, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Button(top, text="刷新状态", command=self.refresh_state).grid(row=0, column=1, sticky="e")

        ttk.Label(shell, textvariable=self.status_var, foreground="#7a6158").grid(row=1, column=0, sticky="ew", pady=(6, 10))

        notebook = ttk.Notebook(shell)
        notebook.grid(row=2, column=0, sticky="nsew")

        state_tab = ttk.Frame(notebook, padding=14)
        action_tab = ttk.Frame(notebook, padding=14)
        log_tab = ttk.Frame(notebook, padding=14)
        notebook.add(state_tab, text="状态调试")
        notebook.add(action_tab, text="动作链路")
        notebook.add(log_tab, text="日志")

        self.build_state_tab(state_tab)
        self.build_action_tab(action_tab)
        self.build_log_tab(log_tab)
        self.write_log("调试工具已启动，等待操作。")
        self.on_species_change()

    def build_state_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        summary_box = ttk.LabelFrame(parent, text="当前状态", padding=12)
        summary_box.grid(row=0, column=0, sticky="ew")
        self.summary_text = tk.Text(summary_box, height=7, wrap="word", relief="solid", bd=1)
        self.summary_text.pack(fill="x")

        editor_box = ttk.LabelFrame(parent, text="真实状态覆写", padding=12)
        editor_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        for idx in range(4):
            editor_box.columnconfigure(idx, weight=1)

        self.build_labeled_option(editor_box, 0, 0, "种族", self.species_var, ["lobster", "sprite", "mecha"], self.on_species_change)
        self.build_labeled_option(editor_box, 0, 1, "阶段", self.stage_var, ["seed"], None, store_stage=True)
        self.build_labeled_option(editor_box, 0, 2, "稀有度", self.rarity_var, ["common", "rare", "epic", "legendary", "mythic"], None)
        self.build_labeled_entry(editor_box, 1, 0, "等级", self.level_var)
        self.build_labeled_entry(editor_box, 1, 1, "经验", self.xp_var)
        self.build_labeled_entry(editor_box, 1, 2, "亲密", self.affinity_var)
        self.build_labeled_entry(editor_box, 1, 3, "精力", self.energy_var)
        self.build_labeled_entry(editor_box, 2, 0, "饥饿", self.hunger_var)
        self.build_labeled_entry(editor_box, 2, 1, "连击", self.streak_var)
        self.build_labeled_entry(editor_box, 2, 2, "进度", self.progress_var)

        actions = ttk.Frame(editor_box)
        actions.grid(row=3, column=0, columnspan=4, sticky="w", pady=(14, 0))
        ttk.Button(actions, text="应用状态", command=self.apply_state).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="模拟升级", command=self.simulate_level_up).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="模拟进化", command=self.simulate_evolution).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="恢复真实", command=self.reload_from_pet).pack(side="left")

    def build_action_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        care_box = ttk.LabelFrame(parent, text="基础动作", padding=12)
        care_box.grid(row=0, column=0, sticky="ew")
        for idx, (label, action) in enumerate([
            ("喂食", "feed"),
            ("玩耍", "play"),
            ("小睡", "nap"),
            ("聚焦", "focus_companion"),
            ("确认初遇", "acknowledge_intro"),
        ]):
            ttk.Button(care_box, text=label, command=lambda act=action: self.trigger_action(act, {})).grid(row=0, column=idx, padx=(0, 8), sticky="w")

        send_box = ttk.LabelFrame(parent, text="发送链路", padding=12)
        send_box.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        ttk.Entry(send_box, textvariable=self.send_text_var).pack(fill="x")
        ttk.Button(send_box, text="触发发送链路", command=lambda: self.trigger_action("send_message", {
            "text": self.send_text_var.get().strip(),
        })).pack(anchor="w", pady=(8, 0))

        learn_box = ttk.LabelFrame(parent, text="学习链路", padding=12)
        learn_box.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(learn_box, text="主题").pack(anchor="w")
        ttk.Entry(learn_box, textvariable=self.learn_topic_var).pack(fill="x", pady=(2, 8))
        ttk.Label(learn_box, text="目标").pack(anchor="w")
        ttk.Entry(learn_box, textvariable=self.learn_goal_var).pack(fill="x", pady=(2, 8))
        ttk.Button(learn_box, text="触发学习", command=lambda: self.trigger_action("learn_request", {
            "topic": self.learn_topic_var.get().strip(),
            "goal": self.learn_goal_var.get().strip(),
        })).pack(anchor="w")

        reply_box = ttk.LabelFrame(parent, text="真实回执链路", padding=12)
        reply_box.grid(row=3, column=0, sticky="ew", pady=(12, 0))
        ttk.Label(reply_box, text="主题").pack(anchor="w")
        ttk.Entry(reply_box, textvariable=self.reply_topic_var).pack(fill="x", pady=(2, 8))
        ttk.Label(reply_box, text="回执文本").pack(anchor="w")
        ttk.Entry(reply_box, textvariable=self.reply_text_var).pack(fill="x", pady=(2, 8))
        ttk.Button(reply_box, text="触发回执完成", command=lambda: self.trigger_action("reply_complete", {
            "topic": self.reply_topic_var.get().strip(),
            "reply": self.reply_text_var.get().strip(),
        })).pack(anchor="w")

    def build_log_tab(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        self.log_text = tk.Text(parent, wrap="word", relief="solid", bd=1)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

    def build_labeled_option(self, parent, row: int, column: int, label: str, variable: tk.StringVar, values, command, store_stage=False):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="ew", padx=(0, 10), pady=(0, 10))
        ttk.Label(frame, text=label).pack(anchor="w")
        combo = ttk.Combobox(frame, textvariable=variable, values=values, state="readonly")
        combo.pack(fill="x", pady=(4, 0))
        if command:
            combo.bind("<<ComboboxSelected>>", lambda _event: command())
        if store_stage:
            self.stage_menu = combo

    def build_labeled_entry(self, parent, row: int, column: int, label: str, variable: tk.StringVar):
        frame = ttk.Frame(parent)
        frame.grid(row=row, column=column, sticky="ew", padx=(0, 10), pady=(0, 10))
        ttk.Label(frame, text=label).pack(anchor="w")
        ttk.Entry(frame, textvariable=variable).pack(fill="x", pady=(4, 0))

    def write_log(self, message: str):
        line = message.strip()
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        log(line)

    def set_summary(self, text: str):
        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", "end")
        self.summary_text.insert("1.0", text)
        self.summary_text.configure(state="disabled")

    def stage_options(self, species_id: str):
        return PET_RUNTIME.evolution_stages(species_id)

    def update_stage_menu(self):
        stages = self.stage_options(self.species_var.get())
        stage_values = [stage["id"] for stage in stages] or ["seed"]
        if self.stage_menu is not None:
            self.stage_menu.configure(values=stage_values)
        if self.stage_var.get() not in stage_values:
            self.stage_var.set(stage_values[0])

    def on_species_change(self, *_args):
        self.update_stage_menu()

    def parse_int(self, variable: tk.StringVar, fallback: int = 0):
        try:
            return int(str(variable.get()).strip())
        except Exception:
            return fallback

    def current_state(self):
        pet = fetch_json(PET_API)
        if isinstance(pet, dict):
            return pet
        return PET_RUNTIME.load_state()

    def refresh_state(self, initial: bool = False):
        self.current_pet = self.current_state()
        pet = self.current_pet
        self.set_summary(
            "\n".join([
                f"名称：{pet.get('name', '伙伴')} · 种族：{pet.get('species_id', 'lobster')} · 阶段：{pet.get('stage_title', 'seed')}",
                f"等级：Lv.{pet.get('level', 1)} · XP {pet.get('xp', 0)}/100 · 稀有度：{pet.get('rarity', 'common')}",
                f"亲密：{pet.get('affinity', 0)} · 精力：{pet.get('energy', 0)} · 饥饿：{pet.get('hunger', 0)}",
                f"连击：{pet.get('reward_streak', 0)} · 进度分：{pet.get('progress_score', pet.get('task_score', 0))}",
                f"最近动作：{pet.get('last_action', 'init')} · 下一阶段：{(pet.get('next_stage') or {}).get('title') or '无'}",
                f"提示：{pet.get('stage_presence', '')}",
            ])
        )
        self.reload_from_pet()
        self.status_var.set("已同步真实宠物状态。")
        if not initial:
            self.write_log("已刷新当前真实状态。")

    def reload_from_pet(self):
        pet = self.current_pet or self.current_state()
        self.species_var.set(str(pet.get("species_id", "lobster")))
        self.update_stage_menu()
        self.stage_var.set(str(pet.get("stage_id", "seed")))
        self.rarity_var.set(str(pet.get("rarity", "common")).lower())
        self.level_var.set(str(int(pet.get("level", 1))))
        self.xp_var.set(str(int(pet.get("xp", 0))))
        self.affinity_var.set(str(int(pet.get("affinity", 75))))
        self.energy_var.set(str(int(pet.get("energy", 78))))
        self.hunger_var.set(str(int(pet.get("hunger", 22))))
        self.streak_var.set(str(int(pet.get("reward_streak", 0))))
        self.progress_var.set(str(int(pet.get("task_score", pet.get("progress_score", 0)))))

    def stage_adjusted_state(self, state: dict, species_id: str, stage_id: str) -> dict:
        stages = self.stage_options(species_id)
        index = next((idx for idx, item in enumerate(stages) if item["id"] == stage_id), 0)
        target = stages[index]
        nxt = stages[index + 1] if index + 1 < len(stages) else None

        level = max(self.parse_int(self.level_var, 1), int(target["min_level"]))
        affinity = max(self.parse_int(self.affinity_var, 0), int(target["min_affinity"]))
        streak = max(self.parse_int(self.streak_var, 0), int(target["min_streak"]))
        progress = max(self.parse_int(self.progress_var, 0), int(target.get("min_progress", 0)))

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
        return state

    def apply_state(self):
        try:
            state = PET_RUNTIME.load_state()
            species_id = self.species_var.get()
            species = PET_RUNTIME.species_config(species_id)
            stage_id = self.stage_var.get()
            state["species_id"] = species_id
            state["species_title"] = species.get("title", species_id)
            state["species"] = species.get("title", species_id)
            state["rarity"] = self.rarity_var.get().lower()
            state["xp"] = max(0, min(99, self.parse_int(self.xp_var, 0)))
            state["energy"] = max(0, min(100, self.parse_int(self.energy_var, 0)))
            state["hunger"] = max(0, min(100, self.parse_int(self.hunger_var, 0)))
            state["onboarding_pending"] = False
            state = self.stage_adjusted_state(state, species_id, stage_id)
            PET_RUNTIME.save_state(state)
            self.current_pet = self.current_state()
            self.status_var.set(f"已应用状态: {species_id}/{stage_id} Lv.{state['level']}")
            self.write_log(f"已应用真实状态: {species_id}/{stage_id} Lv.{state['level']} XP {state['xp']}.")
            self.refresh_state()
        except Exception as exc:
            self.status_var.set("应用状态失败。")
            self.write_log(f"应用状态失败: {exc}")
            self.show_error(exc)

    def simulate_level_up(self):
        self.level_var.set(str(self.parse_int(self.level_var, 1) + 1))
        self.xp_var.set("0")
        self.apply_state()

    def simulate_evolution(self):
        options = [stage["id"] for stage in self.stage_options(self.species_var.get())]
        try:
            idx = options.index(self.stage_var.get())
        except ValueError:
            idx = 0
        self.stage_var.set(options[min(len(options) - 1, idx + 1)] if options else "seed")
        self.apply_state()

    def trigger_action(self, action: str, payload: dict):
        try:
            data = post_json(PET_ACTION_API, {"action": action, **payload})
            self.current_pet = data.get("pet") or self.current_state()
            self.status_var.set(f"{action} 已触发。")
            self.write_log(f"{action} 成功: {json.dumps(data, ensure_ascii=False)}")
            self.refresh_state()
        except Exception as exc:
            self.status_var.set(f"{action} 失败。")
            self.write_log(f"{action} 失败: {exc}")
            self.show_error(exc)

    def periodic_refresh(self):
        try:
            self.current_pet = self.current_state()
        except Exception as exc:
            self.write_log(f"定时刷新失败: {exc}")
        self.root.after(2500, self.periodic_refresh)

    def show_error(self, exc: Exception):
        detail = traceback.format_exc()
        log(detail)
        try:
            messagebox.showerror("LittleClaw 调试工具", f"{exc}\n\n详细日志已写入 {LOG_FILE}")
        except Exception:
            pass


def main():
    log("debug tool boot")
    root = tk.Tk()
    try:
        PetDebugTool(root)
        root.mainloop()
    except Exception as exc:
        log("debug tool fatal:\n" + traceback.format_exc())
        try:
            messagebox.showerror("LittleClaw 调试工具", f"{exc}\n\n详细日志已写入 {LOG_FILE}")
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()
