from universal_baseball.free_agent_market_source import (
    parse_fangraphs_free_agent_tracker_html,
)


HTML = """
<table><tbody>
<tr><td data-stat="Name"><a href="/players/juan-soto/20123/stats/batting">Juan Soto</a></td>
<td data-col-id="position">LF/RF</td><td data-stat="Prev Team">NYY</td>
<td data-col-id="age">26</td><td data-col-id="servicetime">6.134</td>
<td data-col-id="war_prev">8.2</td><td data-col-id="war_proj"></td>
<td data-col-id="med_years">13</td><td data-col-id="med_total">$585.0M</td>
<td data-col-id="med_aav">$45.0M</td><td data-stat="Signing Team">NYM</td>
<td data-col-id="YearsTotal">15</td><td data-col-id="ContractTotal">$765.00M</td>
<td data-col-id="aav">$51.00M</td><td data-col-id="contract_link">📝</td></tr>
</tbody></table>
"""


def test_tracker_parser_keeps_stable_id_and_money() -> None:
    result = parse_fangraphs_free_agent_tracker_html(
        HTML, free_agent_year=2025, source_url="https://example.test",
        source_snapshot_id="fg:2025:test",
    )
    assert result.height == 1
    assert result.item(0, "fangraphs_id") == "20123"
    assert result.item(0, "contract_total_dollars") == 765_000_000
    assert result.item(0, "contract_effective_total_dollars") == 765_000_000
    assert result.item(0, "projected_war") is None
    assert result.item(0, "contract_note_present") is True


def test_tracker_parser_collapses_only_exact_duplicate_table_rows() -> None:
    result = parse_fangraphs_free_agent_tracker_html(
        HTML + HTML, free_agent_year=2025, source_url="https://example.test",
        source_snapshot_id="fg:2025:test",
    )
    assert result.height == 1


def test_tracker_parser_supports_old_contract_columns_and_minor_deals() -> None:
    old_html = """
    <table><tbody><tr>
    <td data-stat="Name"><a href="/players/example/123/stats/batting">Example</a></td>
    <td data-stat="Signing Team">SEA</td>
    <td data-col-id="contract_years">1</td>
    <td data-col-id="contract_total">MiLB</td>
    </tr></tbody></table>
    """
    result = parse_fangraphs_free_agent_tracker_html(
        old_html, free_agent_year=2020, source_url="https://example.test",
        source_snapshot_id="fg:2020:test",
    )
    assert result.item(0, "contract_years") == 1
    assert result.item(0, "contract_total_dollars") is None
    assert result.item(0, "contract_value_status") == "minor_league_contract"
