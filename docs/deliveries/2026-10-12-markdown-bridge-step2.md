- Author: ChatGPT / ForgeDuet authorized step2
- Created: 2026-10-12T20:29:50+01:00

# ForgeDuet 第二步：一次真实 Codex 调用实测

## 结论

**传输链路验证通过；Swift 测试执行门槛未通过，暂不具备正式部署条件。** 仅调用一次真实 CLI，没有自动重试。没有恢复 WristFiles 监听、访问其源码/笔记/设备、安装技能、提交或推送。本报告供用户手动转交 Claude 复核，不假称对方已收到。

人类授权：本聊天 2026-10-12「可以开始第二步」。使用 Claude 已复核的桥接候选 0.2，不改 runtime；其固定源码清单 SHA-256 为 `79e39eb12d2f50ce2a590112bd3ac8ebf5d11941d7cc8a18d09f734af9842152`。本次复制运行的 `markdown_bridge.py` SHA-256 为 `76522e27302a9d79093d56aacc57dd713868a24c3c3c6ced6e94cd1a10346fa0`，与该候选及工作区相同。Claude 最新跟进复核已读，两项 P3（正常结束通知措辞、部署时同步双方已安装技能）仍待部署前处理；本轮不改其原反馈。

## 实际环境与一次调用

- 本机 CLI：`0.162.0-alpha.17.2`，路径 `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`。显式选择 `gpt-6.1-sol / xhigh`，来源为用户已有选择和本机模型缓存的可选 ID；覆盖本机旧全局默认，不修改全局配置。没有降级、换模型或独立服务端身份认证，不能把配置值当成密码学证明。
- 合成项目完整 SHA：`1cc1a6e2e7f73f6d47005f032563ec5c573649e4`；只有三个 Swift 文件、两个 XCTest 用例、无外部依赖。合成 Git bundle 保留真实对象，未导出 WristFiles。
- 临时根目录：`/private/tmp/forgeduet-step2-gqqojy3t`；project、control、runtime、trusted 分开。状态先写，完成交付后不再变动。工作器从固定 SHA 导出快照，在 control 内执行测试。
- 外层系统沙箱的无模型探针返回 `sandbox_apply: Operation not permitted`（71），随后本轮执行获额外批准；CLI 子会话仍以 `workspace-write` 运行，没有使用绕过沙箱的选项。联网授权用于 Codex 调用，合成测试无依赖下载。
- 单次 CLI 于 `2026-10-12T20:21:50+01:00` 开始，`20:26:18+01:00` 持久处理结束，约 268 秒；一个 `thread.started`、一个 `turn.completed`、一个运行目录，24 个完成的 shell 工具操作。一次 CLI 会话包含多次内部模型往返，不等于仅一次模型请求。

## 链路、停止与显示

1. 完成交付之前，五次本地 idle 扫描全为 waiting；禁止启动 subprocess 的断言通过，未创建调用 journal。此项为本方无模型检查，不冒称工作器独立复现。
2. 完成交付出现后启动上述唯一一次真实 CLI，核验任务、交付、状态及源码，并真实执行一次测试命令。
3. 工作器正常返回结构化有界失败报告，桥接在锁内发布报告和追加日志，释放锁后才确认交付精确哈希。运行 journal 为 handled，游标 paused，watcher 已清空，writer 锁已释放；停止是本次授权结束后的人工采用门槛，不是 Swift 测试通过。进程退出码 3 对应 paused，不是 CLI 调用失败。
4. 单独的停止传输通知已完整发布、记录哈希；不将它当作审查或产品批准。macOS 回执为 submitted / 0，**用户在当前聊天明确回复「看到了」**，因此这一回横幅实际显示已确认。通知措辞仍是已知 P3 的故障式措辞，没有隐藏。
5. 本次 thread ID `01a13190-699d-7691-8ca4-767e2d00ec7a` 未出现在结束后 App 返回的 16 条最近/置顶记录中，通常 sessions 目录也未找到该 ID 的 rollout 文件。最初的前置列表请求误填 limit=100 被拒绝，后改为有效 limit=50；没有完整前后基线，不推广为所有版本/界面永不显示的保证。使用了 `--ephemeral`，没有主动创建任何侧栏聊天。

原工作器报告的 FD-SMOKE-002 是其返回前尚不能核验的传输/用量限制；返回后本方已补齐发布、ack、停止通知、一次 CLI 和用量证据，但不将本方核验假称另一独立审查方批准。

## FD-SMOKE-001：Swift 沙箱门槛失败

实际运行 `/usr/bin/swift test` 一次，scratch/cache/temp 都指定到 control，退出码 **1**，耗时约 5.01 秒。SwiftPM 清单处理报 `Invalid manifest`，末尾为 `sandbox-exec: sandbox_apply: Operation not permitted`。**两个 XCTest 均未执行，不能报告 2/2 通过，也不是已证实的产品代码 bug。** 包装器保存日志成功不改变 Swift 子进程失败结果。没有第二次测试、权限绕过或偷偷更换运行方式。

完整命令和环境在 `control/test-result.json`；原始 stdout 为空，stderr 和合并日志保留。源码快照及活动合成源码/index 均复核未变。本次证明默认 CLI 沙箱下此 SwiftPM 路径不可用，不证明其他测试工具、模拟器或 WristFiles Release 构建一定可用/不可用。下一步先进行不调用模型的最小环境诊断，提出有边界的处理方案；任何真实模型复测另需授权，不自动消费第二次。

## 实际用量与解释

| CLI 报告字段 | 数量 |
| --- | ---: |
| input_tokens | 443,949 |
| cached_input_tokens（已包含在 input 中） | 372,992 |
| 非缓存输入（相减） | 70,957 |
| output_tokens | 10,740 |
| reasoning_output_tokens（已包含在 output 中） | 2,503 |
| cache_write_input_tokens（原始流附带，现 parser 未输出） | 0 |

总输入加输出为 454,689，不能再加一次缓存或推理子集。这里是 CLI **整次会话累计**计数，含多次模型往返中的重复上下文；不是 443,949 个不同源码 token，也不是空闲轮询支出。可信角色说明及多份参考文档确被读取，输出报告也较长；可定位存在启动上下文和工具往返开销，不能仅凭这一次把全部开销精确归因给“恢复记忆”。父聊天准备/观察/本报告同样用模型，**不包含在这组子 CLI 数字里**。缓存折扣、账号额度换算及实际金额未知，不估美元、不称免费。

这组数字足以否定“微型新会话自然就很便宜”的预设。零模型 idle 检查成立，但还没有做新会话/续用会话对照，也没有证明审查质量等价。建议先精简明确的 smoke 启动上下文和不必要文档读取，并保留必要证据门槛；不要用未经授权的模型降级或预算上限替代优化。本轮停止在测量结果，不继续跑质量实验。

## 证据与复核请求

原始材料：`evidence/raw/2026-10-12-markdown-bridge-step2/`，清单共 52 份文件，`manifest.json` SHA-256 **`58bb72540315802897640e7d516d865a2984e6750774519cddb72ae186fbd5e3`**。包含实际 CLI JSONL/stderr/answer/attempt、精确配置和可信 smoke 指令、合成任务/状态/交付、发布报告与通知、游标、追加日志、Swift 原始日志/结果、源码 bundle 和本方后验摘要。未拷贝账号凭据、全局配置或构建缓存，原件保留，权限限制为同用户可读写。报告中旧临时绝对路径保持原貌，持久副本按清单映射查找。历史 step1 的假 CLI 测试不冒称本轮重新执行。

请 Claude 复核记录和证据，**不要额外派发真实 CLI 测试或自行启用项目桥接**：核对用量计数/子集关系、唯一调用、先发布后 ack、真实测试失败分类、通知显示依据、sidebar 限制，并就无模型环境诊断和入口精简提出建议。Swift 门槛未过，双方 installed skill 尚未同步，WristFiles/其他项目均未部署。ForgeDuet 仍未提交/暂存/推送；第一步认可不等于第二步正式采用。

交付完成
<!-- FORGEDUET_COMPLETE -->
