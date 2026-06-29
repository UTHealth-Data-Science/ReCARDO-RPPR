# -*- coding: utf-8 -*-
"""
Convert the ACTIVE synthetic raw data (.sas7bdat) into MongoDB JSON files,
following the Plan 2 - MongoDB solution (source-preserving, NO harmonization).

Outputs (into ./mongodb_files):
  - src_<data_type>.json    : JSON array of record documents (one per source row)
  - person_documents.json   : JSON array of person documents (per subject, organized by DATA TYPE)
  - person_timeline.json    : JSON array of person documents (per subject, organized by YEAR)
  - person_index.json       : JSON array of lightweight per-subject documents (counts + coverage)
  - _manifest.csv           : per-collection document counts
  - _conversion_summary.json: run summary

Rules (Plan 2):
  * Read .sas7bdat verbatim; keep ORIGINAL variable names & values under "record".
  * No value recoding, no concept mapping. Link only by BID_ACTIVE_1.
  * Absent (null/blank) fields are omitted per document (sparse-friendly).
  * The ACTIVE data folder is READ-ONLY and never modified.

Each output file is a JSON array of documents; load with
`mongoimport --type json --jsonArray` or pymongo insert_many.
"""
import json
import math
import re
import datetime as dt
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

HERE = Path(__file__).resolve().parent
DATA_ROOT = HERE.parent / "ACTIVE"          # READ-ONLY synthetic data
OUT = HERE / "mongodb_files"
OUT.mkdir(parents=True, exist_ok=True)

YEAR_RE = re.compile(r"((?:19|20)\d{2})")

# ------------------------------------------------------------------ helpers
def jsonify(v):
    """Coerce one value to a JSON-safe scalar. NaN/NaT/NA/blank -> None."""
    if v is None:
        return None
    if isinstance(v, float):
        return None if math.isnan(v) else v
    if isinstance(v, np.integer):
        return int(v)
    if isinstance(v, np.floating):
        f = float(v)
        return None if math.isnan(f) else f
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if isinstance(v, (pd.Timestamp, dt.datetime, dt.date)):
        return None if pd.isna(v) else pd.Timestamp(v).isoformat()
    if isinstance(v, bytes):
        return v.decode("utf-8", "replace")
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(v, str):
        s = v.strip()
        return s if s != "" else None
    return v


def safe_key(k):
    """MongoDB field names cannot contain '.' or start with '$'."""
    k = str(k).replace(".", "_")
    return ("_" + k[1:]) if k.startswith("$") else k


def physical_data_type(rel_parts, stem):
    """Map a file's folder path + name to its physical data type (matches the dictionary)."""
    top = rel_parts[0].upper()
    if top == "DN":
        return "DN"
    if top == "IRFPAI":
        return "IRF-PAI"
    if top == "MAX":
        return f"MAX-{rel_parts[1].upper()}"                 # MAX-IP / LT / OT / PS / RX
    if top == "MBSF":
        m = {"mbs_base": "MBSF-Base", "mbs_cc": "MBSF-CC",
             "mbs_costuse": "MBSF-CU", "mbs_otcc": "MBSF-Other"}
        for pfx, name in m.items():
            if stem.startswith(pfx):
                return name
        return "MBSF-Other"
    if top == "MDS":
        return "MDS"
    if top == "MP":
        return "MedPAR"
    if top == "MTM":
        return "MTM"
    if top == "OASIS":
        return "OASIS"
    if top == "PDE":
        return "PDE"
    if top == "TAF":
        sub = rel_parts[1].upper()
        claim = {"CLAIMIP": "TMSIS-IP", "CLAIMLT": "TMSIS-LT",
                 "CLAIMOT": "TMSIS-OT", "CLAIMRX": "TMSIS-RX"}
        if sub in claim:
            return claim[sub]
        if sub == "DE":
            return "TMSIS-DE " + rel_parts[2].upper().replace("BASE", "Base")
    return top.title()


def collection_name(data_type):
    return "src_" + re.sub(r"[^0-9a-z]+", "_", data_type.lower()).strip("_")


def find_bid_col(columns):
    for c in columns:
        if str(c).upper().replace("_", "") == "BIDACTIVE1":
            return c
    return None


def row_to_doc(row, bid_col, data_type, year, src_file_id, src_row_id):
    """One source row -> a record document (native fields verbatim under 'record')."""
    bid = jsonify(row.get(bid_col))
    bid = str(bid).strip().upper() if bid is not None else None
    record = {}
    for k, v in row.items():
        if k == bid_col:
            continue
        sv = jsonify(v)
        if sv is None:                       # omit absent variables (sparse)
            continue
        record[safe_key(k)] = sv
    return {
        "bid_active_1": bid,
        "src_data_type": data_type,
        "src_year": year,
        "src_file_id": src_file_id,
        "src_row_id": src_row_id,
        "record": record,
    }


def estimate_size(obj):
    return len(json.dumps(obj, default=str).encode("utf-8"))


# ------------------------------------------------------------------ main
def main(person_docs=True, shard_mb=15.0):
    files = sorted(p for p in DATA_ROOT.rglob("*.sas7bdat") if p.is_file())
    print(f"Discovered {len(files)} .sas7bdat files under {DATA_ROOT}")

    # fresh output: remove any prior record / person files (.jsonl or .json)
    for old in (list(OUT.glob("src_*.jsonl")) + list(OUT.glob("src_*.json"))
                + [OUT / "person_documents.jsonl", OUT / "person_documents.json",
                   OUT / "person_timeline.jsonl", OUT / "person_timeline.json",
                   OUT / "person_index.jsonl", OUT / "person_index.json"]):
        try:
            old.unlink()
        except FileNotFoundError:
            pass

    handles = {}                              # collection -> open file handle
    started = {}                              # collection -> bool (any doc written yet)
    coll_counts = defaultdict(int)
    inventory = []
    people = defaultdict(lambda: defaultdict(list)) if person_docs else None
    n_orphan = 0
    total_docs = 0

    for src_file_id, path in enumerate(files, start=1):
        rel = path.relative_to(DATA_ROOT)
        stem = path.stem.lower()
        ym = YEAR_RE.search(stem)
        year = int(ym.group(1)) if ym else None
        dtype = physical_data_type(rel.parts, stem)
        coll = collection_name(dtype)

        try:
            df, _meta = pyreadstat.read_sas7bdat(str(path))
        except Exception as e:               # never abort the whole run on one file
            inventory.append(dict(src_file_id=src_file_id, file=str(rel), data_type=dtype,
                                  year=year, n_rows=0, status=f"READ_ERROR:{e}"))
            continue

        bid_col = find_bid_col(df.columns)

        n_rows = 0
        for src_row_id, row in enumerate(df.to_dict(orient="records")):
            doc = row_to_doc(row, bid_col, dtype, year, src_file_id, src_row_id)
            if not doc["bid_active_1"]:
                n_orphan += 1
                continue
            if coll not in handles:                       # lazy-open + begin JSON array
                handles[coll] = open(OUT / f"{coll}.json", "w", encoding="utf-8")
                handles[coll].write("[")
                started[coll] = False
            handles[coll].write(("," if started[coll] else "") + "\n  "
                                + json.dumps(doc, ensure_ascii=False, default=str))
            started[coll] = True
            coll_counts[coll] += 1
            total_docs += 1
            n_rows += 1
            if person_docs:
                people[doc["bid_active_1"]][dtype].append(
                    {"src_year": year, "src_file_id": src_file_id,
                     "src_row_id": src_row_id, "record": doc["record"]})
        inventory.append(dict(src_file_id=src_file_id, file=str(rel), data_type=dtype,
                              year=year, n_rows=n_rows, status="ok"))

    for fh in handles.values():
        fh.write("\n]\n")                     # close the JSON array
        fh.close()

    # ---- person documents (per subject; by data type AND by year; 16 MB-sharded) ----
    n_people = n_person_docs = n_sharded = 0
    n_timeline_docs = n_timeline_sharded = 0
    if person_docs:
        limit = int(shard_mb * 1024 * 1024)
        with open(OUT / "person_documents.json", "w", encoding="utf-8") as pf, \
             open(OUT / "person_timeline.json", "w", encoding="utf-8") as tf, \
             open(OUT / "person_index.json", "w", encoding="utf-8") as ix:
            pf.write("[")
            tf.write("[")
            ix.write("[")
            state = {"p": False, "t": False, "ix": False}    # array element written yet?

            def emit(fh, key, obj):
                fh.write(("," if state[key] else "") + "\n  "
                         + json.dumps(obj, ensure_ascii=False, default=str))
                state[key] = True

            for bid, sources in people.items():
                years = [e["src_year"] for recs in sources.values() for e in recs
                         if e.get("src_year") is not None]
                summary = {
                    "n_records": sum(len(v) for v in sources.values()),
                    "data_types": sorted(sources.keys()),
                    "first_year": min(years) if years else None,
                    "last_year": max(years) if years else None,
                }
                emit(ix, "ix", {"_id": bid, "bid_active_1": bid, **summary})
                n_people += 1

                # (a) organized by DATA TYPE -> person_documents.json
                full = {"_id": bid, "bid_active_1": bid, "summary": summary, "sources": dict(sources)}
                if estimate_size(full) <= limit:
                    emit(pf, "p", full)
                    n_person_docs += 1
                else:                          # shard by data type
                    stub = {"_id": bid, "bid_active_1": bid, "summary": summary,
                            "sharded": True, "shards": [f"{bid}::{dt_}" for dt_ in sources]}
                    emit(pf, "p", stub)
                    n_person_docs += 1
                    for dt_, recs in sources.items():
                        emit(pf, "p", {"_id": f"{bid}::{dt_}", "bid_active_1": bid,
                                       "src_data_type": dt_, "sources": {dt_: recs}})
                        n_person_docs += 1
                        n_sharded += 1

                # (b) organized by YEAR -> person_timeline.json
                by_year = defaultdict(list)
                for dt_, recs in sources.items():
                    for e in recs:
                        by_year[e["src_year"]].append({
                            "src_data_type": dt_,
                            "src_file_id": e["src_file_id"],
                            "src_row_id": e["src_row_id"],
                            "record": e["record"],
                        })
                timeline = {str(y): sorted(by_year[y], key=lambda r: r["src_data_type"])
                            for y in sorted(by_year, key=lambda v: (v is None, v))}
                tdoc = {"_id": bid, "bid_active_1": bid, "summary": summary, "timeline": timeline}
                if estimate_size(tdoc) <= limit:
                    emit(tf, "t", tdoc)
                    n_timeline_docs += 1
                else:                          # shard by year
                    stub = {"_id": bid, "bid_active_1": bid, "summary": summary,
                            "sharded": True, "shards": [f"{bid}::Y{y}" for y in timeline]}
                    emit(tf, "t", stub)
                    n_timeline_docs += 1
                    for y, recs in timeline.items():
                        emit(tf, "t", {"_id": f"{bid}::Y{y}", "bid_active_1": bid,
                                       "src_year": int(y) if y.isdigit() else y,
                                       "timeline": {y: recs}})
                        n_timeline_docs += 1
                        n_timeline_sharded += 1
            pf.write("\n]\n")
            tf.write("\n]\n")
            ix.write("\n]\n")

    # ---- manifest + summary -----------------------------------------------
    pd.DataFrame(inventory).to_csv(OUT / "_source_file_inventory.csv", index=False)
    man = (pd.DataFrame([{"collection": c, "n_documents": n} for c, n in sorted(coll_counts.items())]))
    man.to_csv(OUT / "_manifest.csv", index=False)
    summary = {
        "data_root": str(DATA_ROOT),
        "files_processed": len(files),
        "record_collections": len(coll_counts),
        "record_documents": total_docs,
        "orphan_rows_skipped_missing_bid": n_orphan,
        "distinct_subjects": n_people,
        "person_documents_written": n_person_docs,
        "person_docs_sharded_parts": n_sharded,
        "person_timeline_written": n_timeline_docs,
        "person_timeline_sharded_parts": n_timeline_sharded,
        "output_folder": str(OUT),
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (OUT / "_conversion_summary.json").write_text(json.dumps(summary, indent=2))

    print("\n== conversion summary ==")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    print("\nper-collection document counts:")
    print(man.to_string(index=False))


if __name__ == "__main__":
    main()
