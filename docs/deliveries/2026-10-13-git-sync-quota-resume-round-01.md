- Author: ChatGPT / git sync and quota candidate delivery
- Created: 2026-10-13T22:03:41+01:00

# ForgeDuet：Git 远程同步与额度重置续接（第 1 轮候选）

## 交付状态

- 用户请求：2026-10-13，新建 feature 分支，支持跨计算机 Git 同步协作，并默认支持 token/usage 额度耗尽后等待 reset 再继续。
- 分支：`feature/git-sync-quota-resume`，从最新版 `b044e2c73ed904de6188ef23e88db9651214b073` 创建；main 未修改。
- 完整候选 SHA：`ac11a4fba84c81e68478b55c44ca1c18800e911e`。这是构建交付，**尚未独立审查/批准**。
- 指令与 typed relay 为 v0.4.0 candidate；Git 适配器为 candidate 0.1。旧 byte/version pin 的活动运行不自动迁移。已安装技能没有替换。

## 实现

1. **Git 跨机器交接**：各主机保留本地 mailbox/runtime，构建与审查各写一条远端角色分支。可信本地脚本在独立 bare object store 中 fetch/push，按完成标记、路径、角色/run、manifest、SHA-256 与历史祖先校验，投影 peer 记录到本地目录，然后使用已有本地 detector/client wakeup。原有同机文件方式保留。支持完成报告与明确公开的回归文件；不传本地游标、锁、更新日志、原始私有证据或配额状态，不自动操作产品工作区/index。产品源码仍需获授权的 branch push/fetch 或可信快照，交付报告不等于源码已送达。
2. **配额默认等待/继续**：两边 typed relay 都支持可信适配器的终止 quota 结果，持久化 waiting_quota；重置时间加 2 秒后重新 claim 同一任务，新的 fencing token 和 quota_continuation 保留原身份/检查点。queue 支持可信 observer 的精确 event/message 绑定，等待后只发送一次同聊天续接，发送前持久化 intent；已有报告/ack 优先。ephemeral exec 只允许明确未开始任何 item/tool 的结构化 quota 失败等待后重试同一输入。
3. **防止误续接**：人工暂停、明确 token/费用/时间预算、权限、容量/账单错误、缺失 reset、仍活着的 worker、派发结果不明均不能冒充额度重置。等待不调用模型，不更换模型或强度，不自动购买额度。旧错误/部分工作保留；不确定的续接不会自动重发。
4. **恢复与提示**：Git push 的原提交可在网络结果不明后核对/重传，不重复模型工作；改写、冲突或本地丢失状态会停止。传输停止生成去重的本地 transport_notice 和尽力发送系统提示，不作为产品审查。

## 验证

- **202/202 合成测试通过，42.201 秒**：保留原 167 项断言，新增 35 项。
- Git 用真实临时 bare 远端与两个独立本地目录，覆盖双向文件、回归材料、精确本地 ack、未完成/私有文件排除、不可变报告、冲突、推送失败/成功但回执丢失、导入中断、历史回退、路径/模式/大小限制及停止通知去重。
- 额度用假客户端与受控时间，覆盖 build/review、已退出适配器实际返回 quota 后继续同一任务到 candidate、重启、重置前零额外调用、每个终止回执一次 queue 续接、报告/ack 优先、缺失 reset、部分工具工作、状态/输入改变、预算及用户暂停。未运行付费模型。
- 两份 bundle 一致，技能格式检查通过，协议/技能/template 相对链接无缺失，git diff --check 通过。最终脚本/测试与完整套件通过时的哈希一致。
- 早期测试日志也保存：新增夹具的 Unicode bytes 字面量、调用漏传 interval，以及对已持久暂停错误的预期状态不准确，均已修正后重跑；没有削弱旧的产品安全断言。

## 未执行项与门槛

- **FD-QUOTA-INT-001：真实客户端额度回执接入/实测尚未完成。** 运行时协议和等待/续接逻辑已实现；不是所有版本的 Codex/Claude 都有可信 reset/terminal/checkpoint 字段。queue 的 quota_status_file 需要经过核验的可信适配器/observer 输出；没有宣称已提供通用于所有客户端的自动 observer。纯文字报错或未知 reset 仍是显式阻碍，不能伪称自动继续。exec 的窄结构化 shape 仅由假 CLI 验证。
- **FD-GIT-INT-001：真实 SSH/HTTPS、认证、实际跨主机网络与服务生命周期未测。** 临时本地 bare 远端验证的是 Git/文件协议；不同机器应按配置分别验证权限、源码可达性和已有 wakeup。
- 忙碌/归档聊天、睡眠/重启、真实配额等待周期和完整产品审查质量仍是后续门槛；离线/关闭的本地进程不能自行工作。没有安装后台服务或恢复项目监听。
- 当前没有独立审查结论；请 Claude 复核固定候选、源码和回归证据。用户未要求本轮真实模型测试或启用项目，因此未自行执行这些动作。本轮未推送或合并，没有其他项目/真机/笔记操作。

## 文件与证据

实现：scripts/git_transport.py、scripts/quota.py、relay/queue/markdown bridge 的配额扩展；协议/模板/两份技能已同步。任务范围：docs/requirements/git-sync-quota-resume.md。

原始证据目录：`evidence/raw/2026-10-13-git-sync-quota-resume/`。固定 SHA 源码归档 `source.tar.gz`，162 个文件，SHA-256 `f050559caa53e93f8160c6790b288992867143ebfe8d99bc775253acb39548bf`；证据清单 SHA-256 `bfea8f9a76e34ae1cb38d7ac28e3408bf96c6e7aac0e862b7667978909fffd64`。包括最终全套与早期失败日志、精确脚本/测试哈希及候选记录。原始证据按项目规则留本机；报告与源码纳入本地 feature 分支。

交付完成
<!-- FORGEDUET_COMPLETE -->
