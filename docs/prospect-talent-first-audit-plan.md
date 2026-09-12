# Prospect talent-first audit plan

Status: frozen before inspecting the talent-only ranking.

## Purpose

Separate prospect talent from playing time. The immediate question is whether the
model's regressed performance per full workload produces a defensible player order.
Arrival probability, expected workload, contracts, team control, and dollars are
excluded.

## Talent measures

- Hitters: conditional whole-player WAR per 600 PA, showing batting, running,
  defense, and position separately. Use the passing private player-level position
  estimate when available; otherwise retain the current position component.
- Pitchers: conditional WAR per 800 BF and pitching runs above average per 800 BF,
  with translated K, BB, HBP, and HR rates visible.
- Existing regression and reliability remain active. Do not reward raw small-sample
  performance.

The 600 PA and 800 BF reference rates are full-workload normalization scales, not
playing-time forecasts. Rank by conditional WAR rate only. Use reliability and source
coverage as warnings, not a second ranking input.

## Review

Create one combined top 50 and compare it with the still-eligible FanGraphs top 50 as
an outside diagnostic. Public rank and FV may not enter talent, thresholds, or model
selection. Every large disagreement must show its model components and evidence
strength.

This audit cannot change production. It identifies whether the next build belongs in
hitter skill, pitcher translation, defense/position, or evidence regression.

