import polars as pl

from universal_baseball.prospect_value import (
    attach_mlbam_ids,
    benchmark_value_from_model_fv,
    display_fv,
    model_fv_from_expected_war,
    parse_fangraphs_top100_html,
)


def _top100_html() -> str:
    rows = []
    for rank in range(1, 101):
        name = "Josuar Gonzalez" if rank == 30 else f"Player {rank}"
        rows.append(
            f"<tr><td>{rank}</td><td><a href='https://example/{rank}'>{name}</a></td>"
            f"<td>SS</td><td>SFG</td><td>18.8</td><td>50</td><td></td><td>2030</td></tr>"
        )
    return "<html><table>" + "".join(rows) + "</table></html>"


def test_top100_parser_attaches_published_50_fv_hitter_value() -> None:
    result = parse_fangraphs_top100_html(_top100_html())
    josuar = result.filter(pl.col("rank") == 30).row(0, named=True)

    assert josuar["player_name"] == "Josuar Gonzalez"
    assert josuar["expected_surplus_value_dollars"] == 45_000_000
    assert josuar["expected_controlled_war"] == 7.0


def test_prospect_identity_requires_name_and_organization() -> None:
    rankings = parse_fangraphs_top100_html(_top100_html()).filter(pl.col("rank") == 30)
    players = pl.DataFrame(
        {
            "player_id": [829034, 1],
            "player_name": ["Josuar González", "Josuar Gonzalez"],
            "organization_id": [137, 135],
        }
    )
    result = attach_mlbam_ids(rankings, players)

    assert result.item(0, "player_id") == 829034
    assert result.item(0, "identity_status") == "exact_name_and_organization"


def test_model_fv_uses_our_war_and_only_benchmark_scale() -> None:
    assert model_fv_from_expected_war(7.0, "hitter") == 50.0
    assert model_fv_from_expected_war(5.0, "pitcher") == 50.0
    assert display_fv(52.4) == 50
    assert display_fv(52.5) == 55
    assert benchmark_value_from_model_fv(50.0, "hitter") == 45_000_000.0
    assert benchmark_value_from_model_fv(50.0, "pitcher") == 33_500_000.0
