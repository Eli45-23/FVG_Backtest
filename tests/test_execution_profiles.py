import pytest
from engine.runner import RunConfig, run
from engine.execution_profiles import data_hashes, source_identity
from engine.data import identities

SOURCE = """from engine.strategy import Entry
from decimal import Decimal as D
class Strategy:
    def on_bar(self,ctx,p):
        if ctx.bar.time=='09:35': return Entry('LONG',ctx.bar.close-D('5'),D('2'))
"""


def test_legacy_missing_field_resolves_legacy():
    assert RunConfig().dataset_profile == "legacy_2024_2026"
    assert data_hashes() == identities()


def test_research_dates():
    RunConfig(
        start="2020-01-01", end="2020-02-01", dataset_profile="research_2020_2026"
    ).validate()
    with pytest.raises(ValueError):
        RunConfig(start="2020-01-01").validate()
    with pytest.raises(ValueError):
        RunConfig(dataset_profile="unknown").validate()


def test_2020_real_execution_and_identity():
    cfg = RunConfig(
        start="2020-01-06", end="2020-01-08", dataset_profile="research_2020_2026"
    )
    a = run(SOURCE, {}, cfg)
    assert len(a["trades"]) == 2
    assert all(t["year"] == 2020 for t in a["trades"])
    assert source_identity(cfg.dataset_profile)["files"]["minutes"]["rows"] == 2388306
