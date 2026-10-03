# V30 reporting repair — no statistical change

The fixed batch finished all 210 fits and saved every prediction. Reporting then failed because the cohort summary referred to `pa_1`, which was not among the saved model inputs. The independent reporting script joins this existing source column by unique row ID solely for reporting and traces. It preserves the original runner, input hashes, models, training memberships and prediction bytes. No refitting, parameter search or forecast repair is authorized by this amendment.
