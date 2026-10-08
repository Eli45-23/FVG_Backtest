"""Separate event-study worker, receives a saved immutable config and local artifact path."""

import sys, json
from pathlib import Path
from engine.research.study import run_detection, run_labels

if __name__ == "__main__":
    root = Path(sys.argv[1])
    config = json.loads((root / "config.json").read_text())
    if sys.argv[2] == "detect":
        run_detection(config, root)
    else:
        run_labels(config, root)
