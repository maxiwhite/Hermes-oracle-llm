"""Exercise the canonical launcher without relying on an already-imported module."""
import os
from pathlib import Path
import re
import subprocess
import sys
import pytest


ROOT = Path(__file__).resolve().parents[1]


def test_canonical_operator_entrypoint_starts_in_fresh_interpreter():
    launcher = (ROOT / "start-hermes.cmd").read_text(encoding="utf-8")
    match = re.search(r"scripts\\([\w]+\.py)", launcher)
    assert match, "The launcher must name an operator entrypoint"
    entrypoint = ROOT / "scripts" / match.group(1)
    result = subprocess.run(
        [sys.executable, str(entrypoint), "--help"],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "Hermes local operator" in result.stdout


@pytest.mark.skipif(os.name != "nt", reason="Windows command launcher")
def test_windows_launcher_passes_arguments_without_starting_model(tmp_path):
    result = subprocess.run(
        ["cmd", "/d", "/c", str(ROOT / "start-hermes.cmd"), "--help"],
        cwd=tmp_path,
        env={**os.environ, "HERMES_PYTHON": sys.executable,
             "HERMES_DATA_DIR": str(tmp_path / "runtime")},
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "--task" in result.stdout
