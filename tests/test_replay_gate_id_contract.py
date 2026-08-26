from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "tools/check_replay_gate_id_contract.py"
RECORDER_PATTERN = r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z"
LOWERCASE_MONITOR_PATTERN = r"[a-z0-9][a-z0-9-]{0,63}\Z"


def _write_helper(path: Path, name: str, pattern: str, *, flags: str = "") -> None:
    suffix = f", {flags}" if flags else ""
    path.write_text(
        f"import re\n{name} = re.compile({pattern!r}{suffix})\n",
        encoding="utf-8",
    )


def _write_source(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")


def _run_checker(recorder: Path, monitor: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECKER), str(recorder), str(monitor)],
        cwd=ROOT,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_checker_accepts_the_recorder_gate_id_contract(tmp_path: Path) -> None:
    recorder = tmp_path / "gate_command_once.py"
    monitor = tmp_path / "gate_live_monitor.py"
    _write_helper(recorder, "SAFE_ID", RECORDER_PATTERN)
    _write_helper(monitor, "_SAFE_ID", RECORDER_PATTERN)

    result = _run_checker(recorder, monitor)

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"gate_id_contract=matched pattern={RECORDER_PATTERN}\n"
    assert result.stderr == ""


def test_checker_rejects_the_mixed_case_contract_mismatch(tmp_path: Path) -> None:
    recorder = tmp_path / "gate_command_once.py"
    monitor = tmp_path / "gate_live_monitor.py"
    _write_helper(recorder, "SAFE_ID", RECORDER_PATTERN)
    _write_helper(monitor, "_SAFE_ID", LOWERCASE_MONITOR_PATTERN)

    result = _run_checker(recorder, monitor)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "gate-id patterns differ" in result.stderr
    assert RECORDER_PATTERN in result.stderr
    assert LOWERCASE_MONITOR_PATTERN in result.stderr


def test_checker_rejects_joint_drift_from_the_canonical_contract(tmp_path: Path) -> None:
    recorder = tmp_path / "gate_command_once.py"
    monitor = tmp_path / "gate_live_monitor.py"
    _write_helper(recorder, "SAFE_ID", LOWERCASE_MONITOR_PATTERN)
    _write_helper(monitor, "_SAFE_ID", LOWERCASE_MONITOR_PATTERN)

    result = _run_checker(recorder, monitor)

    assert result.returncode == 1
    assert result.stdout == ""
    assert "recorder gate-id pattern is not canonical" in result.stderr
    assert RECORDER_PATTERN in result.stderr
    assert LOWERCASE_MONITOR_PATTERN in result.stderr


@pytest.mark.parametrize(
    ("monitor_source", "error_fragment"),
    [
        (
            f"import re\n_SAFE_ID = re.compile({RECORDER_PATTERN!r}, re.IGNORECASE)\n",
            "must be assigned one literal re.compile pattern with no flags",
        ),
        (
            f"import re\nPATTERN = {RECORDER_PATTERN!r}\n_SAFE_ID = re.compile(PATTERN)\n",
            "must be assigned one literal re.compile pattern with no flags",
        ),
        ("import re\n", "expected exactly one module-level binding to _SAFE_ID"),
        (
            "import re\n"
            f"_SAFE_ID = re.compile({RECORDER_PATTERN!r})\n"
            f"_SAFE_ID: object = re.compile({LOWERCASE_MONITOR_PATTERN!r})\n",
            "expected exactly one module-level binding to _SAFE_ID",
        ),
        (
            f"import re\n_SAFE_ID: object = re.compile({RECORDER_PATTERN!r})\n",
            "must use one direct assignment to a literal re.compile pattern with no flags",
        ),
        (
            "import re\n"
            f"_SAFE_ID = re.compile({RECORDER_PATTERN!r})\n"
            "def replace_in_default(value=("
            f"_SAFE_ID := re.compile({LOWERCASE_MONITOR_PATTERN!r})"
            ")):\n"
            "    return value\n",
            "expected exactly one module-level binding to _SAFE_ID",
        ),
    ],
)
def test_checker_rejects_malformed_contract_bindings(
    tmp_path: Path, monitor_source: str, error_fragment: str
) -> None:
    recorder = tmp_path / "gate_command_once.py"
    monitor = tmp_path / "gate_live_monitor.py"
    _write_helper(recorder, "SAFE_ID", RECORDER_PATTERN)
    _write_source(monitor, monitor_source)

    result = _run_checker(recorder, monitor)

    assert result.returncode == 2
    assert result.stdout == ""
    assert error_fragment in result.stderr


def test_checker_parses_helpers_without_executing_them(tmp_path: Path) -> None:
    recorder = tmp_path / "gate_command_once.py"
    monitor = tmp_path / "gate_live_monitor.py"
    _write_source(
        recorder,
        "raise RuntimeError('recorder helper executed')\n"
        "import re\n"
        f"SAFE_ID = re.compile({RECORDER_PATTERN!r})\n",
    )
    _write_source(
        monitor,
        "raise RuntimeError('monitor helper executed')\n"
        "import re\n"
        f"_SAFE_ID = re.compile({RECORDER_PATTERN!r})\n",
    )

    result = _run_checker(recorder, monitor)

    assert result.returncode == 0, result.stderr
    assert result.stdout == f"gate_id_contract=matched pattern={RECORDER_PATTERN}\n"
    assert result.stderr == ""
