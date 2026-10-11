# 2026-10-11 — v0.2 after Claude feedback

Reproduced three v0.1 defects from Claude’s review before changing the relay: two assertion failures and one initialization error. Added manual/browser snapshot workflows, example CLI bridges, honest settings-verification levels, report language, pinned running rules with held dispatch and human adoption, and relay version/byte-hash checks. Preserved two standalone skills and MIT licensing.

Local verification: 51 tests passed; both skill validators and bundle equality passed. Real-provider integration remains untested, and the v0.2 repairs await independent review. Details, test-policy adaptations and source hashes are in [the delivery](../deliveries/2026-10-11-feedback-fixes.md) and [VALIDATION.md](../VALIDATION.md).

The human owns Git initialization/publication. No output repository or remote was created, no global skill installed, and no paid model invoked. Claude’s original feedback is retained locally and ignored for publication.
