"""Frozen source expectations for the Pitching v1 development inventory."""

from __future__ import annotations

from dataclasses import dataclass


PITCHING_DEVELOPMENT_SEASONS = (2021, 2022, 2023, 2024)
PITCHING_FILENAME_LEVELS = ("aaa", "aa", "a+", "a", "rk")

# The 2024 hashes were recovered from successful all-level certification run
# 31925028241, artifact 9257560686.  The 2021-2023 hashes were captured by the
# pre-outcome Pitching v1 inventory on 2026-08-20 before any candidate scoring.
# A later upstream correction is evidence to adjudicate, not a silent source
# replacement.
FROZEN_2021_2024_MILB_PITCHING_SHA256 = {
    "2021_aaa_season_pitching_stats.csv": "64f71c3f0954d76354755c2e0c891b244f2ed851e74c7d645996e837d060884e",
    "2021_aa_season_pitching_stats.csv": "4de7ca48b5defa2a4ba973991dd4e7abfeb3351384f308baa5e24524eb1dd2c3",
    "2021_a+_season_pitching_stats.csv": "3240b815343696b657209a48e815a513d38d9e93f0e85147a3049eeb049e0e34",
    "2021_a_season_pitching_stats.csv": "79875dcd6b00ad944c277364dd3997cfae84da7d8c8d4e26a4185e34f7c760ef",
    "2021_rk_season_pitching_stats.csv": "48a6e0fe7d58ff5e3370d237a85ae7f77cb4374cc38a3eb2f8da72daffa718c8",
    "2022_aaa_season_pitching_stats.csv": "0ee75d2c06cd666bd632b7546f18792d9ec957b94ca9a088c78b8f46185be6db",
    "2022_aa_season_pitching_stats.csv": "f9201e520c8e3d79583488a2524ed5da0848017c6ffe68f7a4349479ea8620ea",
    "2022_a+_season_pitching_stats.csv": "395fccb67525cb5dac7856103be35807a0cb25ff8a371aa6e50a666ce5c583a0",
    "2022_a_season_pitching_stats.csv": "01046476a5cca7f68af5c3eac1cce1ceda7a65afd457ae64730b62a2b3815146",
    "2022_rk_season_pitching_stats.csv": "406fd7f27bad52f926eaf012ad15f90911a30e9bd247a2eae45420bd0ec7ddbd",
    "2023_aaa_season_pitching_stats.csv": "566fa8d03307113dac291a162ddc46d9459a618855a4516ddd0a61e53e956330",
    "2023_aa_season_pitching_stats.csv": "a98c612560a21c668a95dfac854c533a94edf08e91ee81e68ab6ce8e014a7be1",
    "2023_a+_season_pitching_stats.csv": "a3e0dced62fe5a5f018723ed92e8a6710caa0ef16a618a8fd12d2f1d30b4b823",
    "2023_a_season_pitching_stats.csv": "d85e16640cc290cbdd05b754f1cbaa6a9e4f17f68c19a87cb797b776491173e1",
    "2023_rk_season_pitching_stats.csv": "bb9277dcae8a96778671760e301764ea3b15caf2ad10511d518ef9fb8777b2a4",
    "2024_aaa_season_pitching_stats.csv": "3758daea753ef884a2cd195239ac49219ac483346e06decb85d0e9667f612b33",
    "2024_aa_season_pitching_stats.csv": "3a25ba0d1f839b227d00a44bc2f711efa18753ff767a4e4cdab55f95eb014c24",
    "2024_a+_season_pitching_stats.csv": "a04435ae10e10778b18c8da429386cf102ac750aa2bdd6ced3ab511b6242e832",
    "2024_a_season_pitching_stats.csv": "c83051b3991e067feb4356992c2dc7a8eea97004f5548f9e1d0a8579b19711b0",
    "2024_rk_season_pitching_stats.csv": "bda8ce69aaa9201ea410ee1ffa66243a830af2987c7ba28c4f9f25ef1f2b713a",
}


@dataclass(frozen=True, slots=True)
class PitchingSourceSpec:
    season: int
    filename_level: str
    asset_name: str


def expected_pitching_source_specs() -> tuple[PitchingSourceSpec, ...]:
    """Return the fixed pre-2025 MiLB source inventory in deterministic order."""

    return tuple(
        PitchingSourceSpec(
            season=season,
            filename_level=filename_level,
            asset_name=f"{season}_{filename_level}_season_pitching_stats.csv",
        )
        for season in PITCHING_DEVELOPMENT_SEASONS
        for filename_level in PITCHING_FILENAME_LEVELS
    )


def validate_frozen_pitching_sha(asset_name: str, observed_sha256: str) -> None:
    """Fail if a development source asset no longer matches its frozen bytes."""

    expected = FROZEN_2021_2024_MILB_PITCHING_SHA256.get(asset_name)
    if expected is None:
        raise ValueError(f"unexpected Pitching v1 development source asset: {asset_name}")
    if observed_sha256.lower() != expected:
        raise ValueError(
            f"frozen Pitching v1 source byte drift for {asset_name}: "
            f"expected {expected}, observed {observed_sha256.lower()}"
        )
