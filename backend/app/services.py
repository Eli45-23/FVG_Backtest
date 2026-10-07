"""Version snapshots, one local worker queue, process timeout/cancellation."""

import os, sys, json, time, signal, subprocess, tempfile, threading, hashlib
from importlib.metadata import version as package_version
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from sqlalchemy import select
from backend.app import db
from engine.canonical import digest, dumps, clean
from engine.data import identities
from engine.legacy import ROOT, reference
from engine.runner import RunConfig

pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="lab-worker")
processes = {}
lock = threading.RLock()


def event(name, rid):
    with lock, (db.STORE / "events.jsonl").open("a") as log:
        log.write(dumps({"timestamp": db.now(), "event": name, "run_id": rid}) + "\n")


def spawn(request, target, mode, log):
    env = {
        k: os.environ[k]
        for k in ("PATH", "LANG", "TMPDIR", "SYSTEMROOT")
        if k in os.environ
    }
    env["PYTHONPATH"] = str(ROOT)
    env["PYTHONUNBUFFERED"] = "1"
    return subprocess.Popen(
        [sys.executable, "-m", "backend.app.worker", str(request), str(target), mode],
        cwd=ROOT,
        env=env,
        stdout=log,
        stderr=log,
        start_new_session=True,
    )


def terminate(p):
    if p.poll() is None:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    p.wait()


def validate(source, parameters=None, timeout=10):
    with tempfile.TemporaryDirectory(prefix="lab-validate-") as folder:
        root = Path(folder)
        request = root / "request.json"
        output = root / "result.json"
        request.write_text(dumps({"source": source, "parameters": parameters or {}}))
        with (root / "worker.log").open("w") as log:
            p = spawn(request, output, "validate", log)
            try:
                p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                terminate(p)
                return {
                    "valid": False,
                    "error": "Strategy validation timed out",
                    "line": None,
                }
        if not output.exists():
            return {
                "valid": False,
                "error": "Strategy worker exited without a result",
                "line": None,
            }
        value = json.loads(output.read_text())
        if "error" in value:
            value["valid"] = False
        return value


def version(s, strategy, source, force=False):
    old = s.scalar(
        select(db.Version)
        .where(db.Version.strategy_id == strategy.id)
        .order_by(db.Version.number.desc())
    )
    h = hashlib.sha256(source.encode()).hexdigest()
    if old and h == old.source_hash and not force:
        return old
    n = 1 if old is None else old.number + 1
    v = db.Version(strategy_id=strategy.id, number=n, source=source, source_hash=h)
    s.add(v)
    s.flush()
    strategy.current_version = n
    strategy.updated_at = db.now()
    return v


def seed():
    db.migrate()
    with db.Session.begin() as s:
        for r in s.scalars(
            select(db.Run).where(db.Run.status.in_(["queued", "running"]))
        ):
            r.status = "failed"
            r.error = "Server restarted before worker completion"
            r.finished_at = db.now()
        if s.scalar(select(db.Strategy).limit(1)):
            return
        st = db.Strategy(
            name="CONT-A Second Candle",
            description="Validated reference strategy; clone to experiment",
            tags=["built-in", "MNQ"],
        )
        s.add(st)
        s.flush()
        v = version(s, st, (ROOT / "strategies/builtins/cont_a.py").read_text())
        for name, p in [
            ("Baseline", {}),
            ("Risk <100", {"max_risk": 100}),
            ("Risk <100 • No 10:00–10:29", {"max_risk": 100, "exclude_middle": True}),
        ]:
            s.add(
                db.Variant(name=name, strategy_version_id=v.id, parameters=p, config={})
            )


def engine_version():
    paths = sorted((ROOT / "engine").rglob("*.py")) + [
        ROOT / "outputs/cont_a_backtest.py",
        ROOT / "outputs/cont_a_metrics.py",
    ]
    return digest(
        {
            "sources": {
                str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths
            },
            "python": sys.version,
            "packages": {
                p: package_version(p)
                for p in ["pandas", "numpy", "pyarrow", "exchange_calendars"]
            },
        }
    )


def enqueue(
    version_id,
    parameters,
    settings,
    name,
    notes="",
    variant_id=None,
    segment="development",
    extra_config=None,
    expected_identity=None,
):
    cfg = RunConfig(**settings)
    cfg.validate()
    with db.Session() as s:
        v = s.get(db.Version, version_id)
        if not v:
            raise ValueError("Unknown strategy version")
        source = v.source
        source_hash = v.source_hash
        strategy_id = v.strategy_id
        number = v.number
        if variant_id:
            variant = s.get(db.Variant, variant_id)
            if not variant or variant.strategy_version_id != version_id:
                raise ValueError("Variant version mismatch")
    check = validate(source, parameters)
    if not check["valid"]:
        raise ValueError(check.get("error", "Invalid strategy"))
    hashes = identities()
    snapshot = {
        "strategy_id": strategy_id,
        "strategy_version": number,
        "source_hash": source_hash,
        "parameters": check["parameters"],
        "settings": cfg.__dict__,
        "engine_version": engine_version(),
        "data_hashes": hashes,
        "session": "XNYS full sessions / NY calendar date / one trade per day",
        "execution": "minute-start ownership; stop first; fixed bracket; session close; exit-minute extrema",
        "segment": segment,
        "research_split_id": None,
        "management": check.get("management", {"enabled": False}),
    }
    if expected_identity:
        for key in (
            "source_hash",
            "parameters",
            "engine_version",
            "data_hashes",
            "management",
        ):
            if snapshot.get(key) != expected_identity.get(key):
                raise ValueError(
                    f"Frozen experiment {key} changed; create a new experiment"
                )
    snapshot.update(extra_config or {})
    snapshot["run_type"] = {
        "out-of-sample": "OUT_OF_SAMPLE",
        "development": "DEVELOPMENT",
        "validation": "VALIDATION",
        "full-sample": "FULL_SAMPLE",
        "ad-hoc": "AD_HOC",
    }[segment]
    snapshot["reproduction_hash"] = digest(snapshot)
    with db.Session.begin() as s:
        r = db.Run(
            name=name,
            strategy_version_id=version_id,
            variant_id=variant_id,
            config=snapshot,
            notes=notes,
        )
        s.add(r)
        s.flush()
        rid = r.id
        root = db.STORE / "artifacts" / rid
        root.mkdir(parents=True, exist_ok=False)
        (root / "request.json").write_text(
            dumps(
                {
                    "source": source,
                    "parameters": check["parameters"],
                    "settings": cfg.__dict__,
                }
            )
        )
        (root / "config.json").write_text(dumps(snapshot))
    event("queued", rid)
    pool.submit(execute, rid)
    return rid


def execute(rid):
    start = time.monotonic()
    root = db.STORE / "artifacts" / rid
    with lock, db.Session.begin() as s:
        r = s.get(db.Run, rid)
        if r.status != "queued":
            return
        r.status = "running"
        r.progress = "Loading local data"
    event("running", rid)
    try:
        with db.Session() as s:
            snapshot = s.get(db.Run, rid).config
            if (
                snapshot["engine_version"] != engine_version()
                or snapshot["data_hashes"] != identities()
            ):
                raise ValueError(
                    "Engine or data changed after queueing; clone with the current identity"
                )
        with (root / "worker.log").open("w") as log:
            p = spawn(root / "request.json", root / "result.json", "run", log)
            with lock:
                processes[rid] = p
                with db.Session() as s:
                    if s.get(db.Run, rid).status == "cancelled":
                        terminate(p)
            try:
                p.wait(timeout=600)
            except subprocess.TimeoutExpired:
                terminate(p)
                raise ValueError("Backtest exceeded 600-second timeout")
        with lock, db.Session.begin() as s:
            r = s.get(db.Run, rid)
            if r.status == "cancelled":
                return
            if not (root / "result.json").exists():
                raise ValueError("Worker exited without a result; inspect local log")
            result = json.loads((root / "result.json").read_text())
            if p.returncode or "error" in result:
                raise ValueError(result.get("error", "Strategy worker failed"))
            if identities() != r.config["data_hashes"]:
                raise ValueError("Source data changed during execution")
            for t in result["trades"]:
                t.update(
                    run_id=rid,
                    strategy_id=r.config["strategy_id"],
                    strategy_version=r.config["strategy_version"],
                    instrument="MNQ",
                    original_risk_points=t["risk_points"],
                    original_risk_usd=t["risk_usd"],
                    setup_id=t["fvg_id"],
                )
            (root / "trades.json").write_text(dumps(result["trades"]))
            (root / "equity.json").write_text(dumps(result["equity"]))
            s.add(db.RunMetric(run_id=rid, payload=result["summary"]))
            (root / "management_events.json").write_text(
                dumps(result.get("management_events", []))
            )
            for kind in [
                "trades",
                "equity",
                "result",
                "config",
                "request",
                "management_events",
            ]:
                s.add(
                    db.Artifact(
                        run_id=rid, kind=kind, path=str(root / (kind + ".json"))
                    )
                )
            r.status = "completed"
            r.progress = "Completed"
            r.finished_at = db.now()
            r.duration = time.monotonic() - start
    except Exception as e:
        with lock, db.Session.begin() as s:
            r = s.get(db.Run, rid)
            if r.status != "cancelled":
                r.status = "failed"
                r.error = str(e)[:500]
                r.finished_at = db.now()
                r.duration = time.monotonic() - start
    finally:
        with db.Session() as s:
            event(s.get(db.Run, rid).status, rid)
        with lock:
            processes.pop(rid, None)


def cancel(rid):
    with lock, db.Session.begin() as s:
        r = s.get(db.Run, rid)
        if not r:
            raise ValueError("Unknown run")
        if r.status not in ("queued", "running"):
            return r.status
        r.status = "cancelled"
        r.finished_at = db.now()
        r.progress = "Cancelled"
        if rid in processes:
            terminate(processes[rid])
    event("cancelled", rid)
    return "cancelled"


def seed_managed():
    """Add a new example only. Never change an existing saved strategy/version."""
    with db.Session.begin() as s:
        if s.scalar(
            select(db.Strategy).where(db.Strategy.name == "CONT-A Quality R-Step")
        ):
            return
        st = db.Strategy(
            name="CONT-A Quality R-Step",
            description="Causal reference management experiment; no performance assumption",
            tags=["built-in", "managed"],
        )
        s.add(st)
        s.flush()
        v = version(s, st, (ROOT / "strategies/builtins/cont_a_rstep.py").read_text())
        s.add(
            db.Variant(
                name="Quality R-Step",
                strategy_version_id=v.id,
                parameters={},
                config={},
            )
        )
