# Phase 1 missing-buyout assumption — 2026-09-09

The exact contract-input layer keeps every unreported option buyout null. That is the
source-of-truth boundary. It leaves 41 otherwise calculable option rows blocked after
official option-type corrections are applied.

For the broad Phase 1 research scenario only, those rows now use the observed median
buyout as a share of option salary:

- club option: 13.02% from 60 observed rows;
- mutual option: 18.75% from 29 observed rows;
- player option: 11.90% from four observed rows;
- player opt-out: 13.33% overall-median fallback because no same-status rows are
  observed.

The reference contains 93 source-linked rows with both salary and buyout. Exact linked
facts always override the estimate. Estimated rows carry an explicit `salary_basis`
label and remain a research scenario, not a claim about legal contract terms.

This raises scenario coverage from 50,043 to 50,084 of 50,100 annual rows. Phase 2
should replace estimates with exact transaction details and test whether the ratios
need salary-tier, option-year or contract-type adjustments.
