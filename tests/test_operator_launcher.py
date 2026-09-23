import sys

from scripts import operator


def test_local_model_alias_is_kept_when_it_points_to_fast_model() -> None:
    loaded = [
        {
            "identifier": "hermes-free",
            "modelKey": "qwen3-1.7b",
            "path": "lmstudio-community/Qwen3-1.7B-GGUF/Qwen3-1.7B-Q4_K_M.gguf",
        }
    ]

    assert operator.model_needs_reload(loaded) is False


def test_local_model_alias_is_reloaded_when_it_points_to_slow_model() -> None:
    loaded = [
        {
            "identifier": "hermes-free",
            "modelKey": "qwen3.5-4b-verified",
            "path": "qwen3.5-4b-verified",
        }
    ]

    assert operator.model_needs_reload(loaded) is True


def test_freebuff_command_targets_the_hermes_project(tmp_path) -> None:
    executable = tmp_path / "freebuff.cmd"
    project_root = tmp_path / "Hermes-oracle-llm"

    command = operator.freebuff_command(executable=executable, project_root=project_root)

    assert command == [str(executable), "--cwd", str(project_root)]


def test_launch_freebuff_hands_the_hermes_project_to_the_cli(tmp_path) -> None:
    executable = tmp_path / "freebuff.cmd"
    project_root = tmp_path / "Hermes-oracle-llm"
    observed = {}

    def run(command, *, cwd):
        observed["command"] = command
        observed["cwd"] = cwd
        return 0

    exit_code = operator.launch_freebuff(
        executable=executable,
        project_root=project_root,
        run=run,
    )

    assert exit_code == 0
    assert observed == {
        "command": [str(executable), "--cwd", str(project_root)],
        "cwd": str(project_root),
    }


def test_freebuff_mode_does_not_start_the_local_model(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["operator.py", "--freebuff"])
    monkeypatch.setattr(operator, "launch_freebuff", lambda: 0)

    def fail_if_called():
        raise AssertionError("LM Studio must not start for the Freebuff bridge")

    monkeypatch.setattr(operator, "prepare_model", fail_if_called)

    assert operator.main() == 0
