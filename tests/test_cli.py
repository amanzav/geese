import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cli import run_cli


class BatchSpyAnalyzer:
    def __init__(self):
        self.calls = []
        self.config = {}

    def run_realtime_pipeline(self, auto_save_to_folder: bool) -> None:  # pragma: no cover - not used here
        self.calls.append(("realtime", auto_save_to_folder))

    def run_full_pipeline(self, *, detailed: bool, force_rematch: bool, auto_save_to_folder: bool):
        self.calls.append(
            (
                "batch",
                {
                    "detailed": detailed,
                    "force_rematch": force_rematch,
                    "auto_save_to_folder": auto_save_to_folder,
                },
            )
        )


class AnalyzeSpyAnalyzer:
    def __init__(self):
        self.matcher = self
        self.config = {}
        self.analysis_results = [
            {"job": {"title": "Developer"}, "match": {"fit_score": 80}}
        ]
        self.filtered_results = [
            {"job": {"title": "Developer"}, "match": {"fit_score": 80}}
        ]
        self.calls = []

    def batch_analyze(self, jobs, force_rematch=False):
        self.calls.append(("batch_analyze", jobs, force_rematch))
        return self.analysis_results

    def apply_filters(self, results):
        self.calls.append(("apply_filters", results))
        return self.filtered_results

    def save_results(self, results):
        self.calls.append(("save_results", results))

    def show_summary(self, results):
        self.calls.append(("show_summary", results))


def test_run_cli_batch_invokes_pipeline_defaults():
    analyzer = BatchSpyAnalyzer()
    run_cli(["--mode", "batch"], analyzer=analyzer)

    assert analyzer.calls == [
        (
            "batch",
            {
                "detailed": True,
                "force_rematch": False,
                "auto_save_to_folder": False,
            },
        )
    ]


def test_run_cli_batch_with_flags():
    analyzer = BatchSpyAnalyzer()
    run_cli(
        ["--mode", "batch", "--quick", "--force-rematch", "--auto-save"],
        analyzer=analyzer,
    )

    assert analyzer.calls == [
        (
            "batch",
            {
                "detailed": False,
                "force_rematch": True,
                "auto_save_to_folder": True,
            },
        )
    ]


def test_run_cli_analyze_mode(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")

    analyzer = AnalyzeSpyAnalyzer()
    run_cli(["--mode", "analyze", "--jobs-path", str(jobs_path)], analyzer=analyzer)

    assert analyzer.calls[0][0] == "batch_analyze"
    assert analyzer.calls[0][2] is False
    assert analyzer.calls[1][0] == "apply_filters"
    assert analyzer.calls[2][0] == "save_results"
    assert analyzer.calls[3][0] == "show_summary"


def test_run_cli_analyze_mode_force_rematch(tmp_path):
    jobs_path = tmp_path / "jobs.json"
    jobs_path.write_text(json.dumps([{"id": 1}]), encoding="utf-8")

    analyzer = AnalyzeSpyAnalyzer()
    run_cli(
        [
            "--mode",
            "analyze",
            "--jobs-path",
            str(jobs_path),
            "--force-rematch",
        ],
        analyzer=analyzer,
    )

    assert analyzer.calls[0][2] is True


def test_run_cli_realtime_mode():
    analyzer = BatchSpyAnalyzer()
    run_cli(["--mode", "realtime"], analyzer=analyzer)

    assert analyzer.calls == [("realtime", True)]
