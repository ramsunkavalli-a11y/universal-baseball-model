# Compare serialized clinical dates consistently

2026-10-04. The scoped-status preparation exited at its first preservation check:
the unchanged clinical spells contain date objects in memory but ISO strings in
the saved first ledger. The failed preparation and seal remain intact. No new
ledger, fit or forecast was written. The successor compares both records in the
same JSON representation, preserving the exact original clinical content. Source
rules, population and cutoffs do not change. A separate recovery seal pins this
execution correction before materialization resumes.
