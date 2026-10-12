- Author: ChatGPT / queue write smoke evidence
- Created: 2026-10-12T21:34:59+01:00

# ForgeDuet queue 写入闭环实测（FD-QA-001）

## 结论

**本次合成项目权限/交接门槛通过。** 用户授权“开始测试吧”后，只创建一个一次性聊天，启动轮次与一次真实 queue 唤醒均为 `gpt-6.1-sol / xhigh`。被唤醒聊天自行执行可信合成助手，在固定 SHA 的隔离副本运行 2 个 Python 测试，随后加锁、原子发布绑定报告、追加日志、释放锁、精确哈希 ack；适配器独立核验后记为 handled。没有人工点击权限、子聊天提权或父聊天代写报告/ack。

这验证的是传输和现有工作区写权限，不是模型审查质量，也不是 WristFiles/任意项目正式启用批准。真实项目和已暂停监听保持原状态。

## 实际过程与证据

- 一次性聊天：`01a131cb-c2eb-7371-8deb-de5bc158bdf8`；启动轮次 `01a131cb-c38b-7023-bd4d-bb09246f35da`，仅答 `FD_QA_READY`；queue 轮次 `01a131d0-c572-7453-a674-4b0ec44f7a60`，触发类型为 queue，最终答 `FD_QA_WRITE_OK`。
- 实际 cwd：`/Users/soapclancy/Documents/Codex/2026-10-12/forgeduet-queue-write-smoke-20261012`。合成项目在该聊天 outputs 下；实际沙箱为 workspace-write，沿用客户端已有 Documents/Codex、专用 visualization 和临时目录写权限，网络关闭。**不是操作系统强制仅能写此合成目录**；本次助手的实际写入均在合成项目或其同级隔离测试目录。
- 合成 Git SHA：`7cc5b92be913752cf99cad9b694105daf9522b0e`；只导出两个允许的 Python 文件，无产品代码和真实数据。
- 指南仅 1,814 字节。模型读取短指南/核验哈希，再调用一次可信助手；2 个工具往返、4 条本地命令。没有读取整套技能或历史审查文档。
- 交付：`deliveries/synthetic-round-01.md`，SHA-256 `12bbeb8e9bb4ec0dd66f00bfa38a74729a09fa958e95e3e0fb7a4478b059a04e`。
- 唯一事件：`3ed75b6b9f1c22d47e2ae34aa70cf08dd7f7f7df14d9c56b4c801dec98599aea`；queue 只调用一次，回执消息 ID `01a131d0-b035-7f13-a349-0aa1151903ea`。20:32:02 UTC 提交，20:32:08 UTC 开始，20:32:24 UTC 发布/ack，20:32:25 UTC 完成，queued 轮次约 17.9 秒。
- 绑定报告：`reviews/synthetic-review-01.md`，SHA-256 `53814b01c8a5939ebc390f5de27f5e98958ba61fa5c1859df7b95f747cc6d64b`。原始测试日志为 2/2、退出 0；worker-receipt 记录完整顺序，适配器 observations/journal 独立记录 handled。
- 发布交付前做了 3 次本地空扫描，均 waiting、无 dispatch；不把这短检查外推为长时间空闲稳定性。收到交付后本地每秒检查，只有首次调用 queue；后续 awaiting_ack 检查未再启动模型。
- 父聊天启动 queue 需要访问 Codex 本机会话数据库，外层编排经系统提权授权；**子聊天的命令没有提权或权限申请，queue 仍指定 workspace-write**。不隐去这两个层次的区别。
- handled 后父方才暂停合成游标、产生正常暂停通知，局部进程退出；聊天已归档。此处归档是清理，**没有对已归档聊天再发 queue**。本次关闭桌面横幅，横幅显示已在前一轮由用户确认。

## 原始 token 计数

| 范围 | 输入累计 | 其中缓存输入 | 输出累计（含推理） | 总计 |
|---|---:|---:|---:|---:|
| 启动轮次 | 28,823 | 22,400 | 40 | 28,863 |
| queue 唤醒轮次增量 | 90,983 | 88,320 | 605 | 91,588 |
| 本测试聊天合计 | 119,806 | 110,720 | 645 | 120,451 |

缓存输入是输入的子集，推理 122 是输出的子集，都不能再相加。合计非缓存输入 9,086；**仍如实报告总输入 119,806，不称为只用了 9,086 token**。这些是本机 rollout 的原始计数，不等于账户额度百分比或账单金额；父聊天本轮用量、Claude 与历史实验不在此表。读取记录不新增子聊天模型调用。不能用此次小助手实验与完整审查直接比较成本或质量。

## 固定字节、范围与剩余项

- 真实运行的是已交付 queue 第 1 版的字节副本：queue_bridge.py `39b2b9b55fa7cc5c6f933a656310f884542e218ad9fb01fd9aac26a25e8551ba`；handoff.py `9fe5a0fa7b70bfca8e88b1bb1dda446eaf02b6c01c9e976eb8aa6ebedc675e6c`；markdown_bridge.py `76522e27302a9d79093d56aacc57dd713868a24c3c3c6ced6e94cd1a10346fa0`。实验后与源码重新核对一致。本轮没有修改运行时代码、测试或已安装技能。
- 基线 Git 仍 `d2321e1f983531e4e20ed19d2a97b1f85a35ebee`，本轮只新增实验材料、报告和追加日志；没有提交、暂存、推送、产品监控、设备操作、模型变更或额外付费重试。
- 正式项目交接目录位于其他路径时，必须验证其真实授权与写权限；本例不授予 Development/WristFiles 写权限。正式启用前仍需同步技能源码中的 queue 规则。
- 忙碌聊天、归档聊天、睡眠/重启、长期运行及实际产品独立审查尚未测试；不在本次授权范围，未自行开始。FD-QA-001 可就**本例现有工作区内写入闭环**关闭，不能无限外推。

证据目录：`evidence/raw/2026-10-12-queue-write-smoke/`，共 39 个受清单覆盖文件（不含 manifest 自身）；清单 SHA-256 `03f34acccee30ec367d131762d45758a61caef11e3b9f7c9e48f88e0708b7253`。包含可信指南/助手/实际脚本、配置和 pin、API 启动/完成/归档回执、定向 rollout 事件、用量、队列命令/回执、游标、报告、更新日志、测试输出与校验结论。没有收集其他聊天记录。

请 Claude 手动复核此报告与证据；未向其他聊天发消息，未恢复任何自动交接。

交付完成
<!-- FORGEDUET_COMPLETE -->
