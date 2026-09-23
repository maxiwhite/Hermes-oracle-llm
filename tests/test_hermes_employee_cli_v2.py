import subprocess
import sys

from hermes_employee import default_source_registry

COMMANDS = [
    ["status"],
    ["character"],
    ["security"],
    ["rights"],
    ["skills"],
    ["sources"],
    ["ethical-check", "status check"],
    ["source-plan", "build local bridge"],
    ["security-check", "build local bridge"],
    ["decide", "build local bridge"],
    ["tick", "status check"],
    ["validate"],
]


def test_hermes_employee_cli_v2_commands():
    for args in COMMANDS:
        result = subprocess.run([sys.executable, "hermes_employee.py", *args], capture_output=True, text=True)
        assert result.returncode == 0, f"{args} failed: {result.stderr}\n{result.stdout}"


def test_freebuff_logarhythm_is_a_registered_reviewed_source():
    source = next(item for item in default_source_registry() if item["id"] == "source.freebuff.logarhythm")

    assert source["project_id"] == "vast-cars-leave"
    assert source["mode"] == "read_only_import"
    assert source["approval_required"] is True
