import argparse

import pytest

from scripts.materialize_opportunity_40man_history import parse_seasons


def test_parse_seasons_sorts_and_deduplicates() -> None:
    assert parse_seasons("2024, 2022,2024") == (2022, 2024)


def test_parse_seasons_requires_a_value() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        parse_seasons(" , ")
