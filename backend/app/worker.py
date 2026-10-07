"""Trusted source runs here, never inside the HTTP process. Not a security sandbox."""

import sys, json, traceback
from pathlib import Path
from engine.canonical import clean, dumps
from engine.strategy.loading import load
from engine.runner import run, RunConfig


class BoundedLog:
    def __init__(self, stream):
        self.stream = stream
        self.remaining = 65536

    def write(self, text):
        text = text[: self.remaining]
        self.remaining -= len(text)
        self.stream.write(text)
        self.stream.flush()
        return len(text)

    def flush(self):
        self.stream.flush()


def main():
    request = Path(sys.argv[1])
    target = Path(sys.argv[2])
    mode = sys.argv[3]
    data = json.loads(request.read_text())
    sys.stdout = BoundedLog(sys.stdout)
    sys.stderr = BoundedLog(sys.stderr)
    try:
        if mode == "validate":
            obj, params, inputs = load(data["source"], data.get("parameters"))
            result = {
                "valid": True,
                "management": {
                    "enabled": callable(getattr(obj, "manage", None))
                    and params.get("management_enabled", True),
                    "version": "minute-close-next-start-v1",
                },
                "name": getattr(obj, "name", "Strategy"),
                "inputs": inputs,
                "parameters": dict(params),
                "warnings": [
                    "Only run strategy code you trust. Python is not sandboxed."
                ],
            }
        else:

            def progress(stage):
                (target.parent / "progress.txt").write_text(stage)

            result = run(
                data["source"],
                data["parameters"],
                RunConfig(**data["settings"]),
                progress=progress,
            )
        target.write_text(dumps(result))
    except BaseException as e:
        traceback.print_exc()
        target.write_text(
            dumps(
                {
                    "error": str(e)[:500],
                    "type": type(e).__name__,
                    "line": getattr(e, "lineno", None),
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
