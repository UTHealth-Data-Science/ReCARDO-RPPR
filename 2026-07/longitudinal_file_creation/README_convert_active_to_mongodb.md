The longitudinal data generation process transforms the project's annual CMS source files into a person-centered, query-ready document database. The input consists of multiple annual SAS datasets (*.sas7bdat) spanning multiple years and physical data types stored in the ACTIVE folder, all linkable through the common participant identifier BID_ACTIVE_1. The output comprises a set of MongoDB-ready JSON documents, including one record-collection file for each data type and three complementary subject-level views: person_documents.json, organized by data type; person_timeline.json, organized chronologically by year; and a lightweight person_index.json for efficient subject lookup.

The pipeline follows a strictly source-preserving design. Each SAS file is read verbatim, retaining every original variable name and value without harmonization, recoding, or concept mapping. The only additions are a small provenance block containing src_data_type, src_year, src_file_id, and src_row_id, together with a normalized BID_ACTIVE_1 identifier. Each source row is represented as a flexible record object containing its native fields, with empty fields omitted, and records are aggregated for each subject by both data type and calendar year.

Compared with a conventional relational database, the resulting JSON document model naturally accommodates the extreme heterogeneity, sparsity, and year-to-year schema evolution of longitudinal CMS data without requiring schema engineering, column expansion, or database migrations. Because every record preserves its original structure and provenance, the representation provides complete fidelity and full auditability, allowing every value to be traced directly back to its source file and row. The subject-centered organization also enables complete longitudinal retrieval of an individual's history in a single query without relational joins, while leaving any harmonization or variable standardization to be performed at query time rather than being irreversibly embedded during data generation.

To facilitate data exploration, the pipeline also provides a straightforward way to  a self-contained offline visualization interface based on the per-subject timeline documents. For each participant, the interface displays an interactive heatmap in which rows represent data types and columns represent years. Selecting any year and data type cell reveals the corresponding source records with their original variable names and values, transforming hundreds of annual CMS files into an intuitive, drill-down visualization of each participant's longitudinal care history.

# `convert_active_to_mongodb.py`

Converts the **ACTIVE synthetic raw data** (`../ACTIVE/**/*.sas7bdat`) into **MongoDB
JSON files**, following the Plan 2 — MongoDB solution: **source-preserving, NO
harmonization, NO concept mapping**. Records are linked across data types and years
**only by `BID_ACTIVE_1`**.

> The `../ACTIVE` data folder is **read-only** — the script never writes to it.

---

## Requirements
- Python 3.9+
- `pandas`, `numpy`, `pyreadstat`

```bash
pip install pandas numpy pyreadstat
```

## Usage
```bash
cd longitudinal_data_creation
python3 convert_active_to_mongodb.py
```
All output is written to `./mongodb_files/`. The run is **idempotent**: prior
`src_*.json`, `person_documents.json`, `person_timeline.json`, and `person_index.json`
files are deleted first, so re-running produces a clean set.

### Configuration (edit the top of the script)
| Constant | Default | Meaning |
|---|---|---|
| `DATA_ROOT` | `../ACTIVE` | Folder scanned recursively for `*.sas7bdat` (read-only) |
| `OUT` | `./mongodb_files` | Output folder (created if missing) |
| `main(person_docs=…)` | `True` | Also build the person + timeline + index documents |
| `main(shard_mb=…)` | `15.0` | Per-document size limit before a subject is sharded |

---

## What it does
1. **Discover** every `*.sas7bdat` under `DATA_ROOT` (the stray `*.sas7bdat.py` files are
   ignored automatically — the glob matches only the real `.sas7bdat` files).
2. **Map** each file to its physical data type from its folder + name (table below).
3. **Read** each file with `pyreadstat` (verbatim — no recoding).
4. **Normalize** the linkage key `BID_ACTIVE_1` (trim + upper-case only). Rows with a
   missing/blank key are skipped and counted as orphans (never imputed).
5. **Emit one document per row** into a per-data-type collection file, keeping the
   **original variable names and values** under `"record"`; null/blank fields are omitted
   (sparse-friendly). Provenance is added at the top level.
6. **Build per-subject documents** two ways (organized by data type, and by year) plus a
   lightweight index, each a JSON array, with a 16 MB shard guard.
7. Write metadata files (`_manifest.csv`, `_source_file_inventory.csv`,
   `_conversion_summary.json`).

### Data-type mapping
| Source path / file | Physical data type | Collection file |
|---|---|---|
| `DN/dn_*.sas7bdat` | `DN` | `src_dn.json` |
| `IRFPAI/irfpai_*` | `IRF-PAI` | `src_irf_pai.json` |
| `MAX/IP|LT|OT|PS|RX/*` | `MAX-IP` … `MAX-RX` | `src_max_ip.json` … |
| `MBSF/mbs_base_*` | `MBSF-Base` | `src_mbsf_base.json` |
| `MBSF/mbs_cc_*` | `MBSF-CC` | `src_mbsf_cc.json` |
| `MBSF/mbs_costuse_*` | `MBSF-CU` | `src_mbsf_cu.json` |
| `MBSF/mbs_otcc_*` | `MBSF-Other` | `src_mbsf_other.json` |
| `MDS/mds_*` | `MDS` | `src_mds.json` |
| `MP/mp_*` | `MedPAR` | `src_medpar.json` |
| `MTM/mtm_*` | `MTM` | `src_mtm.json` |
| `OASIS/oasis_*` | `OASIS` | `src_oasis.json` |
| `PDE/pde_*` | `PDE` | `src_pde.json` |
| `TAF/CLAIMIP|LT|OT|RX/*` | `TMSIS-IP` … `TMSIS-RX` | `src_tmsis_ip.json` … |
| `TAF/DE/<BASE\|DSB\|DTS\|HSP\|MC\|MFP\|WVR>/*` | `TMSIS-DE Base` … `TMSIS-DE WVR` | `src_tmsis_de_base.json` … |

---

## Output (`mongodb_files/`)
Every output is a **JSON array** of documents (standard `.json`, not newline-delimited).

| File | Contents |
|---|---|
| `src_<data_type>.json` (27) | record collections — one element per source row |
| `person_documents.json` | one element per subject, records organized by **data type** |
| `person_timeline.json` | one element per subject, records organized by **year** |
| `person_index.json` | one lightweight element per subject (counts + coverage) |
| `_manifest.csv` | per-collection document counts |
| `_source_file_inventory.csv` | every file processed (data type, year, row count, status) |
| `_conversion_summary.json` | run summary (a single JSON object) |

### Document shapes
```json
// src_medpar.json  — one record = one element
{ "bid_active_1":"1000000064", "src_data_type":"MedPAR", "src_year":2000,
  "src_file_id":231, "src_row_id":0,
  "record": { "AGE_CNT":79, "SEX":"2", "RACE":"1", "ADMSNDT":"2000-07-03T00:00:00", "NPI":"5756977795" } }

// person_documents.json  — organized by DATA TYPE
{ "_id":"1000000001", "bid_active_1":"1000000001",
  "summary": { "n_records":275, "data_types":["DN","MedPAR","PDE","..."], "first_year":1991, "last_year":2019 },
  "sources": { "DN":[ {"src_year":1991,"record":{ "SEX":"1","AGE":67,"..." }} ], "MedPAR":[ "..." ] } }

// person_timeline.json  — organized by YEAR
{ "_id":"1000000001", "bid_active_1":"1000000001", "summary": { "..." },
  "timeline": { "2000":[ {"src_data_type":"DN","src_row_id":0,"record":{ "SEX":"1","AGE":76 }},
                         {"src_data_type":"MBSF-Base","record":{ "AGE_AT_END_REF_YR":77 }} ] } }
```

### Provenance fields (top level of every record document)
| Field | Meaning |
|---|---|
| `bid_active_1` | Subject linkage key (trim + upper; the only cross-file key) |
| `src_data_type` | Physical data type (e.g. `MedPAR`) |
| `src_year` | Year parsed from the file name |
| `src_file_id` | Sequential id of the source file (see `_source_file_inventory.csv`) |
| `src_row_id` | Row ordinal within that file (back-pointer to the exact source row) |
| `record` | All native variables, original names & values; nulls omitted |

---

## Sharding (16 MB guard)
MongoDB caps a document at 16 MB. If a subject's `person_documents` / `person_timeline`
document would exceed `shard_mb`, it is split: a parent **stub** (`"sharded": true`, with
`shards` pointers) plus child documents keyed `"<bid>::<data_type>"` (by-type) or
`"<bid>::Y<year>"` (by-year). With the synthetic data no subject required sharding.

## Last run
```
379 files → 27 record collections, 153,093 record documents,
1,000 subjects → 1,000 person_documents + 1,000 person_timeline + 1,000 person_index,
0 orphans, 0 sharded.
```

## Load into MongoDB
The files are JSON arrays, so use `--jsonArray`:
```bash
for f in mongodb_files/src_*.json; do
  c=$(basename "$f" .json)
  mongoimport --db active_plan2 --collection "$c" --type json --jsonArray --file "$f"
done
mongoimport --db active_plan2 --collection person   --type json --jsonArray --file mongodb_files/person_documents.json
mongoimport --db active_plan2 --collection timeline --type json --jsonArray --file mongodb_files/person_timeline.json
```
With pymongo: `json.load(open(f))` → `collection.insert_many(docs)`.

## Notes & caveats
- **Verbatim by design.** SAS "missing-date" sentinels (e.g. `EXHST_DT: "1960-01-01T00:00:00"`,
  the SAS date-0) are kept as delivered, because Plan 2 performs no harmonization.
- **Integer codes containing a missing value** may render as floats (e.g. `127.0`) — a pandas
  dtype artifact when a column has any `NaN`, not data loss.
- **Dates** are emitted as ISO-8601 strings; values pyreadstat returns as numeric SAS dates are
  kept as numbers.
- **Field names** are kept exactly as in the source; only the rare illegal Mongo key (`.` or a
  leading `$`) is sanitized (`.` → `_`).
