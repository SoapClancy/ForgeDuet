- Author: ChatGPT / ForgeDuet bridge follow-up
- Created: 2026-10-12T20:11:57+01:00

# ForgeDuet 第一步复核跟进交付：停止通知与 watchdog

## 依据和候选

依据 Claude 的 `Claude反馈/ForgeDuet-桥接第一步复核-2026-10-12.md`（SHA-256 `5e17d1361484c7403cd336f155184008a41df5f3b31edb6e538a1cc822deab65`）修正本轮候选。原交付、归档和 Claude 原反馈均未改写。

- 仓库现有 HEAD：`d2321e1f983531e4e20ed19d2a97b1f85a35ebee`；本轮仍未提交、暂存或推送，不把 HEAD 当作新增代码的候选 SHA。
- 桥接候选 **0.2**：固定清单 `evidence/raw/2026-10-12-markdown-bridge-step1-followup/manifest.json`，SHA-256 `79e39eb12d2f50ce2a590112bd3ac8ebf5d11941d7cc8a18d09f734af9842152`，共 **115 个文件**。相对前轮有 17 个新增/变化路径（含源技能包副本），具体清单及前轮清单哈希已列入 manifest。
- 固定源码归档：`evidence/raw/2026-10-12-markdown-bridge-step1-followup/source.tar.gz`，SHA-256 `f98052469e192ec9300d963b12ecd13d3aacec8484412ad31e5b6ca68101f112`。
- `scripts/markdown_bridge.py`：SHA-256 `76522e27302a9d79093d56aacc57dd713868a24c3c3c6ced6e94cd1a10346fa0`。
- 两个源码技能包已同步；**四份已安装技能入口保持此前接受的 v0.3.2，未部署候选**。`handoff.py` 与 `relay.py` 哈希仍与前轮相同。

## FD-BR-001（P2）：本方修复完成，等待独立复核

桥接持有其 watcher 后，在完整性提醒、连续扫描错误、待恢复、CLI 失败/超时、暂停/中断、审查 stop 等出口生成本地停止通知：

1. 在共享 writer 锁内发布独立、完整、不可覆盖的 `reviews/YYYY-MM-DD-bridge-stopped-<ID>.md` 并追加日志。标题和 JSON 均明确是 **传输通知，不是审查结论**：`record_type=transport_notice`、`review_verdict=null`、`input_acknowledged_by_notice=false`，列出原因、对应输入、诊断位置和恢复步骤。通知不 ack 原交付、不 ack-warning、不恢复游标、不调用模型。构建方可由自己的正常文件扫描发现；构建方监视是否实际启用未假称验证。
2. 共享写失败也会尝试本地 macOS 通知（默认开启，可显式禁用）。使用固定系统路径、字面参数和 5 秒本地通知进程超时，不执行报告提供的命令。通知回执记录 peer/desktop 两通道结果，相同原因/输入去重；第一次写共享目录失败后可显式重试，不重复提交旧桌面通知。
3. 运行中的原桥接不会因第二个并发启动者被拒绝就被假称停止。故障前尚未开始的新输入不会误带上一轮 run 路径。通知、游标暂停或清理失败不能盖掉原错误。

通知生成不消耗模型 token；**Claude 若被唤醒读取通知，那次处理会消耗其模型用量**。本轮测试没有真实模型调用，也没有弹出真实系统横幅。

## 其余建议

- **超时**：CLI 配置现在必须为有限正数，null/零/负数/布尔/无穷值都在派发前拒绝。示例填 3600 秒，仅为 watchdog 示例，没有修改任何项目的实际时间/费用设置，也未新增 token/currency 预算。
- **状态顺序**：指定单一状态所有者，在交付前更新并记录状态哈希，再发布交付；审查期间冻结状态。审查/明确传输 gate 已持久记录且活跃调用结束后，才更新状态进入下一轮。紧急变更须先停止、对账，不能补写状态让正在付费的审查无声作废。
- **真实测试门槛**：第二步必须在隔离合成快照中实际执行测试命令，优先微型无外部依赖 Swift 包，并保留权限、网络、退出码、日志和实际用量。运行受限则如实失败/有限，不能把“生成审查文字”当作测试通过。本轮没有运行第二步。
- **日期与原错误**：审查报告名称已加日期；原错误先保留，暂停/通知/清理的二次故障独立记录。

## 验证

- 桥接相关：**35/35**，4.445 秒：`python3 -m unittest discover -s tests -p 'test*bridge*.py' -v`。
- 全套合成测试：**130/130**，26.428 秒：`python3 -m unittest discover -s tests -v`。
- 新增 14 项通知/watchdog 回归；既有 21 项只适配正数 timeout、禁用测试桌面提示及单独统计有日期的正式审查文件（排除新增传输通知），原断言保留。既有 handoff/relay 测试未改。
- 负向对照：同一 fake CLI 失败，前轮固定源码 **0 份停止通知**，修复后 **1 份**；两者都保留原输入、只调用一次 fake CLI。harness/mock 不调用真实提供方或系统横幅。
- 证明构建方游标能扫描到通知、完成标记和日志有效、同原因不同扫描年龄仍去重、锁占用时不破锁而调用模拟 OS fallback、OS 失败仍保留共享通知、游标损坏/通知失败不盖掉原错误、超时和待恢复出口无自动模型重试。
- `sync_bundle.py --check`、两个源码技能包的 bridge `--help`、`git diff --check` 均通过。

原始材料（相对仓库路径 `evidence/raw/2026-10-12-markdown-bridge-step1-followup/`）：

- `focused-tests.log`：SHA-256 `11aa36da495db4355f356cae28a54a94720c5d1d0f104b5fd03d2f277e311031`。
- `all-tests.log`：SHA-256 `ccd00667c9eba2a8f73e3780c6973c20037101a87498dd145b33b0d48dd23c66`。
- `negative-control.log`：SHA-256 `4948f7a7a3547cff8317d252f1b1ec023e327df10daf7ffc53b6328f72071cb9`。
- `negative-control.py`：SHA-256 `0cea8ff773f974a98344e3d589029ecfcc9d00a73d1e976460aa4ea0d897519b`。

## 限制与下一步

macOS 通知仅测试了桩及参数/超时处理，返回 submitted 不等于用户看到横幅。共享写和系统通知同时失败、进程被强杀/断电/睡眠时，通知不能保证到达；私有回执与 stderr 保留诊断，未安装 supervisor 或后台服务。重启会提示未决调用并保留输入，不自动重复付费。通知不是产品批准或双方闭环。

本轮仅修正 ForgeDuet 候选并用假 CLI 验证。没有恢复 WristFiles 监听、访问/导出 WristFiles、操作设备、安装技能、调用额外真实模型、改模型设置或 Git 提交/推送。当前聊天的编码工作本身仍使用模型；没有将它说成零用量。

请 Claude 对此固定快照再独立复核，尤其检查 FD-BR-001 是否闭合、去重/错误保留、共享写失败的可见性、watchdog 和状态冻结顺序，以及对实测限制的措辞。仍为用户手动转交，未假称自动收到。双方确认后，真实调用的第二步仍需用户另行授权。

交付完成
<!-- FORGEDUET_COMPLETE -->
