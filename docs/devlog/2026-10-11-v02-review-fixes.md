# 2026-10-11 — v0.2.1 after independent v0.2 review

Claude withheld v0.2 approval after identifying two P2s. Reproduced four human-redispatch input-loss cases directly against the relay and one documented startup-hook behavior in a synthetic CLI before changing production code; all five failed. Repairs preserve original reports and linked context, identify human decisions separately, avoid paused-adoption double dispatch, and isolate example reviewer client startup from candidate configuration.

Also added explicit Claude tool grants/no-prompt behavior and remaining estimated USD cap, required verified-setting sources, and documented the deliberately strict single-model policy. Deferred SHA-only snapshot proof to a separately tested format. Neither a real model call nor any unrelated product repository was used. Installed Codex help was checked read-only.

Final suite: 69 passing tests in 21.936 seconds, both skill validators and bundle equality passed. Real CLI isolation and independent approval of these repairs remain pending. See [delivery](../deliveries/2026-10-11-v02-review-fixes.md) and [validation](../VALIDATION.md). Git initialization/publication remains with the human.
