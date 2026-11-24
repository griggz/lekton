"""Every example must run. Each one asserts its own claims, so a passing
run means what the example prints is true.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
EXAMPLES = sorted((ROOT / "examples").glob("*.py"))


def test_there_are_examples():
    assert EXAMPLES


@pytest.mark.parametrize("script", EXAMPLES, ids=lambda path: path.name)
def test_example_runs(script: Path):
    # A fresh process each time: examples define kinds, and kinds are
    # registered per process.
    result = subprocess.run(
        [sys.executable, str(script)], capture_output=True, text=True, cwd=ROOT
    )
    assert result.returncode == 0, result.stderr


def test_every_example_is_listed_for_agents():
    index = (ROOT / "llms.txt").read_text()
    listing = (ROOT / "examples" / "README.md").read_text()
    for script in EXAMPLES:
        assert script.name in index, f"{script.name} is missing from llms.txt"
        assert script.name in listing, f"{script.name} is missing from examples/README.md"
