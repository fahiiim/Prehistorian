import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cmd(args, cwd=REPO_ROOT, env_extra=None):
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_cli_help():
    result = _run_cmd([sys.executable, "-m", "prehistorian", "--help"])
    output = (result.stdout or "") + (result.stderr or "")
    assert result.returncode == 0
    assert "Predictive codebase cartographer" in output


def test_query_without_model():
    with tempfile.TemporaryDirectory() as temp_dir:
        env_extra = {"PYTHONPATH": str(REPO_ROOT)}
        result = _run_cmd(
            [sys.executable, "-m", "prehistorian", "query", "README.md"],
            cwd=temp_dir,
            env_extra=env_extra,
        )
        output = (result.stdout or "") + (result.stderr or "")
        assert result.returncode == 1
        assert "Model not found" in output
