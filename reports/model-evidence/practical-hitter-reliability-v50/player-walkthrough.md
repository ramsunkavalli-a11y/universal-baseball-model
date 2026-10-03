# Actual player review of MLB evidence reliability

Twenty-five actual cases trace source counts through the conditional prior, transported MLB anchor, skill-specific shrinkage, coherent event probabilities and delivered offense. The source cases were checked before fits; actual cases and origin-selected peers remain in cases.json. Every forecast is next calendar year, not present-day minor-league equivalency, full WAR, control years or trade value. Zero next-year PA means unobserved conditional ability.

The 145 actual prior inputs are saved for every case. They cover separate-level minor counts/rates, age, exposure context, position, draft evidence and historical rankings. Own MLB performance enters only the explicit count anchor. Counts use three years with 1/.8/.6 recency; minor rates retain fixed 100-opportunity stabilization. MLB history is transported by completed league environments, not park-neutralized. Source/event alignment and 70 saved heads are replayed. Draft school class is unknown in many old source rows: this is a coverage gap, not a false high-school classification. No new college collection, current biography or protected outcome is used.

Each event blends u=(own count + alpha × prior)/(weighted MLB PA + alpha); eight u values are then normalized. Displayed own influence N/(N+alpha) is before that normalization, not a final causal allocation. Priors are probabilities among future MLB participants, not a validated hypothetical MLB grade for every DSL player.

Original selection adds each arm’s raw unweighted rate and value extrema. Some raw rate extrema have only one to three PA and cannot be the primary conclusion. A supplemental actual-PA-weighted error contribution check identifies Judge 2023 as both arms’ largest meaningful rate gain and Judge 2016 as their largest harm; both were already selected. Repeated historical development evidence remains qualified.

## Aaron Judge from 2016 to 2017

Player 592450, row 23934, fold 3, age 24.0, stage Current MLB. Selection: fixed diagnostic, fixed_reliability value false low, learned_reliability value false low.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | A | 278 | 9 | 59 | 38 |
| 2014 | Aplus | 285 | 8 | 72 | 49 |
| 2015 | AA | 280 | 12 | 70 | 23 |
| 2015 | AAA | 260 | 8 | 74 | 29 |
| 2016 | AAA | 410 | 19 | 98 | 47 |
| 2016 | MLB | 95 | 4 | 42 | 9 |

Weighted transported own MLB PA: 95.000000. Actual-fold active profile: [{'row_id': 23934, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'own_mlb_exposure': 'brief', 'active_profile_players': 34}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.057204 | 287.450116 | 0.860267 |
| fixed_reliability | -1.031461 | 287.450116 | 0.393516 |
| learned_reliability | -0.858240 | 287.450116 | 0.476504 |
| Actual | 5.329876 | 678 | 8.108407 |

Unchanged expected PA = participation 0.93161424 × conditional PA 308.550582. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 28.000000 | 0.474130 | 0.403644 | 100.000000 | 0.487179 | 0.350587 | 0.350587 | 195.0 | -0.000000 |
| K | 42.000000 | 0.211193 | 0.279289 | 100.000000 | 0.487179 | 0.358610 | 0.358610 | 208.0 | 0.000000 |
| UBB | 9.000000 | 0.076693 | 0.092756 | 100.000000 | 0.487179 | 0.093721 | 0.093721 | 116.0 | 0.593138 |
| HBP | 1.000000 | 0.008945 | 0.009881 | 100.000000 | 0.487179 | 0.010195 | 0.010195 | 5.0 | 0.045424 |
| 1B | 9.000000 | 0.149198 | 0.129672 | 100.000000 | 0.487179 | 0.112652 | 0.112652 | 75.0 | -1.613041 |
| 2B | 2.000000 | 0.044718 | 0.042992 | 100.000000 | 0.487179 | 0.032304 | 0.032304 | 24.0 | -0.771195 |
| 3B | 0.000000 | 0.004730 | 0.006243 | 100.000000 | 0.487179 | 0.003202 | 0.003202 | 3.0 | -0.119667 |
| HR | 4.000000 | 0.030393 | 0.035522 | 100.000000 | 0.487179 | 0.038729 | 0.038729 | 52.0 | 0.833880 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.19986329753836185, 'UBB': 0.0923711191745983, 'HBP': 0.2259986788740148, '1B': -0.07117018910907053, '2B': -0.021063743489630197, '3B': 0.30912634690803736, 'HR': 0.10448163639603059}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.1155067285159346, 'UBB': 0.01802300860589531, 'HBP': 0.07643534787215886, '1B': -0.021306586504763022, '2B': 0.016679799624971712, '3B': 0.03238442002028732, 'HR': 0.006788317681793438}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.03, 'effects': {'K': 0.0865747829557009, 'UBB': -0.013587860938850683, 'HBP': 0.007281887409088666, '1B': -0.011270365206058817, '2B': 0.02720775376447523, '3B': -0.03796306950622967, 'HR': 0.00996441184663584}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.5800738007380072, 'effects': {'K': 0.008810837550176752, 'UBB': 0.07763613361485366, 'HBP': -0.005118887499739858, '1B': 0.005736494660793797, '2B': 0.00245392020487562, '3B': -0.0069350308650893405, 'HR': -0.0032523955729811026}}, {'feature': 'scout_listed_1', 'scaled_input': 1.0, 'effects': {'K': 0.05771633971173615, 'UBB': 0.012162880929875984, 'HBP': 0.017902897304364257, '1B': -0.012885914761207694, '2B': 0.0015424390302219372, '3B': -0.014942687830002055, 'HR': 0.05334325843619802}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.006161606783084838, 'UBB': -0.009211297384255903, 'HBP': -0.026233026561994565, '1B': 0.03876033235949084, '2B': 0.019984709340673305, '3B': 0.017353366791156778, 'HR': 0.054749668890241}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.2891364902506964, 'effects': {'K': 0.010110863824680023, 'UBB': 0.05110221244821113, 'HBP': -3.203225482785935e-05, '1B': 0.000817984610550901, '2B': -0.0021894064503058795, '3B': -0.002392291575563771, 'HR': 0.001857595528197728}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': -0.026132681539594107, 'UBB': 0.012595985721653859, 'HBP': -0.0077795650399870514, '1B': 0.017015494252067716, '2B': 0.035718560261862, '3B': 0.006403789803874096, 'HR': 0.048811807794248346}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.019896495194359747, 'UBB': 0.03846297624198248, 'HBP': -0.008372773686419904, '1B': -0.005389106827941861, '2B': 0.029739152017294518, '3B': 0.04845027200121149, 'HR': 0.004611449131284368}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.20974930362116978, 'effects': {'K': 0.047951818849540806, 'UBB': 0.01759692333973901, 'HBP': 0.0012092940727314065, '1B': -0.012896877493008472, '2B': 0.00012017536379404604, '3B': 0.0031609527364456404, 'HR': 0.026894252006891523}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 28.000000 | 0.474130 | 0.400800 | 326.472537 | 0.225400 | 0.376893 | 0.359826 | 195.0 | -0.000000 |
| K | 42.000000 | 0.211193 | 0.286406 | 101.991217 | 0.482255 | 0.361493 | 0.345123 | 208.0 | 0.000000 |
| UBB | 9.000000 | 0.076693 | 0.092990 | 294.912861 | 0.243644 | 0.093415 | 0.089185 | 116.0 | 0.435141 |
| HBP | 1.000000 | 0.008945 | 0.008504 | 307.987804 | 0.235739 | 0.008981 | 0.008574 | 5.0 | -0.013451 |
| 1B | 9.000000 | 0.149198 | 0.129296 | 573.284375 | 0.142155 | 0.124383 | 0.118751 | 75.0 | -1.343875 |
| 2B | 2.000000 | 0.044718 | 0.042940 | 1936.387782 | 0.046766 | 0.041917 | 0.040018 | 24.0 | -0.291933 |
| 3B | 0.000000 | 0.004730 | 0.004783 | 675.121718 | 0.123357 | 0.004193 | 0.004003 | 3.0 | -0.056919 |
| HR | 4.000000 | 0.030393 | 0.034282 | 301.252360 | 0.239746 | 0.036157 | 0.034520 | 52.0 | 0.412795 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18926947529317173, 'UBB': 0.10556570354162786, 'HBP': 0.040948056360785766, '1B': 0.011823567592101134, '2B': 0.07580692682350201, '3B': -0.058662506865346326, 'HR': 0.09111719397513074}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.03, 'effects': {'K': 0.1042520248882923, 'UBB': -0.01639218912344654, 'HBP': 0.014760638188093237, '1B': -0.02299408673971117, '2B': -0.008715723575872848, '3B': -0.011411864976904173, 'HR': 0.01321282335271542}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10071785670845666, 'UBB': -0.007962409288105128, 'HBP': 0.027011934275356708, '1B': -0.023148045066771036, '2B': 0.007464622336067839, '3B': -0.030479994142868373, 'HR': -0.0156786773729876}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.5800738007380072, 'effects': {'K': 0.010111393789104289, 'UBB': 0.09152765896893053, 'HBP': -0.005301167300095238, '1B': -0.000987146574442411, '2B': 0.014704613594092216, '3B': -0.0035971834474117655, 'HR': -0.0021320210831835746}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.003571526646078278, 'UBB': -0.0021960192598723216, 'HBP': -0.00477575100996309, '1B': 0.02807075991585599, '2B': 0.027251525322972443, '3B': 0.0687594015053718, 'HR': 0.08097493691099775}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.012422212089577172, 'UBB': 0.03684611155074105, 'HBP': 0.004356556994165858, '1B': -0.009427319563826274, '2B': 0.008941704649209755, '3B': 0.07385839251161526, 'HR': 0.008538523473559254}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.2891364902506964, 'effects': {'K': 0.013000046972776479, 'UBB': 0.0729379634175544, 'HBP': -7.66929351386611e-05, '1B': -0.006581982792001314, '2B': -0.00886459805159504, '3B': -0.0033475158353239516, 'HR': 0.004134347044027705}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.20974930362116978, 'effects': {'K': 0.05507745410303733, 'UBB': 0.024750623836915932, 'HBP': 0.006047488810257702, '1B': -0.011014898516628157, '2B': 0.013394323758864195, '3B': 0.00114405378907951, 'HR': 0.03978100054398324}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.002342261892591333, 'UBB': -0.02157260276070446, 'HBP': 0.022285104098164556, '1B': 0.0073136694087944515, '2B': -0.04501143902616655, '3B': -0.023450160851118618, 'HR': -0.053839518575655894}}, {'feature': 'scout_listed_1', 'scaled_input': 1.0, 'effects': {'K': 0.049702223895936495, 'UBB': 0.011039274590631972, 'HBP': 0.020083205185883794, '1B': 0.010768486704561936, '2B': -0.011049017062052207, '3B': -0.011537318622052685, 'HR': 0.04360776710520627}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Judge's 2016 AAA season supplied 19 HR in 410 PA, but the 95-PA MLB debut supplied 42 strikeouts. Adaptive reliability still gives that debut 48% pre-normalization K influence; the final 34.5% K and 3.45% HR forecasts compare with 30.7% K and 7.67% HR next year. The new rate is worse than the old one and unchanged expected PA is 287 versus 678. This is the biggest consequential PA-weighted rate deterioration for both arms, not merely a tiny-sample error leaderboard. Poor small-debut anchoring and compressed minor power remain a representation problem; the exact size of the breakout was not guaranteed. Gallo, Bell and Turner succeed among origin-selected peers while Reed fails. Thirty-four coarse active peers do not certify star-breakout translation.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| AJ Reed | 23.0 | 141 | 296.0 | 0.0 | 0.040129 | -0.589009 | 296.788740 | 6 | -15.997855 |
| Joey Gallo | 22.0 | 30 | 433.0 | 0.0 | 0.264428 | -1.067225 | 364.767637 | 532 | 2.301315 |
| Josh Bell | 23.0 | 152 | 484.0 | 0.0 | 0.024288 | 1.006449 | 311.411128 | 620 | 0.939576 |
| Trea Turner | 23.0 | 324 | 371.0 | 0.0 | 0.649107 | 1.787598 | 536.420876 | 447 | 1.017666 |

## Aaron Judge from 2024 to 2025

Player 592450, row 54849, fold 3, age 32.0, stage Current MLB. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |
| 2024 | MLB | 704 | 58 | 171 | 113 |

Weighted transported own MLB PA: 1488.000000. Actual-fold active profile: [{'row_id': 54849, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 195}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 4.553340 | 530.583380 | 5.684172 |
| fixed_reliability | 6.112013 | 530.583380 | 7.062515 |
| learned_reliability | 5.228507 | 530.583380 | 6.281226 |
| Actual | 6.287431 | 679 | 9.231050 |

Unchanged expected PA = participation 0.99179782 × conditional PA 534.971309. For each arm contribution = expected PA × (batting rate/600 + 0.00312416). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 502.179657 | 0.465823 | 0.452179 | 100.000000 | 0.937028 | 0.344709 | 0.344709 | 245.0 | -0.000000 |
| K | 380.793563 | 0.225800 | 0.255542 | 100.000000 | 0.937028 | 0.255887 | 0.255887 | 160.0 | 0.000000 |
| UBB | 228.601113 | 0.079036 | 0.076974 | 100.000000 | 0.937028 | 0.148803 | 0.148803 | 88.0 | 2.430201 |
| HBP | 12.535345 | 0.011072 | 0.013684 | 100.000000 | 0.937028 | 0.008756 | 0.008756 | 7.0 | -0.084124 |
| 1B | 173.486141 | 0.141968 | 0.131254 | 100.000000 | 0.937028 | 0.117514 | 0.117514 | 94.0 | -1.079375 |
| 2B | 64.676893 | 0.042593 | 0.038416 | 100.000000 | 0.937028 | 0.043148 | 0.043148 | 30.0 | 0.034475 |
| 3B | 1.000000 | 0.003820 | 0.005679 | 100.000000 | 0.937028 | 0.000987 | 0.000987 | 2.0 | -0.221866 |
| HR | 124.727288 | 0.029888 | 0.026271 | 100.000000 | 0.937028 | 0.080198 | 0.080198 | 53.0 | 5.032702 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.14664035954243398, 'UBB': 0.056146141437680486, 'HBP': 0.17539050073627802, '1B': -0.031427847927376865, '2B': -0.018580659636938404, '3B': 0.31651699189218474, 'HR': 0.05154219035610447}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.11311343168974716, 'UBB': -0.001202958582088103, 'HBP': 0.05043673496159082, '1B': -0.008577142723502405, '2B': 0.012471161641263748, '3B': 0.0328753301527463, 'HR': 0.035952497165556256}}, {'feature': 'age_centered', 'scaled_input': 1.0, 'effects': {'K': 0.04463157617156734, 'UBB': -0.0076046627862248915, 'HBP': 0.04419285756147274, '1B': -0.029016724817560156, '2B': -0.04420422974486838, '3B': -0.02932948385044155, 'HR': -0.08201095070623171}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.05036462557506239, 'UBB': 0.070466374447624, 'HBP': 0.01496161012114773, '1B': -0.02329216531215426, '2B': 0.012590228021261437, '3B': 0.02483154928056013, 'HR': 0.012715996476023771}}, {'feature': 'position_8', 'scaled_input': 1.0, 'effects': {'K': -0.0006180784366732554, 'UBB': -0.02010671158102589, 'HBP': -0.005180008771074976, '1B': 0.04248460737529795, '2B': -0.012823490321875441, '3B': 0.0643577294486447, 'HR': -0.06542687979345875}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.05212104113534894, 'UBB': -0.017674846440503354, 'HBP': -0.013132891574444422, '1B': 0.024069990810490407, '2B': 0.004756857864935228, '3B': 0.007096228279810538, 'HR': -0.012661542319405857}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': 0.014018763418610128, 'UBB': 0.00931163195200471, 'HBP': -0.04607435113845841, '1B': -0.011800975999381806, '2B': -0.024711428427835382, '3B': 0.01349761877905546, 'HR': -0.0028465219855067126}}, {'feature': 'draft_elapsed', 'scaled_input': 1.0, 'effects': {'K': 0.04125776326289676, 'UBB': -0.024189853443046038, 'HBP': -0.010925427207751887, '1B': 0.00848365348753262, '2B': -0.006265372878754668, '3B': 0.0019407096805074615, 'HR': -0.0033787356282133445}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.018498977129240597, 'UBB': -0.032300807674881624, 'HBP': -0.00738311384520249, '1B': -0.0017086691379611498, '2B': -0.0036613067882817463, '3B': 0.004841011376498385, 'HR': -0.009265351364012717}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.02929521506564576, 'UBB': -0.01414271827137046, 'HBP': 0.0061580397389287824, '1B': 0.0006593334221949945, '2B': -0.0018625571129554704, '3B': -0.0016909897912928986, 'HR': -0.009883731028252074}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 502.179657 | 0.465823 | 0.455403 | 327.307312 | 0.819696 | 0.358747 | 0.357696 | 245.0 | -0.000000 |
| K | 380.793563 | 0.225800 | 0.255815 | 99.640390 | 0.937240 | 0.255904 | 0.255154 | 160.0 | 0.000000 |
| UBB | 228.601113 | 0.079036 | 0.075592 | 269.645522 | 0.846587 | 0.141658 | 0.141243 | 88.0 | 2.166867 |
| HBP | 12.535345 | 0.011072 | 0.011068 | 284.652271 | 0.839420 | 0.008849 | 0.008823 | 7.0 | -0.081679 |
| 1B | 173.486141 | 0.141968 | 0.135392 | 515.553233 | 0.742681 | 0.121428 | 0.121072 | 94.0 | -0.922296 |
| 2B | 64.676893 | 0.042593 | 0.039927 | 1745.125268 | 0.460236 | 0.041556 | 0.041434 | 30.0 | -0.071974 |
| 3B | 1.000000 | 0.003820 | 0.003570 | 653.502984 | 0.694839 | 0.001556 | 0.001552 | 2.0 | -0.177659 |
| HR | 124.727288 | 0.029888 | 0.023235 | 314.876292 | 0.825348 | 0.073240 | 0.073026 | 53.0 | 4.315249 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.14560307446512435, 'UBB': 0.07895843473817596, 'HBP': 0.017417448997485274, '1B': -0.0027479389172836346, '2B': 0.06369019960834223, '3B': -0.01853505393479395, 'HR': 0.03994254096976738}}, {'feature': 'age_centered', 'scaled_input': 1.0, 'effects': {'K': 0.043211262856616355, 'UBB': -0.010059707490878561, 'HBP': 0.019835410136264466, '1B': -0.019339488879949237, '2B': -0.04128361370795051, '3B': -0.11719020642137458, 'HR': -0.11994851846857628}}, {'feature': 'position_8', 'scaled_input': 1.0, 'effects': {'K': -0.002665931143382565, 'UBB': -0.020803755802227507, 'HBP': 0.0043715409723218464, '1B': 0.035993087667354054, '2B': -0.024054008394295157, '3B': 0.11275002946166628, 'HR': -0.0744714835634461}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09779305191390411, 'UBB': -0.013923628289845185, 'HBP': 0.00033708245945866, '1B': -0.01667211544488246, '2B': 0.004267784542828088, '3B': -0.02925845298636744, 'HR': 0.00820386549952089}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.050724982264451095, 'UBB': 0.07327976604087415, 'HBP': 0.031140770396026682, '1B': -0.02810594031888404, '2B': -0.0008533564965085324, '3B': 0.04756412674023458, 'HR': 0.01688719189940998}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.05405867676248502, 'UBB': -0.029871673373547302, 'HBP': -0.010168353339154472, '1B': 0.022424679558283565, '2B': -0.009245593283946134, '3B': 0.004710478226648154, 'HR': -0.019156788045798925}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.8, 'effects': {'K': -0.01868495159436391, 'UBB': 0.007762494061496038, 'HBP': -0.014341403504074344, '1B': -0.001743392954961975, '2B': 0.015259647379681787, '3B': -0.052739955556839094, 'HR': -0.007858810589143473}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': 0.012895944489062302, 'UBB': 0.0055288386689023045, 'HBP': -0.040086968716338676, '1B': -0.01632345473405299, '2B': -0.02402617020523753, '3B': 0.009315648570390259, 'HR': -0.008467758189987767}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.021427272399559754, 'UBB': -0.040060308219066997, 'HBP': -0.00710925523688551, '1B': 0.004425355501099091, '2B': -0.010144752865220673, '3B': 0.0009835910812870975, 'HR': -0.018061695955916116}}, {'feature': 'draft_elapsed', 'scaled_input': 1.0, 'effects': {'K': 0.038532299865214115, 'UBB': -0.03265889143069702, 'HBP': -0.02137684934475423, '1B': 0.024703399242323253, '2B': -0.00018976231334961712, '3B': -0.0001186894292841698, 'HR': -0.0005441088289625243}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Judge had 62, 37 and 58 MLB HR in the three source years. The transported 1,488 weighted PA anchor retains 82.5% pre-normalization HR influence. Adaptive HR probability is 7.30% versus 7.81% actual. The new 5.23 batting wins/600 improves on old 4.55, but fixed-100's 6.11 is closer to actual 6.29 here. Expected PA remains 531 versus 679, so this cannot solve delivered value alone. Castellanos, Chapman, Olson and Ward are exposure/pedigree peers, not equally elite power comparisons; the 195-person coarse profile is not superstar-specific support.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nick Castellanos | 32.0 | 659 | 0.0 | 0.0 | 0.068030 | 0.060128 | 510.684167 | 589 | -0.536256 |
| Matt Chapman | 31.0 | 647 | 0.0 | 0.0 | 0.633808 | 0.511081 | 535.654774 | 535 | 1.227010 |
| Matt Olson | 30.0 | 685 | 0.0 | 0.0 | 2.005782 | 1.897948 | 620.020044 | 724 | 2.702803 |
| Taylor Ward | 30.0 | 663 | 0.0 | 0.0 | 0.901775 | 0.982132 | 559.639782 | 663 | 1.323426 |

## Masyn Winn from 2023 to 2024

Player 691026, row 52733, fold 4, age 21.0, stage Current MLB. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 284 | 3 | 60 | 40 |
| 2021 | Aplus | 154 | 2 | 40 | 6 |
| 2022 | AA | 403 | 11 | 86 | 50 |
| 2022 | Aplus | 147 | 1 | 29 | 13 |
| 2023 | AAA | 498 | 18 | 83 | 44 |
| 2023 | MLB | 137 | 2 | 26 | 10 |

Weighted transported own MLB PA: 137.000000. Actual-fold active profile: [{'row_id': 52733, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'own_mlb_exposure': 'brief', 'active_profile_players': 95}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.796711 | 338.133720 | 0.597896 |
| fixed_reliability | -3.078459 | 338.133720 | -0.687997 |
| learned_reliability | -1.394541 | 338.133720 | 0.260986 |
| Actual | 0.254541 | 637 | 2.259509 |

Unchanged expected PA = participation 0.96360563 × conditional PA 350.904674. For each arm contribution = expected PA × (batting rate/600 + 0.00309608). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 80.000000 | 0.456074 | 0.446446 | 100.000000 | 0.578059 | 0.525927 | 0.525927 | 330.0 | 0.000000 |
| K | 26.000000 | 0.227279 | 0.234294 | 100.000000 | 0.578059 | 0.208563 | 0.208563 | 109.0 | -0.000000 |
| UBB | 10.000000 | 0.083350 | 0.083795 | 100.000000 | 0.578059 | 0.077551 | 0.077551 | 40.0 | -0.201992 |
| HBP | 0.000000 | 0.011472 | 0.012465 | 100.000000 | 0.578059 | 0.005260 | 0.005260 | 1.0 | -0.225636 |
| 1B | 17.000000 | 0.141393 | 0.140542 | 100.000000 | 0.578059 | 0.131031 | 0.131031 | 105.0 | -0.457367 |
| 2B | 2.000000 | 0.044692 | 0.045014 | 100.000000 | 0.578059 | 0.027432 | 0.027432 | 32.0 | -1.072236 |
| 3B | 0.000000 | 0.003867 | 0.005945 | 100.000000 | 0.578059 | 0.002509 | 0.002509 | 5.0 | -0.106416 |
| HR | 2.000000 | 0.031873 | 0.031497 | 100.000000 | 0.578059 | 0.021729 | 0.021729 | 15.0 | -1.014812 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.17229525201771773, 'UBB': 0.0026753139171222825, 'HBP': 0.2265665318170332, '1B': -0.003274624261151743, '2B': 0.00885476507803252, '3B': 0.31388538766567464, 'HR': 0.07306800354935844}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.5274247491638797, 'effects': {'K': -0.15399433395871398, 'UBB': -0.03902873248959169, 'HBP': -0.008943606190643801, '1B': 0.018541910553208165, '2B': -0.009988542939650647, '3B': 0.003067419869772963, 'HR': -0.06812151726365503}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10334981037280626, 'UBB': 0.011612653790025362, 'HBP': 0.056840285540865766, '1B': -0.015099729831478509, '2B': -0.0012229412239883437, '3B': 0.029375211490571894, 'HR': 0.046359591612435844}}, {'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.049342956745184866, 'UBB': 0.027129128263481073, 'HBP': -0.035774589836153704, '1B': 0.037538311690952876, '2B': 0.057500599370223504, '3B': 0.04344168647446201, 'HR': 0.09455933794308956}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.04386858686402975, 'UBB': -0.07573919613879682, 'HBP': -0.016446645186037424, '1B': 0.015890094991710454, '2B': -0.0029522896586869954, '3B': 0.020569487624729304, 'HR': -0.07676196250958281}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.017520727714396264, 'UBB': 0.0343634673424715, 'HBP': -0.07029256409710558, '1B': -0.028900643536929425, '2B': -0.031085162794909055, '3B': 0.011004424815513702, 'HR': 0.00046869579942170726}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.83, 'effects': {'K': 0.06721766144134171, 'UBB': 0.010149595772139721, 'HBP': -0.006298674247461808, '1B': 0.0024829291569438143, '2B': 0.02415078277762698, '3B': 0.0008929626471769252, 'HR': 0.03360777023481485}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.3363636363636363, 'effects': {'K': 0.008907436134056103, 'UBB': 0.06497465391289269, 'HBP': 0.006010897713030369, '1B': -0.015971851818443475, '2B': -0.003515328792493893, '3B': -0.0018962931726901416, 'HR': 0.0061300216413719185}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.0646571034064567, 'UBB': -8.749509650376815e-05, 'HBP': 0.013584158755124576, '1B': -0.004488994912020662, '2B': 0.005563054604240221, '3B': 0.004045203117539563, 'HR': 0.04719316876938221}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.02013559794807021, 'UBB': 0.06066853102883104, 'HBP': 0.019897291875249256, '1B': -0.03442715454083032, '2B': 0.010297719758554902, '3B': 0.014631295944374815, 'HR': 0.013120421715873451}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 80.000000 | 0.456074 | 0.451096 | 289.153989 | 0.321480 | 0.493803 | 0.495819 | 330.0 | 0.000000 |
| K | 26.000000 | 0.227279 | 0.239089 | 94.474605 | 0.591858 | 0.209906 | 0.210762 | 109.0 | -0.000000 |
| UBB | 10.000000 | 0.083350 | 0.083110 | 254.563094 | 0.349880 | 0.079570 | 0.079895 | 40.0 | -0.120334 |
| HBP | 0.000000 | 0.011472 | 0.010934 | 284.731706 | 0.324851 | 0.007382 | 0.007412 | 1.0 | -0.147453 |
| 1B | 17.000000 | 0.141393 | 0.137699 | 537.278616 | 0.203180 | 0.134933 | 0.135484 | 105.0 | -0.260801 |
| 2B | 2.000000 | 0.044692 | 0.043476 | 1637.191527 | 0.077218 | 0.041247 | 0.041415 | 32.0 | -0.203590 |
| 3B | 0.000000 | 0.003867 | 0.005191 | 644.292142 | 0.175351 | 0.004281 | 0.004298 | 5.0 | 0.033748 |
| HR | 2.000000 | 0.031873 | 0.029405 | 304.754731 | 0.310127 | 0.024813 | 0.024915 | 15.0 | -0.696110 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.17565169911431833, 'UBB': 0.027725098382322958, 'HBP': 0.06767073521277521, '1B': -0.0009621057202454161, '2B': 0.07513676879531431, '3B': -0.014203144518797995, 'HR': 0.056305987743562436}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.5274247491638797, 'effects': {'K': -0.1651541024889687, 'UBB': -0.05772079927018092, 'HBP': -0.018773096604162275, '1B': 0.016416626479852047, '2B': -0.03301442349059969, '3B': 0.003455212958858728, 'HR': -0.10213118222231422}}, {'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.051411113096824355, 'UBB': 0.02765203930125874, 'HBP': -0.0030308970862889533, '1B': 0.02196762762266809, '2B': 0.05093709796784342, '3B': 0.15497483006537852, 'HR': 0.13764516443587996}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.049718201263355355, 'UBB': -0.09099187335161617, 'HBP': -0.028130466635688852, '1B': 0.018642676833601834, '2B': -0.017927829735711682, '3B': 0.04125915996530968, 'HR': -0.10528659207631699}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08874054732399411, 'UBB': -0.001677026316787804, 'HBP': 0.004517900943268381, '1B': -0.01942594199044984, '2B': -0.006086729630852387, '3B': -0.030040283087579462, 'HR': 0.018940296888400352}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.83, 'effects': {'K': 0.07427945542157789, 'UBB': 0.00952433579592381, 'HBP': 0.0007445341300209718, '1B': -0.008367705000197819, '2B': -0.005822520193406068, '3B': 0.018479806445561856, 'HR': 0.0387160404172346}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.3363636363636363, 'effects': {'K': 0.008099302559191298, 'UBB': 0.07154746066453876, 'HBP': 0.0063161659225485466, '1B': -0.016385388463186174, '2B': -0.001978268832715547, '3B': -0.0007251010886266374, 'HR': 0.006843894501707349}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.014726741348705703, 'UBB': 0.019375278419562467, 'HBP': -0.06532515558009064, '1B': -0.02242871338682921, '2B': -0.03320029111236591, '3B': 0.0014776379263362306, 'HR': -0.008769633059555686}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.06459588881611156, 'UBB': 0.0021439207517422857, 'HBP': 0.008667396739433487, '1B': -0.012318927999944966, '2B': 0.013696423357085796, '3B': 0.013232749692145506, 'HR': 0.040309707277393546}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.020081190736352943, 'UBB': 0.061862771743214647, 'HBP': 0.033148199258940275, '1B': -0.024146627257720835, '2B': -0.0013784596323974131, '3B': 0.036941715945590266, 'HR': 0.012865025482451612}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Winn's 498-PA AAA season had 83 K and 18 HR. His 137-PA MLB debut had 26 K and two HR. Adaptive weighting improves substantially over fixed-100's poor-debut rate, but remains worse than the working model. Prior K is 23.9%, final 21.1%, actual 17.1%; final singles are 13.6% versus 16.5%. HR is reasonably close at 2.49% versus 2.35%, so power alone is not the explanation. Expected PA remains 338 versus 637. Busch, Soderstrom, Meadows and Edwards also produce MLB value next year; there are 95 coarse active peers, not proof of an exact Winn match.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Michael Busch | 25.0 | 81 | 469.0 | 0.0 | -0.340887 | -1.011723 | 185.327792 | 567 | 1.362614 |
| Tyler Soderstrom | 21.0 | 138 | 335.0 | 0.0 | -0.784320 | -1.748789 | 248.307533 | 213 | 0.586258 |
| Parker Meadows | 23.0 | 145 | 517.0 | 0.0 | -0.863701 | -0.766330 | 230.008832 | 298 | 0.563811 |
| Xavier Edwards | 23.0 | 84 | 433.0 | 0.0 | -0.835588 | 0.038339 | 158.308467 | 303 | 2.456382 |

## Spencer Steer from 2022 to 2023

Player 668715, row 47421, fold 4, age 24.0, stage Current MLB. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AA | 280 | 14 | 73 | 19 |
| 2021 | Aplus | 208 | 10 | 32 | 35 |
| 2022 | AA | 156 | 8 | 23 | 14 |
| 2022 | AAA | 336 | 15 | 66 | 36 |
| 2022 | MLB | 108 | 2 | 26 | 11 |

Weighted transported own MLB PA: 108.000000. Actual-fold active profile: [{'row_id': 47421, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'brief', 'active_profile_players': 248}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.236630 | 243.552996 | 0.666505 |
| fixed_reliability | -0.660436 | 243.552996 | 0.494473 |
| learned_reliability | -0.767699 | 243.552996 | 0.450933 |
| Actual | 1.909209 | 665 | 4.174931 |

Unchanged expected PA = participation 0.90757061 × conditional PA 268.357075. For each arm contribution = expected PA × (batting rate/600 + 0.00313097). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 49.000000 | 0.467680 | 0.456616 | 100.000000 | 0.519231 | 0.455104 | 0.455104 | 289.0 | -0.000000 |
| K | 26.000000 | 0.224178 | 0.238280 | 100.000000 | 0.519231 | 0.239558 | 0.239558 | 139.0 | 0.000000 |
| UBB | 11.000000 | 0.078977 | 0.085469 | 100.000000 | 0.519231 | 0.093975 | 0.093975 | 68.0 | 0.522427 |
| HBP | 2.000000 | 0.011239 | 0.014349 | 100.000000 | 0.519231 | 0.016514 | 0.016514 | 11.0 | 0.191608 |
| 1B | 13.000000 | 0.142135 | 0.130995 | 100.000000 | 0.519231 | 0.125478 | 0.125478 | 95.0 | -0.735195 |
| 2B | 5.000000 | 0.043614 | 0.042028 | 100.000000 | 0.519231 | 0.044244 | 0.044244 | 37.0 | 0.039160 |
| 3B | 0.000000 | 0.003532 | 0.004769 | 100.000000 | 0.519231 | 0.002293 | 0.002293 | 3.0 | -0.097057 |
| HR | 2.000000 | 0.028646 | 0.027494 | 100.000000 | 0.519231 | 0.022834 | 0.022834 | 23.0 | -0.581381 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.15553033369330815, 'UBB': -0.031410734348264996, 'HBP': 0.21256382409439448, '1B': -0.017977454651544506, '2B': 0.02108969392779996, '3B': 0.3271162825650471, 'HR': 0.07295166390845229}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.1030731144609031, 'UBB': 0.019062238295775868, 'HBP': 0.06276534055231237, '1B': -0.009435017549096474, '2B': -0.001325191880542082, '3B': 0.026439535682935805, 'HR': 0.03249048299618268}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.25871559633027535, 'effects': {'K': -0.07643877879387548, 'UBB': -0.019870730721466657, 'HBP': -0.004713677299250564, '1B': 0.00936448108038014, '2B': -0.006077539264090676, '3B': 0.002197389626305213, 'HR': -0.03338394645932086}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.5513513513513514, 'effects': {'K': 0.008662589596670035, 'UBB': 0.06719766799137072, 'HBP': -0.00356756736071669, '1B': -0.008416350492276552, '2B': -0.001530973207567438, '3B': -0.0035320346254159693, 'HR': -0.00301586696518915}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.6333333333333333, 'effects': {'K': 0.06665960694589006, 'UBB': -0.012182474482528948, 'HBP': -0.014446491402445453, '1B': -0.014962268435026347, '2B': 0.0005193554299600485, '3B': -0.0014452055795129385, 'HR': -0.011966793070053508}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.47567567567567554, 'effects': {'K': -0.06526705388757835, 'UBB': -0.031101608943095573, 'HBP': -0.011239511440842847, '1B': 0.012412990963363327, '2B': -0.009975418785301114, '3B': -0.0006994226409359957, 'HR': -0.0478948180674571}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.018796217161014483, 'UBB': 0.05651658949551846, 'HBP': 0.028102612212400888, '1B': -0.033317464069835344, '2B': 0.010007134017868725, '3B': 0.01448605171422992, 'HR': 0.01282354147969103}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.56, 'effects': {'K': 0.04819270954668575, 'UBB': 0.005004365224688123, 'HBP': 0.0013044876698056552, '1B': 0.0026073166798863453, '2B': 0.018928702358386756, '3B': -0.0009206369362950343, 'HR': 0.025469253573493198}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.015386765039645924, 'UBB': 0.014205721281696664, 'HBP': 0.04399163013143757, '1B': -0.021276489993657426, '2B': 0.0032180215140318385, '3B': -0.01140937237904534, 'HR': 0.04800060304301531}}, {'feature': 'scout_listed_1', 'scaled_input': -1.0, 'effects': {'K': 0.006279615356700538, 'UBB': -0.0006274983151052782, 'HBP': 0.0007384147854574607, '1B': 0.008445213609913215, '2B': -0.017367968445155202, '3B': -0.007534371823833853, 'HR': -0.04777646369896518}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 49.000000 | 0.467680 | 0.458454 | 317.270056 | 0.253956 | 0.457247 | 0.457496 | 289.0 | -0.000000 |
| K | 26.000000 | 0.224178 | 0.244699 | 94.897828 | 0.532288 | 0.242592 | 0.242724 | 139.0 | 0.000000 |
| UBB | 11.000000 | 0.078977 | 0.086845 | 269.100839 | 0.286396 | 0.091143 | 0.091192 | 68.0 | 0.425481 |
| HBP | 2.000000 | 0.011239 | 0.012391 | 292.420623 | 0.269716 | 0.014044 | 0.014051 | 11.0 | 0.102158 |
| 1B | 13.000000 | 0.142135 | 0.125030 | 532.701072 | 0.168565 | 0.124244 | 0.124312 | 95.0 | -0.786675 |
| 2B | 5.000000 | 0.043614 | 0.042275 | 1537.056061 | 0.065651 | 0.042539 | 0.042563 | 37.0 | -0.065316 |
| 3B | 0.000000 | 0.003532 | 0.003661 | 661.203941 | 0.140405 | 0.003147 | 0.003149 | 3.0 | -0.029992 |
| HR | 2.000000 | 0.028646 | 0.026645 | 301.218915 | 0.263917 | 0.024500 | 0.024513 | 23.0 | -0.413355 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1425309773240566, 'UBB': -0.0203937301779015, 'HBP': 0.04390005193766169, '1B': 0.0009968043388312764, '2B': 0.08830948371941795, '3B': -0.01565958268183963, 'HR': 0.051490991704191885}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08686778846586, 'UBB': 0.004877794662102235, 'HBP': 0.009299362843313185, '1B': -0.014378362208949193, '2B': -0.006018141647386673, '3B': -0.03459554665059864, 'HR': 0.004897582538221449}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.25871559633027535, 'effects': {'K': -0.08232131880772696, 'UBB': -0.029132269677596884, 'HBP': -0.01013764135035137, '1B': 0.007007218250521613, '2B': -0.016931223340404616, '3B': 0.002568355920496441, 'HR': -0.04962062827809944}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': -0.02195542834280693, 'UBB': 0.018958478584216756, 'HBP': -0.0057438011193854405, '1B': 0.011987192527222542, '2B': 0.027119127356172553, '3B': 0.07688561174378306, 'HR': 0.07153423404934008}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.5513513513513514, 'effects': {'K': 0.00973987759548422, 'UBB': 0.07492722089376645, 'HBP': -0.0021014119289643604, '1B': -0.00936418846138545, '2B': 0.005398271976505829, '3B': -0.0004568122831789707, 'HR': -0.00129992757368159}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.6333333333333333, 'effects': {'K': 0.06708098044798039, 'UBB': -0.019714527174272176, 'HBP': -0.0006342266302299023, '1B': -0.011918999625208862, '2B': -0.005449079227454015, '3B': 0.024841753038659584, 'HR': -0.0015966033855131317}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.47567567567567554, 'effects': {'K': -0.06536804922507175, 'UBB': -0.028694209972803336, 'HBP': -0.010184778347626199, '1B': 0.010589579890935012, '2B': -0.007995150846191528, '3B': 0.008596613791996612, 'HR': -0.05120687649258246}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.011282205250763715, 'UBB': 0.011896418281856731, 'HBP': 0.03847090273474203, '1B': -0.013544612004788457, '2B': 0.01567613159463811, '3B': -0.032206282161889394, 'HR': 0.06057767670927622}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.01774891904982893, 'UBB': 0.05684214403448887, 'HBP': 0.042951629628298495, '1B': -0.02173089237537916, '2B': -0.0010404345092069377, '3B': 0.03771753616403582, 'HR': 0.015376938558110589}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.20917431192660554, 'effects': {'K': 0.007818435930438114, 'UBB': 0.05539426156801333, 'HBP': -0.0005007812681194902, '1B': -0.011615250104216227, '2B': -0.0009600827898817302, '3B': -0.0025253248286109774, 'HR': 0.00959225140997201}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Steer supplied 23 HR across AA/AAA in 2022 before a 108-PA MLB debut with two HR. Both new rates miss the next-year improvement, and adaptive reliability is slightly worse than fixed-100 and the old rate. Final HR is 2.45% versus 3.46%, K 24.3% versus 20.9%, walks 9.12% versus 10.2%. Expected PA is 244 versus 665. These are missing talent translation and opportunity, not just a denominator issue. Brennan, Freeman, Stowers and Kevin Smith are origin-selected peers with poor future rates; a brief debut does not imply every player deserves a breakout prior.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Will Brennan | 24.0 | 45 | 433.0 | 157.0 | -0.482343 | 0.250148 | 296.872517 | 455 | -1.638942 |
| Tyler Freeman | 23.0 | 86 | 343.0 | 0.0 | -0.860867 | 0.234515 | 203.431394 | 168 | -1.521606 |
| Kyle Stowers | 24.0 | 98 | 407.0 | 0.0 | -0.142760 | -1.167471 | 157.897589 | 33 | -9.986743 |
| Kevin Smith | 25.0 | 151 | 370.0 | 0.0 | -1.292683 | -2.562524 | 141.489609 | 146 | -4.421926 |

## Joey Votto from 2016 to 2017

Player 458015, row 23027, fold 0, age 32.0, stage Current MLB. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AAA | 6 | 0 | 2 | 0 |
| 2014 | MLB | 272 | 6 | 49 | 45 |
| 2015 | MLB | 695 | 29 | 135 | 128 |
| 2016 | MLB | 677 | 29 | 120 | 93 |

Weighted transported own MLB PA: 1396.200000. Actual-fold active profile: [{'row_id': 23027, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 112}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 2.941897 | 547.545794 | 4.375577 |
| fixed_reliability | 4.359299 | 547.545794 | 5.669064 |
| learned_reliability | 3.644357 | 547.545794 | 5.016626 |
| Actual | 4.964084 | 707 | 8.024202 |

Unchanged expected PA = participation 0.99392423 × conditional PA 550.892890. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 543.356477 | 0.474130 | 0.477698 | 100.000000 | 0.933164 | 0.395085 | 0.395085 | 323.0 | -0.000000 |
| K | 260.621973 | 0.211193 | 0.223240 | 100.000000 | 0.933164 | 0.189110 | 0.189110 | 83.0 | -0.000000 |
| UBB | 230.424749 | 0.076693 | 0.086981 | 100.000000 | 0.933164 | 0.159820 | 0.159820 | 114.0 | 2.895581 |
| HBP | 10.823881 | 0.008945 | 0.011714 | 100.000000 | 0.933164 | 0.008017 | 0.008017 | 8.0 | -0.033688 |
| 1B | 218.138851 | 0.149198 | 0.123280 | 100.000000 | 0.933164 | 0.154035 | 0.154035 | 108.0 | 0.213477 |
| 2B | 69.575128 | 0.044718 | 0.040060 | 100.000000 | 0.933164 | 0.049179 | 0.049179 | 34.0 | 0.277122 |
| 3B | 3.460762 | 0.004730 | 0.006305 | 100.000000 | 0.933164 | 0.002734 | 0.002734 | 1.0 | -0.156262 |
| HR | 59.798179 | 0.030393 | 0.030723 | 100.000000 | 0.933164 | 0.042020 | 0.042020 | 36.0 | 1.163068 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18086500533628688, 'UBB': 0.020001450135848874, 'HBP': 0.21878787749669762, '1B': -0.05035400250940902, '2B': -0.04633462454262677, '3B': 0.2955609724292239, 'HR': 0.12564861344779013}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09801435265420425, 'UBB': 0.03020662459303759, 'HBP': 0.08108071448484996, '1B': -0.029567969990955477, '2B': 0.021899799811183052, '3B': 0.017001712053170005, 'HR': 0.007759025289403746}}, {'feature': 'age_centered', 'scaled_input': 1.0, 'effects': {'K': -0.01941486783663379, 'UBB': 0.012122177208011316, 'HBP': 0.02742947339528992, '1B': -0.061255409123996206, '2B': -0.06289274643416075, '3B': -0.03849415907220135, 'HR': -0.07898969696633025}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03738124232837742, 'UBB': 0.048530204421231356, 'HBP': -0.00021555861136362826, '1B': -0.019533141424423132, '2B': -0.009626815426547976, '3B': -0.03157434500661088, 'HR': 0.0708407373911696}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': -0.004748022822692502, 'UBB': 0.0013832904869267451, 'HBP': -0.05696212579527247, '1B': -0.04051082909893455, '2B': -0.03535312532684311, '3B': 0.012130823138741588, 'HR': -0.03671668847519849}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.9, 'effects': {'K': -0.05652072248852759, 'UBB': 0.013973176451496743, 'HBP': 0.012743756205395723, '1B': -0.01790799237886429, '2B': -0.012759943263388467, '3B': -0.011857768467237025, 'HR': -0.015712026962234265}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.015916388450934845, 'UBB': -0.021494789036311277, 'HBP': 0.02548683450052227, '1B': 0.010579424674460717, '2B': -0.010424737325486658, '3B': -0.014736755522057002, 'HR': -0.035799902040657215}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.027052324874017267, 'UBB': 0.027513902329469944, 'HBP': -0.01473975753954193, '1B': 0.009045405813874925, '2B': 0.027710395828535322, '3B': 0.02297771251221448, 'HR': -0.009879870772343344}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.014860674045752118, 'UBB': -0.02192912955657227, 'HBP': -0.01740104101015618, '1B': -0.010836410191462578, '2B': -0.01150993007121436, '3B': 0.012742232776933269, 'HR': -0.0025792555336347934}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.010791170154708126, 'UBB': 0.009226680349538958, 'HBP': -0.002446469393658777, '1B': 0.007915464845177671, '2B': 0.013078624411024368, '3B': 0.00434939043362115, 'HR': -0.011558858828399542}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 543.356477 | 0.474130 | 0.472241 | 350.099316 | 0.799519 | 0.405823 | 0.408729 | 323.0 | -0.000000 |
| K | 260.621973 | 0.211193 | 0.227665 | 95.407812 | 0.936037 | 0.189288 | 0.190643 | 83.0 | -0.000000 |
| UBB | 230.424749 | 0.076693 | 0.082975 | 307.427037 | 0.819546 | 0.150229 | 0.151305 | 114.0 | 2.598957 |
| HBP | 10.823881 | 0.008945 | 0.008599 | 328.746663 | 0.809416 | 0.007914 | 0.007970 | 8.0 | -0.035382 |
| 1B | 218.138851 | 0.149198 | 0.134000 | 508.290959 | 0.733109 | 0.150303 | 0.151379 | 108.0 | 0.096261 |
| 2B | 69.575128 | 0.044718 | 0.043831 | 2041.573211 | 0.406135 | 0.046268 | 0.046600 | 34.0 | 0.116913 |
| 3B | 3.460762 | 0.004730 | 0.003325 | 704.485935 | 0.664640 | 0.002763 | 0.002782 | 1.0 | -0.152503 |
| HR | 59.798179 | 0.030393 | 0.027363 | 272.658912 | 0.836620 | 0.040302 | 0.040591 | 36.0 | 1.020112 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.17504194527723554, 'UBB': 0.027327022674042075, 'HBP': 0.04045867255044909, '1B': 0.02524751316634716, '2B': 0.050593736783150496, '3B': -0.059309712036519475, 'HR': 0.10276242988940501}}, {'feature': 'age_centered', 'scaled_input': 1.0, 'effects': {'K': -0.016139309035326416, 'UBB': 0.0035205670879431806, 'HBP': -0.008861051470084374, '1B': -0.042283486270610245, '2B': -0.06602935649337784, '3B': -0.13074046341449105, 'HR': -0.11680246849113336}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.04140657423662597, 'UBB': 0.06833928720282925, 'HBP': -0.002206196273562342, '1B': -0.016259151945325116, '2B': 0.014051838776811917, '3B': -0.0710563591130133, 'HR': 0.09476886121061166}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08164551463874688, 'UBB': 0.008232350570984455, 'HBP': 0.031122024191550093, '1B': -0.02260942498681039, '2B': 0.009299549892359253, '3B': -0.04694343603948884, 'HR': -0.014414889326407216}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.9, 'effects': {'K': -0.05535121571223973, 'UBB': 0.005237580834753157, 'HBP': -0.019931446524658492, '1B': 0.010107264311127837, '2B': 0.02732601329070623, '3B': -0.06662482682955109, 'HR': -0.023638450296456302}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': -0.003947869179531687, 'UBB': -0.003268608203617215, 'HBP': -0.06008182618013612, '1B': -0.03424085214972908, '2B': -0.03088080611304193, '3B': 0.0036444104294553335, 'HR': -0.045197403771175856}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.016408952603332794, 'UBB': -0.018145886707292853, 'HBP': 0.030127857433249094, '1B': 0.009864638460714748, '2B': -0.042104344215447974, '3B': -0.023332655191218132, 'HR': -0.04627642549333893}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.01717568308673412, 'UBB': -0.027170289036190492, 'HBP': -0.02247622438959802, '1B': -0.006972827477569161, '2B': -0.0007573886984712169, '3B': 0.010573096454450755, 'HR': -0.006633985958666085}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.02485310429361054, 'UBB': 0.00941350026980134, 'HBP': -0.015457033477336207, '1B': 0.00418160226107673, '2B': 0.020590323740776826, '3B': 0.017475456100781498, 'HR': -0.01950864846147307}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.012843645569189717, 'UBB': 0.010951327779925602, 'HBP': 0.001377241197592911, '1B': -0.015501946275000265, '2B': 0.0004059606263083885, '3B': 0.0055833619887456325, 'HR': -0.01414913554689921}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Votto already had 29 HR in each of the last two years and 128 then 93 unintentional walks. The 1,396 weighted MLB PA anchor retains his elite on-base ability: final walks 15.1% versus 16.1%. K remains 19.1% versus 11.7%, and HR 4.06% versus 5.09%. Adaptive rate 3.64 improves on old 2.94 but fixed-100 4.36 is closer to actual 4.96. Workload remains 548 versus 707. Established ability is better retained, yet neither shrinkage design resolves the whole forecast; the 112-person profile and ordinary Markakis/Prado/Pedroia/Span peers are not exact skill support.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Nick Markakis | 32.0 | 684 | 0.0 | 0.0 | 0.589012 | 0.182915 | 514.543431 | 670 | -0.049960 |
| Martín Prado | 32.0 | 658 | 0.0 | 0.0 | 0.417100 | 0.342662 | 528.464817 | 147 | -2.205563 |
| Dustin Pedroia | 32.0 | 698 | 0.0 | 0.0 | 0.960629 | 1.127556 | 543.719800 | 463 | 0.471869 |
| Denard Span | 32.0 | 637 | 0.0 | 0.0 | 0.199438 | 0.241159 | 539.954111 | 542 | 0.349071 |

## Cody Bellinger from 2016 to 2017

Player 641355, row 24967, fold 3, age 20.0, stage Upper minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | RK128 | 233 | 3 | 40 | 15 |
| 2015 | Aplus | 544 | 30 | 150 | 51 |
| 2016 | AA | 465 | 23 | 94 | 57 |
| 2016 | AAA | 12 | 3 | 0 | 1 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 24967, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'none', 'active_profile_players': 208}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.084712 | 14.219100 | 0.045917 |
| fixed_reliability | -0.560653 | 14.219100 | 0.030623 |
| learned_reliability | -0.458398 | 14.219100 | 0.033047 |
| Actual | 2.700471 | 548 | 4.152174 |

Unchanged expected PA = participation 0.10101791 × conditional PA 140.758217. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.474130 | 0.433578 | 100.000000 | 0.000000 | 0.433578 | 0.433578 | 222.0 | -0.000000 |
| K | 0.000000 | 0.211193 | 0.264435 | 100.000000 | 0.000000 | 0.264435 | 0.264435 | 146.0 | 0.000000 |
| UBB | 0.000000 | 0.076693 | 0.087001 | 100.000000 | 0.000000 | 0.087001 | 0.087001 | 51.0 | 0.359054 |
| HBP | 0.000000 | 0.008945 | 0.008288 | 100.000000 | 0.000000 | 0.008288 | 0.008288 | 1.0 | -0.023844 |
| 1B | 0.000000 | 0.149198 | 0.127882 | 100.000000 | 0.000000 | 0.127882 | 0.127882 | 59.0 | -0.940842 |
| 2B | 0.000000 | 0.044718 | 0.039667 | 100.000000 | 0.000000 | 0.039667 | 0.039667 | 26.0 | -0.313746 |
| 3B | 0.000000 | 0.004730 | 0.006757 | 100.000000 | 0.000000 | 0.006757 | 0.006757 | 4.0 | 0.158754 |
| HR | 0.000000 | 0.030393 | 0.032392 | 100.000000 | 0.000000 | 0.032392 | 0.032392 | 39.0 | 0.199972 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.19986329753836185, 'UBB': 0.0923711191745983, 'HBP': 0.2259986788740148, '1B': -0.07117018910907053, '2B': -0.021063743489630197, '3B': 0.30912634690803736, 'HR': 0.10448163639603059}}, {'feature': 'age_centered', 'scaled_input': -1.4, 'effects': {'K': 0.014377082493864622, 'UBB': -0.02149302722993044, 'HBP': -0.06121039531132065, '1B': 0.09044077550547862, '2B': 0.046630988461571043, '3B': 0.04049118917936582, 'HR': 0.12774922741056233}}, {'feature': 'age_squared', 'scaled_input': 1.9599999999999997, 'effects': {'K': 0.005213245479188695, 'UBB': 0.046077338850241414, 'HBP': -0.11350310118106191, '1B': -0.05614681887566052, '2B': -0.06365676775244528, '3B': 0.045908889484565445, 'HR': -0.03140106124026825}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.016046417971196436, 'UBB': 0.06705319742733254, 'HBP': 0.003356385357439746, '1B': -0.029488310848784564, '2B': 0.007898945596805266, '3B': -0.024661981970759358, 'HR': 0.0730880049242849}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.775, 'effects': {'K': 0.06603022837304938, 'UBB': -0.04172403189924077, 'HBP': -0.03685783389526147, '1B': -0.001339414353399325, '2B': -0.020382275230147486, '3B': 0.016471392942763546, 'HR': -0.043457011449951656}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.35044247787610616, 'effects': {'K': 0.012919864154201191, 'UBB': 0.0627906242818698, 'HBP': 0.0006124457447295529, '1B': -0.01832106820877377, '2B': -0.00482140604223491, '3B': -0.002506905283419833, 'HR': -0.0011482207261907667}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.22920353982300884, 'effects': {'K': -0.05738396355666128, 'UBB': -0.018055597914208667, 'HBP': -0.012591506326984104, '1B': -0.0008552114562661268, '2B': -0.008684305444698647, '3B': 0.0009731125268924207, 'HR': -0.03140420543910708}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.2464285714285716, 'effects': {'K': -0.05633724647704311, 'UBB': -0.02067413147641224, 'HBP': -0.001420765674237797, '1B': 0.015152179490576421, '2B': -0.00014119066289804206, '3B': -0.003713714676270872, 'HR': -0.031597302051921405}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.7253333333333334, 'effects': {'K': 0.052677485880826026, 'UBB': -0.02221749510032947, 'HBP': -0.020347155021371254, '1B': 0.026583387704690254, '2B': 0.008839780011382033, '3B': 0.000657809744731442, 'HR': -0.012798553821664888}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.019896495194359747, 'UBB': 0.03846297624198248, 'HBP': -0.008372773686419904, '1B': -0.005389106827941861, '2B': 0.029739152017294518, '3B': 0.04845027200121149, 'HR': 0.004611449131284368}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.474130 | 0.434366 | 326.472537 | 0.000000 | 0.434366 | 0.434366 | 222.0 | -0.000000 |
| K | 0.000000 | 0.211193 | 0.262315 | 101.991217 | 0.000000 | 0.262315 | 0.262315 | 146.0 | 0.000000 |
| UBB | 0.000000 | 0.076693 | 0.086388 | 294.912861 | 0.000000 | 0.086388 | 0.086388 | 51.0 | 0.337702 |
| HBP | 0.000000 | 0.008945 | 0.007639 | 307.987804 | 0.000000 | 0.007639 | 0.007639 | 1.0 | -0.047426 |
| 1B | 0.000000 | 0.149198 | 0.129548 | 573.284375 | 0.000000 | 0.129548 | 0.129548 | 59.0 | -0.867321 |
| 2B | 0.000000 | 0.044718 | 0.040888 | 1936.387782 | 0.000000 | 0.040888 | 0.040888 | 26.0 | -0.237889 |
| 3B | 0.000000 | 0.004730 | 0.005506 | 675.121718 | 0.000000 | 0.005506 | 0.005506 | 4.0 | 0.060787 |
| HR | 0.000000 | 0.030393 | 0.033350 | 301.252360 | 0.000000 | 0.033350 | 0.033350 | 39.0 | 0.295749 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18926947529317173, 'UBB': 0.10556570354162786, 'HBP': 0.040948056360785766, '1B': 0.011823567592101134, '2B': 0.07580692682350201, '3B': -0.058662506865346326, 'HR': 0.09111719397513074}}, {'feature': 'age_centered', 'scaled_input': -1.4, 'effects': {'K': 0.008333562174182648, 'UBB': -0.005124044939702084, 'HBP': -0.011143419023247211, '1B': 0.06549843980366397, '2B': 0.06358689242026903, '3B': 0.1604386035125342, 'HR': 0.18894151945899473}}, {'feature': 'age_squared', 'scaled_input': 1.9599999999999997, 'effects': {'K': 0.008810379483774649, 'UBB': 0.026972076262711163, 'HBP': -0.10727460598453782, '1B': -0.04889081277600533, '2B': -0.06974366538810682, '3B': 0.039094356629065054, 'HR': -0.041518583040066996}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.01527834046875891, 'UBB': 0.07777755584807441, 'HBP': 0.0032260613826758477, '1B': -0.0021573291522959184, '2B': 0.03562059576073909, '3B': -0.05779425820575408, 'HR': 0.0934699042251783}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.012422212089577172, 'UBB': 0.03684611155074105, 'HBP': 0.004356556994165858, '1B': -0.009427319563826274, '2B': 0.008941704649209755, '3B': 0.07385839251161526, 'HR': 0.008538523473559254}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.35044247787610616, 'effects': {'K': 0.013146651427960447, 'UBB': 0.07365032234092923, 'HBP': -0.00022481218280604484, '1B': -0.018386781335695792, '2B': 0.0022742126189900878, '3B': -0.0033950253020650664, 'HR': 0.002410576724046793}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.775, 'effects': {'K': 0.06766096495147879, 'UBB': -0.04671476237421552, 'HBP': -0.01911311002559659, '1B': -0.010371458835464573, '2B': -0.03175789050847511, '3B': 0.05276413902002667, 'HR': -0.03423882806219727}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.2464285714285716, 'effects': {'K': -0.06470895539680988, 'UBB': -0.029078813463491053, 'HBP': -0.0071050249155233235, '1B': 0.012941095198036259, '2B': -0.015736615150390126, '3B': -0.001344116695564816, 'HR': -0.046737581316401544}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.22920353982300884, 'effects': {'K': -0.05793744008415807, 'UBB': -0.020702093346847517, 'HBP': -0.01239663765901014, '1B': -0.0026613029331856537, '2B': -0.01230171823848391, '3B': 0.00703077860242139, 'HR': -0.03532223794241494}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.7253333333333334, 'effects': {'K': 0.057326730505516725, 'UBB': -0.023454706354755418, 'HBP': -0.010907793933991489, '1B': 0.01512041357292412, '2B': 0.00280095150031312, '3B': 0.018850541055455618, 'HR': -0.007519881966110117}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Bellinger's 2015 High-A season had 30 HR in 544 PA; 2016 AA had 23 in 465 and the tiny AAA stint three in 12. With no own MLB PA the entire forecast is the learned conditional prior, not an observed MLB anchor. Final K 26.2% is close to actual 26.6%, but HR 3.33% misses actual 7.12%. Expected PA is only 14 versus 548. Changing learned alpha also changes the jointly learned prior even when own influence is zero. The four coarse peers all have zero MLB PA next year; they support non-arrival risk, not suppression of this specific power profile.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Isiah Kiner-Falefa | 21.0 | 0 | 0.0 | 457.0 | -0.135062 | -0.057334 | 18.424211 | 0 | Unobserved |
| Jamie Westbrook | 21.0 | 0 | 0.0 | 473.0 | -0.416239 | -0.574513 | 4.863483 | 0 | Unobserved |
| Kean Wong | 21.0 | 0 | 0.0 | 492.0 | -0.262675 | -0.517138 | 17.667458 | 0 | Unobserved |
| Jacob Nottingham | 21.0 | 0 | 0.0 | 456.0 | -0.201851 | -1.362864 | 15.935382 | 0 | Unobserved |

## Pete Alonso from 2018 to 2019

Player 624413, row 33263, fold 1, age 23.0, stage Upper minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | Aminus | 123 | 5 | 22 | 11 |
| 2017 | AA | 47 | 2 | 7 | 2 |
| 2017 | Aplus | 346 | 16 | 64 | 24 |
| 2018 | AA | 273 | 15 | 50 | 40 |
| 2018 | AAA | 301 | 21 | 78 | 33 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 33263, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'none', 'active_profile_players': 288}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.259881 | 131.538003 | 0.461949 |
| fixed_reliability | -0.279947 | 131.538003 | 0.343602 |
| learned_reliability | -0.138315 | 131.538003 | 0.374652 |
| Actual | 3.282757 | 693 | 5.908536 |

Unchanged expected PA = participation 0.72999787 × conditional PA 180.189571. For each arm contribution = expected PA × (batting rate/600 + 0.00307877). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465785 | 0.425091 | 100.000000 | 0.000000 | 0.425091 | 0.425091 | 268.0 | -0.000000 |
| K | 0.000000 | 0.222573 | 0.272256 | 100.000000 | 0.000000 | 0.272256 | 0.272256 | 183.0 | 0.000000 |
| UBB | 0.000000 | 0.079708 | 0.087442 | 100.000000 | 0.000000 | 0.087442 | 0.087442 | 66.0 | 0.269418 |
| HBP | 0.000000 | 0.010381 | 0.010869 | 100.000000 | 0.000000 | 0.010869 | 0.010869 | 21.0 | 0.017699 |
| 1B | 0.000000 | 0.142174 | 0.121720 | 100.000000 | 0.000000 | 0.121720 | 0.121720 | 70.0 | -0.902783 |
| 2B | 0.000000 | 0.044637 | 0.043460 | 100.000000 | 0.000000 | 0.043460 | 0.043460 | 30.0 | -0.073093 |
| 3B | 0.000000 | 0.004575 | 0.006114 | 100.000000 | 0.000000 | 0.006114 | 0.006114 | 2.0 | 0.120523 |
| HR | 0.000000 | 0.030167 | 0.033048 | 100.000000 | 0.000000 | 0.033048 | 0.033048 | 53.0 | 0.288288 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.07338157988066955, 'UBB': -0.017229684729952933, 'HBP': 0.22413867277502003, '1B': 0.021173853457996664, '2B': -0.005053078146421251, '3B': 0.34127030609413145, 'HR': 0.06687211905597058}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.38572820263029745, 'effects': {'K': -0.10135717295222353, 'UBB': -0.030527942042164958, 'HBP': -0.017146535754522543, '1B': -0.002452730670923696, '2B': -0.01812838928244789, '3B': -0.006657213010600307, 'HR': -0.06419318539181437}}, {'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': 0.004279808848734601, 'UBB': 0.006135237583921405, 'HBP': -0.030161577623086713, '1B': 0.020707088057876716, '2B': 0.04394226873462334, '3B': 0.028116669152425357, 'HR': 0.08027261627751205}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03440271499996671, 'UBB': 0.04713882737294323, 'HBP': -0.009594803183524986, '1B': -0.029995500400662373, '2B': 0.008389732369285679, '3B': -0.01271821176273001, 'HR': 0.07531069769234983}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.027944849812178253, 'UBB': 0.06908175488883637, 'HBP': 0.022397214026563677, '1B': -0.031092329867254298, '2B': 0.02677883404381161, '3B': 0.0357281258027691, 'HR': 0.02303610264129051}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.4079883097905504, 'effects': {'K': 0.0019458913931812484, 'UBB': 0.06495306273328648, 'HBP': 0.0047939800272892436, '1B': -0.012789802828280461, '2B': -0.002328665147407041, '3B': -0.0019796990087643644, 'HR': 0.0026723024188340266}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.5176666666666667, 'effects': {'K': 0.053057428605001275, 'UBB': -0.023635468554146784, 'HBP': -0.021262250230133194, '1B': -0.003052834415027, '2B': -0.008139163402515045, '3B': 0.0013710320028592555, 'HR': -0.024467164362486134}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.4613333333333334, 'effects': {'K': 0.0481845510241041, 'UBB': -0.025448510280549577, 'HBP': -0.008919730259216973, '1B': 0.006133575051866524, '2B': 0.00413169759484455, '3B': 0.0004517702041611616, 'HR': 0.003727514199067434}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.3307855626326964, 'effects': {'K': -0.04808169169549069, 'UBB': -0.022537356860627352, 'HBP': -0.00920711703381398, '1B': 0.008040632838357114, '2B': -0.0019334896424093883, '3B': 0.00023699663840819957, 'HR': -0.03485904236902734}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.21870324189526197, 'effects': {'K': 0.04605089109581765, 'UBB': 0.018672914743443434, 'HBP': 0.0007713642075374672, '1B': -0.009113922570027926, '2B': 0.0013115537119808254, '3B': 0.0029893981791137367, 'HR': 0.024851435800958326}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465785 | 0.421980 | 349.693099 | 0.000000 | 0.421980 | 0.421980 | 268.0 | -0.000000 |
| K | 0.000000 | 0.222573 | 0.273169 | 90.268343 | 0.000000 | 0.273169 | 0.273169 | 183.0 | 0.000000 |
| UBB | 0.000000 | 0.079708 | 0.091616 | 292.977663 | 0.000000 | 0.091616 | 0.091616 | 66.0 | 0.414792 |
| HBP | 0.000000 | 0.010381 | 0.009940 | 317.962888 | 0.000000 | 0.009940 | 0.009940 | 21.0 | -0.016048 |
| 1B | 0.000000 | 0.142174 | 0.119281 | 482.128797 | 0.000000 | 0.119281 | 0.119281 | 70.0 | -1.010440 |
| 2B | 0.000000 | 0.044637 | 0.044270 | 1849.519769 | 0.000000 | 0.044270 | 0.044270 | 30.0 | -0.022797 |
| 3B | 0.000000 | 0.004575 | 0.004772 | 665.951536 | 0.000000 | 0.004772 | 0.004772 | 2.0 | 0.015463 |
| HR | 0.000000 | 0.030167 | 0.034972 | 332.234013 | 0.000000 | 0.034972 | 0.034972 | 53.0 | 0.480715 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': 0.002957265216719046, 'UBB': 0.015670121145596363, 'HBP': 0.0007742707047147384, '1B': 0.010689426380544459, '2B': 0.048711468184618245, '3B': 0.09718596366194948, 'HR': 0.11903100644690688}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.04194200616708403, 'UBB': 0.07125891472319991, 'HBP': -0.011700913656605475, '1B': -0.018839904112043806, '2B': 0.022226112826445606, '3B': -0.044847381753058274, 'HR': 0.10900732826254583}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.38572820263029745, 'effects': {'K': -0.10269936106513912, 'UBB': -0.0328517735309494, 'HBP': -0.016457149386225237, '1B': -0.004150853696951355, '2B': -0.021066388879725985, '3B': 0.001698541559487379, 'HR': -0.06951751956426201}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.4079883097905504, 'effects': {'K': 0.0010759817811924481, 'UBB': 0.07879655835157136, 'HBP': 0.004487748412095724, '1B': -0.012378503120005387, '2B': 0.001597319661368683, '3B': -0.002835831078463511, 'HR': 0.0031932913842612994}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.07655759877496604, 'UBB': 0.0049090063313474075, 'HBP': 0.015528017638859307, '1B': 0.04354436396468877, '2B': 0.03026512278397118, '3B': -0.01671581305274506, 'HR': 0.06969082385982855}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.023977804607124318, 'UBB': 0.07193026240919173, 'HBP': 0.04447008206199325, '1B': -0.030613828066034098, '2B': 0.013284447097982929, '3B': 0.049241816617038345, 'HR': 0.037613386413871415}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.22244389027431422, 'effects': {'K': 0.009865084025373158, 'UBB': 0.05463217591750778, 'HBP': 0.004022875014959958, '1B': -0.010790544792259093, '2B': 0.0014252240007647276, '3B': -0.00201922568335914, 'HR': 0.007665991545563564}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.5176666666666667, 'effects': {'K': 0.05351947020631892, 'UBB': -0.029241285781982377, 'HBP': -0.00674971172497428, '1B': -0.0038410079080797173, '2B': -0.009743687206438796, '3B': 0.023812152670265357, 'HR': -0.019336648379516937}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.21870324189526197, 'effects': {'K': 0.051502429672796675, 'UBB': 0.02563420153271356, 'HBP': 0.004882805405878409, '1B': -0.006640920739005219, '2B': 0.011843426214351527, '3B': 0.0013637914169681072, 'HR': 0.040886806854317594}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.4613333333333334, 'effects': {'K': 0.049581165323962575, 'UBB': -0.02422215426630957, 'HBP': -0.001277844833717552, '1B': 0.00419389863165638, '2B': 0.004042963876249663, '3B': 0.014177872869921154, 'HR': 0.005677053375987237}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Alonso had 15 AA and 21 AAA HR in 2018, with 273 and 301 PA. No MLB history means a pure conditional prior. Final HR 3.50% misses 53/693 = 7.65%, while K and walk probabilities are much closer. Expected PA remains 132 versus 693. Both new talent arms worsen the old rate, showing that explicit own-MLB anchoring does not solve the strong minor-power prior. Dewees and Robson never appear; Lopez and Joe appear with poor rates. The 288-person age/stage/exposure profile is not an Alonso-like power translation certificate.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Donnie Dewees | 24.0 | 0 | 241.0 | 310.0 | -0.966477 | -0.930723 | 52.531597 | 0 | Unobserved |
| Nicky Lopez | 23.0 | 0 | 256.0 | 325.0 | -1.335216 | -0.594344 | 69.854902 | 402 | -3.085707 |
| Connor Joe | 25.0 | 0 | 188.0 | 248.0 | -0.193117 | -0.173291 | 60.218554 | 16 | -11.223792 |
| Jacob Robson | 23.0 | 0 | 245.0 | 311.0 | 0.030993 | -0.736816 | 30.237636 | 0 | Unobserved |

## Anthony Volpe from 2022 to 2023

Player 683011, row 48516, fold 4, age 21.0, stage Upper minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | A | 257 | 12 | 43 | 51 |
| 2021 | Aplus | 256 | 15 | 58 | 26 |
| 2022 | AA | 497 | 18 | 88 | 57 |
| 2022 | AAA | 99 | 3 | 30 | 8 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 48516, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'top20', 'own_mlb_exposure': 'none', 'active_profile_players': 13}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.147697 | 334.418425 | 0.964734 |
| fixed_reliability | -0.867379 | 334.418425 | 0.563609 |
| learned_reliability | -1.100083 | 334.418425 | 0.433909 |
| Actual | -1.344773 | 601 | 0.513728 |

Unchanged expected PA = participation 0.83564897 × conditional PA 400.190077. For each arm contribution = expected PA × (batting rate/600 + 0.00313097). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.467680 | 0.433327 | 100.000000 | 0.000000 | 0.433327 | 0.433327 | 264.0 | -0.000000 |
| K | 0.000000 | 0.224178 | 0.274081 | 100.000000 | 0.000000 | 0.274081 | 0.274081 | 167.0 | 0.000000 |
| UBB | 0.000000 | 0.078977 | 0.080342 | 100.000000 | 0.000000 | 0.080342 | 0.080342 | 52.0 | 0.047520 |
| HBP | 0.000000 | 0.011239 | 0.011480 | 100.000000 | 0.000000 | 0.011480 | 0.011480 | 5.0 | 0.008762 |
| 1B | 0.000000 | 0.142135 | 0.130044 | 100.000000 | 0.000000 | 0.130044 | 0.130044 | 65.0 | -0.533676 |
| 2B | 0.000000 | 0.043614 | 0.039818 | 100.000000 | 0.000000 | 0.039818 | 0.039818 | 23.0 | -0.235822 |
| 3B | 0.000000 | 0.003532 | 0.004787 | 100.000000 | 0.000000 | 0.004787 | 0.004787 | 4.0 | 0.098295 |
| HR | 0.000000 | 0.028646 | 0.026122 | 100.000000 | 0.000000 | 0.026122 | 0.026122 | 21.0 | -0.252458 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.15553033369330815, 'UBB': -0.031410734348264996, 'HBP': 0.21256382409439448, '1B': -0.017977454651544506, '2B': 0.02108969392779996, '3B': 0.3271162825650471, 'HR': 0.07295166390845229}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.4407035175879398, 'effects': {'K': -0.11072725159875531, 'UBB': -0.04485755136667216, 'HBP': -0.016237940336010493, '1B': -0.0004857663236418135, '2B': -0.017997901305215093, '3B': -0.005326376015352797, 'HR': -0.06292769058100617}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.36331658291457264, 'effects': {'K': 0.10734364803465801, 'UBB': 0.027904641576082915, 'HBP': 0.006619458407677372, '1B': -0.013150622981957962, '2B': 0.008534741736790216, '3B': -0.0030858135407575956, 'HR': 0.046881369054843296}}, {'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.04404356812690959, 'UBB': 0.03228768425671579, 'HBP': -0.04465457425756764, '1B': 0.041358016216351774, '2B': 0.05913267619935374, '3B': 0.04244088343982444, 'HR': 0.09532795577439607}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.8283333333333334, 'effects': {'K': 0.08718374908449306, 'UBB': -0.015933394257412862, 'HBP': -0.018894490071093135, '1B': -0.019569072137389724, '2B': 0.0006792622333951161, '3B': -0.001890176771099817, 'HR': -0.015651305673201565}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.044567833038484085, 'UBB': -0.08233652846779985, 'HBP': -0.015958414687859846, '1B': 0.012236825155550904, '2B': 0.0005412869891591689, '3B': 0.02050498083333274, 'HR': -0.07026987355972258}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.07745920993704662, 'UBB': 0.004244630108306718, 'HBP': 0.016767511815230566, '1B': -0.0012159898177993087, '2B': -0.002936563095424795, '3B': 0.005864642459258339, 'HR': 0.04984929911376672}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.007617117400850766, 'UBB': 0.04066583109637076, 'HBP': -0.06876274991166348, '1B': -0.023802902544510136, '2B': -0.029041955127646124, '3B': 0.00801825943113563, 'HR': -0.0006002103679564883}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.018796217161014483, 'UBB': 0.05651658949551846, 'HBP': 0.028102612212400888, '1B': -0.033317464069835344, '2B': 0.010007134017868725, '3B': 0.01448605171422992, 'HR': 0.01282354147969103}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.2887772194304858, 'effects': {'K': 0.007260246545643755, 'UBB': 0.05503758880332533, 'HBP': 0.002855215997196136, '1B': -0.015926190306196762, '2B': -0.00383181029375361, '3B': -0.002605650351396145, 'HR': 0.004511192746767656}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.467680 | 0.433543 | 317.270056 | 0.000000 | 0.433543 | 0.433543 | 264.0 | -0.000000 |
| K | 0.000000 | 0.224178 | 0.278793 | 94.897828 | 0.000000 | 0.278793 | 0.278793 | 167.0 | 0.000000 |
| UBB | 0.000000 | 0.078977 | 0.081392 | 269.100839 | 0.000000 | 0.081392 | 0.081392 | 52.0 | 0.084091 |
| HBP | 0.000000 | 0.011239 | 0.010670 | 292.420623 | 0.000000 | 0.010670 | 0.010670 | 5.0 | -0.020658 |
| 1B | 0.000000 | 0.142135 | 0.124787 | 532.701072 | 0.000000 | 0.124787 | 0.124787 | 65.0 | -0.765698 |
| 2B | 0.000000 | 0.043614 | 0.040508 | 1537.056061 | 0.000000 | 0.040508 | 0.040508 | 23.0 | -0.192952 |
| 3B | 0.000000 | 0.003532 | 0.004354 | 661.203941 | 0.000000 | 0.004354 | 0.004354 | 4.0 | 0.064395 |
| HR | 0.000000 | 0.028646 | 0.025954 | 301.218915 | 0.000000 | 0.025954 | 0.025954 | 21.0 | -0.269260 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.04391085668561386, 'UBB': 0.03791695716843351, 'HBP': -0.011487602238770881, '1B': 0.023974385054445085, '2B': 0.054238254712345106, '3B': 0.1537712234875661, 'HR': 0.14306846809868015}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1425309773240566, 'UBB': -0.0203937301779015, 'HBP': 0.04390005193766169, '1B': 0.0009968043388312764, '2B': 0.08830948371941795, '3B': -0.01565958268183963, 'HR': 0.051490991704191885}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.36331658291457264, 'effects': {'K': 0.11560455061264711, 'UBB': 0.04091070202933774, 'HBP': 0.014236378735827, '1B': -0.009840298098094303, '2B': 0.02377666555806096, '3B': -0.00360676476400732, 'HR': 0.06968268385744641}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.4407035175879398, 'effects': {'K': -0.11129851136138348, 'UBB': -0.04880132712355896, 'HBP': -0.0170729574434259, '1B': -0.0012565308095246511, '2B': -0.020682423241108635, '3B': 0.00120002637896541, 'HR': -0.06866028866017691}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.0496845966994591, 'UBB': -0.09945452404289758, 'HBP': -0.027195085225225995, '1B': 0.016349910894142727, '2B': -0.013019086669459778, '3B': 0.03948253065809514, 'HR': -0.09817492612550376}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.8283333333333334, 'effects': {'K': 0.08773486127012173, 'UBB': -0.025784526330561244, 'HBP': -0.0008295016716427934, '1B': -0.015588796878233696, '2B': -0.007126822042222752, '3B': 0.032490398053194244, 'HR': -0.002088189164736912}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.07876997676129645, 'UBB': 0.008082096803675304, 'HBP': 0.012405872954508354, '1B': -0.00988154085506112, '2B': 0.005636789814881876, '3B': 0.01269808666393437, 'HR': 0.04163629269206334}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.005746356872949449, 'UBB': 0.025952379398264978, 'HBP': -0.06195531535233176, '1B': -0.020190972830969697, '2B': -0.035720169327517336, '3B': -0.004771290585521478, 'HR': -0.006843001052424996}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.2887772194304858, 'effects': {'K': 0.006864352176166326, 'UBB': 0.06181490395945988, 'HBP': 0.002617785326049348, '1B': -0.01582264820098364, '2B': -0.0022342793214598284, '3B': -0.0022750453526950913, 'HR': 0.005322736262373025}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.01774891904982893, 'UBB': 0.05684214403448887, 'HBP': 0.042951629628298495, '1B': -0.02173089237537916, '2B': -0.0010404345092069377, '3B': 0.03771753616403582, 'HR': 0.015376938558110589}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Volpe's 2022 AA/AAA season supplies 21 HR and 118 K in 596 PA. Adaptive prior K 27.9% is almost exactly next year's 27.8%, and the -1.10 rate is closer to actual -1.34 than old -0.15. But unchanged PA is 334 versus 601, and near delivered value partly reflects two errors offsetting: optimistic rate and low playing time. HR 2.60% remains below actual 3.49%. Thirteen coarse active profiles are sparse. Walker and Meadows contribute while Martin never appears; Gonzales has a poor rate.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jordan Walker | 20.0 | 0 | 0.0 | 536.0 | 0.382883 | -0.853963 | 123.548941 | 465 | 1.227766 |
| Nick Gonzales | 23.0 | 0 | 0.0 | 316.0 | -0.057406 | -0.173143 | 146.549145 | 128 | -2.520296 |
| Austin Martin | 23.0 | 0 | 0.0 | 406.0 | -0.687610 | -0.543396 | 87.941929 | 0 | Unobserved |
| Parker Meadows | 22.0 | 0 | 0.0 | 489.0 | -0.841454 | -1.601164 | 73.190257 | 145 | -0.532202 |

## Nick Kurtz from 2024 to 2025

Player 701762, row 57052, fold 2, age 21.0, stage Upper minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2024 | A | 35 | 4 | 7 | 10 |
| 2024 | AA | 15 | 0 | 3 | 2 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 57052, 'stage': 'Upper minors', 'prior_debut': 0, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'none', 'active_profile_players': 413}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.135562 | 1.862081 | 0.005397 |
| fixed_reliability | 0.312747 | 1.862081 | 0.006788 |
| learned_reliability | 0.433042 | 1.862081 | 0.007161 |
| Actual | 5.150009 | 489 | 5.720989 |

Unchanged expected PA = participation 0.01767620 × conditional PA 105.343956. For each arm contribution = expected PA × (batting rate/600 + 0.00312416). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.443366 | 100.000000 | 0.000000 | 0.443366 | 0.443366 | 154.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.247609 | 100.000000 | 0.000000 | 0.247609 | 0.247609 | 151.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.085078 | 100.000000 | 0.000000 | 0.085078 | 0.085078 | 60.0 | 0.210464 |
| HBP | 0.000000 | 0.011072 | 0.011599 | 100.000000 | 0.000000 | 0.011599 | 0.011599 | 2.0 | 0.019151 |
| 1B | 0.000000 | 0.141968 | 0.129151 | 100.000000 | 0.000000 | 0.129151 | 0.129151 | 58.0 | -0.565747 |
| 2B | 0.000000 | 0.042593 | 0.042739 | 100.000000 | 0.000000 | 0.042739 | 0.042739 | 26.0 | 0.009103 |
| 3B | 0.000000 | 0.003820 | 0.005455 | 100.000000 | 0.000000 | 0.005455 | 0.005455 | 2.0 | 0.128034 |
| HR | 0.000000 | 0.029888 | 0.035004 | 100.000000 | 0.000000 | 0.035004 | 0.035004 | 36.0 | 0.511741 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.11500916556047082, 'UBB': 0.015329940508023046, 'HBP': 0.21420571531634314, '1B': 0.002240118261919844, '2B': -0.008669715308389059, '3B': 0.3165046814937752, 'HR': 0.01239728786000714}}, {'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.05381960163792693, 'UBB': -0.0007892794570587783, 'HBP': -0.03175287063450291, '1B': 0.04297563861964337, '2B': 0.06098069259916389, '3B': 0.05399047114041656, 'HR': 0.1068623636794044}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03341940170016123, 'UBB': 0.04504591738827412, 'HBP': -0.007357215824856802, '1B': -0.028177499612217348, '2B': 0.012956422387227882, '3B': -0.021255558919383355, 'HR': 0.07710219933637169}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.02721038278490806, 'UBB': -0.011146525848226028, 'HBP': -0.07696023595073923, '1B': -0.027179778807350397, '2B': -0.04051635590330229, '3B': -0.005166111075146461, 'HR': -0.006696558958113905}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.0595976054335993, 'UBB': 0.06841235987490542, 'HBP': 0.018590163435301205, '1B': -0.03004854554705623, '2B': 0.009644718531642754, '3B': 0.018577548345495944, 'HR': 0.027000741355132366}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.04237280190231877, 'UBB': -0.0009688577902538107, 'HBP': -0.009159643623389299, '1B': 0.012822408502502977, '2B': 0.0043236152179900594, '3B': 0.010850877343457993, 'HR': -0.01062091660777551}}, {'feature': 'draft_college', 'scaled_input': 1.0, 'effects': {'K': -0.03254363424167194, 'UBB': -0.0105769081361822, 'HBP': 0.00500460431676293, '1B': -0.010639884876532777, '2B': 0.006881084436934872, '3B': 0.004967550081079277, 'HR': -0.0036630205000368864}}, {'feature': 'draft_rank', 'scaled_input': 0.8176145045277415, 'effects': {'K': -0.031605456225657635, 'UBB': 0.017843709044527867, 'HBP': 0.007857417323635997, '1B': -0.00013053074155963356, '2B': 0.016867590047169766, '3B': 0.007276756594643315, 'HR': 0.01507333634712824}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.027009511914581074, 'UBB': -0.007261938540635741, 'HBP': -0.006477688421615629, '1B': 0.0007460734450390593, '2B': -0.0034550871426964357, '3B': 0.001080221859518785, 'HR': -0.0005776637384817631}}, {'feature': 'pooled_A_BB', 'scaled_input': 0.5333333333333332, 'effects': {'K': -0.003134393931992884, 'UBB': 0.02473666040246887, 'HBP': 0.001650934450022122, '1B': -0.004369348077820276, '2B': -0.0019773369283131647, '3B': -0.0006979785409517266, 'HR': 0.009103484465261866}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.442948 | 316.726104 | 0.000000 | 0.442948 | 0.442948 | 154.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.246169 | 102.570602 | 0.000000 | 0.246169 | 0.246169 | 151.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.085806 | 254.661873 | 0.000000 | 0.085806 | 0.085806 | 60.0 | 0.235831 |
| HBP | 0.000000 | 0.011072 | 0.010743 | 281.927430 | 0.000000 | 0.010743 | 0.010743 | 2.0 | -0.011940 |
| 1B | 0.000000 | 0.141968 | 0.129659 | 469.239897 | 0.000000 | 0.129659 | 0.129659 | 58.0 | -0.543291 |
| 2B | 0.000000 | 0.042593 | 0.044565 | 1787.417032 | 0.000000 | 0.044565 | 0.044565 | 26.0 | 0.122535 |
| 3B | 0.000000 | 0.003820 | 0.004301 | 693.266683 | 0.000000 | 0.004301 | 0.004301 | 2.0 | 0.037646 |
| HR | 0.000000 | 0.029888 | 0.035808 | 298.077256 | 0.000000 | 0.035808 | 0.035808 | 36.0 | 0.592261 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -1.2, 'effects': {'K': -0.04864522657999628, 'UBB': 0.00027885457984102284, 'HBP': 4.1858082021825195e-05, '1B': 0.026886548408356598, '2B': 0.04681649434787147, '3B': 0.17331387905325074, 'HR': 0.14322976216916944}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1137225959126278, 'UBB': 0.04864678906993214, 'HBP': 0.05417911897833354, '1B': -0.005835734015515962, '2B': 0.05709556039569332, '3B': -0.03180339532507647, 'HR': 0.00909402844591616}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03886808512073132, 'UBB': 0.056906276601900736, 'HBP': -0.008888641741903933, '1B': -0.016333877950987216, '2B': 0.02714304768169432, '3B': -0.04805703337654215, 'HR': 0.10485805103252988}}, {'feature': 'age_squared', 'scaled_input': 1.44, 'effects': {'K': 0.019979604746646448, 'UBB': -0.020098250103196727, 'HBP': -0.06816959543607409, '1B': -0.02862711000166646, '2B': -0.02361018055288669, '3B': -0.012824953525942739, 'HR': -0.011518701517100617}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.05609764071246452, 'UBB': 0.06713600675097882, 'HBP': 0.03603460729329444, '1B': -0.02942332007847478, '2B': -0.0032652298157782767, '3B': 0.03791519567031954, 'HR': 0.029153847404017944}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.045779310433548825, 'UBB': -0.009862260849278846, 'HBP': -0.00292542610341865, '1B': 0.015472676360836735, '2B': -0.004741960983967614, '3B': 0.008105516624092349, 'HR': -0.019215243998504824}}, {'feature': 'draft_college', 'scaled_input': 1.0, 'effects': {'K': -0.03458298510679178, 'UBB': -0.011134922705659033, 'HBP': 0.006924947650556613, '1B': -0.005273431034794358, '2B': 0.015506055620595798, '3B': 0.007420321787927589, 'HR': -0.006628883693558069}}, {'feature': 'draft_rank', 'scaled_input': 0.8176145045277415, 'effects': {'K': -0.03245950852630455, 'UBB': 0.016801805054800382, 'HBP': 0.009358151668673494, '1B': 0.0032143634508146088, '2B': 0.018375924483713273, '3B': 0.009914223368747957, 'HR': 0.021442517084702697}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.027390529838521794, 'UBB': -0.00943542442186493, 'HBP': -0.003011193348682513, '1B': -0.0018733154448351635, '2B': -0.010504401305379307, '3B': 0.0007762158001594104, 'HR': -0.007827639021166176}}, {'feature': 'pooled_A_BB', 'scaled_input': 0.5333333333333332, 'effects': {'K': -0.0036041358596326763, 'UBB': 0.02459338438429754, 'HBP': 0.0017419235173720881, '1B': -0.0053608777372775775, '2B': -0.0010593415280353692, '3B': 0.0007005751475846363, 'HR': 0.00936828360117362}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Kurtz's available professional history is only 35 A PA with four HR and 15 AA PA without a HR. Pick four and college-junior classification are genuinely present, unlike older unknown draft classes. Adaptive rate rises to +0.43 versus old -0.14, but misses actual +5.15 and keeps expected PA under two versus 489. Final HR 3.58% is below actual 7.36%; 24.6% K is lower than actual 30.9%, so rosy contact does not recover elite power. This limited source cannot establish all college talent; no new college collection is authorized. Moore/Smith arrive, Davis/Bradfield do not. Coarse 413-person support does not resolve rapid entry.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Christian Moore | 21.0 | 0 | 0.0 | 98.0 | -0.112921 | 0.069253 | 8.015777 | 184 | -1.224106 |
| Cam Smith | 21.0 | 0 | 0.0 | 20.0 | -0.327950 | 0.207737 | 2.199413 | 493 | -0.636096 |
| Chase Davis | 22.0 | 0 | 0.0 | 31.0 | -0.606643 | -0.303094 | 1.741445 | 0 | Unobserved |
| Enrique Bradfield Jr. | 22.0 | 0 | 0.0 | 120.0 | -0.508031 | -0.019997 | 24.983244 | 0 | Unobserved |

## Ethan Salas from 2024 to 2025

Player 806956, row 57694, fold 3, age 18.0, stage Lower minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2023 | A | 220 | 9 | 57 | 24 |
| 2023 | AA | 33 | 0 | 8 | 4 |
| 2023 | Aplus | 37 | 0 | 10 | 2 |
| 2024 | Aplus | 469 | 4 | 98 | 47 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 57694, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'top20', 'own_mlb_exposure': 'none', 'active_profile_players': 2}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.447557 | 7.139187 | 0.016979 |
| fixed_reliability | -0.153719 | 7.139187 | 0.020475 |
| learned_reliability | -0.453205 | 7.139187 | 0.016911 |
| Actual | Unobserved | 0 | 0.000000 |

Unchanged expected PA = participation 0.02565198 × conditional PA 278.309347. For each arm contribution = expected PA × (batting rate/600 + 0.00312416). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.437987 | 100.000000 | 0.000000 | 0.437987 | 0.437987 | 0.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.264404 | 100.000000 | 0.000000 | 0.264404 | 0.264404 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.073504 | 100.000000 | 0.000000 | 0.073504 | 0.073504 | 0.0 | -0.192678 |
| HBP | 0.000000 | 0.011072 | 0.009837 | 100.000000 | 0.000000 | 0.009837 | 0.009837 | 0.0 | -0.044849 |
| 1B | 0.000000 | 0.141968 | 0.134165 | 100.000000 | 0.000000 | 0.134165 | 0.134165 | 0.0 | -0.344444 |
| 2B | 0.000000 | 0.042593 | 0.040526 | 100.000000 | 0.000000 | 0.040526 | 0.040526 | 0.0 | -0.128420 |
| 3B | 0.000000 | 0.003820 | 0.005229 | 100.000000 | 0.000000 | 0.005229 | 0.005229 | 0.0 | 0.110308 |
| HR | 0.000000 | 0.029888 | 0.034350 | 100.000000 | 0.000000 | 0.034350 | 0.034350 | 0.0 | 0.446365 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.14664035954243398, 'UBB': 0.056146141437680486, 'HBP': 0.17539050073627802, '1B': -0.031427847927376865, '2B': -0.018580659636938404, '3B': 0.31651699189218474, 'HR': 0.05154219035610447}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.045420793476296815, 'UBB': 0.030169687524495264, 'HBP': -0.14928089768860525, '1B': -0.038235162237997056, '2B': -0.08006502810618664, '3B': 0.04373228484413969, 'HR': -0.009222731233041749}}, {'feature': 'age_centered', 'scaled_input': -1.8, 'effects': {'K': -0.08033683710882122, 'UBB': 0.013688393015204805, 'HBP': -0.07954714361065093, '1B': 0.05223010467160828, '2B': 0.07956761354076308, '3B': 0.05279307093079479, 'HR': 0.1476197112712171}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.8310000000000001, 'effects': {'K': 0.07807038801913845, 'UBB': -0.021149458129876193, 'HBP': -0.010035855105793065, '1B': 0.005116318468795801, '2B': 0.0013729743606583466, '3B': 0.003083318529149712, 'HR': -0.00815253241439035}}, {'feature': 'position_2', 'scaled_input': 1.0, 'effects': {'K': 0.022429565246585872, 'UBB': -0.027036962265041136, 'HBP': -0.008538348978779477, '1B': -0.018419902670215017, '2B': -0.006020977073263072, '3B': -0.05350700884829446, 'HR': 0.0037127050381600777}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.03302374894612135, 'UBB': 0.00025374215917264614, 'HBP': 0.010093194106456843, '1B': 0.004142417154862393, '2B': 0.02115820659934331, '3B': 0.006605548266267036, 'HR': 0.05214455132582952}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.05212104113534894, 'UBB': -0.017674846440503354, 'HBP': -0.013132891574444422, '1B': 0.024069990810490407, '2B': 0.004756857864935228, '3B': 0.007096228279810538, 'HR': -0.012661542319405857}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.018498977129240597, 'UBB': -0.032300807674881624, 'HBP': -0.00738311384520249, '1B': -0.0017086691379611498, '2B': -0.0036613067882817463, '3B': 0.004841011376498385, 'HR': -0.009265351364012717}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.02929521506564576, 'UBB': -0.01414271827137046, 'HBP': 0.0061580397389287824, '1B': 0.0006593334221949945, '2B': -0.0018625571129554704, '3B': -0.0016909897912928986, 'HR': -0.009883731028252074}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': 0.005658266300565391, 'UBB': -0.022935523005244846, 'HBP': -0.0006207794664323592, '1B': -0.0007132543887064974, '2B': -0.002664110071018822, '3B': 0.0016641201702062621, 'HR': -0.009383156919104137}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.441527 | 327.307312 | 0.000000 | 0.441527 | 0.441527 | 0.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.266594 | 99.640390 | 0.000000 | 0.266594 | 0.266594 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.073422 | 269.645522 | 0.000000 | 0.073422 | 0.073422 | 0.0 | -0.195541 |
| HBP | 0.000000 | 0.011072 | 0.009292 | 284.652271 | 0.000000 | 0.009292 | 0.009292 | 0.0 | -0.064633 |
| 1B | 0.000000 | 0.141968 | 0.130781 | 515.553233 | 0.000000 | 0.130781 | 0.130781 | 0.0 | -0.493774 |
| 2B | 0.000000 | 0.042593 | 0.039856 | 1745.125268 | 0.000000 | 0.039856 | 0.039856 | 0.0 | -0.170012 |
| 3B | 0.000000 | 0.003820 | 0.004344 | 653.502984 | 0.000000 | 0.004344 | 0.004344 | 0.0 | 0.040985 |
| HR | 0.000000 | 0.029888 | 0.034184 | 314.876292 | 0.000000 | 0.034184 | 0.034184 | 0.0 | 0.429771 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -1.8, 'effects': {'K': -0.07778027314190944, 'UBB': 0.01810747348358141, 'HBP': -0.03570373824527604, '1B': 0.03481107998390863, '2B': 0.07431050467431091, '3B': 0.21094237155847426, 'HR': 0.2159073332434373}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.14560307446512435, 'UBB': 0.07895843473817596, 'HBP': 0.017417448997485274, '1B': -0.0027479389172836346, '2B': 0.06369019960834223, '3B': -0.01853505393479395, 'HR': 0.03994254096976738}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.04178286014456186, 'UBB': 0.01791343728724347, 'HBP': -0.1298817786409373, '1B': -0.05288799333833169, '2B': -0.0778447914649696, '3B': 0.03018270136806444, 'HR': -0.027435536535560367}}, {'feature': 'position_2', 'scaled_input': 1.0, 'effects': {'K': 0.027594004233036356, 'UBB': -0.029740026151857453, 'HBP': -0.0030678748296962904, '1B': -0.02199919650489671, '2B': -0.03396859859183979, '3B': -0.0922775985341279, 'HR': 0.005247864604037928}}, {'feature': 'pooled_Aplus_pa', 'scaled_input': 0.8310000000000001, 'effects': {'K': 0.08041293325796732, 'UBB': -0.02389446966384343, 'HBP': 0.0007504434305148475, '1B': 0.006050825161496583, '2B': -0.0015711311474907348, '3B': 0.023633048681784986, 'HR': -0.003909819372315666}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.05405867676248502, 'UBB': -0.029871673373547302, 'HBP': -0.010168353339154472, '1B': 0.022424679558283565, '2B': -0.009245593283946134, '3B': 0.004710478226648154, 'HR': -0.019156788045798925}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.035698787757818755, 'UBB': 0.0009323132692416186, 'HBP': 0.009103432350669034, '1B': -0.004307590252144793, '2B': 0.023088145367809957, '3B': 0.015255314320499327, 'HR': 0.046890817823017204}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.021427272399559754, 'UBB': -0.040060308219066997, 'HBP': -0.00710925523688551, '1B': 0.004425355501099091, '2B': -0.010144752865220673, '3B': 0.0009835910812870975, 'HR': -0.018061695955916116}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.030013775880265197, 'UBB': -0.013360282078937014, 'HBP': 0.009010666466959109, '1B': -0.011455286675180677, '2B': -0.009759047929244606, '3B': 0.0006904078140306052, 'HR': -0.01851494805549273}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': 0.004576212749959572, 'UBB': -0.02622099065021346, 'HBP': 0.0009449357220198184, '1B': -0.0037819633723535227, '2B': -0.00975682925838722, '3B': 0.000877913807122916, 'HR': -0.01813618562447896}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Salas has 469 High-A PA with four HR and 98 K in 2024, after small AA exposure in 2023. There is no MLB anchor and only two coarse active profiles. Expected MLB PA is seven and actual zero; conditional next-year ability is unobserved, not zero or a failed +rate. The prior is the selected population of rare immediate MLB participants, not a present-day equivalency for an 18-year-old catcher. Gonzalez, Arias, Juan and Acuna also have zero next-year MLB PA. Neither arm is grounds to claim this prospect's long-term value is zero.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gabriel Gonzalez | 20.0 | 0 | 0.0 | 0.0 | -0.319479 | 0.108367 | 1.556116 | 0 | Unobserved |
| Roderick Arias | 19.0 | 0 | 0.0 | 0.0 | -0.506159 | -0.649097 | 1.155300 | 0 | Unobserved |
| Simon Juan | 18.0 | 0 | 0.0 | 0.0 | -0.212125 | -0.242370 | 0.127745 | 0 | Unobserved |
| Bryan Acuña | 18.0 | 0 | 0.0 | 0.0 | -0.228966 | -0.132238 | 0.084848 | 0 | Unobserved |

## Carlos Concepcion from 2024 to 2025

Player 808393, row 57990, fold 4, age 18.0, stage Lower minors. Selection: fixed diagnostic.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2023 | DSL | 133 | 4 | 29 | 13 |
| 2024 | DSL | 199 | 3 | 61 | 23 |

Weighted transported own MLB PA: 0.000000. Actual-fold active profile: [{'row_id': 57990, 'stage': 'Lower minors', 'prior_debut': 0, 'age_band': 3.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'none', 'active_profile_players': 5}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.213215 | 0.101124 | 0.000352 |
| fixed_reliability | 0.428828 | 0.101124 | 0.000388 |
| learned_reliability | 0.382292 | 0.101124 | 0.000380 |
| Actual | Unobserved | 0 | 0.000000 |

Unchanged expected PA = participation 0.00121381 × conditional PA 83.311098. For each arm contribution = expected PA × (batting rate/600 + 0.00312416). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.446973 | 100.000000 | 0.000000 | 0.446973 | 0.446973 | 0.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.241570 | 100.000000 | 0.000000 | 0.241570 | 0.241570 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.080392 | 100.000000 | 0.000000 | 0.080392 | 0.080392 | 0.0 | 0.047229 |
| HBP | 0.000000 | 0.011072 | 0.010477 | 100.000000 | 0.000000 | 0.010477 | 0.010477 | 0.0 | -0.021608 |
| 1B | 0.000000 | 0.141968 | 0.139071 | 100.000000 | 0.000000 | 0.139071 | 0.139071 | 0.0 | -0.127878 |
| 2B | 0.000000 | 0.042593 | 0.041380 | 100.000000 | 0.000000 | 0.041380 | 0.041380 | 0.0 | -0.075352 |
| 3B | 0.000000 | 0.003820 | 0.005515 | 100.000000 | 0.000000 | 0.005515 | 0.005515 | 0.0 | 0.132717 |
| HR | 0.000000 | 0.029888 | 0.034623 | 100.000000 | 0.000000 | 0.034623 | 0.034623 | 0.0 | 0.473720 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18916670455545742, 'UBB': 0.009338356097274708, 'HBP': 0.22847280561530123, '1B': -0.0069727232686050775, '2B': 0.01628210874399012, '3B': 0.32619282357277013, 'HR': 0.059716969916472705}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.04789925202772452, 'UBB': 0.06671369366300142, 'HBP': -0.1536752454102455, '1B': -0.06546194503017719, '2B': -0.08561294450420952, '3B': 0.023773937703831106, 'HR': 0.01365481582530787}}, {'feature': 'age_centered', 'scaled_input': -1.8, 'effects': {'K': -0.09261078036226232, 'UBB': 0.026002657356334006, 'HBP': -0.06523846952922237, '1B': 0.05593509669128361, '2B': 0.08477517284309337, '3B': 0.06310854721328318, 'HR': 0.13744563438217702}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': 1.91005091892056e-05, 'UBB': 0.019788499007690977, 'HBP': -0.0017303937586578848, '1B': 0.018932005386578885, '2B': 0.004851175112969529, '3B': 0.007015030706570083, 'HR': 0.04679314033969328}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.03678437101181849, 'UBB': -0.00857088401536717, 'HBP': -0.008239347324142526, '1B': 0.01605127678541881, '2B': -0.003570195977479671, '3B': 8.36108158705787e-05, 'HR': -0.005395705046083443}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.011157744036343752, 'UBB': -0.02124498095704999, 'HBP': -0.011512815442517803, '1B': 0.0029296221030940175, '2B': -0.011501357829717816, '3B': 0.001301675766736246, 'HR': -0.017861683621205136}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': -0.001139922337656903, 'UBB': -0.0139115748280837, 'HBP': -0.006488688807397282, '1B': 0.00044582069339943437, '2B': -0.004528318039787558, '3B': 0.0006727321396127981, 'HR': -0.015012949406027355}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': 0.0003028238038822375, 'UBB': -0.00836762032591027, 'HBP': 0.008990264228985974, '1B': 0.0003257302841087411, '2B': 0.006783534595003438, '3B': -0.014282198627605127, 'HR': -0.011487429984920985}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.008039045704906666, 'UBB': -0.007528343421199199, 'HBP': -0.0017532813496762376, '1B': -0.00152812139247157, '2B': 0.0021956942712203858, '3B': -4.1424431129785106e-05, 'HR': -0.012836433297162744}}, {'feature': 'scout_list_capacity_0', 'scaled_input': 1.0, 'effects': {'K': 0.003794049093409269, 'UBB': -0.0034510368992797546, 'HBP': -0.0010788459163866158, '1B': -0.0010084115665558563, '2B': 0.001149851311756399, '3B': 2.4483803541738284e-05, 'HR': -0.006519893139206695}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 0.000000 | 0.465823 | 0.450287 | 287.621488 | 0.000000 | 0.450287 | 0.450287 | 0.0 | -0.000000 |
| K | 0.000000 | 0.225800 | 0.239715 | 96.057788 | 0.000000 | 0.239715 | 0.239715 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.079036 | 0.079949 | 260.884119 | 0.000000 | 0.079949 | 0.079949 | 0.0 | 0.031798 |
| HBP | 0.000000 | 0.011072 | 0.009830 | 285.147955 | 0.000000 | 0.009830 | 0.009830 | 0.0 | -0.045098 |
| 1B | 0.000000 | 0.141968 | 0.137595 | 550.138891 | 0.000000 | 0.137595 | 0.137595 | 0.0 | -0.193051 |
| 2B | 0.000000 | 0.042593 | 0.043288 | 1706.410999 | 0.000000 | 0.043288 | 0.043288 | 0.0 | 0.043209 |
| 3B | 0.000000 | 0.003820 | 0.004630 | 645.862003 | 0.000000 | 0.004630 | 0.004630 | 0.0 | 0.063441 |
| HR | 0.000000 | 0.029888 | 0.034706 | 307.861031 | 0.000000 | 0.034706 | 0.034706 | 0.0 | 0.481992 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -1.8, 'effects': {'K': -0.09451669503723195, 'UBB': 0.02693529901114214, 'HBP': -0.02104548853050272, '1B': 0.034006552112661216, '2B': 0.07218508813679245, '3B': 0.23162589873914055, 'HR': 0.19684575971772988}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18913020430282176, 'UBB': 0.03461821805781427, 'HBP': 0.0662195322839522, '1B': -0.008518822222885069, '2B': 0.06962063223779041, '3B': -0.009355513846174316, 'HR': 0.04631476956401121}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.04133328427573629, 'UBB': 0.041508094698612025, 'HBP': -0.13522635857210097, '1B': -0.0481461951558479, '2B': -0.07767215263067169, '3B': 0.010101368421607635, 'HR': -0.00826379493783546}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.0018070962130540985, 'UBB': 0.024370656166994367, 'HBP': 0.00048110131918001656, '1B': 0.011915042980156417, '2B': 0.03321913472174122, '3B': 0.012691646521069763, 'HR': 0.05686571447798267}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.039105961084943804, 'UBB': -0.011727621237307374, 'HBP': -0.0036185229700653053, '1B': 0.01619771116430973, '2B': -0.0050549318995577325, '3B': -0.0015982343661275294, 'HR': -0.013085484212723441}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': -0.011273595588178467, 'UBB': -0.02382258988795663, 'HBP': -0.008232614071138292, '1B': 0.003882025867818495, '2B': -0.015002395546113028, '3B': -0.0025613933411738343, 'HR': -0.02535853602787345}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.0019566995239779688, 'UBB': -0.009177536977820911, 'HBP': 0.01214553855546595, '1B': 3.714184557472816e-05, '2B': -0.013076729315887103, '3B': -0.021320043407566453, 'HR': -0.02203000486837356}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': -0.001450165149050409, 'UBB': -0.017663102601259036, 'HBP': -0.0023555849577990818, '1B': -0.0006336339931896656, '2B': -0.008832198746959457, '3B': -0.0009240798728038837, 'HR': -0.02140898666215209}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.007486291774039555, 'UBB': -0.01282693021025783, 'HBP': 0.0032453946877956954, '1B': -0.0046032693006818086, '2B': -0.002862785827740548, '3B': 0.0007326610856600502, 'HR': -0.018022741491441438}}, {'feature': 'scout_list_capacity_0', 'scaled_input': 1.0, 'effects': {'K': 0.0038199678057988604, 'UBB': -0.005968704756618807, 'HBP': 0.0015610187578792337, '1B': -0.0023314601116787444, '2B': -0.0014462215418508885, '3B': 0.0003908056269290804, 'HR': -0.00893895400335115}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Concepcion's source has 133 DSL PA in 2023 and 199 in 2024, with four then three HR and 29 then 61 K. No own MLB history makes this a pure conditional prior. Expected PA is 0.10 and actual zero. A +0.38 hypothetical active rate must not be sold as MLB readiness or a validated present-day grade. Five coarse active profiles are sparse; Juan, Acuna and the two Ramirez peers all have zero future MLB PA. This test does not certify older repeating-level history outside its three-year window.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Simon Juan | 18.0 | 0 | 0.0 | 0.0 | -0.212125 | -0.242370 | 0.127745 | 0 | Unobserved |
| Bryan Acuña | 18.0 | 0 | 0.0 | 0.0 | -0.228966 | -0.132238 | 0.084848 | 0 | Unobserved |
| Richard Ramirez | 18.0 | 0 | 0.0 | 0.0 | -0.173145 | -0.363556 | 0.095789 | 0 | Unobserved |
| Rafael Ramirez Jr. | 18.0 | 0 | 0.0 | 0.0 | -0.496691 | -0.474300 | 0.118645 | 0 | Unobserved |

## AJ Reed from 2017 to 2018

Player 607223, row 28742, fold 1, age 24.0, stage Current MLB. Selection: fixed_reliability rate largest gain.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2015 | AA | 237 | 11 | 49 | 25 |
| 2015 | Aplus | 385 | 23 | 73 | 58 |
| 2016 | AAA | 296 | 15 | 67 | 31 |
| 2016 | MLB | 141 | 3 | 48 | 18 |
| 2017 | AAA | 556 | 34 | 146 | 69 |
| 2017 | MLB | 6 | 0 | 1 | 0 |

Weighted transported own MLB PA: 118.800000. Actual-fold active profile: [{'row_id': 28742, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'brief', 'active_profile_players': 181}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.176095 | 153.618467 | 0.517643 |
| fixed_reliability | -2.061783 | 153.618467 | -0.055322 |
| learned_reliability | -0.831374 | 153.618467 | 0.259700 |
| Actual | -15.577655 | 3 | -0.068648 |

Unchanged expected PA = participation 0.66956636 × conditional PA 229.429787. For each arm contribution = expected PA × (batting rate/600 + 0.00307618). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 47.945167 | 0.466035 | 0.409425 | 100.000000 | 0.542962 | 0.406251 | 0.406251 | 2.0 | -0.000000 |
| K | 40.076572 | 0.216433 | 0.269939 | 100.000000 | 0.542962 | 0.306538 | 0.306538 | 1.0 | 0.000000 |
| UBB | 14.951101 | 0.080191 | 0.100088 | 100.000000 | 0.542962 | 0.114076 | 0.114076 | 0.0 | 1.180337 |
| HBP | 0.000000 | 0.009515 | 0.011110 | 100.000000 | 0.542962 | 0.005078 | 0.005078 | 0.0 | -0.161159 |
| 1B | 10.828650 | 0.145271 | 0.116628 | 100.000000 | 0.542962 | 0.102795 | 0.102795 | 0.0 | -1.874802 |
| 2B | 2.415086 | 0.045317 | 0.046949 | 100.000000 | 0.542962 | 0.032495 | 0.032495 | 0.0 | -0.796517 |
| 3B | 0.000000 | 0.004290 | 0.005604 | 100.000000 | 0.542962 | 0.002561 | 0.002561 | 0.0 | -0.135411 |
| HR | 2.583424 | 0.032947 | 0.040257 | 100.000000 | 0.542962 | 0.030206 | 0.030206 | 0.0 | -0.274231 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.09856158152123157, 'UBB': 0.02436417565237011, 'HBP': 0.2434060723612608, '1B': 0.0009465387356782488, '2B': 0.010082930354707987, '3B': 0.34359966210804305, 'HR': 0.05319908765219723}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.3213333333333332, 'effects': {'K': 0.09537317869990676, 'UBB': -0.023657829303070962, 'HBP': 0.0161056637688314, '1B': 0.012333338029708636, '2B': 0.02270821947312601, '3B': -0.00429589359821674, 'HR': -0.008358467226464106}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08360197976937886, 'UBB': -0.0009526765774509422, 'HBP': 0.0727224367969711, '1B': -0.04213449348847558, '2B': 0.04435769430749401, '3B': 0.00863016435438496, 'HR': 0.04523275407461155}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.029069738844318335, 'UBB': 0.048165709842426706, 'HBP': -0.013762248301711572, '1B': -0.02538726463835577, '2B': -0.0022756383157609464, '3B': -0.01099713044624908, 'HR': 0.07484150283077509}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.029698284328752093, 'UBB': 0.0703773953160956, 'HBP': 0.02048238641429701, '1B': -0.03628391685722824, '2B': 0.026102545209505525, '3B': 0.032004096271197484, 'HR': 0.053553726094016846}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.4930513595166162, 'effects': {'K': 5.528979079569494e-05, 'UBB': 0.07021109046512382, 'HBP': -0.0043387418678606125, '1B': -0.01342960448553936, '2B': 0.0072449767142757976, '3B': -0.003195897404226079, 'HR': 0.0061964780914480315}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': -0.007793484714380353, 'UBB': -0.0136073488324918, 'HBP': -0.021902475306146977, '1B': 0.029023120552242772, '2B': 0.02305028986263496, '3B': 0.024053214876784964, 'HR': 0.05411433178267193}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.3402329749103942, 'effects': {'K': 0.007037538230208372, 'UBB': 0.05195393270659878, 'HBP': 0.0028874205424630392, '1B': -0.004288985690234942, '2B': 0.002853610564076153, '3B': -0.002797002111244009, 'HR': 0.00701895686927423}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': 0.0002378373742952687, 'UBB': 0.04377755405914491, 'HBP': -0.007934959000564436, '1B': 0.006062358859179982, '2B': 0.00573931671534922, '3B': 0.012833577724528315, 'HR': 0.0032742572105087316}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.2818731117824774, 'effects': {'K': -0.041509080135916594, 'UBB': -0.016101355369690915, 'HBP': -0.009564981855528246, '1B': 0.008547943501763546, '2B': -0.00120833694234587, '3B': 0.0003308052389346625, 'HR': -0.02662091347187284}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 47.945167 | 0.466035 | 0.405240 | 351.323304 | 0.252700 | 0.404820 | 0.394102 | 2.0 | -0.000000 |
| K | 40.076572 | 0.216433 | 0.274818 | 88.501896 | 0.573077 | 0.310651 | 0.302426 | 1.0 | 0.000000 |
| UBB | 14.951101 | 0.080191 | 0.103530 | 300.008130 | 0.283662 | 0.109862 | 0.106953 | 0.0 | 0.932209 |
| HBP | 0.000000 | 0.009515 | 0.009396 | 326.916402 | 0.266537 | 0.006891 | 0.006709 | 0.0 | -0.101904 |
| 1B | 10.828650 | 0.145271 | 0.116614 | 500.846407 | 0.191722 | 0.111732 | 0.108774 | 0.0 | -1.610905 |
| 2B | 2.415086 | 0.045317 | 0.045769 | 2066.184480 | 0.054371 | 0.044386 | 0.043211 | 0.0 | -0.130852 |
| 3B | 0.000000 | 0.004290 | 0.004030 | 638.952370 | 0.156779 | 0.003399 | 0.003309 | 0.0 | -0.076901 |
| HR | 2.583424 | 0.032947 | 0.040603 | 316.420602 | 0.272965 | 0.035455 | 0.034517 | 0.0 | 0.156978 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'pooled_AAA_pa', 'scaled_input': 1.3213333333333332, 'effects': {'K': 0.10589947858626622, 'UBB': -0.02726548919520731, 'HBP': 0.041317993609242015, '1B': -0.013258835240286853, '2B': -0.015197807041248616, '3B': 0.03296391846015423, 'HR': -0.005048933771257993}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03693470605748538, 'UBB': 0.0749890543742655, 'HBP': -0.013289564018423268, '1B': -0.0172972533391754, '2B': 0.013257930843968925, '3B': -0.04118285727308152, 'HR': 0.10525397480656172}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.09837498302253198, 'UBB': 0.036124533572865804, 'HBP': 0.033075171226241776, '1B': 0.04087918745117407, '2B': 0.025539682091705398, '3B': -0.006656045145895458, 'HR': 0.0496560999493523}}, {'feature': 'pooled_Aplus_BB', 'scaled_input': 0.4930513595166162, 'effects': {'K': 0.0019127287318977692, 'UBB': 0.08491820007884571, 'HBP': -0.004604270012842822, '1B': -0.01604587568887798, '2B': 0.016388420737196045, '3B': -0.001764188082485799, 'HR': 0.005978052846398186}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': -0.007876972141946829, 'UBB': -0.0070572821878997416, 'HBP': -1.1776549666334191e-05, '1B': 0.015954550243463376, '2B': 0.030296984623466656, '3B': 0.0722686787472681, 'HR': 0.08023398760514848}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.3402329749103942, 'effects': {'K': 0.009283451968173826, 'UBB': 0.07964215607487488, 'HBP': 0.0034868127261553665, '1B': -0.0133367227588676, '2B': -0.0007286275675792032, '3B': -0.0046892346398869295, 'HR': 0.009695191739539675}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.026032314407560115, 'UBB': 0.07462288342170151, 'HBP': 0.04109315045970855, '1B': -0.035035737699678035, '2B': 0.018336400498823468, '3B': 0.048433796893501004, 'HR': 0.06581689604460658}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.07011348226297867, 'UBB': -0.019623577562522237, 'HBP': 0.019959390881613245, '1B': -0.03996346577508156, '2B': 0.03765925930637181, '3B': -0.05063540911398581, 'HR': 0.029780903284290138}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.19327956989247302, 'effects': {'K': 0.044579597197317716, 'UBB': 0.0255686879643656, 'HBP': 0.005426833149000704, '1B': -0.008270144550964764, '2B': 0.01157065992488042, '3B': 0.0009668270165560504, 'HR': 0.03826096234763802}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.2818731117824774, 'effects': {'K': -0.04222800365198238, 'UBB': -0.014764703494852571, 'HBP': -0.008556627538068167, '1B': 0.005769561065054559, '2B': 0.0011977170183372983, '3B': 0.006698346573245259, 'HR': -0.029473875629447126}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Reed's 2017 AAA season has 34 HR and 146 K in 556 PA, against earlier poor MLB evidence (48 K in 141 PA). Both new forecasts appropriately reduce the optimistic old hitting rate. But his next-year rate of -15.58 arises from only three PA, so the unweighted largest-rate-gain label is not evidence of learning true decline. Expected PA is 154 versus three; fixed-100's near-zero value partly results from a bad rate offsetting too much playing time. Vogelbach and Smith produce, May never appears, Goodrum produces moderately. Judge 2023, not this three-PA row, is the primary PA-weighted rate gain.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Daniel Vogelbach | 24.0 | 31 | 541.0 | 0.0 | -0.173743 | -0.740719 | 86.781207 | 102 | -0.092324 |
| Niko Goodrum | 25.0 | 18 | 499.0 | 0.0 | -0.516502 | -1.352291 | 39.937714 | 492 | 0.485089 |
| Dwight Smith Jr. | 24.0 | 29 | 449.0 | 0.0 | -0.757287 | -0.690031 | 89.534882 | 75 | 2.055471 |
| Jacob May | 25.0 | 42 | 467.0 | 0.0 | -0.985573 | -1.873969 | 102.478849 | 0 | Unobserved |

## Erik Kratz from 2016 to 2017

Player 456124, row 22991, fold 2, age 36.0, stage Current MLB. Selection: fixed_reliability rate largest harm, fixed_reliability rate false low, learned_reliability rate false low.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AAA | 100 | 3 | 18 | 9 |
| 2014 | MLB | 115 | 5 | 22 | 3 |
| 2015 | AAA | 202 | 7 | 34 | 26 |
| 2015 | MLB | 28 | 0 | 5 | 1 |
| 2016 | AAA | 109 | 0 | 23 | 8 |
| 2016 | MLB | 87 | 1 | 32 | 1 |

Weighted transported own MLB PA: 178.400000. Actual-fold active profile: [{'row_id': 22991, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 7.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'brief', 'active_profile_players': 3}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -2.297435 | 8.222939 | -0.006093 |
| fixed_reliability | -4.766104 | 8.222939 | -0.039926 |
| learned_reliability | -3.849422 | 8.222939 | -0.027363 |
| Actual | 37.132070 | 2 | 0.129926 |

Unchanged expected PA = participation 0.25016630 × conditional PA 32.869891. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 97.631571 | 0.474130 | 0.484104 | 100.000000 | 0.640805 | 0.524576 | 0.524576 | 0.0 | 0.000000 |
| K | 49.866460 | 0.211193 | 0.241962 | 100.000000 | 0.640805 | 0.266030 | 0.266030 | 0.0 | 0.000000 |
| UBB | 3.813125 | 0.076693 | 0.080494 | 100.000000 | 0.640805 | 0.042610 | 0.042610 | 0.0 | -1.187233 |
| HBP | 0.000000 | 0.008945 | 0.011260 | 100.000000 | 0.640805 | 0.004045 | 0.004045 | 0.0 | -0.177976 |
| 1B | 16.052116 | 0.149198 | 0.115806 | 100.000000 | 0.640805 | 0.099256 | 0.099256 | 1.0 | -2.204343 |
| 2B | 6.033121 | 0.044718 | 0.036069 | 100.000000 | 0.640805 | 0.034626 | 0.034626 | 1.0 | -0.626899 |
| 3B | 0.000000 | 0.004730 | 0.005852 | 100.000000 | 0.640805 | 0.002102 | 0.002102 | 0.0 | -0.205783 |
| HR | 5.003608 | 0.030393 | 0.024452 | 100.000000 | 0.640805 | 0.026756 | 0.026756 | 0.0 | -0.363870 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.19909200664424398, 'UBB': 0.13531410778131875, 'HBP': 0.2502960137683623, '1B': -0.05521000676315288, '2B': -0.029173549806557727, '3B': 0.30116461701162595, 'HR': 0.10885681445148702}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.039195629880731324, 'UBB': -0.055740025730370894, 'HBP': -0.17804124374690478, '1B': -0.08934233936117497, '2B': -0.1329877848504949, '3B': -0.00827225806779834, 'HR': -0.09547728050383451}}, {'feature': 'age_centered', 'scaled_input': 1.8, 'effects': {'K': -0.018140316974336733, 'UBB': 0.015475101127742277, 'HBP': 0.045389643263299764, '1B': -0.10604477048872141, '2B': -0.10043479333131546, '3B': -0.0864767128515237, 'HR': -0.15822454891280413}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08776678402666692, 'UBB': 0.01691303724585467, 'HBP': 0.06597684228370206, '1B': -0.022201513588803335, '2B': 0.0253208196857707, '3B': 0.02840273231389542, 'HR': 0.026404455694694868}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.3492336274965166, 'effects': {'K': -0.08495197951507068, 'UBB': -0.046384310736282706, 'HBP': -0.004177218319151735, '1B': 0.027259778214783606, '2B': -0.0037645187727787903, '3B': -0.0024047969071040783, 'HR': -0.05673534706595948}}, {'feature': 'position_2', 'scaled_input': 1.0, 'effects': {'K': 0.04699154441981884, 'UBB': -0.029642907352962225, 'HBP': -0.010064291456985803, '1B': -0.023376056626227378, '2B': 0.020431118454540882, '3B': -0.05914509028084741, 'HR': 0.008016308569050085}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.00912416439503658, 'UBB': -0.038098266596774774, 'HBP': 0.02070092335692473, '1B': 0.015290253339402173, '2B': -0.026346546802173822, '3B': -0.02072467632659364, 'HR': -0.04582998998542176}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.551, 'effects': {'K': 0.04095884832029105, 'UBB': -0.017396796327216538, 'HBP': 0.013134547476452353, '1B': -0.004438024682358576, '2B': 0.020472836379532986, '3B': -0.006168631070377274, 'HR': -0.004795670286527415}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.032377909223129366, 'UBB': 0.036140119574781235, 'HBP': -0.0008996935338455949, '1B': 0.005227290101531407, '2B': 0.009258992183798876, '3B': 0.02273502387043838, 'HR': -0.004214498090156554}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.6, 'effects': {'K': -0.03427125770608857, 'UBB': 0.012122112218883424, 'HBP': 0.009256455894167959, '1B': -0.007020242874527427, '2B': -0.009997382430932214, '3B': -0.007515626977142401, 'HR': -0.012153374905245989}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 97.631571 | 0.474130 | 0.484480 | 303.858160 | 0.369926 | 0.507705 | 0.500061 | 0.0 | 0.000000 |
| K | 49.866460 | 0.211193 | 0.247308 | 92.862885 | 0.657665 | 0.268493 | 0.264451 | 0.0 | 0.000000 |
| UBB | 3.813125 | 0.076693 | 0.074617 | 301.486992 | 0.371754 | 0.054824 | 0.053999 | 0.0 | -0.790521 |
| HBP | 0.000000 | 0.008945 | 0.007958 | 350.609009 | 0.337234 | 0.005274 | 0.005195 | 0.0 | -0.136207 |
| 1B | 16.052116 | 0.149198 | 0.123553 | 530.631288 | 0.251611 | 0.115105 | 0.113372 | 1.0 | -1.581270 |
| 2B | 6.033121 | 0.044718 | 0.037804 | 1693.226702 | 0.095318 | 0.037424 | 0.036861 | 1.0 | -0.488108 |
| 3B | 0.000000 | 0.004730 | 0.002904 | 711.054782 | 0.200572 | 0.002321 | 0.002287 | 0.0 | -0.191339 |
| HR | 5.003608 | 0.030393 | 0.021377 | 252.394733 | 0.414118 | 0.024139 | 0.023776 | 0.0 | -0.661978 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': 1.8, 'effects': {'K': -0.01089082949762378, 'UBB': 0.007980687824102578, 'HBP': -0.02910904227628312, '1B': -0.06758693290446889, '2B': -0.09281065156613187, '3B': -0.2446049687845168, 'HR': -0.2133998146258827}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1970265344403878, 'UBB': 0.13617641291749125, 'HBP': 0.03870373073879303, '1B': -0.010394874437104013, '2B': 0.09261277007193783, '3B': -0.0584269078953021, 'HR': 0.09142169340146644}}, {'feature': 'age_squared', 'scaled_input': 3.24, 'effects': {'K': 0.03508218164456163, 'UBB': -0.08477548411871363, 'HBP': -0.16645402490671948, '1B': -0.08310963576705026, '2B': -0.09195322171940473, '3B': -0.05410526934240983, 'HR': -0.0832770057896139}}, {'feature': 'position_2', 'scaled_input': 1.0, 'effects': {'K': 0.052762614075360384, 'UBB': -0.0159019381717599, 'HBP': -0.009796284964749493, '1B': -0.0321654433446884, '2B': -0.004666194532487744, '3B': -0.09549952633980836, 'HR': 0.012002890111101065}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.3492336274965166, 'effects': {'K': -0.09331303063448222, 'UBB': -0.05859580397512086, 'HBP': -0.0106645536960281, '1B': 0.026276323301650927, '2B': -0.027148836343579206, '3B': 0.003616438131092866, 'HR': -0.07690586563174874}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.07584250483543593, 'UBB': -0.010962420451361641, 'HBP': 0.011882584520479304, '1B': -0.02431383480421337, '2B': 0.01608176049321912, '3B': -0.0346968603897224, 'HR': 0.006862723965575824}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.011948346778482064, 'UBB': -0.0504235980840426, 'HBP': 0.02575244759713866, '1B': 0.016573413887141977, '2B': -0.06221923976698111, '3B': -0.02665547950076023, 'HR': -0.05750410666122067}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.18002786809103583, 'effects': {'K': 0.0048703459141415184, 'UBB': 0.047881830011320556, 'HBP': -0.00010035935179737261, '1B': -0.0033395993559095305, '2B': -0.0028685916822670148, '3B': -0.003845221435094145, 'HR': 0.005395181987803285}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.551, 'effects': {'K': 0.04562017377350872, 'UBB': -0.011884522071601218, 'HBP': 0.01999768601511862, '1B': -0.015278562260909458, '2B': -0.004263050478037594, '3B': 0.010737629260949, 'HR': -0.0038909066434455954}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.6, 'effects': {'K': -0.03502851337875062, 'UBB': 0.005290989843376984, 'HBP': -0.014760905543570776, '1B': 0.01329889771808907, '2B': 0.017650167064207738, '3B': -0.04284382648120481, 'HR': -0.015592050871262163}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Kratz has weak aging catcher history: 87 MLB PA with one HR and 32 K in 2016, following smaller MLB samples. The negative adaptive rate is plausible at origin. Actual +37.13 wins/600 comes from a single and a double in only two PA, not a 37-win true talent. Expected PA is eight versus two. The raw false-low leaderboard must not be interpreted as a significant talent failure. The three-person coarse active profile is sparse; Hanigan produces poorly, Martinez also struggles, Infante and Crawford never appear.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Ryan Hanigan | 35.0 | 113 | 31.0 | 8.0 | -1.585550 | -1.700558 | 34.396416 | 112 | -1.847903 |
| Omar Infante | 34.0 | 149 | 116.0 | 0.0 | -2.251114 | -2.551878 | 35.737781 | 0 | Unobserved |
| Michael Martinez | 33.0 | 106 | 114.0 | 0.0 | -1.794871 | -2.569360 | 31.524182 | 43 | -5.370513 |
| Carl Crawford | 34.0 | 87 | 8.0 | 0.0 | -0.980103 | -0.691778 | 23.651466 | 0 | Unobserved |

## Yasmany Tomás from 2018 to 2019

Player 630111, row 33310, fold 4, age 27.0, stage Upper minors. Selection: fixed_reliability rate false high, learned_reliability rate false high.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | MLB | 563 | 31 | 136 | 27 |
| 2017 | MLB | 180 | 8 | 50 | 13 |
| 2017 | RK121 | 7 | 1 | 2 | 0 |
| 2018 | AAA | 371 | 14 | 101 | 10 |

Weighted transported own MLB PA: 481.800000. Actual-fold active profile: [{'row_id': 33310, 'stage': 'Upper minors', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'intermediate', 'active_profile_players': 6}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.126568 | 40.655815 | 0.133746 |
| fixed_reliability | 0.680782 | 40.655815 | 0.171299 |
| learned_reliability | 0.154232 | 40.655815 | 0.135621 |
| Actual | -16.159458 | 6 | -0.143266 |

Unchanged expected PA = participation 0.20715367 × conditional PA 196.259213. For each arm contribution = expected PA × (batting rate/600 + 0.00307877). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 211.871467 | 0.465785 | 0.447235 | 100.000000 | 0.828120 | 0.441036 | 0.441036 | 3.0 | -0.000000 |
| K | 127.127212 | 0.222573 | 0.252346 | 100.000000 | 0.828120 | 0.261880 | 0.261880 | 3.0 | 0.000000 |
| UBB | 27.171942 | 0.079708 | 0.074957 | 100.000000 | 0.828120 | 0.059587 | 0.059587 | 0.0 | -0.700873 |
| HBP | 0.696521 | 0.010381 | 0.013765 | 100.000000 | 0.828120 | 0.003563 | 0.003563 | 0.0 | -0.247651 |
| 1B | 62.543856 | 0.142174 | 0.128244 | 100.000000 | 0.828120 | 0.129543 | 0.129543 | 0.0 | -0.557502 |
| 2B | 26.634296 | 0.044637 | 0.045184 | 100.000000 | 0.828120 | 0.053545 | 0.053545 | 0.0 | 0.553422 |
| 3B | 1.433072 | 0.004575 | 0.006259 | 100.000000 | 0.828120 | 0.003539 | 0.003539 | 0.0 | -0.081128 |
| HR | 24.321634 | 0.030167 | 0.032009 | 100.000000 | 0.828120 | 0.047306 | 0.047306 | 0.0 | 1.714513 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.22032100033660432, 'UBB': 0.013131216471728038, 'HBP': 0.19902090751589172, '1B': -0.028684158439422056, '2B': 0.015370071988364672, '3B': 0.33007708190544593, 'HR': 0.07103593166102039}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.1258873411721377, 'UBB': 0.012019229356721551, 'HBP': 0.0798298611085762, '1B': -0.010573568438205536, '2B': 0.010947550454343173, '3B': 0.02194801024160164, 'HR': 0.015803456693082567}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.33269639065817397, 'effects': {'K': 0.08390363506646908, 'UBB': 0.028769362130722335, 'HBP': 0.00428423192699681, '1B': -0.017172894574810197, '2B': 0.00881820850803536, '3B': -0.0008924863158156451, 'HR': 0.04520389586319643}}, {'feature': 'pooled_AAA_BB', 'scaled_input': -0.4178343949044586, 'effects': {'K': -0.011985451283149236, 'UBB': -0.07654723524992853, 'HBP': -0.0015106356791870096, '1B': 0.0028000757515671522, '2B': -0.006397327548180776, '3B': 0.003232621699927322, 'HR': -0.014419850611115047}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.6183333333333333, 'effects': {'K': 0.061906565069940994, 'UBB': 0.00214944407478348, 'HBP': 0.01432490117900211, '1B': 0.0008897917914299561, '2B': 0.027673540519176348, '3B': 0.002300218284564597, 'HR': 0.02419150143102508}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.030827139036947074, 'UBB': -0.01817467473005277, 'HBP': 0.014520424042104935, '1B': 0.012857654316303126, '2B': -0.0028987384508342238, '3B': -0.021420911038807857, 'HR': -0.03835669843118177}}, {'feature': 'position_7', 'scaled_input': 1.0, 'effects': {'K': -0.0013762866902122003, 'UBB': 0.00822120249535741, 'HBP': 0.0038551554293985305, '1B': -0.01958876090450412, '2B': 0.01282369541769685, '3B': 0.005351462758176019, 'HR': 0.015764673854139693}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.008960000740311603, 'UBB': 0.018752264857209, 'HBP': 0.0008992358828576349, '1B': 0.003686487985384587, '2B': -0.00029972142311680627, '3B': 0.001654964565310264, 'HR': 0.009061395736173369}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.013538759498797707, 'UBB': -0.007232472890323172, 'HBP': -0.0056854471226090615, '1B': -0.006808580293935448, '2B': -0.014120663276363405, '3B': 0.0036198437981497557, 'HR': -0.010490606078111163}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': -0.013359902543717163, 'UBB': -0.002922242422262468, 'HBP': 0.005601691718856099, '1B': 0.0036720863830730127, '2B': 0.004388785581914223, '3B': 0.002533297589264131, 'HR': -0.00893888612104606}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 211.871467 | 0.465785 | 0.445712 | 316.294013 | 0.603688 | 0.442113 | 0.442993 | 3.0 | -0.000000 |
| K | 127.127212 | 0.222573 | 0.259226 | 100.727589 | 0.827085 | 0.263058 | 0.263581 | 3.0 | 0.000000 |
| UBB | 27.171942 | 0.079708 | 0.072683 | 287.683734 | 0.626134 | 0.062486 | 0.062610 | 0.0 | -0.595568 |
| HBP | 0.696521 | 0.010381 | 0.010936 | 321.238520 | 0.599971 | 0.005242 | 0.005252 | 0.0 | -0.186294 |
| 1B | 62.543856 | 0.142174 | 0.130327 | 541.729293 | 0.470724 | 0.130085 | 0.130344 | 0.0 | -0.522150 |
| 2B | 26.634296 | 0.044637 | 0.046333 | 1590.991749 | 0.232440 | 0.048413 | 0.048509 | 0.0 | 0.240567 |
| 3B | 1.433072 | 0.004575 | 0.004105 | 659.636098 | 0.422100 | 0.003628 | 0.003635 | 0.0 | -0.073596 |
| HR | 24.321634 | 0.030167 | 0.030678 | 293.178106 | 0.621695 | 0.042989 | 0.043075 | 0.0 | 1.291275 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.2164313417583085, 'UBB': 0.03330393709436172, 'HBP': -0.002734127600577575, '1B': -0.013623410655848217, '2B': 0.06775351202378173, '3B': -0.033385038179851424, 'HR': 0.06755384424065199}}, {'feature': 'pooled_AAA_BB', 'scaled_input': -0.4178343949044586, 'effects': {'K': -0.01680158417952784, 'UBB': -0.11144057880829274, 'HBP': -0.002975648996484783, '1B': 0.014632827676825305, '2B': -0.003118313639849308, '3B': 0.005800978227967536, 'HR': -0.017222971499615415}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10873794198653433, 'UBB': -0.006154124630769936, 'HBP': 0.023638870247426707, '1B': -0.01232161765399087, '2B': -0.0005050511907572074, '3B': -0.037568934078827554, 'HR': -0.008272121052143346}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.33269639065817397, 'effects': {'K': 0.09326901714103653, 'UBB': 0.041560470547543, 'HBP': 0.012599947790223354, '1B': -0.013569999179835384, '2B': 0.0224836259265483, '3B': -0.0026999566903123298, 'HR': 0.06725035382011452}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.6183333333333333, 'effects': {'K': 0.06835352818681165, 'UBB': 5.82506656141472e-05, 'HBP': 0.022032899972099715, '1B': -0.006553221161099047, '2B': 0.007082954916859938, '3B': 0.017737748991539744, 'HR': 0.028242776676158106}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.03334118287515905, 'UBB': -0.022133515849544653, 'HBP': 0.02431112955996878, '1B': 0.013031711964822524, '2B': -0.03652854104156128, '3B': -0.026079095970227534, 'HR': -0.057762002908314826}}, {'feature': 'position_7', 'scaled_input': 1.0, 'effects': {'K': 0.0035073774772427808, 'UBB': 0.016214972231409455, 'HBP': 0.011687602466535782, '1B': -0.011976802461048314, '2B': 0.026444446169749, '3B': 0.014197469115431951, 'HR': 0.030022841340607963}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.010000355690497603, 'UBB': 0.020563478563177827, 'HBP': 0.00165189497743004, '1B': 0.001773478547156194, '2B': 0.004041417369269834, '3B': 0.0007773639406494982, 'HR': 0.0025679176813453875}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.3, 'effects': {'K': -0.01373969731586905, 'UBB': 0.0022713443669132942, 'HBP': -0.006508191469210054, '1B': -0.0028649575343350294, '2B': 0.003292632206504966, '3B': -0.018552207375650914, 'HR': -0.004699380218752799}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.017551814590409665, 'UBB': -0.006703475820609961, 'HBP': -0.005590416609885235, '1B': -0.010881137061840842, '2B': -0.010151658100254, '3B': 8.311106515997946e-05, 'HR': -0.015660530644159787}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Tomas has older MLB power (31 HR in 563 PA in 2016), then 14 AAA HR in 371 PA in 2018. Adaptive rate nearly returns to the old rate and retains 4.31% HR with low 6.26% walks. The future -16.16 rate is based on six PA without hits. Expected PA 41 versus six is a genuine opportunity miss, but six unsuccessful PA do not establish that his forecast ability was absurd. The re-entry profile has only six distinct active people. Puello succeeds; Liriano never appears, Tovar and Tejada struggle.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| César Puello | 27.0 | 0 | 358.0 | 0.0 | -0.359839 | -0.449022 | 10.416249 | 147 | 0.131764 |
| Rymer Liriano | 27.0 | 0 | 404.0 | 0.0 | -0.602229 | -0.921961 | 6.669268 | 0 | Unobserved |
| Wilfredo Tovar | 26.0 | 0 | 389.0 | 0.0 | -1.080730 | -0.681855 | 2.274481 | 88 | -5.133435 |
| Rubén Tejada | 28.0 | 0 | 392.0 | 0.0 | -1.384219 | -1.175340 | 17.632561 | 9 | -16.159458 |

## Hernán Pérez from 2016 to 2017

Player 541650, row 23512, fold 4, age 25.0, stage Current MLB. Selection: fixed_reliability rate ordinary.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | AAA | 596 | 6 | 65 | 35 |
| 2014 | MLB | 6 | 0 | 1 | 1 |
| 2015 | MLB | 272 | 1 | 59 | 4 |
| 2016 | AAA | 67 | 1 | 10 | 3 |
| 2016 | MLB | 430 | 13 | 94 | 18 |

Weighted transported own MLB PA: 651.200000. Actual-fold active profile: [{'row_id': 23512, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'intermediate', 'active_profile_players': 194}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.792800 | 340.302613 | 0.601233 |
| fixed_reliability | -1.081267 | 340.302613 | 0.437622 |
| learned_reliability | -1.088527 | 340.302613 | 0.433505 |
| Actual | -1.080773 | 458 | 0.583899 |

Unchanged expected PA = participation 0.96824177 × conditional PA 351.464505. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 322.780836 | 0.474130 | 0.477151 | 100.000000 | 0.866880 | 0.493205 | 0.493205 | 248.0 | 0.000000 |
| K | 143.942316 | 0.211193 | 0.196721 | 100.000000 | 0.866880 | 0.217804 | 0.217804 | 79.0 | 0.000000 |
| UBB | 22.115846 | 0.076693 | 0.074354 | 100.000000 | 0.866880 | 0.039339 | 0.039339 | 19.0 | -1.301171 |
| HBP | 1.000000 | 0.008945 | 0.012271 | 100.000000 | 0.866880 | 0.002965 | 0.002965 | 0.0 | -0.217202 |
| 1B | 112.888284 | 0.149198 | 0.156804 | 100.000000 | 0.866880 | 0.171151 | 0.171151 | 76.0 | 0.968946 |
| 2B | 30.062034 | 0.044718 | 0.046010 | 100.000000 | 0.866880 | 0.046143 | 0.046143 | 19.0 | 0.088571 |
| 3B | 4.493056 | 0.004730 | 0.006917 | 100.000000 | 0.866880 | 0.006902 | 0.006902 | 3.0 | 0.170131 |
| HR | 13.917629 | 0.030393 | 0.029773 | 100.000000 | 0.866880 | 0.022491 | 0.022491 | 14.0 | -0.790542 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.27884136811108734, 'UBB': 0.09932720087021965, 'HBP': 0.19828282447530765, '1B': -0.04059226476644232, '2B': -0.00231439369977951, '3B': 0.3329452345732168, 'HR': 0.09644696391778536}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.9275257338924894, 'effects': {'K': -0.22599283152839125, 'UBB': -0.10508240257629116, 'HBP': 0.006986274641780941, '1B': 0.05977171881516384, '2B': -0.02339427326316959, '3B': 0.0038286493344621866, 'HR': -0.1372418157519661}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.12024730549413426, 'UBB': 0.013754394388738902, 'HBP': 0.07923921130721245, '1B': -0.0163000008089512, '2B': 0.011393817997638108, '3B': 0.027405922314907738, 'HR': -0.004135997688806723}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.04957536666847617, 'UBB': 0.019541069443919996, 'HBP': 0.021582056348000443, '1B': -0.004366761645815426, '2B': 0.01076959432008264, '3B': -0.006633119332505006, 'HR': 0.07729408705106816}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.7076666666666666, 'effects': {'K': 0.049282960831673335, 'UBB': -0.010352703529292608, 'HBP': 0.00641486664883979, '1B': 0.0016003493947829384, '2B': 0.024055807162904695, '3B': -0.003414610749523249, 'HR': -0.004935028669309549}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.01899586220485565, 'UBB': -0.02089307532343702, 'HBP': 0.018159206288028185, '1B': 0.006662316675055164, '2B': -0.007562275543231602, '3B': -0.030134807763894374, 'HR': -0.03220821503210097}}, {'feature': 'pooled_AAA_BB', 'scaled_input': -0.1900114372855508, 'effects': {'K': -0.0072267740330737825, 'UBB': -0.03171835511202575, 'HBP': 0.00048118794182818304, '1B': -0.0017920282234317934, '2B': -0.002474777868310385, '3B': 0.0020788612447949985, 'HR': -0.00529741957377403}}, {'feature': 'age_centered', 'scaled_input': -0.4, 'effects': {'K': -0.00013071106283015288, 'UBB': -3.342503161398579e-05, 'HBP': -0.012034880279809928, '1B': 0.02579446434603241, '2B': 0.0202352592125737, '3B': 0.011746738996524618, 'HR': 0.03128593868776173}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.020889223524098586, 'UBB': 0.031049401643576967, 'HBP': -0.004332448539062348, '1B': 0.006357514356407625, '2B': 0.004930985044411555, '3B': 0.008848614830782194, 'HR': 0.009402991479194179}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.4, 'effects': {'K': -0.024040260622154547, 'UBB': 0.007668888260543617, 'HBP': 0.007060773049318706, '1B': -0.006557171680908053, '2B': -0.004497145430252683, '3B': -0.0019035863105061471, 'HR': -0.004699463982809573}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 322.780836 | 0.474130 | 0.484881 | 331.005848 | 0.662997 | 0.492035 | 0.491365 | 248.0 | 0.000000 |
| K | 143.942316 | 0.211193 | 0.198121 | 89.848689 | 0.878755 | 0.218263 | 0.217966 | 79.0 | 0.000000 |
| UBB | 22.115846 | 0.076693 | 0.068151 | 296.085653 | 0.687438 | 0.044648 | 0.044587 | 19.0 | -1.118347 |
| HBP | 1.000000 | 0.008945 | 0.009674 | 326.944999 | 0.665750 | 0.004256 | 0.004250 | 0.0 | -0.170514 |
| 1B | 112.888284 | 0.149198 | 0.161790 | 605.831317 | 0.518046 | 0.167781 | 0.167553 | 76.0 | 0.810122 |
| 2B | 30.062034 | 0.044718 | 0.045398 | 1723.494572 | 0.274225 | 0.045608 | 0.045546 | 19.0 | 0.051441 |
| 3B | 4.493056 | 0.004730 | 0.004618 | 659.530617 | 0.496822 | 0.005751 | 0.005744 | 3.0 | 0.079405 |
| HR | 13.917629 | 0.030393 | 0.027368 | 246.946991 | 0.725048 | 0.023021 | 0.022989 | 14.0 | -0.740635 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.28341273713995685, 'UBB': 0.10355912089675476, 'HBP': 0.007074270761716113, '1B': -0.0010573261882780348, '2B': 0.0724366301591232, '3B': -0.03549579154287614, 'HR': 0.08389429024988546}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.9275257338924894, 'effects': {'K': -0.25082851815936485, 'UBB': -0.14426561992046613, 'HBP': -0.01563369880239864, '1B': 0.05590639478507537, '2B': -0.06911546825461627, '3B': 0.014987823392673742, 'HR': -0.194137638665913}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10447136535540179, 'UBB': -0.012947232030750508, 'HBP': 0.024540323497720326, '1B': -0.018700294089456726, '2B': -0.003125093621330238, '3B': -0.03622635648329068, 'HR': -0.024359127684870974}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.042591004102918426, 'UBB': 0.00379760711776919, 'HBP': 0.017716102740759763, '1B': 0.007808321187734954, '2B': 0.022425126301267754, '3B': -0.02632684919453532, 'HR': 0.09665660639165152}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.7076666666666666, 'effects': {'K': 0.054873185828346056, 'UBB': -0.005242284206073559, 'HBP': 0.013377018835136822, '1B': -0.01298399872855119, '2B': 0.007370375017645965, '3B': 0.012480464565947529, 'HR': 0.006050960922969322}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.021532690601063553, 'UBB': -0.023249246379418147, 'HBP': 0.02521575785524354, '1B': 0.0010697432878296858, '2B': -0.05067226926992777, '3B': -0.03512762095083585, 'HR': -0.045286757082793457}}, {'feature': 'pooled_AAA_BB', 'scaled_input': -0.1900114372855508, 'effects': {'K': -0.00892134232764426, 'UBB': -0.0468051312630133, 'HBP': 5.8516798894403044e-05, '1B': 0.003546540266710744, '2B': 0.0002248276359356268, '3B': 0.003326454893744339, 'HR': -0.006325492874657068}}, {'feature': 'age_centered', 'scaled_input': -0.4, 'effects': {'K': -0.0012838294724377998, 'UBB': 0.004456460632242552, 'HBP': 0.0005408027711742545, '1B': 0.015342465535356169, '2B': 0.018140830617538618, '3B': 0.04677221410595836, 'HR': 0.0445441907820473}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.02133640155342741, 'UBB': 0.03149947441612812, 'HBP': -0.00409721273624043, '1B': 0.003988100903450228, '2B': 0.00623100084896586, '3B': 0.005160718046466387, 'HR': 0.0002273943378135058}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.4, 'effects': {'K': -0.023578568286155666, 'UBB': 0.0029288908850684035, 'HBP': -0.006668785775893262, '1B': 0.0039489522364915906, '2B': 0.006128399765188755, '3B': -0.02462016461658876, 'HR': -0.007932503954000698}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Perez's 430-PA season supplies 13 HR, 94 K and only 18 walks. Adaptive -1.09 is near actual -1.08, better than old -0.79. Yet final K 21.8% is too high and HR 2.30% too low, showing event errors can offset even when combined rate is right. Expected PA 340 versus 458 leaves value low. Avisail Garcia and Puig improve while Diaz and Iglesias struggle. The 194-person coarse profile supports this ordinary exposure range, not causal proof of each learned component.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Avisaíl García | 25.0 | 453 | 14.0 | 0.0 | 0.123440 | -0.321980 | 370.545535 | 561 | 2.740741 |
| Yasiel Puig | 25.0 | 368 | 75.0 | 0.0 | 1.223064 | 1.313982 | 434.310908 | 570 | 1.318632 |
| Aledmys Díaz | 25.0 | 460 | 0.0 | 0.0 | -0.016444 | 1.137017 | 550.492117 | 301 | -1.442416 |
| Jose Iglesias | 26.0 | 513 | 16.0 | 0.0 | -1.008741 | -0.744663 | 322.987973 | 489 | -1.807470 |

## Aaron Judge from 2023 to 2024

Player 592450, row 50698, fold 3, age 31.0, stage Current MLB. Selection: fixed_reliability value largest gain, learned_reliability value largest gain.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | MLB | 633 | 39 | 158 | 73 |
| 2022 | MLB | 696 | 62 | 175 | 92 |
| 2023 | MLB | 458 | 37 | 130 | 79 |

Weighted transported own MLB PA: 1394.600000. Actual-fold active profile: [{'row_id': 50698, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 173}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 3.399637 | 524.328479 | 4.594239 |
| fixed_reliability | 4.949290 | 524.328479 | 5.948451 |
| learned_reliability | 4.292751 | 524.328479 | 5.374713 |
| Actual | 7.557649 | 704 | 11.066146 |

Unchanged expected PA = participation 0.98536513 × conditional PA 532.115928. For each arm contribution = expected PA × (batting rate/600 + 0.00309608). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 485.135584 | 0.456074 | 0.446638 | 100.000000 | 0.933092 | 0.354476 | 0.354476 | 231.0 | -0.000000 |
| K | 363.199045 | 0.227279 | 0.252310 | 100.000000 | 0.933092 | 0.259889 | 0.259889 | 171.0 | 0.000000 |
| UBB | 199.728467 | 0.083350 | 0.083319 | 100.000000 | 0.933092 | 0.139208 | 0.139208 | 113.0 | 1.945728 |
| HBP | 6.617792 | 0.011472 | 0.014526 | 100.000000 | 0.933092 | 0.005400 | 0.005400 | 9.0 | -0.220550 |
| 1B | 172.022436 | 0.141393 | 0.126820 | 100.000000 | 0.933092 | 0.123581 | 0.123581 | 85.0 | -0.786165 |
| 2B | 53.561720 | 0.044692 | 0.041165 | 100.000000 | 0.933092 | 0.038591 | 0.038591 | 36.0 | -0.379012 |
| 3B | 0.000000 | 0.003867 | 0.005237 | 100.000000 | 0.933092 | 0.000350 | 0.000350 | 1.0 | -0.275439 |
| HR | 114.334958 | 0.031873 | 0.029985 | 100.000000 | 0.933092 | 0.078505 | 0.078505 | 58.0 | 4.664729 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.12138533968629973, 'UBB': 0.05502311724750755, 'HBP': 0.18031684986261767, '1B': -0.02635652569664262, '2B': -0.02257609381568395, '3B': 0.3205408036532428, 'HR': 0.07825841434234707}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10283322984543719, 'UBB': -0.0016758842422859698, 'HBP': 0.05485789618338382, '1B': -0.01572111188238408, '2B': 0.01051790423114404, '3B': 0.028967570583964722, 'HR': 0.03350869339894221}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.04240776307498913, 'UBB': 0.06589186996384695, 'HBP': 0.02370606068419897, '1B': -0.024473610162311317, '2B': 0.014400301162420666, '3B': 0.022396241239901308, 'HR': 0.009728392995238923}}, {'feature': 'age_centered', 'scaled_input': 0.8, 'effects': {'K': 0.026733274033431773, 'UBB': -0.008456613656587841, 'HBP': 0.03179069308765722, '1B': -0.023581858976509, '2B': -0.03421438007045768, '3B': -0.022362244987719472, 'HR': -0.06463918007290896}}, {'feature': 'scout_listed_2', 'scaled_input': -1.0, 'effects': {'K': -0.013097767892755238, 'UBB': -0.007772339114592185, 'HBP': -0.006209571554794671, '1B': -0.004999511308845608, '2B': -0.015946087337054528, '3B': -0.017169650253366232, 'HR': -0.052272446130957724}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.0075682181773970725, 'UBB': 0.017652235966454995, 'HBP': -0.004520327798375074, '1B': 0.015337518428897147, '2B': -0.004676318999591895, '3B': -0.0005015099001059508, 'HR': 0.04772131143768288}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 0.99, 'effects': {'K': -0.035518327967783675, 'UBB': -0.007315255307733647, 'HBP': -0.009732386684294185, '1B': 0.015082235514561853, '2B': 0.004031750471803804, '3B': 0.005839034522890695, 'HR': -0.010463824893567368}}, {'feature': 'scout_rank_score_2', 'scaled_input': -1.0, 'effects': {'K': 0.017752336270881387, 'UBB': -0.022898350721546157, 'HBP': -0.004539454311469989, '1B': -0.008961818298394908, '2B': 0.0012569739581312985, '3B': -0.014940697977337821, 'HR': -0.035129799612101005}}, {'feature': 'draft_elapsed', 'scaled_input': 1.0, 'effects': {'K': 0.030327759861944727, 'UBB': -0.023850214784372492, 'HBP': -0.012744414641212481, '1B': 0.009016145812840652, '2B': -0.004243313580634297, '3B': 0.0021210749354320917, 'HR': -0.00169117433982353}}, {'feature': 'age_squared', 'scaled_input': 0.6400000000000001, 'effects': {'K': 0.008781092784260607, 'UBB': 0.006979930011409238, 'HBP': -0.029105318596221418, '1B': -0.00807433963844622, '2B': -0.01620326040102299, '3B': 0.006508969796420761, 'HR': -0.007110050723466417}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 485.135584 | 0.456074 | 0.448338 | 322.195912 | 0.812327 | 0.366723 | 0.364689 | 231.0 | -0.000000 |
| K | 363.199045 | 0.227279 | 0.252682 | 100.709544 | 0.932650 | 0.259910 | 0.258469 | 171.0 | 0.000000 |
| UBB | 199.728467 | 0.083350 | 0.082435 | 265.587812 | 0.840025 | 0.133492 | 0.132752 | 113.0 | 1.720844 |
| HBP | 6.617792 | 0.011472 | 0.011659 | 285.164941 | 0.830235 | 0.005919 | 0.005886 | 9.0 | -0.202879 |
| 1B | 172.022436 | 0.141393 | 0.130992 | 497.117055 | 0.737214 | 0.125357 | 0.124662 | 85.0 | -0.738445 |
| 2B | 53.561720 | 0.044692 | 0.043636 | 1619.238119 | 0.462732 | 0.041216 | 0.040988 | 36.0 | -0.230128 |
| 3B | 0.000000 | 0.003867 | 0.003291 | 672.147898 | 0.674780 | 0.001070 | 0.001064 | 1.0 | -0.219523 |
| HR | 114.334958 | 0.031873 | 0.026966 | 313.453896 | 0.816485 | 0.071887 | 0.071489 | 58.0 | 3.962881 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.11903710133413437, 'UBB': 0.07052372941856494, 'HBP': 0.01573346810955311, '1B': 0.0031879954083284066, '2B': 0.06348861951039163, '3B': -0.017381967259760246, 'HR': 0.05822480818844724}}, {'feature': 'age_centered', 'scaled_input': 0.8, 'effects': {'K': 0.02538227389280702, 'UBB': -0.013090367287648933, 'HBP': 0.010195112342124986, '1B': -0.015377243783518313, '2B': -0.03390848023483031, '3B': -0.09437190336785725, 'HR': -0.09781017651845132}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08776559625395317, 'UBB': -0.012735505366707702, 'HBP': 0.004250057355748144, '1B': -0.022478049781444145, '2B': 0.005501557439719756, '3B': -0.03189915889994659, 'HR': 0.007166771728794253}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.04314437340173541, 'UBB': 0.06975251694145626, 'HBP': 0.038691119879812226, '1B': -0.02514171940867766, '2B': 0.0012633370642957302, '3B': 0.04460537191065561, 'HR': 0.013127681227465951}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.008320576676014577, 'UBB': 0.022952728123653978, 'HBP': -0.003072151320125301, '1B': 0.007930051687609591, '2B': 0.020979692552523695, '3B': 0.002085629972995141, 'HR': 0.05378335760428933}}, {'feature': 'scout_listed_2', 'scaled_input': -1.0, 'effects': {'K': -0.009540177132556216, 'UBB': -0.004555011518858202, 'HBP': -0.0020580431757638283, '1B': -0.010782478343043743, '2B': -0.011847232128368992, '3B': -0.006604587499459279, 'HR': -0.052189682325341775}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.7, 'effects': {'K': -0.01912744867662609, 'UBB': 0.008544663942445326, 'HBP': -0.013727914995904575, '1B': 0.0006810939793813689, '2B': 0.011315632092742979, '3B': -0.04659357905138084, 'HR': -0.009312356255433776}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 0.99, 'effects': {'K': -0.03615446558945776, 'UBB': -0.013994694650895945, 'HBP': -0.0052579732409108754, '1B': 0.011388595657243768, '2B': -0.007713686333078643, '3B': 0.005452065296800848, 'HR': -0.014348766585645129}}, {'feature': 'scout_rank_score_2', 'scaled_input': -1.0, 'effects': {'K': 0.016844178570573364, 'UBB': -0.02108304149088874, 'HBP': -0.0013720671109155, '1B': -0.006166633734968598, '2B': -0.014237232519042057, '3B': -0.006269605059805265, 'HR': -0.03296641800705542}}, {'feature': 'draft_elapsed', 'scaled_input': 1.0, 'effects': {'K': 0.02705442978656803, 'UBB': -0.032874043710274574, 'HBP': -0.025392296014248195, '1B': 0.029028972377363856, '2B': 0.0023039870718287404, '3B': 0.0007168813551333638, 'HR': 0.003072574352638043}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Judge had 39, 62 and 37 HR in the three known MLB seasons. His 1,395 weighted PA anchor retains 81.6% pre-normalization HR influence; final HR is 7.15% versus actual 8.24%. Both new arms improve rate and value over old 3.40; fixed 4.95 beats adaptive 4.29 here, but actual is 7.56. Expected PA remains 524 versus 704. This is both arms' largest primary PA-weighted rate gain as well as a consequential value gain, unlike one-to-three-PA extrema. Joe/Ward produce modestly, Grichuk/Trout produce stronger rates with fewer PA; these are not elite power matches.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Connor Joe | 30.0 | 472 | 0.0 | 0.0 | 0.392870 | 0.302987 | 393.910872 | 416 | -0.183000 |
| Randal Grichuk | 31.0 | 471 | 36.0 | 0.0 | -0.341906 | -0.238303 | 353.060752 | 279 | 3.176388 |
| Taylor Ward | 29.0 | 409 | 0.0 | 0.0 | 0.859894 | 1.168730 | 510.027929 | 663 | 0.839669 |
| Mike Trout | 31.0 | 362 | 0.0 | 0.0 | 1.158138 | 2.548870 | 414.666245 | 126 | 2.607406 |

## Miguel Andujar from 2018 to 2019

Player 609280, row 33062, fold 4, age 23.0, stage Current MLB. Selection: fixed_reliability value largest harm.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 319 | 2 | 42 | 21 |
| 2016 | Aplus | 251 | 10 | 30 | 18 |
| 2017 | AA | 272 | 7 | 38 | 12 |
| 2017 | AAA | 250 | 9 | 33 | 16 |
| 2017 | MLB | 8 | 0 | 0 | 1 |
| 2018 | MLB | 606 | 27 | 97 | 23 |

Weighted transported own MLB PA: 612.400000. Actual-fold active profile: [{'row_id': 33062, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': '21plus', 'own_mlb_exposure': 'intermediate', 'active_profile_players': 27}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.972246 | 567.344400 | 2.666052 |
| fixed_reliability | 2.235209 | 567.344400 | 3.860278 |
| learned_reliability | 1.259802 | 567.344400 | 2.937958 |
| Actual | -10.043989 | 49 | -0.670576 |

Unchanged expected PA = participation 0.99307234 × conditional PA 571.302190. For each arm contribution = expected PA × (batting rate/600 + 0.00307877). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 314.423031 | 0.465785 | 0.490605 | 100.000000 | 0.859629 | 0.510224 | 0.510224 | 31.0 | 0.000000 |
| K | 97.000000 | 0.222573 | 0.186706 | 100.000000 | 0.859629 | 0.162367 | 0.162367 | 11.0 | -0.000000 |
| UBB | 23.803240 | 0.079708 | 0.070805 | 100.000000 | 0.859629 | 0.043352 | 0.043352 | 1.0 | -1.266393 |
| HBP | 4.000000 | 0.010381 | 0.013328 | 100.000000 | 0.859629 | 0.007486 | 0.007486 | 0.0 | -0.105179 |
| 1B | 95.581768 | 0.142174 | 0.155890 | 100.000000 | 0.859629 | 0.156051 | 0.156051 | 6.0 | 0.612489 |
| 2B | 48.591962 | 0.044637 | 0.046008 | 100.000000 | 0.859629 | 0.074667 | 0.074667 | 0.0 | 1.865554 |
| 3B | 2.000000 | 0.004575 | 0.006950 | 100.000000 | 0.859629 | 0.003783 | 0.003783 | 0.0 | -0.062022 |
| HR | 27.000000 | 0.030167 | 0.029708 | 100.000000 | 0.859629 | 0.042070 | 0.042070 | 0.0 | 1.190761 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.22032100033660432, 'UBB': 0.013131216471728038, 'HBP': 0.19902090751589172, '1B': -0.028684158439422056, '2B': 0.015370071988364672, '3B': 0.33007708190544593, 'HR': 0.07103593166102039}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.7557956777996072, 'effects': {'K': -0.18024334522463234, 'UBB': -0.08095447357840717, 'HBP': -0.03641047459408406, '1B': -0.015247501930225272, '2B': -0.043367290596013304, '3B': -0.005001569689121313, 'HR': -0.12076239813541814}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.6533333333333332, 'effects': {'K': -0.16476596415222636, 'UBB': -0.056495903732392334, 'HBP': -0.008413170699269041, '1B': 0.03372331281787234, '2B': -0.01731677806057844, '3B': 0.0017526221384989813, 'HR': -0.08876925867915003}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.1258873411721377, 'UBB': 0.012019229356721551, 'HBP': 0.0798298611085762, '1B': -0.010573568438205536, '2B': 0.010947550454343173, '3B': 0.02194801024160164, 'HR': 0.015803456693082567}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.663926576217079, 'effects': {'K': -0.09206200020929768, 'UBB': -0.05395897506522339, 'HBP': -0.01702066123337851, '1B': 0.019345343685160738, '2B': -0.0182831528456459, '3B': 0.0040662357651013335, 'HR': -0.07317599380142642}}, {'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': -0.005147797043834016, 'UBB': 0.023819827145952318, 'HBP': -0.028438307218244942, '1B': 0.031069416191787776, '2B': 0.05126587156529905, '3B': 0.021549087258022077, 'HR': 0.07711810661455314}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.6816666666666666, 'effects': {'K': 0.0687377063093476, 'UBB': -0.012949406336955698, 'HBP': -0.01961217263864654, '1B': -0.008323119919016016, '2B': -0.006152702703492104, '3B': -0.005160866039815304, 'HR': -0.01800628433469868}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.02373768766003688, 'UBB': 0.021584474536269854, 'HBP': 0.03536082753009518, '1B': -0.01518158584578122, '2B': 0.005073418939664174, '3B': -0.009252058482998506, 'HR': 0.0624928033704399}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.04436385803879152, 'UBB': 0.019389708414451253, 'HBP': 0.0060192012708811795, '1B': -0.00810991837583521, '2B': -0.006629631304543208, '3B': 0.000937686028484112, 'HR': 0.05332440763322694}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.030827139036947074, 'UBB': -0.01817467473005277, 'HBP': 0.014520424042104935, '1B': 0.012857654316303126, '2B': -0.0028987384508342238, '3B': -0.021420911038807857, 'HR': -0.03835669843118177}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 314.423031 | 0.465785 | 0.498517 | 316.294013 | 0.659421 | 0.508349 | 0.517883 | 31.0 | 0.000000 |
| K | 97.000000 | 0.222573 | 0.188269 | 100.727589 | 0.858752 | 0.162613 | 0.165663 | 11.0 | -0.000000 |
| UBB | 23.803240 | 0.079708 | 0.066901 | 287.683734 | 0.680381 | 0.047828 | 0.048725 | 1.0 | -1.079212 |
| HBP | 4.000000 | 0.010381 | 0.010986 | 321.238520 | 0.655928 | 0.008064 | 0.008215 | 0.0 | -0.078670 |
| 1B | 95.581768 | 0.142174 | 0.155230 | 541.729293 | 0.530616 | 0.155680 | 0.158599 | 6.0 | 0.724966 |
| 2B | 48.591962 | 0.044637 | 0.046813 | 1590.991749 | 0.277935 | 0.055855 | 0.056903 | 0.0 | 0.761995 |
| 3B | 2.000000 | 0.004575 | 0.005324 | 659.636098 | 0.481433 | 0.004333 | 0.004414 | 0.0 | -0.012588 |
| HR | 27.000000 | 0.030167 | 0.027961 | 293.178106 | 0.676253 | 0.038868 | 0.039596 | 0.0 | 0.943311 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.2164313417583085, 'UBB': 0.03330393709436172, 'HBP': -0.002734127600577575, '1B': -0.013623410655848217, '2B': 0.06775351202378173, '3B': -0.033385038179851424, 'HR': 0.06755384424065199}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.6533333333333332, 'effects': {'K': -0.18315725561352753, 'UBB': -0.08161447349642587, 'HBP': -0.024743177626085078, '1B': 0.026648118363873294, '2B': -0.04415227421900092, '3B': 0.005302046411888387, 'HR': -0.1320630432515995}}, {'feature': 'pooled_AA_K', 'scaled_input': -0.7557956777996072, 'effects': {'K': -0.18229259831027025, 'UBB': -0.08780417319837579, 'HBP': -0.03685044489866422, '1B': -0.020290633282101546, '2B': -0.04842089639859272, '3B': 0.01001487470260215, 'HR': -0.12773246856582898}}, {'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': -0.007180747880256977, 'UBB': 0.0268898186801802, 'HBP': -0.0016701594149335264, '1B': 0.017071685882150113, '2B': 0.04573432323277599, '3B': 0.0975284610080088, 'HR': 0.10963801688222788}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10873794198653433, 'UBB': -0.006154124630769936, 'HBP': 0.023638870247426707, '1B': -0.01232161765399087, '2B': -0.0005050511907572074, '3B': -0.037568934078827554, 'HR': -0.008272121052143346}}, {'feature': 'pooled_Aplus_K', 'scaled_input': -0.663926576217079, 'effects': {'K': -0.09298746927155305, 'UBB': -0.05353379849594614, 'HBP': -0.015036600047913398, '1B': 0.01562299590368313, '2B': -0.009547979443475534, '3B': 0.018690755984869474, 'HR': -0.07746458765916832}}, {'feature': 'position_5', 'scaled_input': 1.0, 'effects': {'K': 0.017765517707164787, 'UBB': 0.01666023810832269, 'HBP': 0.030306083823686485, '1B': -0.004952302229678547, '2B': 0.02115855238079087, '3B': -0.02788922050287999, 'HR': 0.08572979401965505}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.6816666666666666, 'effects': {'K': 0.07047922776386477, 'UBB': -0.02094827486623582, 'HBP': -0.001591389526007722, '1B': -0.007688901391830875, '2B': -0.012692975572530267, '3B': 0.026865008615269876, 'HR': -0.0077749874851922975}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.03334118287515905, 'UBB': -0.022133515849544653, 'HBP': 0.02431112955996878, '1B': 0.013031711964822524, '2B': -0.03652854104156128, '3B': -0.026079095970227534, 'HR': -0.057762002908314826}}, {'feature': 'scout_listed_0', 'scaled_input': 1.0, 'effects': {'K': 0.04481716735853772, 'UBB': 0.020339717604495194, 'HBP': 0.004042109945558678, '1B': -0.014010484163256448, '2B': 0.01268070378264531, '3B': 0.011708106152151026, 'HR': 0.05089862866775606}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Andujar's 606-PA debut season supplies 27 HR and only 97 K. Fixed-100 retains too much of that productive year relative to the old forecast; adaptive shrinks more and mitigates the harm, but still loses to old. Final adaptive HR 3.96%, K 16.6% and walks 4.87% are traceable to known skills. Next year's -10.04 rate comes from only 49 PA and expected PA remains 567. Without cutoff-known evidence for the future disruption, neither a health explanation nor a talent collapse can be inserted into the forecast. Rosario/Candelario/Moncada/Marte have mixed future rates.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Amed Rosario | 22.0 | 592 | 0.0 | 0.0 | -0.686914 | -0.854077 | 462.208668 | 655 | -0.054566 |
| Jeimer Candelario | 24.0 | 619 | 9.0 | 0.0 | 0.459532 | 0.037401 | 473.908365 | 386 | -1.807474 |
| Yoán Moncada | 23.0 | 650 | 0.0 | 0.0 | 0.823334 | -0.142612 | 526.299954 | 559 | 3.080017 |
| Ketel Marte | 24.0 | 580 | 0.0 | 0.0 | 0.125168 | -0.126745 | 525.519323 | 628 | 4.412568 |

## Fernando Tatis Jr. from 2021 to 2022

Player 665487, row 43296, fold 0, age 22.0, stage Current MLB. Selection: fixed_reliability value false high.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 8 | 0 | 1 | 3 |
| 2019 | MLB | 372 | 22 | 110 | 29 |
| 2020 | MLB | 257 | 17 | 61 | 26 |
| 2021 | MLB | 546 | 42 | 153 | 56 |

Weighted transported own MLB PA: 974.800000. Actual-fold active profile: [{'row_id': 43296, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'unknown', 'own_mlb_exposure': 'intermediate', 'active_profile_players': 15}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 2.746999 | 541.377302 | 4.175825 |
| fixed_reliability | 3.646859 | 541.377302 | 4.987764 |
| learned_reliability | 2.741975 | 541.377302 | 4.171292 |
| Actual | Unobserved | 0 | 0.000000 |

Unchanged expected PA = participation 0.99075027 × conditional PA 546.431647. For each arm contribution = expected PA × (batting rate/600 + 0.00313500). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 358.342904 | 0.456423 | 0.462836 | 100.000000 | 0.906959 | 0.376467 | 0.376467 | 0.0 | -0.000000 |
| K | 268.336353 | 0.231798 | 0.231878 | 100.000000 | 0.906959 | 0.271236 | 0.271236 | 0.0 | 0.000000 |
| UBB | 93.425464 | 0.083001 | 0.076274 | 100.000000 | 0.906959 | 0.094020 | 0.094020 | 0.0 | 0.383846 |
| HBP | 9.066866 | 0.011616 | 0.013061 | 100.000000 | 0.906959 | 0.009651 | 0.009651 | 0.0 | -0.071371 |
| 1B | 126.614188 | 0.137533 | 0.135187 | 100.000000 | 0.906959 | 0.130380 | 0.130380 | 0.0 | -0.315704 |
| 2B | 47.403276 | 0.043247 | 0.043120 | 100.000000 | 0.906959 | 0.048116 | 0.048116 | 0.0 | 0.302512 |
| 3B | 4.804207 | 0.003691 | 0.005619 | 100.000000 | 0.906959 | 0.004993 | 0.004993 | 0.0 | 0.101980 |
| HR | 66.806742 | 0.032692 | 0.032026 | 100.000000 | 0.906959 | 0.065137 | 0.065137 | 0.0 | 3.245597 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.13279995100500805, 'UBB': -0.031213482699841404, 'HBP': 0.22676187166474976, '1B': -0.03922168344857221, '2B': -0.027964963468725595, '3B': 0.2967077795981923, 'HR': 0.08210451023546966}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10977990408770207, 'UBB': 0.011133460205324037, 'HBP': 0.05182204253381668, '1B': -0.013888902658674103, '2B': 0.01919409307570314, '3B': 0.017352591234293103, 'HR': 0.025043752516335865}}, {'feature': 'age_centered', 'scaled_input': -1.0, 'effects': {'K': -0.009949783154508073, 'UBB': 0.01406545579539635, 'HBP': -0.03333972341767102, '1B': 0.022594137136244728, '2B': 0.05717672163303864, '3B': 0.03776241179408119, 'HR': 0.07615256410061204}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.05255867780720575, 'UBB': -0.06873383631638244, 'HBP': -0.031049995747887683, '1B': 0.015205134206287236, '2B': -0.0041828659656153585, '3B': 0.01616251057406093, 'HR': -0.06360078493305864}}, {'feature': 'scout_listed_1', 'scaled_input': -1.0, 'effects': {'K': 0.007292803469818034, 'UBB': -0.011657271198316365, 'HBP': -0.0036232181689405747, '1B': -0.007386529523048994, '2B': -0.01914030403801975, '3B': -0.004252830799900789, 'HR': -0.06003712525288014}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': 0.0023028505906457124, 'UBB': 0.002278581368670048, 'HBP': -0.05653235647209601, '1B': -0.02266442014500712, '2B': -0.021497168961243613, '3B': 0.0058588080021826335, 'HR': -0.009105725374864504}}, {'feature': 'scout_listed_0', 'scaled_input': -1.0, 'effects': {'K': -0.04724743137844255, 'UBB': -0.018172168307624345, 'HBP': -0.013076175735125636, '1B': -0.0004032376040156436, '2B': -0.001894806157442709, '3B': -0.0016140657420119471, 'HR': -0.03578419349320518}}, {'feature': 'scout_rank_score_0', 'scaled_input': -1.0, 'effects': {'K': 0.03866751895584557, 'UBB': -0.0199038669894855, 'HBP': -0.007322408292882845, '1B': -0.010891966957134338, '2B': -0.01334523632660857, '3B': 0.0006771375672034345, 'HR': -0.018371204048713525}}, {'feature': 'scout_listed_2', 'scaled_input': 1.0, 'effects': {'K': 0.012029597717655148, 'UBB': -0.016407919723306165, 'HBP': 0.0022827883852325533, '1B': 0.005052964427890455, '2B': 0.022919394253315063, '3B': 0.016308314051644564, 'HR': 0.03785083258195994}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.035830576995977054, 'UBB': -0.01558792581036331, 'HBP': 0.0024382975028678405, '1B': 0.01697235313808275, '2B': -0.008619999809481136, '3B': -0.007852600092982857, 'HR': -0.020766710247660834}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 358.342904 | 0.456423 | 0.466027 | 351.989513 | 0.734706 | 0.393717 | 0.390444 | 0.0 | -0.000000 |
| K | 268.336353 | 0.231798 | 0.232570 | 94.564442 | 0.911569 | 0.271497 | 0.269240 | 0.0 | 0.000000 |
| UBB | 93.425464 | 0.083001 | 0.073972 | 288.502161 | 0.771629 | 0.090846 | 0.090091 | 0.0 | 0.246991 |
| HBP | 9.066866 | 0.011616 | 0.010626 | 293.320911 | 0.768696 | 0.009608 | 0.009528 | 0.0 | -0.075846 |
| 1B | 126.614188 | 0.137533 | 0.137792 | 496.852512 | 0.662385 | 0.132556 | 0.131454 | 0.0 | -0.268301 |
| 2B | 47.403276 | 0.043247 | 0.045176 | 1763.182789 | 0.356029 | 0.046405 | 0.046019 | 0.0 | 0.172260 |
| 3B | 4.804207 | 0.003691 | 0.004039 | 696.862088 | 0.583132 | 0.004558 | 0.004520 | 0.0 | 0.064952 |
| HR | 66.806742 | 0.032692 | 0.029797 | 309.688331 | 0.758901 | 0.059195 | 0.058702 | 0.0 | 2.601918 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'age_centered', 'scaled_input': -1.0, 'effects': {'K': -0.011343259357408052, 'UBB': 0.016601718176012966, 'HBP': -0.003050572647880758, '1B': 0.014899249597337237, '2B': 0.05516392537929855, '3B': 0.1296792980309837, 'HR': 0.11902329621075189}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.12084775326295956, 'UBB': -0.03104573427446057, 'HBP': 0.05802471159607098, '1B': 0.005382611881901288, '2B': 0.0589715650688995, '3B': -0.04557858393010247, 'HR': 0.06368369343988838}}, {'feature': 'position_6', 'scaled_input': 1.0, 'effects': {'K': -0.06071857411507359, 'UBB': -0.08881243837324632, 'HBP': -0.04970272629637776, '1B': 0.014310842288531743, '2B': -0.02316697468187927, '3B': 0.027597413799268944, 'HR': -0.09549833746446347}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09519569083112503, 'UBB': -0.004323174492800913, 'HBP': 0.003083997696017253, '1B': -0.014994812091682987, '2B': 0.010966086596839054, '3B': -0.044158492112579745, 'HR': -0.007236373419249647}}, {'feature': 'age_squared', 'scaled_input': 1.0, 'effects': {'K': 0.002038257457902261, 'UBB': -0.0036695373078090214, 'HBP': -0.05810894749997807, '1B': -0.029108390924778182, '2B': -0.021078779646161592, '3B': -0.006280413335144208, 'HR': -0.019858332417869162}}, {'feature': 'scout_listed_1', 'scaled_input': -1.0, 'effects': {'K': 0.009795172212328854, 'UBB': -0.003840498114096009, 'HBP': -0.0058745282509164755, '1B': -0.020825351163904753, '2B': 0.004099389186593073, '3B': 0.0027900048869384476, 'HR': -0.05630755431937643}}, {'feature': 'scout_listed_0', 'scaled_input': -1.0, 'effects': {'K': -0.050329464071504675, 'UBB': -0.024626788769760946, 'HBP': -0.014119512429012335, '1B': 0.007542852407405196, '2B': -0.00434096568901001, '3B': -0.010353567735187722, 'HR': -0.02778042334224645}}, {'feature': 'scout_rank_score_0', 'scaled_input': -1.0, 'effects': {'K': 0.039435118594794476, 'UBB': -0.02029686894494833, 'HBP': -0.005979605411147308, '1B': -0.011853137990119908, '2B': -0.0153948454568464, '3B': -0.004675268454442959, 'HR': -0.01002412069929389}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.038744203389411175, 'UBB': -0.01771419990057065, 'HBP': 0.008497678089409965, '1B': 0.016472926854117498, '2B': -0.025121531235631902, '3B': -0.014170012971646452, 'HR': -0.03319495060625164}}, {'feature': 'scout_listed_2', 'scaled_input': 1.0, 'effects': {'K': 0.005892914824889611, 'UBB': -0.02269061711807523, 'HBP': -0.0004886500521672723, '1B': 0.016677679651316748, '2B': 0.01881228463873452, '3B': 0.00893782598555008, 'HR': 0.03821642757709803}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Tatis's three MLB years have 22, 17 (short 2020) and 42 HR. The adaptive +2.74 rate almost equals old +2.75, while fixed +3.65 lifts expected contribution further. Actual next-year PA is zero; conditional ability is unobserved. The large false-high delivered forecast is therefore not proof of bad hitting talent, and future nonparticipation causes are not available inputs. Preserve the canceled MiLB/short MLB distinctions. The fifteen-person young established profile is sparse. Urias, Torres, Alvarez and Arraez all play and produce next year; this one exit cannot justify a universal young-star penalty.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Luis Urías | 24.0 | 570 | 0.0 | 0.0 | 0.933763 | 0.453922 | 461.875722 | 472 | 0.937754 |
| Gleyber Torres | 24.0 | 516 | 7.0 | 4.0 | 0.628691 | 0.302096 | 480.607762 | 572 | 0.861911 |
| Yordan Alvarez | 24.0 | 598 | 0.0 | 0.0 | 2.748397 | 2.288773 | 574.312122 | 561 | 5.456003 |
| Luis Arraez | 24.0 | 479 | 9.0 | 0.0 | 0.798179 | 0.729862 | 475.801732 | 603 | 2.055070 |

## Tyler Nevin from 2023 to 2024

Player 663527, row 51185, fold 0, age 26.0, stage Current MLB. Selection: fixed_reliability value ordinary.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2021 | AAA | 453 | 16 | 91 | 42 |
| 2021 | MLB | 18 | 1 | 5 | 4 |
| 2022 | AAA | 191 | 7 | 36 | 21 |
| 2022 | MLB | 184 | 2 | 46 | 20 |
| 2023 | AAA | 385 | 15 | 65 | 38 |
| 2023 | MLB | 111 | 2 | 25 | 12 |

Weighted transported own MLB PA: 269.000000. Actual-fold active profile: [{'row_id': 51185, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'brief', 'active_profile_players': 373}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -0.601792 | 132.558461 | 0.277457 |
| fixed_reliability | -1.234380 | 132.558461 | 0.137699 |
| learned_reliability | -0.700898 | 132.558461 | 0.255561 |
| Actual | -1.577731 | 278 | 0.137144 |

Unchanged expected PA = participation 0.80878635 × conditional PA 163.897994. For each arm contribution = expected PA × (batting rate/600 + 0.00309608). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 119.766247 | 0.456074 | 0.443446 | 100.000000 | 0.728997 | 0.444745 | 0.444745 | 134.0 | -0.000000 |
| K | 65.261022 | 0.227279 | 0.238301 | 100.000000 | 0.728997 | 0.241439 | 0.241439 | 64.0 | 0.000000 |
| UBB | 31.301429 | 0.083350 | 0.088097 | 100.000000 | 0.728997 | 0.108702 | 0.108702 | 25.0 | 0.883112 |
| HBP | 6.267109 | 0.011472 | 0.014135 | 100.000000 | 0.728997 | 0.020815 | 0.020815 | 5.0 | 0.339352 |
| 1B | 33.517153 | 0.141393 | 0.130026 | 100.000000 | 0.728997 | 0.126070 | 0.126070 | 33.0 | -0.676327 |
| 2B | 7.520932 | 0.044692 | 0.046326 | 100.000000 | 0.728997 | 0.032936 | 0.032936 | 10.0 | -0.730294 |
| 3B | 1.000000 | 0.003867 | 0.005132 | 100.000000 | 0.728997 | 0.004101 | 0.004101 | 0.0 | 0.018274 |
| HR | 4.366109 | 0.031873 | 0.034537 | 100.000000 | 0.728997 | 0.021192 | 0.021192 | 7.0 | -1.068498 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1354659735340915, 'UBB': 0.01622937363038833, 'HBP': 0.23349247187590422, '1B': -0.03432423134992133, '2B': -0.05185730942269441, '3B': 0.30156289932030783, 'HR': 0.06127019457234279}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.41565523306948127, 'effects': {'K': -0.11658269785264341, 'UBB': -0.03635780752021551, 'HBP': -0.002541581948177776, '1B': 0.008613272616813779, '2B': 0.0019508157501219048, '3B': -0.001050393271425402, 'HR': -0.05051158774317987}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.3493333333333333, 'effects': {'K': 0.11063046832873508, 'UBB': 0.0048587101283929365, 'HBP': 0.002971764894735655, '1B': 0.020701768951732452, '2B': 0.04243279253007917, '3B': -0.008328653412583901, 'HR': 0.04077572380987727}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09973230092384866, 'UBB': 0.0010834939961513988, 'HBP': 0.04299448353220966, '1B': -0.014743263251966423, '2B': 0.014030295985724292, '3B': 0.023997614922167922, 'HR': 0.02842213799235352}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.027059864500886318, 'UBB': 0.05503193395159753, 'HBP': -0.014979631058054712, '1B': -0.028312825973814907, '2B': 0.00415093007085354, '3B': -0.023431592332423538, 'HR': 0.09140423647679742}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.03616864345422415, 'UBB': 0.06483432263283749, 'HBP': 0.025623869779999073, '1B': -0.022779058146650873, '2B': 0.01303217894299485, '3B': 0.01793026303910645, 'HR': 0.02068383463954518}}, {'feature': 'scout_listed_2', 'scaled_input': -1.0, 'effects': {'K': -0.009622654497336559, 'UBB': -0.001962852600593954, 'HBP': -0.010007293201982806, '1B': -0.017533547974458993, '2B': -0.01382941828848285, '3B': -0.01599777462604961, 'HR': -0.04146634730430208}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.16745822339489888, 'effects': {'K': 0.003594773804425664, 'UBB': 0.03169753599897449, 'HBP': -0.0009920319809665985, '1B': -0.003853689728077752, '2B': 0.0005879422694022078, '3B': -0.0007022272189517901, 'HR': 0.004476342573023269}}, {'feature': 'scout_rank_score_2', 'scaled_input': -1.0, 'effects': {'K': -0.0050925633274550705, 'UBB': -0.030733059698928495, 'HBP': -0.0031079139778593633, '1B': -0.003680871539119861, '2B': 0.005682287518715228, '3B': -0.010593176856301054, 'HR': -0.02183201567220841}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 0.99, 'effects': {'K': -0.029883792897032194, 'UBB': -0.002777501324315327, 'HBP': -0.01050038332323782, '1B': 0.014829047309941694, '2B': 0.014202544803928147, '3B': 0.008500498291284115, 'HR': -0.008813042054761801}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 119.766247 | 0.456074 | 0.444781 | 346.309448 | 0.437178 | 0.444976 | 0.442285 | 134.0 | -0.000000 |
| K | 65.261022 | 0.227279 | 0.244666 | 88.034411 | 0.753429 | 0.243114 | 0.241643 | 64.0 | 0.000000 |
| UBB | 31.301429 | 0.083350 | 0.089384 | 271.239180 | 0.497928 | 0.102817 | 0.102195 | 25.0 | 0.656446 |
| HBP | 6.267109 | 0.011472 | 0.011989 | 296.970387 | 0.475290 | 0.017364 | 0.017259 | 5.0 | 0.210192 |
| 1B | 33.517153 | 0.141393 | 0.128930 | 519.767011 | 0.341039 | 0.127453 | 0.126682 | 33.0 | -0.649313 |
| 2B | 7.520932 | 0.044692 | 0.043715 | 1759.122039 | 0.132635 | 0.041625 | 0.041373 | 10.0 | -0.206187 |
| 3B | 1.000000 | 0.003867 | 0.003576 | 671.605131 | 0.285986 | 0.003616 | 0.003594 | 0.0 | -0.021388 |
| HR | 4.366109 | 0.031873 | 0.032961 | 305.034962 | 0.468613 | 0.025121 | 0.024969 | 7.0 | -0.690646 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.13713607249129783, 'UBB': 0.030558924363565873, 'HBP': 0.07522339471731761, '1B': -0.0013641823824942594, '2B': 0.04648260442126732, '3B': -0.024634969053562873, 'HR': 0.04100491542809586}}, {'feature': 'position_3', 'scaled_input': 1.0, 'effects': {'K': 0.03182814881146789, 'UBB': 0.06737416800803156, 'HBP': -0.015661088840987197, '1B': -0.02009274132615237, '2B': 0.020128140356251694, '3B': -0.056582778261328105, 'HR': 0.1250906354367874}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.41565523306948127, 'effects': {'K': -0.12414475528847364, 'UBB': -0.04737255591601343, 'HBP': -0.009844343475710412, '1B': 0.0056155584802307455, '2B': -0.021421425342852903, '3B': -0.0009355292823384688, 'HR': -0.07383518783620896}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.3493333333333333, 'effects': {'K': 0.12203005071647054, 'UBB': 0.009304257871119053, 'HBP': 0.017945265224969385, '1B': -0.0022883522658327616, '2B': -0.011518171342763232, '3B': 0.023341546920194935, 'HR': 0.04079136556565525}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08547777054828669, 'UBB': -0.011461394469485676, 'HBP': -0.009830245439430296, '1B': -0.019402950427621024, '2B': 0.006888582000324304, '3B': -0.03904565397660199, 'HR': -0.0005379151187777485}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.03755902216131015, 'UBB': 0.0688800648368621, 'HBP': 0.04320436888732588, '1B': -0.030663547423665206, '2B': -0.002023593997879551, '3B': 0.03727115849902833, 'HR': 0.023972911764450298}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.16745822339489888, 'effects': {'K': 0.0052186563506483475, 'UBB': 0.044674485338803506, 'HBP': -0.0005451882939003856, '1B': -0.00819475070491202, '2B': -0.0017543784666678316, '3B': -0.0013159697117367647, 'HR': 0.006317570833988231}}, {'feature': 'scout_listed_2', 'scaled_input': -1.0, 'effects': {'K': -0.005415551934771245, 'UBB': 0.008305812145465408, 'HBP': -0.006353535874054505, '1B': -0.02373439034647652, '2B': -0.01655418741718212, '3B': -0.013053981771521396, 'HR': -0.03865513438537285}}, {'feature': 'scout_rank_score_2', 'scaled_input': -1.0, 'effects': {'K': -0.0058636452319649505, 'UBB': -0.03553035935228703, 'HBP': 0.0009013575978084018, '1B': 0.003709946222522286, '2B': -0.010458170201548858, '3B': -0.0078119602603176005, 'HR': -0.019148626004284575}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 0.99, 'effects': {'K': -0.03182503708918815, 'UBB': -0.01079905831716256, 'HBP': -0.009083840472903214, '1B': 0.012202512974978433, '2B': 0.0033108767783162196, '3B': 0.008768124348502833, 'HR': -0.017176325618419155}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Nevin has 385 AAA PA with 15 HR and 111 MLB PA with two HR in 2023, after smaller MLB work. Fixed-100's delivered value nearly matches actual, but only because expected PA 133 undershoots 278 while the rate is too optimistic. Adaptive -0.70 is closer to old -0.60 than fixed -1.23; actual is -1.58. Thus exact value alone would misleadingly favor a formula for the wrong reason. Trammell, Hill, Lee and Fletcher all have poor next-year rates. There are 373 coarse active profiles, yet the known minor/MLB discrepancy still needs interpretation.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Taylor Trammell | 25.0 | 56 | 391.0 | 0.0 | -0.375309 | -1.025811 | 160.712078 | 8 | -5.484938 |
| Derek Hill | 27.0 | 50 | 360.0 | 0.0 | -1.370481 | -1.683423 | 33.163606 | 172 | -0.822888 |
| Korey Lee | 24.0 | 70 | 357.0 | 0.0 | -1.261543 | -2.533253 | 135.190936 | 394 | -2.575192 |
| Dominic Fletcher | 25.0 | 102 | 334.0 | 0.0 | -0.703020 | -0.576904 | 271.577014 | 241 | -4.205248 |

## Dylan Cozens from 2018 to 2019

Player 622226, row 33177, fold 1, age 24.0, stage Current MLB. Selection: learned_reliability rate largest gain.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AA | 586 | 40 | 186 | 58 |
| 2017 | AAA | 542 | 27 | 194 | 57 |
| 2018 | AAA | 348 | 21 | 124 | 43 |
| 2018 | MLB | 44 | 1 | 24 | 6 |

Weighted transported own MLB PA: 44.000000. Actual-fold active profile: [{'row_id': 33177, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'brief', 'active_profile_players': 210}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.134456 | 99.393225 | 0.328282 |
| fixed_reliability | -1.438617 | 99.393225 | 0.067694 |
| learned_reliability | -1.526272 | 99.393225 | 0.053174 |
| Actual | -16.159458 | 1 | -0.023878 |

Unchanged expected PA = participation 0.77187212 × conditional PA 128.769031. For each arm contribution = expected PA × (batting rate/600 + 0.00307877). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 8.000000 | 0.465785 | 0.363033 | 100.000000 | 0.305556 | 0.307662 | 0.307662 | 1.0 | -0.000000 |
| K | 24.000000 | 0.222573 | 0.350729 | 100.000000 | 0.305556 | 0.410229 | 0.410229 | 0.0 | 0.000000 |
| UBB | 6.000000 | 0.079708 | 0.089438 | 100.000000 | 0.305556 | 0.103776 | 0.103776 | 0.0 | 0.838394 |
| HBP | 0.000000 | 0.010381 | 0.010995 | 100.000000 | 0.305556 | 0.007636 | 0.007636 | 0.0 | -0.099735 |
| 1B | 3.000000 | 0.142174 | 0.102139 | 100.000000 | 0.305556 | 0.091763 | 0.091763 | 0.0 | -2.225010 |
| 2B | 2.000000 | 0.044637 | 0.041381 | 100.000000 | 0.305556 | 0.042626 | 0.042626 | 0.0 | -0.124934 |
| 3B | 0.000000 | 0.004575 | 0.005533 | 100.000000 | 0.305556 | 0.003842 | 0.003842 | 0.0 | -0.057373 |
| HR | 1.000000 | 0.030167 | 0.036751 | 100.000000 | 0.305556 | 0.032466 | 0.032466 | 0.0 | 0.230040 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.07338157988066955, 'UBB': -0.017229684729952933, 'HBP': 0.22413867277502003, '1B': 0.021173853457996664, '2B': -0.005053078146421251, '3B': 0.34127030609413145, 'HR': 0.06687211905597058}}, {'feature': 'pooled_AAA_K', 'scaled_input': 1.127858439201452, 'effects': {'K': 0.23748567101734466, 'UBB': 0.09629671830821702, 'HBP': 0.003977945747990854, '1B': -0.04700074125904977, '2B': 0.006763717399452098, '3B': 0.015416405971986303, 'HR': 0.12815951584205193}}, {'feature': 'pooled_AA_K', 'scaled_input': 0.6805137289636844, 'effects': {'K': 0.17881748664627464, 'UBB': 0.05385834775636688, 'HBP': 0.030250453312854978, '1B': 0.0043271839695207745, '2B': 0.0319826699385214, '3B': 0.011744862883908119, 'HR': 0.11325162035639413}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.3026666666666666, 'effects': {'K': 0.11607006392926375, 'UBB': -0.012547747580519266, 'HBP': 0.02671421725139857, '1B': 0.011368165712082138, '2B': 0.036038167730171794, '3B': -0.005899023905432386, 'HR': 0.005063859337159869}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.0850129816769237, 'UBB': 0.005804463763819286, 'HBP': 0.0717233962880186, '1B': -0.044118408966210755, '2B': 0.04436504834090036, '3B': 0.016147379779552183, 'HR': 0.033609525023777696}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.027944849812178253, 'UBB': 0.06908175488883637, 'HBP': 0.022397214026563677, '1B': -0.031092329867254298, '2B': 0.02677883404381161, '3B': 0.0357281258027691, 'HR': 0.02303610264129051}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.0032098566365509505, 'UBB': 0.004601428187941054, 'HBP': -0.022621183217315034, '1B': 0.015530316043407533, '2B': 0.0329567015509675, '3B': 0.021087501864319017, 'HR': 0.06020446220813403}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.586, 'effects': {'K': 0.06006114583875868, 'UBB': -0.026755411280225395, 'HBP': -0.02406892202483847, '1B': -0.0034558164208740925, '2B': -0.009213553935364745, '3B': 0.001552011758548983, 'HR': -0.027696893077431176}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.29573502722323036, 'effects': {'K': 0.010957991094621694, 'UBB': 0.04748432620987514, 'HBP': 0.004643146011711519, '1B': -0.005718684312948013, '2B': 0.0031326320366732623, '3B': -0.0014734079947706282, 'HR': 0.007109627200055057}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.010222260159888398, 'UBB': 0.03437605614253426, 'HBP': -0.009939724137319864, '1B': 0.0066515075693903535, '2B': 0.002469543581584805, '3B': 0.007767143351953375, 'HR': 0.003721115120556427}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 8.000000 | 0.465785 | 0.354422 | 349.693099 | 0.111762 | 0.335132 | 0.321736 | 1.0 | -0.000000 |
| K | 24.000000 | 0.222573 | 0.359014 | 90.268343 | 0.327702 | 0.420111 | 0.403318 | 0.0 | 0.000000 |
| UBB | 6.000000 | 0.079708 | 0.092932 | 292.977663 | 0.130572 | 0.098603 | 0.094662 | 0.0 | 0.520898 |
| HBP | 0.000000 | 0.010381 | 0.009498 | 317.962888 | 0.121559 | 0.008343 | 0.008010 | 0.0 | -0.086149 |
| 1B | 3.000000 | 0.142174 | 0.098865 | 482.128797 | 0.083630 | 0.096299 | 0.092450 | 0.0 | -2.194712 |
| 2B | 2.000000 | 0.044637 | 0.041787 | 1849.519769 | 0.023237 | 0.041872 | 0.040198 | 0.0 | -0.275715 |
| 3B | 0.000000 | 0.004575 | 0.004018 | 665.951536 | 0.061976 | 0.003769 | 0.003619 | 0.0 | -0.074899 |
| HR | 1.000000 | 0.030167 | 0.039464 | 332.234013 | 0.116948 | 0.037507 | 0.036008 | 0.0 | 0.584304 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'pooled_AAA_K', 'scaled_input': 1.127858439201452, 'effects': {'K': 0.26559940055054765, 'UBB': 0.13219625955388334, 'HBP': 0.025180757433105713, '1B': -0.034247404997965164, '2B': 0.061076864198076876, '3B': 0.007033108634368666, 'HR': 0.2108543511427523}}, {'feature': 'pooled_AA_K', 'scaled_input': 0.6805137289636844, 'effects': {'K': 0.18118541678843836, 'UBB': 0.057958123767382685, 'HBP': 0.029034216374545396, '1B': 0.007323065589794112, '2B': 0.037165980487254606, '3B': -0.0029966200100603126, 'HR': 0.12264497681110446}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 1.3026666666666666, 'effects': {'K': 0.1261043356578416, 'UBB': -0.019530460805695236, 'HBP': 0.052048372185280904, '1B': -0.007769513233672018, '2B': -0.01024511078844642, '3B': 0.03444220167744648, 'HR': 0.005904762229732623}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.0022179489125392846, 'UBB': 0.011752590859197273, 'HBP': 0.0005807030285360537, '1B': 0.008017069785408344, '2B': 0.036533601138463684, '3B': 0.0728894727464621, 'HR': 0.08927325483518016}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.07655759877496604, 'UBB': 0.0049090063313474075, 'HBP': 0.015528017638859307, '1B': 0.04354436396468877, '2B': 0.03026512278397118, '3B': -0.01671581305274506, 'HR': 0.06969082385982855}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.29573502722323036, 'effects': {'K': 0.013115446278184725, 'UBB': 0.07263246480856074, 'HBP': 0.005348337734058289, '1B': -0.014345829206443766, '2B': 0.001894808880322966, '3B': -0.002684523102440163, 'HR': 0.010191793605230249}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.023977804607124318, 'UBB': 0.07193026240919173, 'HBP': 0.04447008206199325, '1B': -0.030613828066034098, '2B': 0.013284447097982929, '3B': 0.049241816617038345, 'HR': 0.037613386413871415}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.0711616184979449, 'UBB': -0.009925462954270069, 'HBP': 0.021801279888834513, '1B': -0.0414728785216955, '2B': 0.0375279266571029, '3B': -0.0412378192648221, 'HR': 0.016053367572266497}}, {'feature': 'pooled_AA_pa', 'scaled_input': 0.586, 'effects': {'K': 0.06058417812151232, 'UBB': -0.03310121082081456, 'HBP': -0.007640691057633472, '1B': -0.004348030845076717, '2B': -0.011029879014114232, '3B': 0.026955418154749833, 'HR': -0.021889135770245184}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.01331354695620898, 'UBB': 0.04472075481709143, 'HBP': -0.008355851358344768, '1B': 0.01591208189620144, '2B': 0.02454766366034574, '3B': 0.018590337834368517, 'HR': 0.034089372474592386}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Cozens supplies 194 K in 542 AAA PA in 2017 and 124 in 348 in 2018, then 24 K in only 44 MLB PA. Both levels already indicate a contact problem: prior K 35.9%, adaptive final 40.3%. The negative new rate is mechanically sensible, but actual -16.16 is one PA. This raw unweighted gain is not the primary talent success; Judge 2023 is. Expected PA 99 versus one remains excessive. Travis and Smith struggle; Stevenson has a strong rate in 37 PA, Luplow succeeds in 261. Nontrivial 210-profile count does not stabilize a one-PA outcome.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Sam Travis | 24.0 | 38 | 398.0 | 0.0 | -0.250442 | -0.695088 | 97.502596 | 157 | -2.404187 |
| Andrew Stevenson | 24.0 | 86 | 331.0 | 0.0 | -0.919114 | -1.239014 | 104.928273 | 37 | 5.002636 |
| Dwight Smith Jr. | 25.0 | 75 | 361.0 | 0.0 | -0.342579 | -0.206428 | 183.648162 | 392 | -0.945891 |
| Jordan Luplow | 24.0 | 103 | 357.0 | 0.0 | -0.211925 | -0.313101 | 162.346917 | 261 | 3.384818 |

## Khalil Lee from 2021 to 2022

Player 666137, row 43369, fold 4, age 23.0, stage Current MLB. Selection: learned_reliability rate largest harm.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2019 | AA | 546 | 8 | 154 | 65 |
| 2021 | AAA | 388 | 14 | 115 | 71 |
| 2021 | MLB | 18 | 0 | 13 | 0 |

Weighted transported own MLB PA: 18.000000. Actual-fold active profile: [{'row_id': 43369, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'unknown', 'own_mlb_exposure': 'brief', 'active_profile_players': 37}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.285723 | 42.963928 | 0.155152 |
| fixed_reliability | -2.107820 | 42.963928 | -0.016242 |
| learned_reliability | -1.536488 | 42.963928 | 0.024669 |
| Actual | 34.732496 | 2 | 0.122037 |

Unchanged expected PA = participation 0.65264412 × conditional PA 65.830559. For each arm contribution = expected PA × (batting rate/600 + 0.00313500). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 4.000000 | 0.456423 | 0.385706 | 100.000000 | 0.152542 | 0.360768 | 0.360768 | 1.0 | -0.000000 |
| K | 13.000000 | 0.231798 | 0.305627 | 100.000000 | 0.152542 | 0.369176 | 0.369176 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.083001 | 0.105180 | 100.000000 | 0.152542 | 0.089135 | 0.089135 | 0.0 | 0.213690 |
| HBP | 0.000000 | 0.011616 | 0.012946 | 100.000000 | 0.152542 | 0.010972 | 0.010972 | 0.0 | -0.023407 |
| 1B | 0.000000 | 0.137533 | 0.112940 | 100.000000 | 0.152542 | 0.095712 | 0.095712 | 0.0 | -1.845883 |
| 2B | 1.000000 | 0.043247 | 0.038247 | 100.000000 | 0.152542 | 0.040887 | 0.040887 | 0.0 | -0.146550 |
| 3B | 0.000000 | 0.003691 | 0.004481 | 100.000000 | 0.152542 | 0.003797 | 0.003797 | 0.0 | 0.008360 |
| HR | 0.000000 | 0.032692 | 0.034872 | 100.000000 | 0.152542 | 0.029553 | 0.029553 | 1.0 | -0.314031 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.17230000570110907, 'UBB': -0.03149137080427794, 'HBP': 0.22472564503658063, '1B': -0.015749045617841885, '2B': 0.02422830013592738, '3B': 0.3152994092727511, 'HR': 0.06407961391078855}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.527868852459016, 'effects': {'K': 0.14943631809893754, 'UBB': 0.04526976986062157, 'HBP': 0.013481420549464815, '1B': -0.026789505523552592, '2B': 0.0093734715372517, '3B': -0.003340423264452291, 'HR': 0.07240659673279747}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.8188524590163935, 'effects': {'K': 0.019236391594027066, 'UBB': 0.14849888908804465, 'HBP': 0.001248847934705027, '1B': -0.022763262825670184, '2B': 0.013700438125605825, '3B': -0.008792891618099413, 'HR': 0.03230479038350343}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.11569223932428324, 'UBB': 0.011980085158207974, 'HBP': 0.06403335648626717, '1B': -0.004409713645627855, '2B': 0.0015101375487962642, '3B': 0.023280942436821665, 'HR': 0.031993268489181}}, {'feature': 'pooled_AA_K', 'scaled_input': 0.39878391019644494, 'effects': {'K': 0.09415147241744547, 'UBB': 0.042553038104913676, 'HBP': 0.019564776471289385, '1B': 0.002800098284713215, '2B': 0.01713763023474677, '3B': 0.003958055564673072, 'HR': 0.060624280873178726}}, {'feature': 'scout_listed_0', 'scaled_input': -1.0, 'effects': {'K': -0.07108326040269465, 'UBB': -0.0028543005611948915, 'HBP': -0.016872761911478688, '1B': -0.003432351792285256, '2B': 0.0008868161466477592, '3B': -0.0076314606544602235, 'HR': -0.052499581618124236}}, {'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': -0.02149239501665709, 'UBB': 0.027420138377250554, 'HBP': -0.023235940651599903, '1B': 0.031532435571956334, '2B': 0.04335323151329254, '3B': 0.02503170291871995, 'HR': 0.06694653075854581}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.6466666666666666, 'effects': {'K': 0.05805622781646146, 'UBB': 0.005631997316800694, 'HBP': 0.0010163854594658634, '1B': 0.0008608511701403028, '2B': 0.020812777821902613, '3B': -0.0003850707092799934, 'HR': 0.031458157686972354}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.2991580916744622, 'effects': {'K': 0.00901530945154709, 'UBB': 0.057401149199374855, 'HBP': 0.003304201046004495, '1B': -0.015166988148249003, '2B': -0.0013474967204723878, '3B': -0.003162669423958413, 'HR': 0.006991889351656651}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.03043147545967251, 'UBB': 0.05559201535423408, 'HBP': 0.025317268349525277, '1B': -0.0360376857419875, '2B': 0.019610189102108034, '3B': 0.014923424260960922, 'HR': 0.02528425617748669}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 4.000000 | 0.456423 | 0.376835 | 309.516960 | 0.054959 | 0.368337 | 0.354499 | 1.0 | -0.000000 |
| K | 13.000000 | 0.231798 | 0.313741 | 103.411873 | 0.148256 | 0.374301 | 0.360239 | 0.0 | 0.000000 |
| UBB | 0.000000 | 0.083001 | 0.113096 | 268.230504 | 0.062886 | 0.105984 | 0.102002 | 0.0 | 0.661879 |
| HBP | 0.000000 | 0.011616 | 0.011339 | 283.403800 | 0.059721 | 0.010662 | 0.010261 | 0.0 | -0.049210 |
| 1B | 0.000000 | 0.137533 | 0.108751 | 556.705012 | 0.031320 | 0.105345 | 0.101387 | 0.0 | -1.595386 |
| 2B | 1.000000 | 0.043247 | 0.038261 | 1598.148738 | 0.011138 | 0.038454 | 0.037009 | 0.0 | -0.387466 |
| 3B | 0.000000 | 0.003691 | 0.003359 | 655.972567 | 0.026707 | 0.003269 | 0.003146 | 0.0 | -0.042631 |
| HR | 0.000000 | 0.032692 | 0.034619 | 304.032820 | 0.055895 | 0.032684 | 0.031456 | 1.0 | -0.123674 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'pooled_AAA_BB', 'scaled_input': 0.8188524590163935, 'effects': {'K': 0.02951396083779921, 'UBB': 0.21743558056634893, 'HBP': 0.003902596447931081, '1B': -0.04069863463066131, '2B': 0.004393715495661739, '3B': -0.013666817592078455, 'HR': 0.041822612513852844}}, {'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.16775910699426674, 'UBB': -0.014593151295302816, 'HBP': 0.0591287735993992, '1B': -0.013728897419846875, '2B': 0.09932163849822807, '3B': -0.023264362654612545, 'HR': 0.05475197078242011}}, {'feature': 'pooled_AAA_K', 'scaled_input': 0.527868852459016, 'effects': {'K': 0.1638075992421747, 'UBB': 0.06267579117751876, 'HBP': 0.024153636225953477, '1B': -0.020741492076004127, '2B': 0.03191975072002859, '3B': -0.004780494379221186, 'HR': 0.10695317806286184}}, {'feature': 'age_centered', 'scaled_input': -0.8, 'effects': {'K': -0.021941525119421133, 'UBB': 0.031375082531857466, 'HBP': -0.0008573430278995117, '1B': 0.017769503436446923, '2B': 0.039029216474733675, '3B': 0.09817475212765192, 'HR': 0.09972618593425758}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09862843198469584, 'UBB': -0.0031205805897084886, 'HBP': 0.012581515172390107, '1B': -0.009211698116660042, '2B': -0.0075835670458938775, '3B': -0.03654868510406756, 'HR': 0.0012045067267576468}}, {'feature': 'pooled_AA_K', 'scaled_input': 0.39878391019644494, 'effects': {'K': 0.09507007048744383, 'UBB': 0.046198226186678626, 'HBP': 0.019699514392284737, '1B': 0.003461091520584106, '2B': 0.019679812713165393, '3B': -0.0031581060772502946, 'HR': 0.0649580052773927}}, {'feature': 'scout_listed_0', 'scaled_input': -1.0, 'effects': {'K': -0.07245205659523762, 'UBB': -0.006173610433452714, 'HBP': -0.011432206088533887, '1B': 0.007917939624899645, '2B': -0.006011240417044672, '3B': -0.012792271712687308, 'HR': -0.04432915026529666}}, {'feature': 'pooled_AAA_pa', 'scaled_input': 0.6466666666666666, 'effects': {'K': 0.06583252972394626, 'UBB': 0.0032094585433930342, 'HBP': 0.007315730079518675, '1B': -0.007500266404708354, '2B': -0.002631906655529064, '3B': 0.012949739966320794, 'HR': 0.03566972925486073}}, {'feature': 'pooled_AA_BB', 'scaled_input': 0.2991580916744622, 'effects': {'K': 0.008353573086367388, 'UBB': 0.06414276390026294, 'HBP': 0.0029428640121756085, '1B': -0.014488929363052296, '2B': 0.0010865387196883178, '3B': -0.0030344010712544064, 'HR': 0.007646081033478823}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.0259678623723349, 'UBB': 0.055823745614109604, 'HBP': 0.041383709672252036, '1B': -0.019249415262094574, '2B': 0.002523838281237738, '3B': 0.039876534419813994, 'HR': 0.02473673368965324}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Lee's 2021 AAA record has 14 HR, 115 K and 71 walks in 388 PA; the tiny MLB debut has 13 K in 18 PA. Adaptive K is 36.0% despite only 14.8% pre-normalization own-MLB influence. Actual +34.73 comes from a HR in two PA, so the unweighted harm is not evidence of 35-win true ability or a broken future denominator. Expected PA is 43 versus two. 2020's canceled minor season is missing opportunity, not zero talent. Kevin Smith and Padlo struggle, Jones and Hurst never appear; 37 coarse active profiles are not a star comparison.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Kevin Smith | 24.0 | 36 | 410.0 | 0.0 | -0.779943 | -1.581769 | 134.398922 | 151 | -4.323310 |
| Kevin Padlo | 24.0 | 15 | 403.0 | 0.0 | -0.051046 | -1.149931 | 77.962193 | 34 | -8.538151 |
| Jahmai Jones | 23.0 | 72 | 295.0 | 0.0 | -0.868898 | -1.926861 | 106.036138 | 0 | Unobserved |
| Scott Hurst | 25.0 | 5 | 305.0 | 0.0 | -0.746098 | -1.642227 | 8.101070 | 0 | Unobserved |

## Neil Walker from 2016 to 2017

Player 435522, row 22870, fold 1, age 30.0, stage Current MLB. Selection: learned_reliability rate ordinary.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2014 | Aplus | 5 | 0 | 1 | 1 |
| 2014 | MLB | 571 | 23 | 88 | 43 |
| 2015 | MLB | 603 | 16 | 110 | 39 |
| 2016 | MLB | 458 | 23 | 84 | 39 |

Weighted transported own MLB PA: 1283.000000. Actual-fold active profile: [{'row_id': 22870, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 104}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 0.667687 | 474.604298 | 1.993767 |
| fixed_reliability | 1.455002 | 474.604298 | 2.616539 |
| learned_reliability | 1.322824 | 474.604298 | 2.511985 |
| Actual | 1.319952 | 448 | 2.363691 |

Unchanged expected PA = participation 0.99224269 × conditional PA 478.314736. For each arm contribution = expected PA × (batting rate/600 + 0.00308809). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 619.803305 | 0.474130 | 0.472978 | 100.000000 | 0.927693 | 0.482358 | 0.482358 | 211.0 | 0.000000 |
| K | 229.854260 | 0.211193 | 0.214608 | 100.000000 | 0.927693 | 0.181717 | 0.181717 | 77.0 | -0.000000 |
| UBB | 100.352604 | 0.076693 | 0.084170 | 100.000000 | 0.927693 | 0.078648 | 0.078648 | 53.0 | 0.068082 |
| HBP | 14.120072 | 0.008945 | 0.012278 | 100.000000 | 0.927693 | 0.011097 | 0.011097 | 5.0 | 0.078196 |
| 1B | 208.223594 | 0.149198 | 0.137947 | 100.000000 | 0.927693 | 0.160534 | 0.160534 | 65.0 | 0.500326 |
| 2B | 49.650293 | 0.044718 | 0.043554 | 100.000000 | 0.927693 | 0.039050 | 0.039050 | 21.0 | -0.352113 |
| 3B | 5.060716 | 0.004730 | 0.006647 | 100.000000 | 0.927693 | 0.004140 | 0.004140 | 2.0 | -0.046190 |
| HR | 55.935157 | 0.030393 | 0.027819 | 100.000000 | 0.927693 | 0.042456 | 0.042456 | 14.0 | 1.206701 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.11993107320385087, 'UBB': 0.04401596269909897, 'HBP': 0.250382265243886, '1B': 0.007649766105529963, '2B': -0.022519870344507222, '3B': 0.34175117489493895, 'HR': 0.06173106164332415}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.07299991926794991, 'UBB': 0.002995226222560254, 'HBP': 0.07479913362363609, '1B': -0.04323032866026037, '2B': 0.047588928606776736, '3B': 0.017979603496021356, 'HR': 0.03434515075192197}}, {'feature': 'position_4', 'scaled_input': 1.0, 'effects': {'K': -0.056659584009159984, 'UBB': -0.012988760831267323, 'HBP': -0.002239575102727076, '1B': 0.030532108096353493, '2B': -0.013470730949547935, '3B': -0.002296613096567274, 'HR': -0.06712599892946558}}, {'feature': 'age_centered', 'scaled_input': 0.6, 'effects': {'K': 0.007999883768868702, 'UBB': 0.02013865135301537, 'HBP': 0.015578955239536623, '1B': -0.03249842321020722, '2B': -0.031501416862446945, '3B': -0.02126719818843266, 'HR': -0.057032189960185234}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.7, 'effects': {'K': -0.04378812400124549, 'UBB': 0.013469730728373918, 'HBP': 0.013275796693439831, '1B': -0.008516022142022055, '2B': -0.0032543188137023425, '3B': -0.004105839547126371, 'HR': -0.004504677073583962}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.010669536184438094, 'UBB': 0.03813531493920584, 'HBP': -0.008765772993203037, '1B': 0.0032728944505054647, '2B': 0.01298533333145925, '3B': 0.01843992542026301, 'HR': -0.002432575268494021}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.029866700325053678, 'UBB': -0.011619511297672809, 'HBP': -0.009238458127830394, '1B': -0.010547120409217122, '2B': -0.007169361384875355, '3B': 0.01387043812783054, 'HR': -0.0012211283114723212}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.008111380691806726, 'UBB': -0.015073237764728301, 'HBP': 0.013376875242865283, '1B': -0.005424024546656834, '2B': -0.012870968924150548, '3B': -0.0243267582353947, 'HR': -0.014995149115813813}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': 0.02370411036859598, 'UBB': -0.0003326566004827917, 'HBP': -0.00476193492224066, '1B': -0.005516181995320958, '2B': 0.0028126006248921486, '3B': 0.004579295302323979, 'HR': -0.007561054853196638}}, {'feature': 'age_squared', 'scaled_input': 0.36, 'effects': {'K': 0.003194610730654042, 'UBB': -0.0027130944837140563, 'HBP': -0.021914253684125112, '1B': -0.01181631360884194, '2B': -0.01617995272188977, '3B': 0.004726915766187174, 'HR': -0.004968815285838634}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 619.803305 | 0.474130 | 0.475145 | 349.714153 | 0.785808 | 0.481387 | 0.483444 | 211.0 | 0.000000 |
| K | 229.854260 | 0.211193 | 0.218919 | 82.461132 | 0.939609 | 0.181555 | 0.182331 | 77.0 | -0.000000 |
| UBB | 100.352604 | 0.076693 | 0.077849 | 299.127661 | 0.810933 | 0.078148 | 0.078481 | 53.0 | 0.062295 |
| HBP | 14.120072 | 0.008945 | 0.009086 | 331.144304 | 0.794848 | 0.010612 | 0.010657 | 5.0 | 0.062196 |
| 1B | 208.223594 | 0.149198 | 0.145568 | 516.795816 | 0.712859 | 0.157491 | 0.158164 | 65.0 | 0.395736 |
| 2B | 49.650293 | 0.044718 | 0.044700 | 2173.632909 | 0.371170 | 0.042472 | 0.042654 | 21.0 | -0.128218 |
| 3B | 5.060716 | 0.004730 | 0.004047 | 663.268269 | 0.659210 | 0.003979 | 0.003996 | 2.0 | -0.057424 |
| HR | 55.935157 | 0.030393 | 0.024687 | 290.993717 | 0.815124 | 0.040101 | 0.040272 | 14.0 | 0.988239 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.12399563415718362, 'UBB': 0.06108887318264763, 'HBP': 0.04132630922208368, '1B': 0.06952201291049591, '2B': 0.033984313408647195, '3B': -0.024515795259534897, 'HR': 0.06587271568699986}}, {'feature': 'position_4', 'scaled_input': 1.0, 'effects': {'K': -0.06262235652724875, 'UBB': -0.03410339945894944, 'HBP': -0.005616981054378666, '1B': 0.022969006658025634, '2B': -0.022479964020359126, '3B': 0.011396016637254593, 'HR': -0.09574469201694431}}, {'feature': 'age_centered', 'scaled_input': 0.6, 'effects': {'K': 0.010240045523798797, 'UBB': 0.01002060944696845, 'HBP': -0.009660162663893858, '1B': -0.020972395152684415, '2B': -0.034262411239514116, '3B': -0.06885879483058005, 'HR': -0.07891034050281505}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.05935778399199899, 'UBB': -0.015399395248767317, 'HBP': 0.02169203785364258, '1B': -0.0412577944752023, '2B': 0.0317224224810734, '3B': -0.042538367619522705, 'HR': 0.019025386664549712}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.7, 'effects': {'K': -0.04294924245207106, 'UBB': 0.003307287002078888, 'HBP': -0.012412604847876109, '1B': 0.012370587602652113, '2B': 0.019631930746757374, '3B': -0.04388958172052912, 'HR': -0.009446675519239615}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.009664218900690361, 'UBB': -0.024075475454576074, 'HBP': 0.0199603235368439, '1B': -0.0008956481285971846, '2B': -0.04276098855963752, '3B': -0.023529605116774554, 'HR': -0.03493260954281269}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.03171067585096528, 'UBB': -0.015951535439739137, 'HBP': -0.010228156637537475, '1B': -0.005245811679642957, '2B': -0.00699000472266776, '3B': 0.010054253140269427, 'HR': -0.007900832618463414}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.012288930852851898, 'UBB': 0.027066844255941344, 'HBP': -0.006765527721939412, '1B': -0.004609843376944068, '2B': 0.015131646148345466, '3B': 0.014380951247077466, 'HR': -0.012299962021438569}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': 0.025034063875017998, 'UBB': -0.004933954386203968, 'HBP': -0.004066149132290588, '1B': -0.01468021911205962, '2B': 0.0004470288505458185, '3B': 0.005200907337833141, 'HR': -0.014784276411985701}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.018357451899070766, 'UBB': 0.006083626667331182, 'HBP': 0.002095858372956336, '1B': -0.02411462654447629, '2B': 0.007884062423759388, '3B': 0.00034756153539685486, 'HR': -0.021667720205507994}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Walker's three established MLB seasons supply 23, 16 and 23 HR in 571, 603 and 458 PA. Adaptive +1.323 is near actual +1.320 and improves old +0.668, but HR is high and walks low relative to next-year events. Individual component offsets remain despite accurate combined rate. Expected PA 475 slightly exceeds 448, so delivered contribution is somewhat high. Cain/Gomez/Castillo produce, Orlando struggles; 104 coarse active profiles provide ordinary exposure support rather than validation of every component.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Lorenzo Cain | 30.0 | 434 | 8.0 | 0.0 | 0.290102 | 0.493898 | 505.574879 | 645 | 1.438976 |
| Carlos Gómez | 30.0 | 453 | 14.0 | 21.0 | 0.295950 | 0.207382 | 407.478504 | 426 | 1.178042 |
| Paulo Orlando | 30.0 | 484 | 0.0 | 0.0 | -0.821668 | -0.803051 | 351.459137 | 90 | -4.624957 |
| Welington Castillo | 29.0 | 457 | 0.0 | 0.0 | -0.301804 | -0.046759 | 389.500600 | 365 | 1.315248 |

## Mookie Betts from 2017 to 2018

Player 605141, row 28634, fold 0, age 24.0, stage Current MLB. Selection: learned_reliability value largest harm.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2015 | AA | 4 | 1 | 0 | 0 |
| 2015 | MLB | 654 | 18 | 82 | 45 |
| 2016 | MLB | 730 | 31 | 80 | 48 |
| 2017 | MLB | 712 | 24 | 79 | 68 |

Weighted transported own MLB PA: 1688.400000. Actual-fold active profile: [{'row_id': 28634, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 4.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 32}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 2.564790 | 665.742617 | 4.893758 |
| fixed_reliability | 1.899856 | 665.742617 | 4.155966 |
| learned_reliability | 1.654690 | 665.742617 | 3.883938 |
| Actual | 6.544501 | 614 | 8.588348 |

Unchanged expected PA = participation 0.99043759 × conditional PA 672.170187. For each arm contribution = expected PA × (batting rate/600 + 0.00307618). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 905.384487 | 0.466035 | 0.446477 | 100.000000 | 0.944084 | 0.531219 | 0.531219 | 262.0 | 0.000000 |
| K | 197.566300 | 0.216433 | 0.227793 | 100.000000 | 0.944084 | 0.123208 | 0.123208 | 91.0 | -0.000000 |
| UBB | 138.900566 | 0.080191 | 0.088160 | 100.000000 | 0.944084 | 0.082597 | 0.082597 | 73.0 | 0.083809 |
| HBP | 5.029967 | 0.009515 | 0.011751 | 100.000000 | 0.944084 | 0.003470 | 0.003470 | 8.0 | -0.219564 |
| 1B | 261.505320 | 0.145271 | 0.135965 | 100.000000 | 0.944084 | 0.153826 | 0.153826 | 96.0 | 0.377578 |
| 2B | 105.872578 | 0.045317 | 0.045690 | 100.000000 | 0.944084 | 0.061754 | 0.061754 | 47.0 | 1.021135 |
| 3B | 9.708282 | 0.004290 | 0.006112 | 100.000000 | 0.944084 | 0.005770 | 0.005770 | 5.0 | 0.115891 |
| HR | 64.432500 | 0.032947 | 0.038053 | 100.000000 | 0.944084 | 0.038156 | 0.038156 | 32.0 | 0.521006 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.17880187464648767, 'UBB': 0.0029877585042790825, 'HBP': 0.22302742714691134, '1B': -0.04995528090329869, '2B': -0.02163098272617181, '3B': 0.294137922202717, 'HR': 0.1111691486685647}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.10478055184976, 'UBB': 0.018245584436344452, 'HBP': 0.07150068822845565, '1B': -0.020405567071787995, '2B': 0.019975956698293308, '3B': 0.008764177256315822, 'HR': 0.027618095017351338}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.04505514186535846, 'UBB': 0.07042420412496249, 'HBP': 0.00969437975376362, '1B': -0.028632709360214715, '2B': 0.020799579191278228, '3B': 0.028387979634240307, 'HR': 0.048773791080005846}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.00044451555873867613, 'UBB': -0.008780306999391592, 'HBP': -0.021007987158793685, '1B': 0.03551665166933011, '2B': 0.029125918128992633, '3B': 0.023460424956620853, 'HR': 0.04633369630991724}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.006308536515138044, 'UBB': 0.03626606785185554, 'HBP': 0.005929704257069928, '1B': 0.038184676556422, '2B': -0.0043504994761362084, '3B': -0.0015543760421523466, 'HR': 0.027153441651344323}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.024775682178834125, 'UBB': -0.009794388574107483, 'HBP': 0.019704500221142892, '1B': 0.018334653308645168, '2B': -0.009970103850069214, '3B': -0.011115205282114292, 'HR': -0.033875854153053844}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.014948045173175334, 'UBB': 0.023803999261455083, 'HBP': -0.012068886347351038, '1B': 0.012462110076414283, '2B': 0.022226198016142215, '3B': 0.01971477405512055, 'HR': -0.004862407674028764}}, {'feature': 'age_squared', 'scaled_input': 0.36, 'effects': {'K': 0.0014651245492104004, 'UBB': -0.004575487241052136, 'HBP': -0.021861623227722435, '1B': -0.013515323418801841, '2B': -0.01349393711557643, '3B': 0.006916599039494009, 'HR': -0.008455366579544854}}, {'feature': 'draft_rank', 'scaled_input': 0.32277851160274396, 'effects': {'K': -0.004289437525498547, 'UBB': 0.01740897492065162, 'HBP': 0.001048544421136664, '1B': -0.0006913645213525825, '2B': 0.005468728049449161, '3B': 0.005390355863798266, 'HR': 0.010920912663734744}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.013142343190380767, 'UBB': -0.010861232123016675, 'HBP': -0.014197492709499536, '1B': -0.01220398756332597, '2B': -0.008699455409191821, '3B': 0.011499751938958896, 'HR': -0.003234711793325333}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 905.384487 | 0.466035 | 0.448834 | 354.563422 | 0.826447 | 0.521069 | 0.531488 | 262.0 | 0.000000 |
| K | 197.566300 | 0.216433 | 0.228168 | 101.899824 | 0.943082 | 0.123341 | 0.125807 | 91.0 | -0.000000 |
| UBB | 138.900566 | 0.080191 | 0.086929 | 294.926554 | 0.851297 | 0.082961 | 0.084620 | 73.0 | 0.154262 |
| HBP | 5.029967 | 0.009515 | 0.009750 | 327.816329 | 0.837410 | 0.004080 | 0.004162 | 8.0 | -0.194429 |
| 1B | 261.505320 | 0.145271 | 0.138733 | 510.964051 | 0.767676 | 0.151131 | 0.154153 | 96.0 | 0.392047 |
| 2B | 105.872578 | 0.045317 | 0.047162 | 1823.222021 | 0.480803 | 0.054635 | 0.055728 | 47.0 | 0.646751 |
| 3B | 9.708282 | 0.004290 | 0.004262 | 693.669829 | 0.708795 | 0.005317 | 0.005423 | 5.0 | 0.088696 |
| HR | 64.432500 | 0.032947 | 0.036162 | 297.703663 | 0.850107 | 0.037862 | 0.038619 | 32.0 | 0.567362 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.16334349885442906, 'UBB': 0.0011327602587, 'HBP': 0.0425076822039271, '1B': 0.008885820705160011, '2B': 0.051093740434956826, '3B': -0.05207390860960233, 'HR': 0.09037335710499982}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.08887832047510694, 'UBB': 0.00016740800532927917, 'HBP': 0.02124319449712765, '1B': -0.01715939724729772, '2B': 0.01222315827017854, '3B': -0.05541763298400515, 'HR': 0.0019340772966928482}}, {'feature': 'age_centered', 'scaled_input': -0.6, 'effects': {'K': 0.0011524256087035983, 'UBB': -0.004763654524633946, 'HBP': -0.0006344421505976896, '1B': 0.022052889461571315, '2B': 0.03498896842623236, '3B': 0.07913658915227202, 'HR': 0.07219170438708385}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.041177848063483645, 'UBB': 0.0747554798435274, 'HBP': 0.029157097566690757, '1B': -0.043721806398138836, '2B': 0.007530544031000925, '3B': 0.04794115161036431, 'HR': 0.05472795233597699}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.02732829669211374, 'UBB': -0.010441893139367003, 'HBP': 0.02701481286329588, '1B': 0.019139976413322116, '2B': -0.036997645155634175, '3B': -0.021274053140532267, 'HR': -0.04710568340826712}}, {'feature': 'position_9', 'scaled_input': 1.0, 'effects': {'K': -0.012487273719588889, 'UBB': 0.04139636996599783, 'HBP': 0.007576037299122799, '1B': 0.03564151275681952, '2B': -0.002975234062059831, '3B': 0.00665326626379056, 'HR': 0.02956417220479218}}, {'feature': 'age_squared', 'scaled_input': 0.36, 'effects': {'K': 0.0015266272118995622, 'UBB': -0.005870100608396041, 'HBP': -0.023353130868451772, '1B': -0.01266625304494693, '2B': -0.01170814104298106, '3B': 0.0030770135589881127, 'HR': -0.013987616352269914}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.3, 'effects': {'K': -0.013516170555870522, 'UBB': 0.004077813752761282, 'HBP': -0.006156556934354302, '1B': 0.0004201047737833919, '2B': 0.0054242378898493575, '3B': -0.022155074674438627, 'HR': -0.003984655510279082}}, {'feature': 'draft_rank', 'scaled_input': 0.32277851160274396, 'effects': {'K': -0.005600388757196721, 'UBB': 0.018936851307325663, 'HBP': 0.0022141580968066373, '1B': 0.0035361743233141185, '2B': 0.002490183691845206, '3B': 0.0055595465317994875, 'HR': 0.011793035061182155}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.016727866024502918, 'UBB': -0.009269844451416206, 'HBP': -0.018116469443421383, '1B': -0.006530102061458638, '2B': 0.00234278371693062, '3B': 0.009282544814903477, 'HR': -0.00790281077354834}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Betts has 654, 730 and 712 MLB PA with 18, 31 and 24 HR and consistently low K. The strong own-MLB anchor does not foresee next-year HR/walk growth: final HR 3.86% versus actual 5.21%, walks 8.46% versus 11.9%. Adaptive +1.65 worsens old +2.56 against actual +6.54 and is the largest delivered-value harm. Expected PA 666 versus 614 is slightly high, so this deterioration is not an opportunity fix. The age/exposure profile has 32 people, but Lamb/Myers/Rizzo/Healy are not equivalent superstar-development comparables. Explicit anchoring alone can lose useful nonlinear development information.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jake Lamb | 26.0 | 635 | 0.0 | 0.0 | 1.423762 | 1.019673 | 521.781260 | 238 | -1.075285 |
| Wil Myers | 26.0 | 649 | 0.0 | 0.0 | 1.357717 | 0.974090 | 544.828481 | 343 | 0.736285 |
| Anthony Rizzo | 27.0 | 691 | 0.0 | 0.0 | 3.226269 | 2.998726 | 564.154126 | 665 | 1.952272 |
| Ryon Healy | 25.0 | 605 | 0.0 | 0.0 | 0.518811 | 0.265837 | 505.416124 | 524 | -0.798332 |

## Yordan Alvarez from 2024 to 2025

Player 670541, row 55521, fold 2, age 27.0, stage Current MLB. Selection: learned_reliability value false high.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2022 | MLB | 561 | 37 | 106 | 69 |
| 2023 | AAA | 11 | 0 | 1 | 2 |
| 2023 | MLB | 496 | 31 | 92 | 64 |
| 2024 | MLB | 635 | 35 | 95 | 53 |

Weighted transported own MLB PA: 1368.400000. Actual-fold active profile: [{'row_id': 55521, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 5.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 255}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | 3.709704 | 554.241843 | 5.158329 |
| fixed_reliability | 4.283925 | 554.241843 | 5.688758 |
| learned_reliability | 3.733922 | 554.241843 | 5.180700 |
| Actual | 0.919648 | 199 | 0.925104 |

Unchanged expected PA = participation 0.99011544 × conditional PA 559.774972. For each arm contribution = expected PA × (batting rate/600 + 0.00312416). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 617.922171 | 0.465823 | 0.467301 | 100.000000 | 0.931899 | 0.452637 | 0.452637 | 98.0 | -0.000000 |
| K | 232.498649 | 0.225800 | 0.221329 | 100.000000 | 0.931899 | 0.173407 | 0.173407 | 33.0 | -0.000000 |
| UBB | 143.192939 | 0.079036 | 0.080027 | 100.000000 | 0.931899 | 0.102966 | 0.102966 | 23.0 | 0.833574 |
| HBP | 23.634672 | 0.011072 | 0.014199 | 100.000000 | 0.931899 | 0.017063 | 0.017063 | 0.0 | 0.217602 |
| 1B | 196.177294 | 0.141968 | 0.139385 | 100.000000 | 0.931899 | 0.143092 | 0.143092 | 31.0 | 0.049575 |
| 2B | 69.368731 | 0.042593 | 0.042428 | 100.000000 | 0.931899 | 0.050130 | 0.050130 | 8.0 | 0.468260 |
| 3B | 4.090773 | 0.003820 | 0.005485 | 100.000000 | 0.931899 | 0.003159 | 0.003159 | 0.0 | -0.051755 |
| HR | 81.514770 | 0.029888 | 0.029846 | 100.000000 | 0.931899 | 0.057545 | 0.057545 | 6.0 | 2.766670 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.11500916556047082, 'UBB': 0.015329940508023046, 'HBP': 0.21420571531634314, '1B': 0.002240118261919844, '2B': -0.008669715308389059, '3B': 0.3165046814937752, 'HR': 0.01239728786000714}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.11313121402892415, 'UBB': -0.009400463576786035, 'HBP': 0.0432317063875065, '1B': -0.016814164808711226, '2B': 0.020009198635639512, '3B': 0.03266311492409629, 'HR': 0.048074967737733114}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.04237280190231877, 'UBB': -0.0009688577902538107, 'HBP': -0.009159643623389299, '1B': 0.012822408502502977, '2B': 0.0043236152179900594, '3B': 0.010850877343457993, 'HR': -0.01062091660777551}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.1125000000000001, 'effects': {'K': -0.029625222330202372, 'UBB': -0.00761852998002835, 'HBP': -0.0015788331333503084, '1B': 0.0021170565768634814, '2B': -0.0007112975112531256, '3B': 0.00016764252034087222, 'HR': -0.01454656315081999}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.027009511914581074, 'UBB': -0.007261938540635741, 'HBP': -0.006477688421615629, '1B': 0.0007460734450390593, '2B': -0.0034550871426964357, '3B': 0.001080221859518785, 'HR': -0.0005776637384817631}}, {'feature': 'position_10', 'scaled_input': 1.0, 'effects': {'K': -0.012857917249240961, 'UBB': 0.023951288741094704, 'HBP': 0.004042110905948371, '1B': -0.006151087684866653, '2B': -0.0010847428495128408, '3B': -0.0035053836155132505, 'HR': -0.0016229889934856107}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': 0.0009286027811985947, 'UBB': 0.00215834781686936, 'HBP': 0.011432471900120892, '1B': 0.007037383597500028, '2B': -0.007553542528689753, '3B': -0.008102877558520943, 'HR': -0.019598667729929912}}, {'feature': 'scout_list_capacity_1', 'scaled_input': 1.0, 'effects': {'K': 0.017139804659355176, 'UBB': -0.010354095101122123, 'HBP': -0.005635132245070619, '1B': -0.005111344397016701, '2B': -0.0019590546256421904, '3B': 0.00550473532825977, 'HR': -0.0053395019322612725}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.08235294117647063, 'effects': {'K': 0.0023053576848009747, 'UBB': 0.015123320161800919, 'HBP': 8.77041421879978e-06, '1B': -0.00257146452291147, '2B': -0.0001948318061867568, '3B': -0.00026640365212489956, 'HR': 0.0009986903320093933}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.00630123313242725, 'UBB': -0.013999636188231001, 'HBP': -0.005115339570292924, '1B': -0.010625086505816754, '2B': -0.00040529805683430913, '3B': 0.009912100893759077, 'HR': -0.010338477987132935}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 617.922171 | 0.465823 | 0.468576 | 316.726104 | 0.812046 | 0.454763 | 0.458445 | 98.0 | -0.000000 |
| K | 232.498649 | 0.225800 | 0.223250 | 102.570602 | 0.930270 | 0.173625 | 0.175031 | 33.0 | -0.000000 |
| UBB | 143.192939 | 0.079036 | 0.080911 | 254.661873 | 0.843098 | 0.100919 | 0.101736 | 23.0 | 0.790726 |
| HBP | 23.634672 | 0.011072 | 0.011603 | 281.927430 | 0.829169 | 0.016303 | 0.016435 | 0.0 | 0.194822 |
| 1B | 196.177294 | 0.141968 | 0.141130 | 469.239897 | 0.744651 | 0.142792 | 0.143948 | 31.0 | 0.087393 |
| 2B | 69.368731 | 0.042593 | 0.043390 | 1787.417032 | 0.433612 | 0.046557 | 0.046934 | 8.0 | 0.269667 |
| 3B | 4.090773 | 0.003820 | 0.003436 | 693.266683 | 0.663735 | 0.003140 | 0.003165 | 0.0 | -0.051315 |
| HR | 81.514770 | 0.029888 | 0.027704 | 298.077256 | 0.821133 | 0.053870 | 0.054306 | 6.0 | 2.442629 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.1137225959126278, 'UBB': 0.04864678906993214, 'HBP': 0.05417911897833354, '1B': -0.005835734015515962, '2B': 0.05709556039569332, '3B': -0.03180339532507647, 'HR': 0.00909402844591616}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.09975408163628914, 'UBB': -0.023066557417438953, 'HBP': -0.003446713760358475, '1B': -0.021482134234377344, '2B': 0.014222465992350218, '3B': -0.03166114926556387, 'HR': 0.022240340400847238}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.045779310433548825, 'UBB': -0.009862260849278846, 'HBP': -0.00292542610341865, '1B': 0.015472676360836735, '2B': -0.004741960983967614, '3B': 0.008105516624092349, 'HR': -0.019215243998504824}}, {'feature': 'position_10', 'scaled_input': 1.0, 'effects': {'K': -0.010495118096823788, 'UBB': 0.04050119189160899, 'HBP': 0.002677143214845782, '1B': 0.0007488018460670916, '2B': 0.0014184812184235218, '3B': -0.01529346061249013, 'HR': 0.007112503438213109}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.5, 'effects': {'K': -0.007100514180477636, 'UBB': 0.00730385190298939, 'HBP': -0.009661460871518063, '1B': -0.002780058640039459, '2B': 0.002959744659124658, '3B': -0.037724245899307056, 'HR': -0.004512607726876166}}, {'feature': 'pooled_AAA_K', 'scaled_input': -0.1125000000000001, 'effects': {'K': -0.03263730905388743, 'UBB': -0.011132341893143079, 'HBP': -0.0031147042007371563, '1B': 0.001717469534285845, '2B': -0.0059370902658743094, '3B': 0.00035895262608773954, 'HR': -0.021833657142741162}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.003589260448696965, 'UBB': -0.0053705682488608105, 'HBP': 0.012218028280753732, '1B': 0.009562486161791743, '2B': -0.019662116586648994, '3B': -0.013511381910294565, 'HR': -0.028370226405349162}}, {'feature': 'scout_list_available_1', 'scaled_input': 1.0, 'effects': {'K': 0.027390529838521794, 'UBB': -0.00943542442186493, 'HBP': -0.003011193348682513, '1B': -0.0018733154448351635, '2B': -0.010504401305379307, '3B': 0.0007762158001594104, 'HR': -0.007827639021166176}}, {'feature': 'scout_list_available_2', 'scaled_input': 1.0, 'effects': {'K': 0.005856128374110091, 'UBB': -0.022136843187651696, 'HBP': -0.001595476139937533, '1B': -0.0032679111615703986, '2B': -0.006800462652187272, '3B': 0.004467929825327343, 'HR': -0.02099097302790255}}, {'feature': 'pooled_AAA_BB', 'scaled_input': 0.08235294117647063, 'effects': {'K': 0.00290134493865878, 'UBB': 0.021342387149238015, 'HBP': 0.00017923349782130542, '1B': -0.004285778959506529, '2B': -0.0013562582721222095, '3B': -0.0005547240225915114, 'HR': 0.0017157527236165955}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Alvarez's known MLB seasons have 37, 31 and 35 HR with strong on-base production. Adaptive +3.73 nearly equals old +3.71, below fixed +4.28. Expected PA remains 554 versus actual 199 and actual rate drops to +0.92. Final HR 5.43% is well above realized 3.02%. The origin forecast is reasonable from that record; no future diagnosis can be inserted to explain it away. Castro/DeLaCruz/Torres/Devers have mixed rates and exposure. This false high is mainly a common opportunity/performance uncertainty failure, not an incremental adaptive-shrinkage benefit.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Willi Castro | 27.0 | 635 | 0.0 | 0.0 | -0.383134 | -0.122763 | 495.679791 | 454 | -0.522583 |
| Bryan De La Cruz | 27.0 | 622 | 0.0 | 0.0 | -0.441748 | -0.676990 | 466.770643 | 50 | -5.101019 |
| Gleyber Torres | 27.0 | 665 | 0.0 | 0.0 | 0.592595 | 0.675578 | 583.993781 | 628 | 1.063161 |
| Rafael Devers | 27.0 | 601 | 0.0 | 0.0 | 1.768685 | 1.655329 | 553.053540 | 729 | 2.438448 |

## Logan Forsythe from 2018 to 2019

Player 523253, row 32428, fold 3, age 31.0, stage Current MLB. Selection: learned_reliability value ordinary.

| Source year | Level | PA | HR | K | Unintentional walks |
|---|---|---:|---:|---:|---:|
| 2016 | AAA | 7 | 1 | 0 | 1 |
| 2016 | MLB | 567 | 20 | 127 | 46 |
| 2017 | Aplus | 20 | 0 | 9 | 4 |
| 2017 | MLB | 439 | 6 | 109 | 68 |
| 2018 | Aplus | 10 | 0 | 2 | 0 |
| 2018 | MLB | 416 | 2 | 83 | 40 |

Weighted transported own MLB PA: 1107.400000. Actual-fold active profile: [{'row_id': 32428, 'stage': 'Current MLB', 'prior_debut': 1, 'age_band': 6.0, 'rank_band': 'not_listed', 'own_mlb_exposure': 'substantial', 'active_profile_players': 132}]. Full actual and scaled prior inputs, old counts/environments, saved fold support and all prior log-odds terms are in cases.json.

| Forecast | Batting wins per 600 PA | Expected PA | Batting plus replacement contribution |
|---|---:|---:|---:|
| binary_scout | -1.043190 | 224.694176 | 0.301117 |
| fixed_reliability | -0.513772 | 224.694176 | 0.499378 |
| learned_reliability | -0.545732 | 224.694176 | 0.487410 |
| Actual | -1.034883 | 367 | 0.488095 |

Unchanged expected PA = participation 0.72039695 × conditional PA 311.903285. For each arm contribution = expected PA × (batting rate/600 + 0.00307877). These are mechanical comparisons, not an exact joint talent/workload distribution.

### fixed_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 492.876070 | 0.465785 | 0.466068 | 100.000000 | 0.917177 | 0.446814 | 0.446814 | 148.0 | -0.000000 |
| K | 252.627515 | 0.222573 | 0.223231 | 100.000000 | 0.917177 | 0.227721 | 0.227721 | 100.0 | 0.000000 |
| UBB | 122.582704 | 0.079708 | 0.088679 | 100.000000 | 0.917177 | 0.108871 | 0.108871 | 44.0 | 1.015845 |
| HBP | 12.044102 | 0.010381 | 0.014494 | 100.000000 | 0.917177 | 0.011176 | 0.011176 | 3.0 | 0.028849 |
| 1B | 161.394944 | 0.142174 | 0.129442 | 100.000000 | 0.917177 | 0.144392 | 0.144392 | 47.0 | 0.097894 |
| 2B | 45.285062 | 0.044637 | 0.043391 | 100.000000 | 0.917177 | 0.041100 | 0.041100 | 17.0 | -0.219711 |
| 3B | 2.316999 | 0.004575 | 0.006853 | 100.000000 | 0.917177 | 0.002487 | 0.002487 | 1.0 | -0.163553 |
| HR | 18.272604 | 0.030167 | 0.027842 | 100.000000 | 0.917177 | 0.017440 | 0.017440 | 7.0 | -1.273097 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.18548159561267313, 'UBB': 0.05725277003760207, 'HBP': 0.188424337888687, '1B': -0.07438949507799174, '2B': -0.01356266769439693, '3B': 0.3265618132411719, 'HR': 0.100249966739873}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.1261542171732849, 'UBB': 0.008452275800063672, 'HBP': 0.07682858800523022, '1B': -0.020575555653956835, '2B': 0.02889912755702427, '3B': 0.026538485660782544, 'HR': 0.020092238127996175}}, {'feature': 'age_centered', 'scaled_input': 0.8, 'effects': {'K': 0.000574385688431482, 'UBB': -0.011514794893471585, 'HBP': 0.039079924799300184, '1B': -0.028741462885823528, '2B': -0.032207937752089646, '3B': -0.01650682923013411, 'HR': -0.07318516098759399}}, {'feature': 'position_4', 'scaled_input': 1.0, 'effects': {'K': -0.04853375856112188, 'UBB': -0.00889780302727799, 'HBP': -0.005483922528188057, '1B': 0.02254970754771804, '2B': -0.011294060174662945, '3B': 0.0031686867296098907, 'HR': -0.06840265134529423}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.029607121280075706, 'UBB': 0.048238385071555694, 'HBP': 0.015981255527476607, '1B': -0.014411440568423157, '2B': 0.030373509732192477, '3B': 0.03788712103494243, 'HR': 0.005222365076965767}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.015313007829259312, 'UBB': -0.011671594332561869, 'HBP': 0.01699051334280175, '1B': 0.012310486920049154, '2B': 0.0010342560580484652, '3B': -0.019086095797860574, 'HR': -0.040862012503046635}}, {'feature': 'age_squared', 'scaled_input': 0.6400000000000001, 'effects': {'K': 0.0012800297158753055, 'UBB': 0.01621419124188248, 'HBP': -0.028840763890741434, '1B': -0.006315397780698196, '2B': -0.024138841630794775, '3B': 0.009158090305028089, 'HR': -0.007568537326643991}}, {'feature': 'pooled_Aplus_K', 'scaled_input': 0.2555555555555558, 'effects': {'K': 0.028412862031520186, 'UBB': 0.019596933202907042, 'HBP': 0.0074190286858174, '1B': -0.007686287160656395, '2B': 0.000348073750052845, '3B': -0.0016478859949436995, 'HR': 0.02245201527790456}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.7, 'effects': {'K': -0.027763944716711706, 'UBB': 0.013316636101895396, 'HBP': 0.009950218218222071, '1B': -0.006229572616654761, '2B': -0.007561539003106783, '3B': -0.00134891927740572, 'HR': -0.010122412110709857}}, {'feature': 'scout_list_capacity_2', 'scaled_input': 1.0, 'effects': {'K': -0.02449997925038794, 'UBB': 0.01400426603168502, 'HBP': -0.010619525777571697, '1B': 0.01624534843881002, '2B': 0.0030638838540415817, '3B': 0.013251485953893076, 'HR': -0.0069871342480715345}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

### learned_reliability actual probability construction

| Event | Transported count | Origin environment | Prior | Alpha | Own influence before normalization | Blend | Final probability | Actual count | Batting wins per 600 contribution |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| other | 492.876070 | 0.465785 | 0.471403 | 324.313436 | 0.773479 | 0.451039 | 0.450262 | 148.0 | -0.000000 |
| K | 252.627515 | 0.222573 | 0.222137 | 107.072711 | 0.911836 | 0.227599 | 0.227207 | 100.0 | 0.000000 |
| UBB | 122.582704 | 0.079708 | 0.085188 | 286.343458 | 0.794551 | 0.105454 | 0.105272 | 44.0 | 0.890497 |
| HBP | 12.044102 | 0.010381 | 0.011261 | 314.542817 | 0.778794 | 0.010961 | 0.010942 | 3.0 | 0.020373 |
| 1B | 161.394944 | 0.142174 | 0.139785 | 533.910546 | 0.674705 | 0.143804 | 0.143557 | 47.0 | 0.061018 |
| 2B | 45.285062 | 0.044637 | 0.042480 | 1722.458403 | 0.391327 | 0.041859 | 0.041787 | 17.0 | -0.177024 |
| 3B | 2.316999 | 0.004575 | 0.004166 | 691.558749 | 0.615578 | 0.002889 | 0.002884 | 1.0 | -0.132404 |
| HR | 18.272604 | 0.030167 | 0.023579 | 328.499832 | 0.771224 | 0.018120 | 0.018089 | 7.0 | -1.208192 |

Largest actual conditional-prior log-odds accounting terms: [{'feature': 'intercept', 'scaled_input': 1.0, 'effects': {'K': 0.16829563916331855, 'UBB': 0.07194247423382868, 'HBP': -0.009081120102721423, '1B': -0.023990686442387017, '2B': 0.04852606710240515, '3B': -0.050050979107286266, 'HR': 0.0877473423338069}}, {'feature': 'age_centered', 'scaled_input': 0.8, 'effects': {'K': 0.001908031830962575, 'UBB': -0.022003840855976165, 'HBP': 0.011673747444806483, '1B': -0.021308189279691234, '2B': -0.040754200926004014, '3B': -0.09040757377196379, 'HR': -0.11416033757776028}}, {'feature': 'prior_debut', 'scaled_input': 1.0, 'effects': {'K': -0.11075367189972359, 'UBB': -0.006596171161144673, 'HBP': 0.027267028832365016, '1B': -0.022816970388250726, '2B': 0.022109512281764068, '3B': -0.033114256026125014, 'HR': -0.004056840974755469}}, {'feature': 'position_4', 'scaled_input': 1.0, 'effects': {'K': -0.05670090305413042, 'UBB': -0.01761335559530166, 'HBP': -0.010944514301949952, '1B': 0.0245074522413938, '2B': -0.0229185952166103, '3B': 0.017092056547171348, 'HR': -0.09620604367082247}}, {'feature': 'draft_known', 'scaled_input': 1.0, 'effects': {'K': 0.024301867964183353, 'UBB': 0.05225768991336001, 'HBP': 0.030958422903846098, '1B': -0.01625221905808649, '2B': 0.010930146753111254, '3B': 0.06147932416345276, 'HR': 0.009908921595629502}}, {'feature': 'draft_class_unknown', 'scaled_input': 1.0, 'effects': {'K': -0.01716611321180059, 'UBB': -0.0205688327710032, 'HBP': 0.026443258214436532, '1B': 0.011830079062292479, '2B': -0.0338117303274842, '3B': -0.016420060340563425, 'HR': -0.05721814208490634}}, {'feature': 'elapsed_scaled', 'scaled_input': 0.7, 'effects': {'K': -0.03174401187907159, 'UBB': 0.009013888775744336, 'HBP': -0.013858609811470595, '1B': 0.00913491637918252, '2B': 0.01705535310051263, '3B': -0.04186454287542801, 'HR': -0.020325383490528058}}, {'feature': 'draft_elapsed', 'scaled_input': 1.0, 'effects': {'K': -0.013578633580344484, 'UBB': -0.017197340352014732, 'HBP': -0.005132053322742395, '1B': 0.03905791567494701, '2B': -0.020428445822687297, '3B': 0.008704079971527272, 'HR': -0.006949059483841624}}, {'feature': 'pooled_Aplus_K', 'scaled_input': 0.2555555555555558, 'effects': {'K': 0.028680550504297853, 'UBB': 0.0185715281398277, 'HBP': 0.006402508741609735, '1B': -0.006648452340393244, '2B': -0.0021708383150149065, '3B': -0.006037629719867877, 'HR': 0.023249512542672254}}, {'feature': 'age_squared', 'scaled_input': 0.6400000000000001, 'effects': {'K': 0.0032222909357994683, 'UBB': 0.009986939902246257, 'HBP': -0.025507662008409714, '1B': -0.012601837261564783, '2B': -0.022026933626522152, '3B': 0.007025134941926743, 'HR': -0.014624799404713014}}]. These are saved fitted coefficients multiplied by this row's scaled inputs, not causal effects.

Forsythe's HR decline is 20 to six to two across 567, 439 and 416 PA. Adaptive -0.55 remains too optimistic versus actual -1.03, while old -1.04 is close. Expected PA is 225 versus 367, so adaptive delivered value 0.487 happens to match actual 0.488 through offsetting mistakes. Older power retained in the pooled anchor explains the optimism; perfect product accuracy is not proof of better talent. Mercer/Frazier produce modestly, Gyorko/Descalso struggle. The 132-person coarse profile does not excuse evaluating only the final product.

| Origin selected peer | Age | Prior MLB PA | AAA PA | AA PA | Old rate | Adaptive rate | Expected PA | Actual PA | Actual rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Jordy Mercer | 31.0 | 436 | 0.0 | 0.0 | -1.117998 | -0.914631 | 402.198210 | 271 | -0.192851 |
| Todd Frazier | 32.0 | 472 | 11.0 | 0.0 | 0.150902 | 0.344244 | 419.747891 | 499 | 0.517181 |
| Jedd Gyorko | 29.0 | 402 | 0.0 | 0.0 | 0.613521 | 0.965753 | 341.861009 | 101 | -4.778515 |
| Daniel Descalso | 31.0 | 423 | 0.0 | 0.0 | -0.115684 | 0.370874 | 332.920500 | 194 | -4.215922 |

## Decision after the actual reviews

Do not replace the existing batting forecast with either new arm. Learned reliability improves on fixed-100, but rate RMSE 1.85346 is worse than working 1.82465 and contribution RMSE .44351 is worse than .43815 on the same binary workload. Nominal player-clustered intervals favor working. Adaptive alpha never hits declared bounds and all 70 heads converge; these execution passes do not make it a predictive winner.

Established Judge and Votto demonstrate a useful MLB anchor; Judge’s debut, Winn, Steer and Betts demonstrate missing development/translation. Alonso/Bellinger/Kurtz power and fast entry remain major failures. Volpe improves talent but workload remains low. Forsythe and Nevin show how accurate delivered value can hide opposing errors. Tiny-sample Kratz/Lee/Cozens/Reed rates are not latent-talent conclusions. Only origin 2021 improves versus the working rate; do not generalize that result.

Retain this implementation and learned differential trust as research, not deployment or proof that all explicit shrinkage fails. Next complete a common-unit public hitting comparison and isolate substantive talent/population gaps under the controlling plan. No frozen forecast change or goal completion.
