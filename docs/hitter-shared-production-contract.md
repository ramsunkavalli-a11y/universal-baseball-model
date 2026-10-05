# Shared production test for future MLB hitting

2026-10-05. Test whether one coherent event profile can use minor and foreign
production without estimating separate rare-source production coefficients.
This is historical development work. The completed, sealed 2026 evaluation is
not read, altered or used for selection.

## What changes

Keep the incumbent's three origin-known talent routes: never debuted, prior
debut with recent MLB tracking, and prior debut without tracking. As in the
incumbent, each rate head trains on all eligible future participants rather
than only its routed subgroup. Retain the corresponding non-event features,
MLB tracking inputs and prospect scouting priors. Replace the 98 separate
pooled event-rate columns and the old prospect translation profile with eight
shared, mutually exclusive event contrasts and exposure controls. Do not use
the failed pooled talent head or refit playing time.

Pool three observed years with weights 1, 0.8 and 0.6. Domestic MLB counts and
translated minor probabilities contribute weighted actual PA. Rebuild domestic
translation graphs excluding both the outer test fold and each source player's
own fold; use only counts through that row's origin. References also exclude
those folds. Foreign profiles already exclude both folds. Reanchor each foreign
translated profile by its centered log-ratio difference from its own MLB
reference to the common domestic MLB reference. This aligns coordinates; it
does not establish perfect international league equivalence.

Add 1200 reference PA once to the pooled counts. Express all eight contrasts
in ten-percentage-point units and retain all eight for a symmetric Ridge
penalty. Sample influence is bounded, and newer MLB PA dilute older evidence.
1200 is an explicit fixed design assumption inherited from earlier work, not
a newly estimated stabilization threshold. Tango's
[Marcel description](https://tangotiger.net/archives/stud0346.shtml) supports
regression toward a league mean, not this exact normalized weight/prior pairing
or its validity for minor and foreign players. Those require this test.

Use Ridge alpha 100, fixed physical scaling and the incumbent's equal-origin
row weights times uncapped future PA, globally normalized. No parameter search,
learned standardization, outcome-selected routing or supervised stacking. The
[Ridge objective](https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.Ridge.html)
penalizes coefficients, so shared columns let abundant MLB evidence inform the
same relationships used for other sources. This is a proposed representation,
not a claim that equal PA imply equal translation precision. Sparse mover
support and park/opponent limitations remain explicit.

## Population and comparison

Use the existing 35 chronological player-grouped cells and all 30,519 forecasts
through target 2025: 30,506 original identities plus 13 admitted source additions.
Training labels mature by the test origin; 2020 target is excluded. Canceled
minor seasons remain missing, and no new school or college collection is made.
Retain non-arrivals in delivered-value scores. Hitting rate is evaluated only
where actual MLB PA are positive; zero PA is not zero ability.

Hold original incumbent probability, conditional PA and expected PA exactly
fixed for all original rows. Additions have no incumbent forecast; evaluate
them separately with the already completed research employment PA, without
pretending that its availability gain is a hitting gain. Retain failed repair
and historical Steamer/ZiPS as qualified secondary anchors. Source/context and
the simultaneous coordinate replacement mean this is a coherent design test,
not a causal estimate of adding foreign data alone.

## Gates and stopping rule

Before any fit, persist all 105 head checks, training full/active profile counts,
feature-range warnings, excluded-fold graph membership, source hashes and
source walkthroughs for Yordan 2018, Judge 2016, Kurtz 2024, Suzuki 2021,
Lee 2024, Yoshida 2024 and Maitan 2017. Check probabilities, actual count units,
small-sample bounds, reanchoring identity and source removal. No internal
supervised tuning exists; graph and foreign-transform memberships are the
actual internal transformations to audit, not hypothetical tuning folds.

Primary: PA-weighted next-year MLB hitting RMSE with equal origin PA totals.
Secondary: all-person batting-plus-replacement value RMSE/MAE, bias and totals,
matched public common-reference hitting, origins and origin-known stages.
Report paired player-cluster intervals as nominal development evidence; years
and experiments are exposed. A pooled gain alone does not authorize promotion.
Any origin/stage rate RMSE worsening over 5%, extreme talent forecasts, implausible
event direction, or worsening overall delivered value blocks an unqualified win.
These are predeclared review triggers, not subgroup deletion rules.

After scoring, replay saved models and walk the fixed cases, largest gain/harm,
false high/low and one ordinary participant. Show dated source counts, translated
contributions, reliability, exact coefficient accounting, held training support,
fixed PA, rate and delivered value, and actual results. Include three origin-known
comparison people where possible, selected by age, prior debut, MLB exposure and
draft/scout context without reading their outcomes. Source-removal probes use
unchanged fitted models and recompute the entire shared profile; they explain
mechanics, not causal effects or approved forecasts.

Do not close the experiment or launch another model until that review is done.
Preserve every seal and failed attempt. No explorer promotion, 2026 reopening,
full WAR, six-year control or trade-value claim follows automatically.
