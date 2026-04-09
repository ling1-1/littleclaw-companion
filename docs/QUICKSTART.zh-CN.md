# 快速开始

[English](QUICKSTART.md) | 简体中文

## 1. 安装

```bash
./installer/install.sh
```

## 2. 验证

```bash
curl -s http://127.0.0.1:18793/health
curl -s http://127.0.0.1:18793/pet
/bin/zsh -lc "launchctl print gui/$(id -u)/ai.openclaw.littleclaw-companion"
```

正常情况下你应该看到：
- 宠物 API 返回健康状态
- 当前宠物 JSON 正常返回
- Companion LaunchAgent 已加载

## 3. 升级

```bash
./installer/upgrade.sh
```

## 4. 卸载

```bash
./installer/uninstall.sh
```

## 说明

- 默认会保留现有宠物成长数据。
- 首次安装时，如果还没有宠物状态，会自动初始化首宠。
- 如果已经有宠物，安装器会保留当前主宠，只刷新运行时文件。
