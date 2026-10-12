- Author: ChatGPT / authorized queue and sandbox experiments
- Created: 2026-10-12T20:43:20+01:00

# ForgeDuet：queue 唤醒与 Swift 沙箱对照实测

## 结论

**两项能力验证通过：本机 queue 能唤醒已有空闲桌面聊天；合成 Swift 包在保留 Codex 外层沙箱、仅关闭 SwiftPM 内层沙箱时可运行两个 XCTest。** 这不是正式桥接已接入、完整审查质量或 WristFiles 验收通过。本轮只做用户在当前聊天明确同意的两项实验，没有新增真实 `codex exec` 调用、部署、安装技能、提交/推送或恢复 WristFiles。

依据 Claude 的 `Claude反馈/ForgeDuet-桥接第二步复核-2026-10-12.md`，授权来源为用户「我同意，你去做这两项」。原始第二步报告/证据不修改。CLI 仍为 `0.162.0-alpha.17.2`，两个测试聊天回合的本地 turn-context 均记录 `gpt-6.1-sol / xhigh`；未切换模型。只改变单次命令参数，不修改全局模型或沙箱设置。

## 1. queue：真实桌面空闲聊天被自动唤醒

新建用户授权的一次性聊天「ForgeDuet queue 一次性测试」，ID `01a1319c-d665-75e0-99c1-192ff1ed2837`，初始消息只要求回复 `FD_QUEUE_READY`，不使用工具。首轮 `01a1319c-d6de-7bc2-980d-505eddc03b26` 完成后已确认 idle。

随后向同一 ID 用 `codex queue` 发送一条消息：“仅回复 FD_QUEUE_AWAKE_20261012，不使用工具。”CLI 返回成功，排队消息 ID `01a1319e-3283-7153-beb1-7579a49e41f1`。App 接着自动启动第二轮 `01a1319e-43b5-7e82-8151-319ac0e38909`，回复精确标记，耗时 2,073 ms，最终 idle。两轮之间没有人工发言，也没有调用另一个发送消息工具；创建聊天的初始回合另计。App read/wait 原始回执、命令和日志均保存。结束后已归档这一个测试聊天，保留可恢复历史。

首次本地 queue 尝试在打开 SQLite 状态库时被外层文件权限阻止，尚未成功投递；获本次执行权限后才投递成功。没有循环发送，只有一条成功排队消息、两个完成回合。之前只读查询默认 daemon control socket 返回“不存在”；没有主动运行 daemon start/remote-control 或改配置，queue 内部工作机制未调查，不能据此推断必须安装额外服务。

这项结果证明本机该版本的一次真实已有桌面聊天可被 queue 自动启动新回合。还没证明电脑睡眠/重启、额度不足、重复投递、忙碌聊天、归档聊天、长期监视或其他版本的行为。尚未把 ForgeDuet 检测器连接到 queue，也没有向当前长期审查聊天投递任何消息。

### 实测用量

| 范围 | 输入（含缓存） | 缓存输入 | 相减所得非缓存输入 | 输出 |
| --- | ---: | ---: | ---: | ---: |
| 初始化聊天一轮 | 28,740 | 22,400 | 6,340 | 39 |
| queue 唤醒一轮 | 28,800 | 28,544 | 256 | 13 |
| 两轮合计 | 57,540 | 50,944 | 6,596 | 52 |

来源是该测试会话的原始 `token_count` 字段，含推理输出 30（已在输出总数中）。这是测试聊天两轮累计，父聊天准备/协调/报告用量另计，实际金额/账号额度换算未知。queue 消息处理仍调用所选模型并消耗 token，**只有本地等待/检测不需要模型**。这次仅回复标记，不是完整审查，不能和之前 44 万输入的审查任务直接比较、声称节省比例或质量等价。沿用会话也不会让长上下文免费。

## 2. Swift：同一外层策略下的对照

使用 `codex sandbox` 直接执行脚本，不调用提供方模型。四次命令均从同一临时 control 目录启动，显式 `sandbox_mode=workspace-write`、`sandbox_workspace_write.network_access=false`，构建/cache/temp 指向 control。没有 danger-full-access 或关闭 Codex 外层沙箱。

| 合成副本 | SwiftPM 内层沙箱 | Swift 子进程退出码 | 观察 |
| --- | --- | ---: | --- |
| 原始第二步 fixture | 保留 | 1 | 清单阶段复现 sandbox_apply 拒绝，测试未执行 |
| 原始第二步 fixture | 关闭 | 1 | 越过清单阶段；合成测试自身存在 add 命名歧义，编译失败 |
| 单独修正的 fixture | 保留 | 1 | 仍复现相同清单沙箱拒绝 |
| 同一修正的 fixture | 关闭 | 0 | **2 个 XCTest、0 失败** |

原始 fixture 是我编写的，未限定的 `add` 与 XCTestCase 方法发生歧义，这是本次发现的合成测试错误，不是 WristFiles bug。仅在 `source-qualified/` 新副本把两个调用改为 `Arithmetic.add(...)`，断言值及实现不变，原始 `source/` 和既有证据保留。修正后测试文件 SHA-256：`36e8ca88e1123bc8a5e5efae74a85dbcd8e2a4a6eccffd78d7f068b669243b1a`；其保留/关闭内层沙箱两次测试的全部源码哈希相同。原始 stderr、四次命令/退出码/日志和修正记录都已保存，未隐藏中途失败。

成功用例耗时约 17.63 秒，原始 XCTest 输出确有 “Executed 2 tests, with 0 failures”。后面 Swift Testing 的 “0 tests” 是另一套框架，不把它误计为 XCTest 没跑。脚本/外层 helper 退出 0 不自动代表 Swift 成功，报告采用独立保存的 Swift 子进程退出码。

外层限制的探针：control 内写入成功，一次性测试聊天 Documents 输出目录中的合成文件写入被拒绝（errno 1），该文件不存在。最初用 `/private/tmp` 兄弟目录作“目录外”探针时写入成功：系统临时目录本身可能属于允许写入范围，因此那一次不能证明限制失效；原结果保留，改用 Documents 的合成路径验证。探针只证实这两个具体写入行为，不冒称穷尽沙箱权限。还遇到一次 CLI 参数校验：`sandbox -C` 要求命名 permission profile，随后改为从 control 作为 cwd 启动并保留显式策略，未偷偷改成宽权限。

本次为 FD-SMOKE-001 提供了嵌套沙箱原因与可行处理的对照证据，但没有重新跑付费的完整桥接。`--disable-sandbox` 放宽 SwiftPM 子进程隔离，授权仅用于这个合成实验，不自动推广到候选项目、插件、依赖或真实审查。没有运行 WristFiles、模拟器或 Release；不能仅凭推测把这些环境判为必然失败，也不能把微型包成功推广到它们。

## 材料、剩余工作

证据：`evidence/raw/2026-10-12-queue-sandbox-smoke/`，清单共 **53 个文件**；`manifest.json` SHA-256：`fc3fb8add7205566001c9b9febe8272709ab7f7206e7a9d8544dcff472fbebcd`。包含 API 原始观察、queue 命令/回执、仅该测试聊天的用量和模型上下文摘录、四次 Swift 结果/原始输出、两份源码、探针与 runner。未复制凭据、全局配置、真实项目、构建缓存或整个聊天 prompt。原临时路径保持原貌，按清单查持久副本。

下一步建议优先设计“本地 detector → queue 唤醒指定原聊天”的适配器，而非继续假定只能新会话。仍需保留单实例、事件精确哈希、未完成文件诊断、成功排队不等于完成审查、完成报告后才 ack、失败通知/防重复与人工停用规则；不能把 queue 返回 0 直接标记交付已处理。机械预处理可脚本化，但不执行报告中任意粘贴的命令，不取代独立审查。正式启用前处理既有通知措辞和双方技能同步 P3。

本轮未修改 ForgeDuet 代码或已安装技能，未启动长期进程或新 heartbeat。请用户手动把本报告交 Claude 做独立复核，重点核对 queue 自动第二轮证据、真实用量、两组 Swift 对照与权限边界、失败材料保留及结论限制；没有假称已自动转交。当前实验完成不等于正式部署授权。

交付完成
<!-- FORGEDUET_COMPLETE -->
