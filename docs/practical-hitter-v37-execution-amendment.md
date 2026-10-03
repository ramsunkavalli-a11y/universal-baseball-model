# Anchor code isolation before fitting

2026-10-03. No V37 models have been fitted or scores inspected. The first
preparation captured helper additions in the shared V36 likelihood module.
Those helpers now live in a separate anchor module so the completed V36 source
can remain byte-exact and its original input hashes reproducible. The original
V37 preflight is preserved as `preflight-before-code-isolation.json`; repeat
preparation with hashes for both modules before fits. Counts, formulas, settings,
feature/evaluation/training identities and intended comparison are unchanged.
This is an execution-source isolation repair, not post-score model tuning.
