"""Refresh presentation only; require all economic artifacts unchanged and repeatable."""

import json, sys, subprocess, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.level_combination.run import P, sha
from scripts.level_combination.verify import artifacts


def main():
    m = json.loads((P / "reproducibility_manifest.json").read_text())
    assert m["status"] == "PASS"
    before = artifacts()
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/level_combination/report.py")],
        check=True,
        cwd=ROOT,
    )
    once = artifacts()
    assert before.keys() == once.keys()
    assert all(before[k] == once[k] for k in before if k != "study.html")
    subprocess.run(
        [sys.executable, str(ROOT / "scripts/level_combination/report.py")],
        check=True,
        cwd=ROOT,
    )
    assert once == artifacts()
    m["artifacts"] = once
    m.pop("presentation_only_refresh", None)
    m["code_hashes"] = {
        str(p.relative_to(ROOT)): sha(p)
        for p in sorted((ROOT / "scripts/level_combination").glob("*.py"))
    }
    (P / "reproducibility_manifest.json").write_text(
        json.dumps(m, sort_keys=True, indent=2) + "\n"
    )
    archive = P / "study_bundle.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for name in [*sorted(once), "reproducibility_manifest.json"]:
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (P / name).read_bytes())
    m["artifacts"][archive.name] = {
        "sha256": sha(archive),
        "bytes": archive.stat().st_size,
    }
    (P / "reproducibility_manifest.json").write_text(
        json.dumps(m, sort_keys=True, indent=2) + "\n"
    )
    print(
        "PASS: display-only change; all economic artifacts unchanged; report repeats byte-identically"
    )


if __name__ == "__main__":
    main()
