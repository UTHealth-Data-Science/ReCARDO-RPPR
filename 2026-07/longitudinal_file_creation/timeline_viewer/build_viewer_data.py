# -*- coding: utf-8 -*-
"""
Prepare data for the person-timeline viewer (index.html).

Splits ../mongodb_files/person_timeline.json (one big JSON array) into:
  - data/index.json            : lightweight subject list (bid, summary, per-year totals)
  - data/subjects/<bid>.json   : that subject's full timeline document

This keeps the browser fast: the viewer loads the small index, then fetches one
subject file on demand. No data is changed - records stay verbatim.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "mongodb_files" / "person_timeline.json"
DATA = HERE / "data"
SUBJ = DATA / "subjects"
SUBJ.mkdir(parents=True, exist_ok=True)


def main():
    if not SRC.exists():
        raise SystemExit(f"Missing {SRC}. Run ../convert_active_to_mongodb.py first.")
    docs = json.load(open(SRC, encoding="utf-8"))
    index = []
    for d in docs:
        bid = d.get("bid_active_1") or d.get("_id")
        if d.get("sharded"):              # skip shard stubs/parts in the index split
            continue
        timeline = d.get("timeline", {})
        per_year = {y: len(recs) for y, recs in timeline.items()}
        (SUBJ / f"{bid}.json").write_text(json.dumps(d, ensure_ascii=False))
        index.append({
            "bid_active_1": bid,
            "n_records": d.get("summary", {}).get("n_records"),
            "data_types": d.get("summary", {}).get("data_types", []),
            "first_year": d.get("summary", {}).get("first_year"),
            "last_year": d.get("summary", {}).get("last_year"),
            "per_year": per_year,
        })
    index.sort(key=lambda r: r["bid_active_1"])
    DATA.joinpath("index.json").write_text(
        json.dumps({"n_subjects": len(index), "subjects": index}, ensure_ascii=False))
    print(f"Wrote {len(index)} subject files + index.json under {DATA}")
    print("Now serve the viewer folder, e.g.:")
    print(f"    cd {HERE}")
    print("    python3 -m http.server 8000")
    print("    open http://localhost:8000/")


if __name__ == "__main__":
    main()
