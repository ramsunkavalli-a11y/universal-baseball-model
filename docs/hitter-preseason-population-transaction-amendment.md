# Preserve every player in a transaction

2026-10-04. The first collection stopped in 2012 before materialization because
its transaction-ID uniqueness assumption was wrong. Preserve its partial
captures and code. A trade is one transaction with several player records;
the ID alone is not a player-event key. The captured November 2011 Cabrera,
Sánchez and Verdugo trade demonstrates three distinct people under one ID.
Cash legs may have person ID zero and must remain source rows, not players.

Compare complete raw-record multisets between the broad window and monthly
windows, rather than overwriting records in an ID-keyed dictionary. Preserve
exact duplicates and report them. Materialization uses a composite event key
including person, teams, type and dates; contradictory content under that key
must stop the source review. Requested-window dates and advertised counts must
also reconcile. This repairs extraction, not the forecast or transaction timing.

## Experienced foreign players are a separate talent profile

User clarification, 2026-10-04: Japanese professionals such as Ohtani have
different expectations. Do not equate missing MLB history with an inexperienced
player. NPB/KBO professional history, age, scouting and signed role should inform
translation and opportunity where dated sources exist. Nationality alone does
not establish league, experience or talent. A minor contract and absence from
40Man do not establish low readiness, especially under international signing
rules. Preserve two-way and unknown-role candidates before any hitter filter.

This source milestone marks missing foreign performance and ambiguous roles;
it does not fabricate a translation, a Japanese-player bonus or a zero talent
label. The integration contract must specify supported foreign baselines and
fallbacks before fitting or projecting new entrants. Do not claim a complete
foreign-player solution from domestic roster collection alone.
