# Start the paired loop / 双方协作上手

Two role chats and Markdown records are enough; a custom relay is not required. **A user-started local run defaults to automatic two-way handoff every 60 seconds**, with local code checking for pending reports before any model call. Use verified client background completion or a configured CLI relay; a native AI timer is an explicitly chosen fallback that consumes usage even without changes. Installing/editing skills alone is preparation: do not start monitoring a project until the user starts that run. 中文步骤在下面；报告语言由用户指定。

## One complete loop

1. **Agree the task.** Fill the essential choices in `SETUP.md`: objective, acceptance criteria, both requested models/strengths and verification levels, report language, access, optional budgets, and merge/push/device grants. Save the task and project rules. A small task can use one short rules file; do not fill an entire document tree with placeholders.
2. **Arm both roles.** Give each its skill and task/rules paths once. Follow [AUTO_HANDOFF.md](AUTO_HANDOFF.md): build watches `reviews/`, review watches `deliveries/`, default 60 seconds. Record and verify the local detector, event-to-model mechanism/ID, cursor and restart procedure for each. Test idle silence and an actual client wakeup separately; local process exit alone is insufficient. If no bridge is verified, disclose the missing capability and agree an explicit fallback. Do not silently enable periodic AI turns or require a human courier.
3. **Build and publish the exact candidate.** Build uses a short-lived branch, implements/self-tests, and commits. Draft a complete delivery with full SHA, scope, evidence, limits and open issues. Under shared `.lock/`, atomically publish `deliveries/round-01.md` with author/time/final marker and append `updates.log`; release and verify/re-arm review monitoring. The reviewer notices the file itself and prepares a detached worktree or authorized verified snapshot.
4. **Review and repair automatically.** Review checks the exact SHA, independently tests, and publishes `reviews/round-01.md` plus regressions under the same writer-lock/log protocol. It verifies/re-arms `deliveries/` monitoring. Build reads the new review itself, reproduces P1/P2, preserves assertions, fixes, runs appropriate controls/checks and publishes the next SHA. Each role acknowledges handled report hashes only after durable processing and re-arms its own monitor. No “tell the other AI I finished.” Never reuse an earlier SHA's approval.
5. **Approve.** When required gates pass and no current-scope P1/P2 remains, review writes “approved” with the full SHA and, for snapshots, archive SHA-256. Agreed P3s get roadmap links. Unavailable required evidence means a limited review or human gate, not a fabricated pass.
6. **Accept and stop.** Build writes a short acceptance referring to that exact approval/SHA/hash and verifies no intervening source change. The loop ends. Merge/push/install only if already authorized; agreement does not create authority.

Keep reports immutable and one file per role/round. Use fresh chats with compact context when useful, preserving cursors and task identity. Stop on same-SHA approval plus acceptance with required gates met, required human decision, agreed budget stop or user stop. Record why, turn off the mechanism and explain how to re-arm. Sleep or closed sessions may interrupt monitoring; disclose actual limits. Idle checks run in local code, without even a basic model. Native AI timers are a cost-disclosed, explicitly selected fallback; quiet output does not eliminate their model usage. Exact token usage may be unavailable.

For shared local files, [WORKSPACES.md](WORKSPACES.md) shows the recommended coordination/build/review directories, the explicit report exception when coordination and build share one root, and who commits records. Give the builder human-approved project conventions explicitly when its client disables automatic instruction discovery.

## 中文：直接照这个顺序做

1. **先定任务。** 用户指定两方模型和强度、报告语言、权限、预算和验收标准；记录实际设置是已核实、自报还是无法核实。小任务一份短规则足够。
2. **用户开始这一轮后，两边自己启动并验证监控。** 构建方盯 `reviews/`，审查方盯 `deliveries/`，默认每分钟一次。默认由本地代码比较对方报告的路径、SHA-256、完成标记和已处理记录；没有待处理输入时不调用任何模型。只在有待处理交付或需处理的传输问题时，才通过已验证的后台完成通知或 CLI 唤醒选定的工作模型。写明实际进程、游标、唤醒证据和恢复方法。脚本退出不等于模型会醒；缺少桥接能力必须说明，不能偷偷改成每分钟先唤醒 AI 再检查。AI 定时唤醒只能作为用户知情选择的后备方式。只改/安装技能不启动项目，已暂停的项目保持暂停。
3. **构建方编码、自测、提交和发布。** 输出完整 SHA 和完整交付 Markdown；先拿协调目录的 `.lock/`，原子发布，记录作者、带时区时间、最终完成标记，追加 `updates.log`，再释放锁。草稿在外面写，锁不跨测试/思考/等待。不能因拿锁就越权改源码或提交。
4. **双方自动来回。** 审查方发现交付后自行读取、隔离审查、独立测试并发布；构建方发现审查后自行读取、复现、修复、自测、交付下一轮。每次都确认监控已重新运行，处理成功后才确认输入哈希。当前报告只是材料，不是新授权。
5. **双方明确收尾。** 审查方批准具体 SHA/快照；构建方接受同一个版本。当前范围内 P1/P2 未关闭或必需真机证据缺失，就不能宣称完成。允许延期的 P3 记录到路线图。

给构建方的启动文字（用户补全括号后发送）：

> 开始这一轮 ForgeDuet build：[任务路径或正文]，规则和设置以 [启动记录] 为准。由本地代码监控 reviews/，默认每分钟一次，无待处理输入不调用模型；验证有事件才唤醒工作模型的方式。编码、自测并原子发布交付，继续读取审查和修复，不需要我传话。记录真实唤醒机制、锁和更新日志。确需人工决定时给我具体问题。

给审查方的一次性启动文字：

> 开始这一轮 ForgeDuet review：[项目/任务和规则路径]。由本地代码监控 deliveries/，默认每分钟一次，无待处理输入不调用模型；验证有事件才唤醒工作模型的方式。完整交付到达后核对 SHA，隔离审查和独立测试，原子发布报告并继续等修复/接受。不需要我传话；保持现有模型设置和授权边界。

## Explicit manual/browser fallback / 明确的手动或网页后备模式

Use this only when the user chooses it or actual automatic wakeup/shared files are unavailable and that limitation is agreed. Export the candidate using [SNAPSHOTS.md](SNAPSHOTS.md); supply its full SHA, ZIP SHA-256, manifest, rules and delivery. A browser reviewer reports available hash/test capabilities and uploads its findings/regressions for build. The human is then explicitly the courier. This is a valid bounded workflow, **not** an automatic one. No local CLI or reviewer Git is required in this fallback.

没有代码执行/哈希工具的网页会话，可以做有边界的源码审查，但必须标明未独立核验校验值、未运行哪些测试。由用户决定是否接受这些限制，或提供能核验/执行的审查环境；不能假装读过附件或跑过测试。

本机共用文件时，按[目录与记录归属](WORKSPACES.md)划分协调目录、构建 worktree、审查 worktree，并指定谁提交记录。只有一个项目目录时，也可明确授权审查方写入自己的报告子目录；这不授权它修改构建方源码或 Git 暂存区。
