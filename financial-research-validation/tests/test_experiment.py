import json
from pathlib import Path

from backtest_demo import DATA_FILES, experiment, generate


def test_each_cost_case_has_a_matching_benchmark_and_shared_dataset():
    first_data, cases = experiment()
    assert first_data == experiment()[0] and len(cases) == 4
    for case in cases:
        s, b = case["strategy"], case["benchmark"]
        assert (s["start"], s["end"]) == (b["start"], b["end"])
        assert case["excess_return"] == s["cumulative_return"] - b["cumulative_return"]
        assert s["total_execution_costs"] >= 0 and b["total_execution_costs"] >= 0
    identities = [fill.id for case in cases for model in ["strategy", "benchmark"] for fill in case[model]["fills"]]
    assert len(identities) == len(set(identities))


def test_report_and_figures_are_generated_from_repeated_identical_runs(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    generated = generate(a)
    generate(b)
    for name in DATA_FILES:
        assert (a / name).read_bytes() == (b / name).read_bytes()
    summary = json.loads((a / "summary.json").read_text())
    assert summary["dataset_sha256"] == generated["dataset_sha256"]
    assert summary["scenarios"][0]["strategy"]["fees"] == "0.00" or float(
        summary["scenarios"][0]["strategy"]["fees"]) == 0
    assert (a / "cost-experiment.png").read_bytes() == (b / "cost-experiment.png").read_bytes()


def test_committed_numeric_results_match_current_code():
    from tempfile import TemporaryDirectory
    target = Path(__file__).resolve().parents[1] / "examples/backtest"
    with TemporaryDirectory() as folder:
        generate(folder)
        for name in DATA_FILES:
            assert (Path(folder) / name).read_bytes() == (target / name).read_bytes()
