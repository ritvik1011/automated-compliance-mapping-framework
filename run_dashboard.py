"""Compliance Dashboard Launcher.

This launcher script ensures seamless execution of the Streamlit dashboard by:
1. Dynamically locating the project root directory using `pathlib`.
2. Injecting the project root into `sys.path` so that all `src.*` imports resolve.
3. Propagating the project root via the `PYTHONPATH` environment variable to child processes.
4. Invoking Streamlit through `subprocess` using the active Python interpreter.

Usage:
    python run_dashboard.py
    python run_dashboard.py --server.port 8502
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    """Configure environment and execute Streamlit dashboard."""
    # 1. Dynamically locate project root (directory containing this script)
    project_root = Path(__file__).resolve().parent

    # 2. Inject project root into sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # 3. Propagate to child processes via PYTHONPATH and UTF-8 encoding
    existing_pythonpath = os.environ.get("PYTHONPATH", "")
    os.environ["PYTHONPATH"] = (
        f"{project_root}{os.pathsep}{existing_pythonpath}"
        if existing_pythonpath
        else str(project_root)
    )
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # 4. Resolve path to dashboard entry point
    dashboard_app = project_root / "src" / "dashboard" / "app.py"
    if not dashboard_app.is_file():
        print(f"[ERROR] Dashboard entry point not found at: {dashboard_app}", file=sys.stderr)
        return 1

    # 5. Build Streamlit execution command using current Python interpreter
    cmd = [sys.executable, "-m", "streamlit", "run", str(dashboard_app)] + sys.argv[1:]

    print("=" * 60)
    print("  Compliance Monitoring Dashboard Launcher")
    print("=" * 60)
    print(f"[INFO] Project Root : {project_root}")
    print(f"[INFO] Python Exec  : {sys.executable}")
    print(f"[INFO] Target Script: {dashboard_app}")
    print(f"[INFO] Command      : {' '.join(cmd)}")
    print("=" * 60)

    # 6. Execute Streamlit process
    try:
        process = subprocess.run(cmd, cwd=project_root)
        return process.returncode
    except KeyboardInterrupt:
        print("\n[INFO] Dashboard stopped by user.")
        return 0
    except Exception as exc:
        print(f"[ERROR] Failed to run dashboard: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
