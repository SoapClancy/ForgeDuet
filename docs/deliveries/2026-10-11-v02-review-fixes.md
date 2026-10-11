# ForgeDuet v0.2 复核：修复与逐条回应

日期：2026-10-11。作者：ChatGPT，实现与自测方。当前 relay：**0.2.1**，schema：2。

## 结论

两个 P2 成立，已修复，现有与新增测试合计 **69/69 通过**。本轮新增 18 项，其中先加入的五个回归场景在未修改的 v0.2 上全部失败，修复后通过，断言未放松。

**这是修复方自测，不是独立批准。** Claude 对 v0.2 的 51 项测试通过，但明确发现两个新 P2；因此不能记成 v0.2 已通过独立复核。v0.2.1 可以交回它复核；真实 CLI 接入和隔离行为仍未测。

文件全部写在 ForgeDuet 项目目录。没有初始化 Git、推送、安装客户端或技能、调用付费模型，也没有使用 WristFiles、设备或真实笔记作测试材料。所有仓库都是隔离的临时 fixture。Claude 的两份原反馈原样保留，整个反馈目录已被 Git ignore。

## P2-01：采纳/恢复把原始输入替换成决定说明

**成立，且 `resume()` 同样受影响。** 两个控制操作以前重新发布的是人的说明，构建方拿不到原任务，审查方拿不到原交付；发给审查方时还冒用了 build sender 和模型验证标签。

现在：

- 构建方新任务的 `report` 保留最初的原任务；审查方候选的 `report` 保留当前 SHA 最近一次真实 build 交付。
- `reply_to` 接上此前消息；领取的 job 包含校验过的 `context_messages`，能看到原任务、候选、反馈、求助等链接和哈希，不需要猜路径。这里只是消息元数据和报告指针，不是重新塞入整段聊天历史。
- 人的采纳/恢复说明放在单独的 `human_decision`，带自己的哈希、类型和说明；重新派发标为 `sender: human`，不盖 build 的模型验证标签。
- 规则采纳历史随 job 提供并检查其报告哈希。原输入和人的决定都仍是不可变记录，改动会拦住派发。
- 已在 `needs_human` 的运行，采纳只记录规则、清除 hold、作废旧批准/待派发项，不额外排一个任务；之后 `resume` 只派发一次。
- 尚未有原任务时，采纳不会把说明冒充任务。必须随后真正发布原任务。

生产实现：[relay.py](../../scripts/relay.py) 中的 `redispatch`、`linked_context`、`publish`、`claim`、`resume`、`adopt_rules`。原任务和候选优先级没有变：新规则让旧批准失效，必须重新审查和接受。

## P2-02：审查适配器自动执行候选仓库配置

**Claude 方面由官方文档明确支持该发现；本地用合成启动过程复现了旧例子的问题。** `-p` 不应直接当作“无项目配置”的模式。[官方 headless 文档](https://code.claude.com/docs/en/headless)。

本轮示例改为：

- Claude 两种角色都使用 `--safe-mode`、`--setting-sources user`、空的 strict MCP 配置和关闭 hooks 的覆盖设置，避免自动加载候选配置/CLAUDE.md。安全模式保留正常登录，未改成需要 API key 的 bare 模式。[CLI 文档](https://code.claude.com/docs/en/cli-reference)。
- Codex 审查要求在候选和构建项目之外的可信 `--control-dir` 启动，并关闭这次调用的项目文档加载；不再把候选作为客户端启动目录。所需写目录单独列出，而且必须落在已记录的 write roots。[配置来源](https://learn.chatgpt.com/docs/config-file/config-basic)、[目录参数](https://learn.chatgpt.com/docs/cli/reference)。
- 两种示例的审查 SKILL 都必须来自候选/构建项目之外的可信安装位置，不能把候选里的技能文件当权威。
- 审查 SKILL 和提示要求单独检查 `.claude/`、`.codex/`、`.agents/`、`.mcp.json`、`CLAUDE.md`、`AGENTS.md` 的变化，不在候选里启动嵌套 AI CLI。

本轮没有真实 Claude 调用，所以不能写“已实测 hooks/MCP 全部被隔离”。测试证明的是 argv、启动位置、参数拒绝与合成客户端中的行为。Codex 只跑了已安装客户端的 `exec --help`，核对列出的参数，没有触发模型。

正常用户/组织策略和测试代码执行仍是另外的信任边界。若必要限制依赖自定义 hook，不能直接用禁用该 hook 的例子；需要用户先确认等效的权限/外部沙盒约束。这个例子不是运行任意恶意测试代码的容器。

实现与使用限制：[common.py](../../scripts/adapters/common.py)、[ADAPTERS.md](../../protocol/ADAPTERS.md)。

## 对其余建议的判断

| 编号 | 处理 |
| --- | --- |
| 4.3 非交互权限不足 | 采纳。增加来自人工配置的 `--allowed-tools`，默认不擅自放行；加 `--permission-prompts none`。文档分别给构建和审查示例，明确未授权工具拒绝后须求助，不是假成功。文件规则用绝对路径的 `//` 和覆盖编辑/新建的 `Edit(path)`，不误用 `Write(path)`。[官方语法](https://code.claude.com/docs/en/permissions#read-and-edit) |
| 4.4 多模型误判 | 保留严格拒绝额外模型的策略。“指定模型用量最大”不能证明主代理没有回退；没有用户授权时，不应悄悄接纳其他模型。若以后需要多模型/子代理，应另定策略和适配器；目前属于已知严格限制，未做真实 smoke test |
| 4.4 美元预算 | 采纳。Claude 例子把正的剩余 USD 限额传给 `--max-budget-usd`；仍是客户端估计，不是实际账单硬限额。未知 tokens/失败用量仍照旧暂停 |
| 4.5 直接绑定提交对象与树 | 技术方向可行，但本轮不更换快照格式。完整方案还需独立验证树排序、子目录、编码、权限位及不同 Git 对象格式。记入路线图，继续使用完整 SHA + 独立转交的 ZIP SHA-256，不假称 ZIP 注释就能证明提交内容 |
| 4.6 verified 缺依据 | 已修：配置 verified 必须有非空 verification_source；没有依据就不能用该级别 |
| 4.6 旧配置兼容和语言默认 | 旧布尔键保留为已注明的弃用映射，只用于手动更新过的 schema-2 配置，不是 schema-1 迁移。job 的报告语言默认值已删，直接使用启动时必填的语言 |
| 4.6 暂停时采纳重复排队 | 已修，见 P2-01；采纳不派发，resume 才派发 |
| 4.6 空格/错字导致重审 | 保留安全策略。文档注明可以先恢复原字节，再确认同一个哈希；真正采纳不同字节则旧批准失效 |
| 4.6 .DS_Store | 已有 ignore 规则；不纳入公开交付。没有借机删除用户文件 |

## 验证记录

| 验证 | 结果与范围 |
| --- | --- |
| 未修改 v0.2 + 五项新回归 | 5 项全部失败：adopt 的两种场景、resume 的两种场景、合成 CLI 启动 hook |
| 修复后完整包测试 | 69/69，21.936 秒；原 51 项的测试断言没动 |
| 新增补充验证 | 13 项，覆盖暂停采纳、无任务采纳、重复采纳、原任务/决定不可变、新审查可完整收尾、verified 依据、可信 SKILL、Codex 外部启动/目录拒绝、写权限范围、Claude 允许规则与剩余费用、额外模型拒绝 |
| 资源一致性 | `sync_bundle.py --check` 通过 |
| 两个 SKILL 格式 | quick_validate 都通过 |
| Codex 客户端 | 只核对 exec help，非模型接入验收 |
| 真实 Claude/Codex 调用 | 未做；没有新增付费调用或登录变化 |

合成 hook 测试模拟文档所述的自动配置发现，不能冒充真实 Claude 进程的验证。五项旧版失败只覆盖对应场景；其余 13 项没有逐一在旧版做反向控制。所有新测试可在本地无付费模型重跑：

```sh
python3 -m unittest discover -s tests -v
python3 scripts/sync_bundle.py --check
```

测试文件：[五项回归](../../tests/test_v02_review.py)、[补充验证](../../tests/test_v02_review_verification.py)。原反馈没有附测试文件；这些是根据它的场景重新编写的生产代码回归，不应写成“Claude 原样提供的测试”。

## 版本与下一步复核

仍没有项目 Git 提交，按用户指示留待自己处理。当前核心脚本哈希见 [VALIDATION.md](../VALIDATION.md)。runtime 字节/版本变了，旧信箱不能改 hash 强行接上新脚本；保留旧证据和预算，按已授权设置开始新的运行，或用匹配的旧 runtime 完成原运行。

下一位审查方建议关注：人的控制消息能否保留真实输入/反馈而不冒用模型身份；暂停与采纳的顺序；真实客户端是否遵守新的启动隔离参数。单元测试可直接独立重跑。真实接入若要做，需先由用户选定实际客户端/模型/强度、权限和小额预算；本轮未越过这一门槛。
