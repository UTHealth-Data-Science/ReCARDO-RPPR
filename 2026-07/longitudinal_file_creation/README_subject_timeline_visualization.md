# Subject Timeline Visualization

A self-contained, **offline** web interface (`timeline_viewer/index.html`) that visualizes
one subject's records across **data types × years**, built from `person_timeline.json`
(Plan 2, source-preserving — values are shown verbatim, no harmonization). No internet or
CDN is required, so it runs inside the Enclave.

---

## Launch

```bash
cd longitudinal_file_creation/timeline_viewer
python3 build_viewer_data.py      # run:  subject files + index.json
python3 -m http.server 8000       # then open http://localhost:8000/
```

- **Step 1 — `build_viewer_data.py`** splits `../mongodb_files/person_timeline.json` (one
  large JSON array) into browser-friendly pieces under `timeline_viewer/data/`:
  - `data/index.json` — a small subject list (BID_ACTIVE_1, record counts, per-year totals)
  - `data/subjects/<bid>.json` — each subject's full timeline document
  This only needs to be re-run when the upstream `person_timeline.json` changes.
- **Step 2 — `python3 -m http.server 8000`** serves the folder locally (a web server is
  needed because browsers block `fetch()` of local files under `file://`).
- Open **http://localhost:8000/** in a browser. (Use any free port, e.g. `8001`, if 8000 is busy.)

To stop the server, press `Ctrl+C` in that terminal.

---

## What you see
- **Sidebar** — a searchable list of all subjects; type a `BID_ACTIVE_1` to filter, click to open.
- **Activity by year** — a small bar row of total records per year.
- **Timeline heatmap** — rows are data types, columns are years; each colored cell shows the
  record count for that (data type, year). Color marks the data-type family; intensity scales
  with the count.
- **Click any cell** — the underlying source records expand below, each field shown verbatim
  (original variable names and values) with provenance (`src_row_id`, `src_file_id`).

---

## No-server fallback (open the file directly)
If you cannot run a local server, open `timeline_viewer/index.html` directly in a browser and
**drag a subject file onto the panel** — either a `data/subjects/<bid>.json` file or any
element copied from `person_timeline.json`. The viewer renders it without a server.

---

## Requirements
- Python 3 (for `build_viewer_data.py` and the built-in `http.server`).
- A modern browser (Chrome/Edge/Firefox/Safari). No internet connection needed.
- `timeline_viewer/data/` must exist — created by Step 1.

## Troubleshooting
| Symptom | Fix |
|---|---|
| Sidebar says "index.json not loaded" | You opened the file via `file://`. Run `python3 -m http.server` (Step 2) and use the `http://localhost` URL, or use the drag-and-drop fallback. |
| "Address already in use" on port 8000 | Use another port: `python3 -m http.server 8001`, then open `http://localhost:8001/`. |
| Empty / missing subjects | Re-run `python3 build_viewer_data.py`; confirm `../mongodb_files/person_timeline.json` exists (produced by `convert_active_to_mongodb.py`). |

---

## Files
| Path | Purpose |
|---|---|
| `timeline_viewer/index.html` | the viewer (self-contained, offline) |
| `timeline_viewer/build_viewer_data.py` | splits `person_timeline.json` for the browser |
| `timeline_viewer/data/index.json` | subject list + per-year totals (generated) |
| `timeline_viewer/data/subjects/<bid>.json` | one subject's full timeline (generated) |
