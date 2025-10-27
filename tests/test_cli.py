import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.cli import run_cli


class BatchSpyAnalyzer:
    def __init__(self):
        self.calls = []
        self.config = {}

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

