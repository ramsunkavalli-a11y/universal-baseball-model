# Affiliated team context source

Status: source foundation accepted; no model effect promoted.

The official MLB StatsAPI team endpoint now supplies season-specific team, sport,
league, division and home-venue identity for every affiliated level. The 2023–2025
capture used 18 requests and matched all 695 distinct team-seasons present in both
the hitter and pitcher component tables. No league or venue was imputed.

This closes the identity gap, not the adjustment problem. A league label does not
prove league strength, and a team's home venue does not identify a park effect from
aggregate player totals. League effects require matched-player validation. Park
effects require game or home/away context.

Reproduce with:

```powershell
.\.venv\Scripts\python.exe scripts\materialize_affiliated_team_context.py
```
