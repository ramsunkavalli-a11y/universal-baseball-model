# Current basic talent checkpoint

Last updated: 2026-09-12  
Status: **CURRENT RATE FOUNDATION BUILT; FUTURE CEILING IS NEXT**

The current StatsAPI path now produces a simple rate-only diagnostic for every player
in the dated roster universe:

- 3,940 hitters; 2,151 clear the fixed 100-effective-event ranking line;
- 5,690 pitchers; 2,644 clear it;
- all 50 FanGraphs comparison players are found (36 hitters and 14 pitchers);
- 43 of those 50 have enough translated evidence to rank; seven remain unresolved.

The hitter score uses translated and regressed strikeout, UBB, HBP, single, double,
triple, HR and other-ball-in-play-out rates. The pitcher score uses translated and
regressed K, UBB, HBP, HR and
other-event rates. It does not include playing time, position, defense, arrival,
contracts, replacement, organization, public rank or public FV. The public list is
joined only after scoring.

This confirms the data pipeline needed for a current talent model exists at scale,
including rookie/complex aggregate data. It also confirms why the present-rate list is
not the final prospect list: the median present-rate rank among supported FanGraphs
top-50 hitters is 586, and among supported top-50 pitchers is 931. Young players are
being compared with today's MLB and upper-minors performers before future development
is considered.

Do not patch that gap with an assumed age bonus. The repo's earlier generic one-year
hitter age/level adjustment improved two periods and reversed in the third, so it stays
rejected. The next test must directly model future talent from historical player paths:

1. freeze current translated component rates, level, age relative to level and evidence;
2. target one- and two-year future component rates, with fixed minimum future evidence;
3. compare carry-forward, transparent age/level, and strongly regularized component
   interactions on identical players and chronological folds;
4. report missing future observations separately rather than calling them poor talent;
5. attach FanGraphs only after model selection to explain the top-50 agreements and
   disagreements.

This is the immediate P0. Opportunity work remains paused.
