from audit_events import render, R, folder, LEVELS
import pandas as pd, json
from PIL import Image, ImageOps, ImageDraw

idx = pd.read_csv(R / "chart_audit_index.csv")
for level in LEVELS[:10]:
    e = pd.read_parquet(
        folder(level) / "events.parquet", columns=["event_id", "payload"]
    )
    lookup = {r.event_id: json.loads(r.payload) for r in e.itertuples()}
    group = idx[idx.level == level]
    for r in group.itertuples():
        p = lookup[r.event_id]
        render(p, lookup[p.get("root_event_id", p["event_id"])], R / r.chart)
    w, h = 900, 310
    sheet = Image.new("RGB", (w * 2, h * ((len(group) + 1) // 2)), "#101922")
    for i, r in enumerate(group.itertuples()):
        im = Image.open(R / r.chart)
        im.thumbnail((w, h))
        sheet.paste(im, ((i % 2) * w, (i // 2) * h))
    sheet.save(folder(level) / "chart_audit" / "CONTACT_SHEET.jpg", quality=90)
    print(level, len(group), flush=True)
