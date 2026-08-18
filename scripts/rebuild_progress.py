import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw")
MANIFEST_DIR = Path("data/manifests")

in_path = RAW_DIR / "tickets_v1.0.jsonl"
lines = [l for l in open(in_path, encoding="utf-8") if l.strip()]
print(f"Rows found in {in_path}: {len(lines)}")

max_num = 0
batch_id = None
for line in lines:
    rec = json.loads(line)
    m = re.search(r"-(\d+)$", rec["fields"]["ticket_id"])
    if m:
        max_num = max(max_num, int(m.group(1)))
    batch_id = rec["metadata"]["generation_batch"]

progress = {
    "next_index": max_num,
    "accepted": len(lines),
    "rejected": 0,
    "batch_id": batch_id,
}
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
out_path = MANIFEST_DIR / "progress_v1.0.json"
out_path.write_text(json.dumps(progress, indent=2), encoding="utf-8")
print(f"Reconstructed: {out_path}")
print(json.dumps(progress, indent=2))
