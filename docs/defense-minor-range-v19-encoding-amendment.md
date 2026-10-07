# Correct the recovery wrapper encoding name

2026-10-07. The first recovery wrapper failed before reading the reviewed
source receipt or fitting any additional cell: `utf8-sig` is not the Python
codec name. Its sealed script and additive resume preflight remain intact.
The second sibling uses `utf-8-sig` and a separate resume preflight filename.
These are its only code differences. Statistical inputs, the sealed model
module, comparison rules and all completed fits remain unchanged. The prior
wrapper's process was observed terminal before this correction was launched.
