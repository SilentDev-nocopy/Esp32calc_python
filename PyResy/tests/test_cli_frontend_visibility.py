import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

def run(*args, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    return subprocess.run(
        [sys.executable, "-m", "resiris", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def main():
    home = ROOT / "tests" / ".cli_test_home"
    home.mkdir(exist_ok=True)

    enabled = run("--enable-frontend-visibility", home=home)
    if enabled.returncode != 0:
        raise SystemExit(enabled.stderr or enabled.stdout)
    if "Frontend visibility enabled." not in enabled.stdout:
        raise SystemExit("Frontend visibility was not enabled")

    enabled_run = run("tests/test_resy_for_cli.resy", home=home)
    if enabled_run.returncode != 0:
        raise SystemExit(enabled_run.stderr or enabled_run.stdout)
    if "<TOKENS>" not in enabled_run.stdout:
        raise SystemExit("Frontend output was not enabled persistently")
    if "<AST>" not in enabled_run.stdout:
        raise SystemExit("AST output was not enabled persistently")

    disabled = run("--disable-frontend-visibility", home=home)
    if disabled.returncode != 0:
        raise SystemExit(disabled.stderr or disabled.stdout)

    disabled_run = run("tests/test_resy_for_cli.resy", home=home)
    if disabled_run.returncode != 0:
        raise SystemExit(disabled_run.stderr or disabled_run.stdout)
    if "<TOKENS>" in disabled_run.stdout:
        raise SystemExit("Frontend output was not disabled")
    if "<AST>" in disabled_run.stdout:
        raise SystemExit("AST output was not disabled")

    both = run(
        "--enable-frontend-visibility",
        "--disable-frontend-visibility",
        home=home,
    )
    if both.returncode == 0:
        raise SystemExit("Enable and disable flags should be mutually exclusive")
    if "usage:" in both.stdout.lower() or "usage:" in both.stderr.lower():
        raise SystemExit("Invalid CLI arguments should not print the full usage page")

    shutil = __import__("shutil")
    shutil.rmtree(home)


if __name__ == "__main__":
    main()
