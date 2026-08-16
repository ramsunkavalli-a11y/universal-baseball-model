from universal_baseball.bin_value_policy import (
    bin_value_policy_for_league,
    bin_value_policy_for_level,
)


def test_certified_level_policies() -> None:
    aaa = bin_value_policy_for_level("AAA")
    aa = bin_value_policy_for_level("AA")
    high_a = bin_value_policy_for_level("High-A")
    single_a = bin_value_policy_for_level("single_a")
    rookie = bin_value_policy_for_level("rookie_complex")

    assert (aaa.status, aaa.prior_strength, aaa.uses_pooling) == (
        "certified_pooled",
        25,
        True,
    )
    assert (aa.status, aa.prior_strength, aa.uses_pooling) == (
        "certified_pooled",
        75,
        True,
    )
    assert (high_a.status, high_a.prior_strength, high_a.uses_pooling) == (
        "certified_direct",
        0,
        False,
    )
    assert (single_a.status, single_a.prior_strength, single_a.uses_pooling) == (
        "certified_pooled",
        25,
        True,
    )
    assert (rookie.status, rookie.prior_strength, rookie.uses_pooling) == (
        "certified_direct",
        0,
        False,
    )


def test_league_mapping_uses_only_same_level_policy() -> None:
    for league_id in (109, 111, 113):
        assert bin_value_policy_for_league(league_id).level_group == "AA"
        assert bin_value_policy_for_league(league_id).prior_strength == 75
    for league_id in (116, 118, 126):
        assert bin_value_policy_for_league(league_id).level_group == "HIGH_A"
        assert bin_value_policy_for_league(league_id).prior_strength == 0
    for league_id in (110, 122, 123):
        assert bin_value_policy_for_league(league_id).level_group == "SINGLE_A"
        assert bin_value_policy_for_league(league_id).prior_strength == 25


def test_unknown_levels_and_leagues_are_not_silently_certified() -> None:
    assert bin_value_policy_for_level("MLB").status == "uncertified"
    assert bin_value_policy_for_league(999999).status == "uncertified"
