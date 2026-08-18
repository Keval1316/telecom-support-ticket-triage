import json, re
from pathlib import Path
from collections import Counter

in_path = Path("data/raw/tickets_v1.0.jsonl")
lines = [l for l in open(in_path, encoding="utf-8") if l.strip()]
print(f"Total rows: {len(lines)}")

records = [json.loads(l) for l in lines]
ids = [r["fields"]["ticket_id"] for r in records]
id_counts = Counter(ids)
dupes = {k: v for k, v in id_counts.items() if v > 1}
print(f"Unique ticket_ids: {len(id_counts)}")
print(f"Duplicate ticket_ids: {len(dupes)}")
if dupes:
    print("Examples (first 10):")
    for k in list(dupes.keys())[:10]:
        print(f"  {k}: appears {dupes[k]} times")

nums = []
for tid in ids:
    m = re.search(r"-(\d+)$", tid)
    if m:
        nums.append(int(m.group(1)))
print(f"Min index: {min(nums) if nums else 'N/A'}  Max index: {max(nums) if nums else 'N/A'}")

num_set = set(nums)
max_n = max(nums) if nums else 0
missing = [n for n in range(1, max_n + 1) if n not in num_set]
print(f"Missing indices in range 1..{max_n}: {len(missing)}")
if missing:
    print(f"First 20 missing: {missing[:20]}")

seen = set()
deduped = []
for l, r in zip(lines, records):
    tid = r["fields"]["ticket_id"]
    if tid in seen:
        continue
    seen.add(tid)
    deduped.append(l if l.endswith("\n") else l + "\n")

if len(deduped) != len(lines):
    out_path = in_path.with_suffix(".dedup.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(deduped)
    print(f"\nWrote deduped file ({len(deduped)} rows) -> {out_path}")
    print("If this looks right, replace the original with:")
    print(f"  Move-Item -Force {out_path} {in_path}")
else:
    print("\nNo duplicates found - file is already clean.")
