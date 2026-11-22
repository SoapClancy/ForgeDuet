- Author: build / claude-opus-5-5 / forgeduet-queue-compat-20261122
- Created: 2026-11-22T18:30:00+00:00

# queue 适配器适配 codex-cli 0.171：已审查、已接受、已真实验证

## 结论

修复版本 `48e8032a205f3312e1d6d6523bf0a282d9d7d1cc`（分支 `fix/queue-cli-0171`）满足以下全部条件：

- Codex 审查方（`gpt-6.1-sol` / `xhigh`）批准；
- Claude 构建方接受同一个 SHA；
- 修复后的 `queue_bridge.py` 在真实 codex-cli 0.171.0-alpha.13 上完成了一次完整的派发→审查→handled 闭环。

**修复内容**：

- 只传 `--thread` 和 `--message`；
- 派发前检查 `queue --help`，检查之后再核对暂停、输入和 pins；
- 审查报告首行必须自报模型和强度，适配器会核对；
- 测试替身改为严格解析参数。

Workflow 版本为 v0.4.1 candidate，queue adapter 版本为 0.2。

## 过程

| 轮次 | SHA | 结论 |
|---|---|---|
| 候选 1 | `78ff19a` | request_changes：发现 FD-QC-001（P2）——help 检查期间发生 stop 或输入变更时，仍会派发 |
| 候选 2 | `48e8032` | technical_approved_pending_adapter_smoke，FD-QC-001 已关闭 |
| 接受与冒烟 | `48e8032` | review_approved；适配器 handled，`model_report: matched` |

- 测试：238/238 通过（基线 232 个，新增 6 个）；`sync_bundle --check` 通过。
- 负对照：
  - 新测试在修复前的 `9177027` 上：4 个失败、29 个错误；
  - FD-QC-001 的两个回归测试在 `78ff19a` 上：2 个都失败。
- 审查方另外做了独立检查：严格 fake CLI 8/8 通过；边界回归 2/2 通过。

## 真实适配器冒烟（2026-11-22）

- CLI：App 内的 Mach-O 可执行文件 `CodexCLI.app/Contents/MacOS/codex`，sha256 `3b6d00de…`。
- 目标是一个已有的 review 对话。冒烟范围只有 mailbox 传输，不执行产品代码。
- 时间线：
  - 18:20:59Z 写入 intent；
  - 18:21:00Z 提交，回执 `Queued message 01a2047d-72a6-76f0-930a-0a3d8ef7cb38`；
  - 18:22:24Z 审查方发布绑定响应并亲自 ack；
  - 18:22:32Z 适配器记录 handled。
- 实际命令只有 `queue --thread <uuid> --message <envelope>`。审查方确认，这一回合确实是由适配器发出的消息触发的。

## 局限

- 只验证了一个现有对话、空闲状态、一次派发。忙碌或已归档的对话、睡眠、重启、其他机器均未验证。
- quota 续接的竞争情况只做了代码审读。
- 模型自报属于自我声明，不能证明实际用了哪个模型。
- token 和费用未知。

## 其他

- `9177027`：把 2026-10-29 留在工作区、一直没提交的改动原样提交，内容是「peer 协调只走 ForgeDuet 记录，不操控对方 AI 客户端 UI」。已一并审查，没有阻塞问题。
- 已按用户授权完成：push 分支（不强推），并把两个 skill 包安装到 `~/.claude/skills` 和 `~/.codex/skills`。安装前的旧版本备份在仓库内被忽略的 `.forgeduet/backups/installed-before-2026-11-22/`。未合并 main。
- 完整的协调记录和证据在被忽略的 `.forgeduet/queue-cli-compat-2026-11-22/` 和 `.forgeduet/queue-smoke-2026-11-22/` 中。
