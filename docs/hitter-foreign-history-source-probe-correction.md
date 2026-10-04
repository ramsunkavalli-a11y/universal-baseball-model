# Correct the NPB index parser before collection

2026-10-04. The first source probe stopped before any complete batting table
was materialized: the 2005 season index returned zero accepted links against
the required twelve. Its HTML uses relative links such as `idb1_f.html`, not
root-relative links. This was a parser-design error, not missing season data.

The failed parser hash is
`4fa94d7f0d542891bbb9339e1ec74cafb431185ca2c777b9809002b9d5679f3e`.
The original index bytes and request receipt stay in the private source cache.
No completed successful qualification or model result is overwritten.

Resolve links against their exact requested season index, require the same
official host and contracted first-team path, and test both relative and
root-relative duplicates. The twelve-team requirement and original source
scope are unchanged. Repeat qualification only after this correction; no broad
capture or fitting was permitted by the failed probe.
