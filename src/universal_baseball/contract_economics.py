"""Static annual contract economics with explicit rights and obligations."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Mapping

import polars as pl

from universal_baseball.cba_rules import CBARuleset
from universal_baseball.free_agent_market import market_war_tier


ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "season": pl.Int64,
    "projected_war_mean": pl.Float64,
    "projected_war_lower": pl.Float64,
    "projected_war_upper": pl.Float64,
    "control_status": pl.String,
    "known_salary_dollars": pl.Int64,
    "buyout_dollars": pl.Int64,
    "arbitration_class": pl.Int64,
    "arbitration_salary_basis_war": pl.Float64,
    "arbitration_salary_basis_source": pl.String,
    "projection_source_id": pl.String,
    "contract_source_id": pl.String,
    "contract_structure_review_reason": pl.String,
}

ANNUAL_CONTRACT_ECONOMICS_SCHEMA: dict[str, pl.DataType] = {
    **ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA,
    "ruleset_id": pl.String,
    "assumptions_id": pl.String,
    "market_model_id": pl.String,
    "arbitration_model_id": pl.String,
    "dollars_per_war": pl.Float64,
    "market_war_tier": pl.String,
    "fa_equivalent_value_dollars": pl.Float64,
    "salary_cost_dollars": pl.Float64,
    "salary_basis": pl.String,
    "static_surplus_dollars": pl.Float64,
    "contract_control_value_dollars": pl.Float64,
    "optionality_premium_dollars": pl.Float64,
    "contract_value_lower_dollars": pl.Float64,
    "contract_value_upper_dollars": pl.Float64,
    "discount_factor": pl.Float64,
    "discounted_contract_value_dollars": pl.Float64,
    "decision_at_mean": pl.String,
    "calculation_status": pl.String,
    "review_reason": pl.String,
}

AGGREGATE_CONTRACT_ECONOMICS_SCHEMA: dict[str, pl.DataType] = {
    "as_of_date": pl.Date,
    "player_id": pl.Int64,
    "organization_id": pl.Int64,
    "ruleset_id": pl.String,
    "assumptions_id": pl.String,
    "annual_rows": pl.Int64,
    "review_rows": pl.Int64,
    "fa_equivalent_value_dollars": pl.Float64,
    "salary_cost_dollars": pl.Float64,
    "static_surplus_dollars": pl.Float64,
    "contract_control_value_dollars": pl.Float64,
    "optionality_premium_dollars": pl.Float64,
    "discounted_contract_value_dollars": pl.Float64,
    "calculation_status": pl.String,
}


@dataclass(frozen=True)
class ContractEconomicsAssumptions:
    """Named research assumptions that are not CBA facts."""

    assumptions_id: str
    market_model_id: str
    arbitration_model_id: str
    dollars_per_war_by_year: Mapping[int, float]
    arbitration_share_by_class: Mapping[int, float]
    annual_discount_rate: float
    tiered_dollars_per_war_by_year: Mapping[int, Mapping[str, float]] | None = None
    floor_market_value_at_zero: bool = True

    def validate(self) -> None:
        if not self.assumptions_id or not self.market_model_id:
            raise ValueError("economics assumptions require stable model IDs")
        if not self.arbitration_model_id:
            raise ValueError("arbitration assumptions require a stable model ID")
        if not isfinite(self.annual_discount_rate) or self.annual_discount_rate < 0:
            raise ValueError("annual discount rate must be finite and nonnegative")
        tiers = self.tiered_dollars_per_war_by_year or {}
        if not self.dollars_per_war_by_year and not tiers:
            raise ValueError("at least one dated dollars-per-WAR assumption is required")
        if set(self.dollars_per_war_by_year) & set(tiers):
            raise ValueError("a season cannot have both flat and tiered market rates")
        if any(not isfinite(float(value)) or float(value) <= 0 for value in self.dollars_per_war_by_year.values()):
            raise ValueError("dollars-per-WAR assumptions must be finite and positive")
        for season, season_tiers in tiers.items():
            if set(season_tiers) != {"0-1", "1-2", "2+"}:
                raise ValueError(
                    f"tiered market rates for {season} require 0-1, 1-2, and 2+"
                )
            if any(
                not isfinite(float(value)) or float(value) <= 0
                for value in season_tiers.values()
            ):
                raise ValueError("tiered dollars-per-WAR assumptions must be positive")
        if any(
            int(year) not in {1, 2, 3, 4}
            or not isfinite(float(share))
            or not 0 <= float(share) <= 1
            for year, share in self.arbitration_share_by_class.items()
        ):
            raise ValueError("arbitration shares require classes 1-4 and values from 0 to 1")

    def dollars_per_war(self, season: int) -> float:
        try:
            return float(self.dollars_per_war_by_year[season])
        except KeyError as exc:
            raise ValueError(f"no dollars-per-WAR assumption for {season}") from exc

    def market_rate(self, season: int, projected_war: float) -> tuple[float, str]:
        """Return the flat rate or whole-season projected-WAR tier rate."""

        if season in self.dollars_per_war_by_year:
            return float(self.dollars_per_war_by_year[season]), "flat"
        tiers = self.tiered_dollars_per_war_by_year or {}
        try:
            season_tiers = tiers[season]
        except KeyError as exc:
            raise ValueError(f"no dollars-per-WAR assumption for {season}") from exc
        tier = market_war_tier(projected_war)
        return float(season_tiers[tier]), tier


@dataclass(frozen=True)
class ContractEconomicsResult:
    annual: pl.DataFrame
    aggregate: pl.DataFrame
    reviews: pl.DataFrame


def _market_value(war: float, dollars_per_war: float, *, floor_at_zero: bool) -> float:
    value = war * dollars_per_war
    return max(value, 0.0) if floor_at_zero else value


def _decision_value(status: str, market_value: float, salary: float, buyout: float) -> tuple[float, float, str]:
    exercise = market_value - salary
    if status == "current_season_committed":
        return salary, exercise, "current_season_committed"
    if status in {"pre_arbitration", "arbitration", "arbitration_eligible", "super_two_eligible"}:
        return (salary, exercise, "tender") if exercise >= 0 else (0.0, 0.0, "non_tender")
    if status == "club_option":
        decline = -buyout
        return (salary, exercise, "exercise_club_option") if exercise >= decline else (buyout, decline, "decline_club_option")
    if status in {"player_option", "player_opt_out"}:
        leave = -buyout
        return (salary, exercise, "player_stays") if exercise <= leave else (buyout, leave, "player_leaves")
    if status == "mutual_option":
        # At one shared exercise price, the player and club generally prefer
        # opposite branches. Phase 1 therefore uses the normal expiration outcome
        # instead of inventing a negotiated extension or correlated valuation gap.
        return buyout, -buyout, "decline_mutual_option"
    if status == "guaranteed_contract":
        return salary, exercise, "guaranteed"
    if status in {"free_agent", "free_agent_eligible"}:
        return 0.0, 0.0, "no_incumbent_rights"
    raise ValueError(f"unsupported control status: {status}")


def _empty_result() -> ContractEconomicsResult:
    annual = pl.DataFrame(schema=ANNUAL_CONTRACT_ECONOMICS_SCHEMA)
    return ContractEconomicsResult(
        annual=annual,
        aggregate=pl.DataFrame(schema=AGGREGATE_CONTRACT_ECONOMICS_SCHEMA),
        reviews=annual,
    )


def value_annual_contract_states(
    annual_inputs: pl.DataFrame,
    *,
    cba_ruleset: CBARuleset,
    assumptions: ContractEconomicsAssumptions,
) -> ContractEconomicsResult:
    """Value annual mean scenarios without changing the supplied WAR forecast.

    Lower and upper WAR inputs are sensitivity bounds. They are not probabilities.
    Unsupported or insufficiently specified states are retained as review rows.
    """

    assumptions.validate()
    missing = sorted(set(ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA) - set(annual_inputs.columns))
    if missing:
        raise ValueError(f"contract economics inputs missing columns: {missing}")
    source = annual_inputs.select(list(ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA)).cast(
        ANNUAL_CONTRACT_ECONOMICS_INPUT_SCHEMA, strict=True
    )
    if source.is_empty():
        return _empty_result()
    required_non_null = [
        "as_of_date",
        "player_id",
        "organization_id",
        "season",
        "projected_war_mean",
        "control_status",
        "projection_source_id",
        "contract_source_id",
    ]
    if sum(source.select(required_non_null).null_count().row(0)):
        raise ValueError("contract economics inputs contain null required values")
    if (
        source.group_by(["player_id", "organization_id", "season"])
        .len()
        .filter(pl.col("len") > 1)
        .height
    ):
        raise ValueError("contract economics inputs contain duplicate player-season rights")
    if source.get_column("as_of_date").n_unique() != 1:
        raise ValueError("contract economics inputs require one as-of date")
    if source.filter(
        (pl.col("player_id") <= 0)
        | (pl.col("organization_id") <= 0)
        | (pl.col("season") < pl.col("as_of_date").dt.year())
        | pl.col("projected_war_mean").is_nan()
        | pl.col("projected_war_mean").is_infinite()
        | pl.col("projected_war_lower").is_nan()
        | pl.col("projected_war_lower").is_infinite()
        | pl.col("projected_war_upper").is_nan()
        | pl.col("projected_war_upper").is_infinite()
        | (pl.col("known_salary_dollars") < 0)
        | (pl.col("buyout_dollars") < 0)
        | (pl.col("control_status") == "")
        | (pl.col("projection_source_id") == "")
        | (pl.col("contract_source_id") == "")
    ).height:
        raise ValueError("contract economics inputs contain invalid identities, dates, WAR or costs")
    if source.filter(
        (pl.col("projected_war_lower").is_not_null() & (pl.col("projected_war_lower") > pl.col("projected_war_mean")))
        | (pl.col("projected_war_upper").is_not_null() & (pl.col("projected_war_upper") < pl.col("projected_war_mean")))
    ).height:
        raise ValueError("WAR sensitivity bounds must contain the mean")

    rows: list[dict[str, object]] = []
    for source_row in source.iter_rows(named=True):
        row = dict(source_row)
        season = int(row["season"])
        status = str(row["control_status"])
        calculation_status = "available"
        review_reason = ""
        salary_basis = ""
        decision = ""
        market_tier = ""
        rate: float | None = None
        market: float | None = None
        cost: float | None = None
        static: float | None = None
        value: float | None = None
        premium: float | None = None
        lower_value: float | None = None
        upper_value: float | None = None
        try:
            mean_war = float(row["projected_war_mean"])
            rate, market_tier = assumptions.market_rate(season, mean_war)
            if market_tier != "flat" and season == row["as_of_date"].year:
                raise ValueError(
                    "tiered market rates require a full-season WAR tier, not current "
                    "rest-of-season WAR"
                )
            lower_war = mean_war if row["projected_war_lower"] is None else float(row["projected_war_lower"])
            upper_war = mean_war if row["projected_war_upper"] is None else float(row["projected_war_upper"])
            market = _market_value(mean_war, rate, floor_at_zero=assumptions.floor_market_value_at_zero)
            market_lower = _market_value(lower_war, rate, floor_at_zero=assumptions.floor_market_value_at_zero)
            market_upper = _market_value(upper_war, rate, floor_at_zero=assumptions.floor_market_value_at_zero)

            if row["contract_structure_review_reason"]:
                raise ValueError(str(row["contract_structure_review_reason"]))

            known_salary = row["known_salary_dollars"]
            if status in {"free_agent", "free_agent_eligible"}:
                salary = 0.0
                buyout = 0.0
                salary_basis = "none_no_incumbent_rights"
            elif status == "pre_arbitration":
                salary = float(known_salary) if known_salary is not None else float(cba_ruleset.minimum_salary(season))
                buyout = 0.0
                salary_basis = "known_salary" if known_salary is not None else "cba_minimum"
            elif status in {"arbitration", "arbitration_eligible", "super_two_eligible"}:
                if known_salary is not None:
                    salary = float(known_salary)
                    salary_basis = "known_salary"
                else:
                    arbitration_class = row["arbitration_class"]
                    if arbitration_class is None or int(arbitration_class) not in assumptions.arbitration_share_by_class:
                        raise ValueError("arbitration salary requires a configured arbitration class")
                    arbitration_basis_war = row["arbitration_salary_basis_war"]
                    if arbitration_basis_war is None:
                        raise ValueError("arbitration salary requires a prior-performance WAR basis")
                    arbitration_rate, _ = assumptions.market_rate(
                        season, float(arbitration_basis_war)
                    )
                    arbitration_market_value = _market_value(
                        float(arbitration_basis_war),
                        arbitration_rate,
                        floor_at_zero=assumptions.floor_market_value_at_zero,
                    )
                    salary = max(
                        float(cba_ruleset.minimum_salary(season)),
                        arbitration_market_value
                        * float(
                            assumptions.arbitration_share_by_class[
                                int(arbitration_class)
                            ]
                        ),
                    )
                    salary_basis = (
                        "configured_arbitration_share_of_"
                        + str(row["arbitration_salary_basis_source"])
                    )
                buyout = 0.0
            elif status in {
                "guaranteed_contract",
                "current_season_committed",
                "club_option",
                "player_option",
                "player_opt_out",
                "mutual_option",
            }:
                if known_salary is None:
                    raise ValueError(f"{status} requires a known salary")
                salary = float(known_salary)
                if status in {
                    "club_option",
                    "player_option",
                    "player_opt_out",
                    "mutual_option",
                } and row["buyout_dollars"] is None:
                    raise ValueError(f"{status} requires an explicit buyout, including zero")
                buyout = float(row["buyout_dollars"] or 0)
                salary_basis = "known_contract"
            elif status == "vesting_option":
                raise ValueError(f"{status} requires a future trigger/decision model")
            else:
                raise ValueError(f"unsupported control status: {status}")

            cost, value, decision = _decision_value(status, market, salary, buyout)
            _, lower_value, _ = _decision_value(status, market_lower, salary, buyout)
            _, upper_value, _ = _decision_value(status, market_upper, salary, buyout)
            static = 0.0 if status in {"free_agent", "free_agent_eligible"} else market - salary
            premium = value - static
        except ValueError as exc:
            calculation_status = "review"
            review_reason = str(exc)

        years_out = season - row["as_of_date"].year
        discount_factor = 1.0 / ((1.0 + assumptions.annual_discount_rate) ** years_out)
        rows.append(
            {
                **row,
                "ruleset_id": cba_ruleset.ruleset_id,
                "assumptions_id": assumptions.assumptions_id,
                "market_model_id": assumptions.market_model_id,
                "arbitration_model_id": assumptions.arbitration_model_id,
                "dollars_per_war": rate,
                "market_war_tier": market_tier,
                "fa_equivalent_value_dollars": market,
                "salary_cost_dollars": cost,
                "salary_basis": salary_basis,
                "static_surplus_dollars": static,
                "contract_control_value_dollars": value,
                "optionality_premium_dollars": premium,
                "contract_value_lower_dollars": lower_value,
                "contract_value_upper_dollars": upper_value,
                "discount_factor": discount_factor,
                "discounted_contract_value_dollars": None if value is None else value * discount_factor,
                "decision_at_mean": decision,
                "calculation_status": calculation_status,
                "review_reason": review_reason,
            }
        )

    annual = pl.DataFrame(rows, schema=ANNUAL_CONTRACT_ECONOMICS_SCHEMA).sort(
        ["player_id", "organization_id", "season"]
    )
    aggregate_rows: list[dict[str, object]] = []
    for group in annual.partition_by(["player_id", "organization_id"], maintain_order=True):
        first = group.row(0, named=True)
        review_count = group.filter(pl.col("calculation_status") != "available").height
        available = review_count == 0

        def total(column: str) -> float | None:
            return float(group.get_column(column).sum()) if available else None

        aggregate_rows.append(
            {
                "as_of_date": first["as_of_date"],
                "player_id": first["player_id"],
                "organization_id": first["organization_id"],
                "ruleset_id": first["ruleset_id"],
                "assumptions_id": first["assumptions_id"],
                "annual_rows": group.height,
                "review_rows": review_count,
                "fa_equivalent_value_dollars": total("fa_equivalent_value_dollars"),
                "salary_cost_dollars": total("salary_cost_dollars"),
                "static_surplus_dollars": total("static_surplus_dollars"),
                "contract_control_value_dollars": total("contract_control_value_dollars"),
                "optionality_premium_dollars": total("optionality_premium_dollars"),
                "discounted_contract_value_dollars": total("discounted_contract_value_dollars"),
                "calculation_status": "available" if available else "review",
            }
        )
    aggregate = pl.DataFrame(
        aggregate_rows, schema=AGGREGATE_CONTRACT_ECONOMICS_SCHEMA
    ).sort(["player_id", "organization_id"])
    reviews = annual.filter(pl.col("calculation_status") != "available")
    return ContractEconomicsResult(annual=annual, aggregate=aggregate, reviews=reviews)
