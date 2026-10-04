# Preparation export repair before hitting fits

2026-10-03. The first preparation process exited with a table-width error when
combining broad and refined support tables. All graphs and original-head replays
had run, but no preflight manifest or new hitting fit was saved. The repaired
runner uses a diagonal table union so that the refined columns can be missing
in broad rows. It also passes a list to the identity membership check to remove
a deprecation warning. Neither change affects predictors, labels, identities,
adjustments, training membership or model settings.

The original preparation runner SHA256 is
`ea5c8e5e958fbbf12e674c01864e641fb534552970643494c580169ae5277a88`.
Its five source-only feature caches and graph metadata are retained unchanged.
Reuse is permitted only if every source hash is identical except that exact
old runner hash. The final preflight seals the repaired runner and those original
cache hashes. All full/active checks and 35 anchor replays are repeated before
any new hitting fit. The original experiment contract remains unchanged.
