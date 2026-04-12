# 输入法失焦与合成态被打断修复

- 日期：2026-04-12
- 类型：输入稳定性 / 宿主状态同步
- 影响范围：主输入框、学习弹层输入框、中文输入法候选词

## 现象

- 用户在主输入框或学习弹层里连续输入中文时，大约每 5 秒左右会被打断一次。
- 表面上看起来焦点仍然在输入框里，但输入法候选会被清空，拼音合成态中断。
- 前端单独做 `focus / blur` 修补后，问题仍然存在。

## 根因

- 真正的问题不在普通 DOM 焦点，而在宿主层的周期性状态同步。
- Companion 宿主会定时调用 `pushState()`，然后执行 `window.updatePet(...)`。
- 这类 WebView 注入在中文输入法合成期间会打断 IME composition，即使输入框焦点没有真正丢失。
- 所以“输入法候选被打掉但焦点还在”是宿主刷新打断合成态，不是纯前端 blur 问题。

## 修复

分两层做了处理：

1. 前端补强

- 给主输入框和学习输入框增加统一的文本焦点状态记录。
- 在 UI 重绘前后尽量恢复输入框和光标位置，减少普通重渲染造成的影响。

2. 宿主层止损

- 在 `companion_webview.py` 的 `pushState()` 里先检查 `is_input_active()`。
- 如果用户正在输入，就暂缓本次 `window.updatePet(...)` 注入。
- 把待推送状态记为 `needsDeferredPush`，等输入结束后再补推最新状态。

这个策略比“被打断后再抢回焦点”更稳，因为它直接避免了输入法合成期间的宿主刷新。

## 涉及文件

- `/Users/baijingting/Documents/Playground/littleclaw-companion/ui/index.html`
- `/Users/baijingting/Documents/Playground/littleclaw-companion/companion_webview.py`
- `/Users/baijingting/.openclaw/workspace/littleclaw-runtime/ui/index.html`
- `/Users/baijingting/.openclaw/workspace/littleclaw-runtime/companion_webview.py`

## 回归验证

建议每次改动后至少验证下面几项：

1. 在主输入框里连续输入中文，持续超过 10 秒，确认候选词不会被固定节拍打断。
2. 在学习弹层里连续输入中文，确认候选词不会中断。
3. 输入期间观察宠物状态是否仍能在停止输入后恢复同步。
4. 输入完成后再等待几秒，确认灵动岛和宠物状态会补齐最新状态，不会永久停在旧状态。

## 后续建议

- 如果后面仍出现输入被打断，优先排查宿主定时器、WebView 注入和窗口状态切换，不要只在前端继续堆 `blur / focus` 补丁。
- 后续可以考虑为宿主同步增加更细粒度日志，记录 `refresh_()`、`pushState()`、`applyCompactState()` 的时间点，便于秒级定位类似问题。
