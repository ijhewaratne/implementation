#!/usr/bin/env python3
"""
CLI wrapper for the dual-pipe workflow orchestrator.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.orchestration.dual_pipe_runner import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())

