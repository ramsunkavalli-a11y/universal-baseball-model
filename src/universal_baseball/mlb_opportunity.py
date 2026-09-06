"""Strict official PA labels and a fixed, prior-season opportunity benchmark."""

import numpy as np
import polars as pl

from universal_baseball.hitter_history_transport import canonical_level


def project_pages(pages, season):
    """Refuse partial pages, changing totals, duplicate IDs, and invalid counts."""
    rows = []
    total = None
    for payload in pages:
        groups = payload.get("stats", [])
        if len(groups) != 1:
            raise ValueError("Expected one stats group")
        group = groups[0]
        declared = group.get("totalSplits")
        if not isinstance(declared, int) or declared <= 0:
            raise ValueError("Missing positive pagination total")
        if total is not None and total != declared:
            raise ValueError("Pagination total changed")
        total = declared
        splits = group.get("splits", [])
        if not splits:
            raise ValueError("Empty participation page")
        for split in splits:
            if str(split.get("season")) != str(season):
                raise ValueError("Wrong participation season")
            pid = split.get("player", {}).get("id")
            pa = split.get("stat", {}).get("plateAppearances")
            if type(pid) is not int or pid <= 0 or type(pa) is not int or pa < 0:
                raise ValueError("Invalid participant ID or PA")
            rows.append({"player_id": pid, "mlb_pa": pa})
    if not rows or len(rows) != total:
        raise ValueError("Incomplete participation pagination")
    frame = pl.DataFrame(rows)
    if frame["player_id"].n_unique() != frame.height:
        raise ValueError("Duplicate participant")
    return frame.sort("player_id")


def certify_participation(all_mlb, al, nl):
    combined = pl.concat([al, nl]).group_by("player_id").agg(pl.col("mlb_pa").sum())
    if not all_mlb.sort("player_id").equals(combined.sort("player_id")):
        raise ValueError("MLB and AL/NL participation disagree")
    return all_mlb


def build_cohort(history, prior_mlb, year):
    if history["season"].max() >= year:
        raise ValueError("History crosses forecast cutoff")
    previous = history.filter(pl.col("season") == year - 1)
    minor = (
        previous.with_columns(
            pl.col("level_group").map_elements(canonical_level, return_dtype=pl.String)
        )
        .filter((pl.col("level_group") != "MLB") & (pl.col("batting_PA") > 0))
        .select("player_id", "level_group", pl.col("batting_PA").alias("prior_pa"))
    )
    major = prior_mlb.filter(pl.col("mlb_pa") > 0).select(
        "player_id",
        pl.lit("MLB").alias("level_group"),
        pl.col("mlb_pa").alias("prior_pa"),
    )
    rows = (
        pl.concat([minor, major])
        .group_by("player_id", "level_group")
        .agg(pl.col("prior_pa").sum())
    )
    cohort = (
        rows.sort(
            ["player_id", "prior_pa", "level_group"], descending=[False, True, False]
        )
        .unique("player_id", keep="first", maintain_order=True)
        .rename({"level_group": "origin", "prior_pa": "origin_pa"})
        .join(prior_mlb, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col("mlb_pa").fill_null(0).alias("prior_mlb_pa"))
        .drop("mlb_pa")
        .with_columns(
            pl.when(pl.col("prior_mlb_pa") == 0)
            .then(pl.lit("0"))
            .when(pl.col("prior_mlb_pa") < 100)
            .then(pl.lit("1-99"))
            .otherwise(pl.lit("100+"))
            .alias("exposure"),
            pl.lit(year).alias("year"),
        )
        .sort("player_id")
    )
    return cohort


def label_cohort(cohort, certified_participation):
    """Caller must supply the season's fully certified participation frame."""
    return (
        cohort.join(certified_participation, on="player_id", how="left", validate="1:1")
        .with_columns(pl.col("mlb_pa").fill_null(0))
        .with_columns(
            (pl.col("mlb_pa") > 0).cast(pl.Float64).alias("any_pa"),
            (pl.col("mlb_pa") >= 100).cast(pl.Float64).alias("pa100"),
        )
    )


def predict_opportunity(training, cohort):
    if training.is_empty() or training["year"].max() >= cohort["year"].min():
        raise ValueError("Opportunity training must precede forecasts")
    targets = ["any_pa", "pa100", "mlb_pa"]
    global_mean = training.select(targets).mean().row(0)
    references = {
        key[0]: group.select(targets).mean().row(0)
        for key, group in training.group_by("exposure")
    }
    cells = {}
    for key, group in training.group_by("origin", "exposure"):
        prior = np.array(references[key[1]])
        means = (group.select(targets).sum().to_numpy()[0] + 50 * prior) / (
            group.height + 50
        )
        cells[key] = means.tolist()
    rows = []
    for row in cohort.to_dicts():
        reference = references.get(row["exposure"], global_mean)
        level = cells.get((row["origin"], row["exposure"]), reference)
        rows.append(
            {
                **row,
                **{
                    f"{model}_{target}": float(value)
                    for model, values in (("REFERENCE", reference), ("LEVEL", level))
                    for target, value in zip(targets, values)
                },
            }
        )
    parameters = {
        "global": list(global_mean),
        "references": references,
        "cells": [
            {"origin": k[0], "exposure": k[1], "means": v}
            for k, v in sorted(cells.items())
        ],
        "training_years": sorted(training["year"].unique().to_list()),
    }
    return pl.DataFrame(rows), parameters
