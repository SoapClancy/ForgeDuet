- Author: ChatGPT / git transport and quota resume
- Created: 2026-10-13T22:54:44+01:00

# Git 同步第 3 轮交付：长时间断网继续重试

## 固定版本与上一轮结论

- 本轮源码候选：`85a655fe73d9370535f14b94986d082b66ec8af7`，分支 `feature/git-sync-quota-resume`，仅本地提交。
- 源码归档：`evidence/raw/2026-10-13-git-sync-round-03/source.tar.gz`，167 个文件，430338 字节；SHA-256 `5f7130f99ba0b3735fa1b6c5de8a370ebb176fe6ad2d0a6157b1c006ab904d6e`。
- 根据 Claude 的 `Claude反馈/ForgeDuet-Git同步与额度续接第2轮复核-2026-10-13.md`，SHA-256 `9b53e337c222660c4a28c0d5c310ca625f7d77972936229b43aada48aec57d4a`。
- 构建方已另行接受上一轮 `8096fd2c18900ba8f3e547a80eafc1873d7751a8` 的限定批准：`docs/deliveries/2026-10-13-git-round-02-accepted.md`。FD-GIT-001/002 在旧 SHA 的合成范围闭环；该批准不自动转移到本轮。
- 本轮处理反馈的两条 P3 建议；并未触发真实项目或客户端监听。

## 改动与可复核行为

1. 新默认 `network_failure_policy: notify_continue`：达到 `max_network_errors`（默认 5）后提醒一次，继续按 `retry_max_seconds`（默认 300 秒，且不小于 interval）重试。退避时间、累计连续失败次数和 incident 均持久化，重启不清零；网络恢复并成功同步后记录恢复并清零。仅保留最近 100 条错误明细，避免长期断网使状态无限增长。可显式选择 `stop` 保留有限重试/人工恢复模式，原断言仍在。
2. 断网/恢复提醒写入**私有 runtime JSON**并尽力发送系统通知；不写完整 Markdown 到模型输入，不同步给对方，不产生需要报告/ack 的队列事件。否则普通断网提醒本身仍会唤醒模型，甚至阻断正在继续的重试。认证/完整性等真实停止仍保留原本地 gate 通知。
3. 每个 incident 的 outage/recovered 各至多尝试一次系统通知。OS 调用前先落意图；崩溃后 pending 表示不确定，不自动重发。通知文件或横幅失败不会停止网络重试；成功发出不等于用户看到了。恢复记录在重置失败计数前落盘，覆盖该崩溃窗口。
4. 补识别 `SSL_ERROR_SYSCALL`、`RPC failed`、`unexpected disconnect`、HTTP 429/500 及已有 502/503/504。同时在 stderr/stdout 全部诊断上先判认证、证书/host key、推送拒绝和完整性错误，再截短显示；未知远程错误和本地 Git plumbing 错误仍立即停止。不是将一切错误都当成断网。
5. Git protocol、模板、双语 README 和两份独立技能源码包已同步。额度运行时代码未改，已安装技能未替换。

## 验证与原始证据

- 最终全套 **232/232 通过，53.326 秒**：218 个既有测试 + 14 个新增测试。
- 新增测试覆盖：超过阈值继续重试、真实 watch 子进程保持存活并在临时 bare remote 恢复后送达、重启不提前请求、没有模型输入提醒、每个 incident 去重、通知失败、崩溃窗口、畸形提醒回执保留、历史长度、临时/永久诊断优先级、旧身份拒绝和非法配置。
- 反向对照：导出固定旧 SHA `8096fd2`，加入同一个新测试文件，仅运行两条相关方法；结果为 7 个错误（旧版第 5 次断网停止 + 6 个临时 HTTPS 字样未识别）。在固定本轮归档上同样两条 **2/2 通过，0.174 秒**。断言和测试文件哈希一致，未用修改后的运行时代替旧版对照。
- 两份技能 quick_validate 通过；bundle --check 通过；151 个相对 Markdown 链接无断链；git diff --check 通过。
- 原始日志、源码清单、测试代码哈希、控制组和来源摘要均在 `evidence/raw/2026-10-13-git-sync-round-03/`；完整证据清单 `evidence-manifest.json` SHA-256 `eee3432842f8ffba9b6ba01b6bbb3de7718d408e2146fae41fd22731812d1f7b`。逐文件源码归档清单在 `source-manifest.json`。
- 初次 focused 14/14 通过后又加强畸形回执/TLS 检查，最终全套覆盖所有修改。一次多文件补丁未匹配而整体失败，没有写入；updates.log 已追加更正，不改旧日志。
- 所有测试仅用合成数据、本地临时 bare remote、假系统通知/假客户端；没有真实模型、远程网络服务或真机调用。

## 限制与待复核

- 有效重试策略版本纳入 runtime identity。旧候选 runtime 会被原样拒绝，不自动迁移、不自动解除旧暂停；未提供迁移工具。须用原已审工具协调/排空旧运行，不能删改 journal 或新建 runtime 去接管既有 role branch。文档已说明。
- 真正 GitHub SSH/HTTPS 认证与网络、两台电脑协作、睡眠/服务恢复未验证。本轮本地 Git 和合成错误测试不替代这些门槛。
- **当前 Claude Code 桌面构建 + Codex App/queue 审查仍不能在额度重置后自动继续。** FD-QUOTA-DESKTOP-001/002 继续开放，不因本轮网络改善宣称完成。
- 请 Claude 对此新完整 SHA 独立复核，特别看继续重试是否会造成模型输入、通知失败是否意外停止，以及永久错误优先级。无新独立批准前不沿用上一轮接受记录。
- 未推送、合并、安装技能或启动/恢复任何项目监控；继续手动文件交接。

交付完成
<!-- FORGEDUET_COMPLETE -->
