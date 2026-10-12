- Author: ChatGPT / ForgeDuet v0.3.2 review follow-up / 2026-10-12
- Created: 2026-10-12T08:24:38+01:00

# ForgeDuet v0.3.2 复核反馈处理与 Codex 接入核查

## 接受范围

接受 Claude 对源提交 `d2321e1f983531e4e20ed19d2a97b1f85a35ebee` 的有界复核：其报告称 95/95 测试通过，没有 P1/P2；两份 Claude 已安装技能与该源版本一致。原反馈 SHA-256 为 `a9f01f2d97146da6954d2f9f57fd0a45c74be4ed7c39ee44414e2e76f017572e`，原件留在忽略的私人反馈目录，本次未改。

本次继续处理其非阻断建议，只改文档、技能说明和追加日志。此次跟进文档尚未经过新的独立复核；不能把对源提交的批准扩大为 Codex 自动唤醒已通过。

## 已处理

1. README（中英文）、ROADMAP 和两个 SKILL 入口统一标注工作流说明 v0.3.2，relay 运行时仍为 0.3.0；没有改变状态版本或脚本。
2. 明确 AI 定时唤醒仅是用户知情选择的后备方式：第一项实质操作先本地扫描，无变化立即安静结束，不读取旧报告/源码或另加模型判断。用户选择间隔；新建专用聊天也需要授权。
3. 写清事件唤醒仍会使用模型上下文和推理额度，精简上下文有助于控制用量，但不能保证金额或 token 数。
4. SETUP 新增已安装副本同步责任、目标路径、源身份和授权来源记录；未知额外文件及局部差异不得直接覆盖。
5. ADAPTERS 补充 Codex 的真实能力边界及 CLI 预检查，不再根据 PATH 中没有命令断言没有 CLI，也不笼统断言 Codex 没有任何事件入口。

## Claude 客户端实测的边界

以下是复核方提供、由本方核读的证据，未在其客户端独立重放：临时邮箱约 77 秒、约 8 次本地检查未唤醒；08:03:27 报告出现，08:03:34 检出退出，08:03:39 Claude Code 通知唤醒。检测延迟 7 秒，通知再用 5 秒，总计 12 秒；不能说总计在 10 秒间隔以内。部分等待期间 Claude 仍在回复，完全空闲不足一分钟。`seen` 未自动确认，符合规则。

这支持其特定 Claude Code 会话的后台完成通知路径；不证明 Codex、电脑睡眠/会话关闭后的恢复或完整双客户端循环。

## Codex 只读核查结果

- 本机已有 `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`，版本 `0.162.0-alpha.17.2`。只运行版本、帮助和 daemon version 等预检查，没有模型调用、登录或设置修改。
- 官方文档说明，后台 hook 结束不会开启闲置聊天的新回合：[Hooks](https://learn.chatgpt.com/docs/hooks)。这条路径不能拿来假称零空闲调用的桌面唤醒。
- 公共 [App Server](https://learn.chatgpt.com/docs/app-server) 提供 `turn/start` 和本地传输，但仍属实验性、生产不受支持。本机默认 daemon version 检查报默认控制 socket 不存在。未启动 daemon、启用远程控制、猜测其他私有连接或向聊天发消息。因此当前桌面聊天的事件唤醒仍未验证；该错误只证明默认端点不可用。
- [非交互 CLI](https://learn.chatgpt.com/docs/non-interactive-mode) 可由程序在事件后开启新调用，现有 adapter/typed relay 是准备路线。它不接管现有 Markdown `deliveries/`，也不恢复本桌面聊天。实际使用需要双方配置 typed relay，或者另行实现并审查 Markdown 桥接；真实账户、模型、权限与端到端唤醒尚未实测。

## 安装审计与验证

同步者：ChatGPT，技能维护方。授权来源：用户要求“对于这个 Forge Duet Skill，你能不能 update 一下”，本次又要求继续；系统本回合已给予下列精确目录的写权限。未把任务材料或对方报告作为额外授权。

四个实际目标：

- `/Users/soapclancy/.codex/skills/forgeduet-build`
- `/Users/soapclancy/.codex/skills/forgeduet-review`
- `/Users/soapclancy/.claude/skills/forgeduet-build`
- `/Users/soapclancy/.claude/skills/forgeduet-review`

上次 28 项同步为每个目标的 `SKILL.md` 与 `references/{AUTO_HANDOFF,MANUAL,PROJECT_RULES,PROTOCOL,SETUP,WATCHER}.md`。本次写入前四份副本均与源提交一致；比较 108 个文件，仅更新每个目标的 `SKILL.md`、`references/ADAPTERS.md`、`references/AUTO_HANDOFF.md`、`references/SETUP.md`、`references/WATCHER.md`，共 20 个。完整绝对路径、前后哈希和时间保存在忽略的 `evidence/raw/v032/installed-followup.json`；没有删除额外文件。

本次验证：源 bundle 一致、两个源技能及四个已安装技能校验通过；164 个相对 Markdown 目标有效，四份安装副本逐字节匹配；差异空白检查通过。文档跟进不重复跑行为套件；已有实现方 95/95 与 Claude 独立 95/95 仍按原范围保留。

运行时未变：`handoff.py` SHA-256 `9fe5a0fa7b70bfca8e88b1bb1dda446eaf02b6c01c9e976eb8aa6ebedc675e6c`；`relay.py` SHA-256 `b519024f736e4eef2dc9b5892b74bdd2066e6ece700e629a36d3c17bad43fd4f`。

本次没有操作 WristFiles，没有恢复监听，没有启动额外 CLI/模型会话、修改模型设置、提交或推送。本聊天的回复和工具编排仍会使用模型额度。真实 Codex 冒烟测试仍是明确未完成的接入门槛，不把说明更新称为已实现的桌面自动唤醒。实际本聊天累计 token/费用不可读，不估算 Astra 或当前模型消耗。

交付完成
<!-- FORGEDUET_COMPLETE -->
