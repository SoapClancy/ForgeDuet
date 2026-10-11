# ForgeDuet：Claude 初版反馈的核实与修复

日期：2026-10-11。作者：ChatGPT，当前角色为实现与自测方。运行时版本：0.2.0，信箱 schema：2。

## 结论

Claude 指出的主要问题成立，已完成修复和文档补充。当前共 51 项本地测试通过，两份 SKILL 的格式检查和资源同步检查通过。可以交回 Claude 复核；**这些结果不是“第二方已批准 v0.2”，真实 Claude/Codex 接入也没有验证**。

文件都在 ForgeDuet 项目内。按用户先前指示，没有初始化 Git、建立远程、推送、全局安装技能或调用付费模型。没有项目提交号，当前核心脚本的 SHA-256 见 [VALIDATION.md](../VALIDATION.md)。

## 对反馈的逐条处理

| Claude 编号 | 核实与处理 | 当前入口/证据 |
| --- | --- | --- |
| 4.1 网页审查没有本机 Git | 成立。补充完整的手动快照交接和 `snapshot.py`：导出指定提交，附清单和 ZIP 哈希；审查端无需 Git 即可核验、解包 | [SNAPSHOTS.md](../../protocol/SNAPSHOTS.md)、`tests/test_snapshot.py` |
| 4.2 初版重、缺简单流程和适配器 | 成立。README 优先引导手动完整闭环；加入 Codex/Claude CLI 示例。保留可选 relay，不要求第一步就配 JSON/租约 | [MANUAL.md](../../protocol/MANUAL.md)、[ADAPTERS.md](../../protocol/ADAPTERS.md) |
| 4.3 `settings_verified` 挡住诚实用户 | 成立。改为 verified / self_reported / unavailable，记录要求值、观察值、依据；无法验证本身不阻止使用，也不准伪称验证 | `test_honest_self_reported_settings_can_use_mailbox`、`test_unavailable_identity_is_explicit_and_not_promoted` |
| 4.4 改规则会杀掉运行中的适配器 | 成立。规则按领取时的字节固定；变化只设置 dispatch hold，当前任务可完成。人类确认 `adopt-rules` 后继续，新规则让旧批准失效。活动检查间隔改为约 1 秒 | `test_rules_typo_does_not_kill_active_adapter` 等四个相关新测试；[TRANSPORT.md](../../protocol/TRANSPORT.md) |
| 4.5 三份 runtime 不一致却不报错 | 成立。state 记录运行时版本和 relay 字节哈希；不同版本/字节拒绝共用。继续用同步工具保证两份独立安装资源一致 | `test_different_relay_hash_cannot_share_run`、`sync_bundle.py --check` |
| 4.6 Claude 安装/触发说明缺失 | 采纳。补项目和个人技能位置、整目录复制说明；description 明确 ForgeDuet/build role/review role；同一份 SKILL 可供两类客户端使用 | README 和两个 SKILL 的 frontmatter |
| 4.7 缺报告语言 | 采纳。启动清单、规则、配置、任务及两份 SKILL 都记录并使用指定报告语言 | SETUP / PROJECT_RULES / run.example.json / relay job |
| 4.8 自测不等于独立验证 | 同意。保留创建方自测身份，单独记录 Claude 对 v0.1 的审查；v0.2 尚待 Claude 或其他审查方复核 | [VALIDATION.md](../VALIDATION.md) |
| 4.9 可读性、Git 初始化 | 技能各节增加直白入口，README 简化上手。Git 初始化未执行：用户已明确说自己处理，优先遵循该指示 | 两份 SKILL、README；目录仍无 `.git` |

## 新行为的边界

### 快照不是伪造的本机工作目录

网页/离线审查走手动文件交接，明确写下完整提交号、ZIP SHA-256、核验结果和测试环境。本地 relay 仍要求独立本机 worktree，并检查审查 HEAD；没有宣称已经把快照模式接进 relay。

校验值应通过用户转交文字等独立于所收清单的方式提供。ZIP 注释和清单是出处与一致性记录，不是提交图的密码学证明。面对不可信作者，仍需可信 Git 对象或 bundle。没有哈希/执行工具的网页会话只能给有限源码审查，不能假称已校验/已运行。

### 规则变化不再等于立即撤权

任务按原来领取时固定的规则继续。规则变化阻止新派发，完成结果留档；hold 未解决不能结束整轮。人类确认新规则后，当前候选需要按新规则重审。要立即撤销原任务权限，必须显式 pause。配置、模型、权限、预算的变更仍需新一轮经核实的配置；不允许靠改 Markdown 扩权。

relay 哈希按脚本字节计算，所以即使只改脚本注释，两端也要同步。旧 schema-1 信箱不自动迁移，保留旧证据和用量，开始经确认的新运行；新目录不能当作抹掉已消费预算的方法。

### 示例适配器仍待真实接入

本次只用合成 CLI 检查入参与输出，没有真实登录或付费调用。示例通过 argv 传入明确的模型与强度，沿用正常权限，不启用绕过权限；不支持的设置应失败。

Codex 只接受一个无歧义的 turn.completed 用量记录，缓存输入不重复计数，费用未知。Claude 示例尚不汇总 tokens，费用只是客户端估计。配置相应限额时，未知用量会暂停循环。这不是供应商端的硬预算保证。

## 测试和控制

先在未修改的 v0.1 上加入三个回归场景：自报设置可初始化、运行时哈希不一致被拒绝、改规则不杀运行中的合成适配器。三个全部复现原问题：**两处断言失败、一处初始化报错**。修复后通过。

最终完整测试：**51/51，通过，19.629 秒**。原 34 项之外新增 17 项：反馈回归 7、快照 6、适配器 4。原测试中有一项规则文件变化测试按新政策调整：从“抛错停止”改为“hold 新派发”，因为这正是有意变更的行为；不是降低安全断言来掩盖失败。

三项旧版复现是本轮的前后对照证据。其余新增测试没有逐个在旧版上反向验证，不宣称全都完成了这种控制。技能格式验证只证明结构有效；fake CLI 测试只证明示例的本地接线；这些都不等于真实模型协作验收。

## 留给下一位审查方

建议重点复核：三档设置的实际记录是否清楚；规则 hold/adopt/pause/recover 是否会丢结果或放过旧批准；快照是否确实绑定导出提交；两个示例适配器是否只按授权参数运行、失败时是否保留未知用量。

运行 `python3 -m unittest discover -s tests -v` 和 `python3 scripts/sync_bundle.py --check` 即可复现本地检查，不需要真实模型。若要验证 CLI，先由用户选定具体客户端、模型、强度、权限和小额预算，再单独开展真实 smoke test。

## Claude 原反馈的保留

原反馈 `Claude反馈/ForgeDuet-初版反馈-2026-10-11.md` 原样保留，没有删除。已将 `Claude反馈/` 加入 `.gitignore`，避免公开时误带私人反馈。上面的脱敏摘要作为公开交付记录；Git ignore 对已经跟踪的文件不生效，用户日后初始化仓库时仍需检查发布清单。
