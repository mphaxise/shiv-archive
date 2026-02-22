# Shiv Archive Corpus (v1.1)

This workspace contains:
- a dual-database corpus with stable master records + independent analysis layers
- curated v1 enrichment imports
- a public v0.1 website (search + filters + browse cards)
- a Next.js Layered View Engine (Shiv Archive v1.0)

## Current artifacts
- Seed CSV: `/Users/praneet/shiv-archive/data/seed/tnie_shiv_articles_ctrl_a_2026-02-22.csv`
- Curated JSON seed: `/Users/praneet/shiv-archive/data/seed/tnie_shiv_curated_v1_2026-02-22.json`
- Legacy SQLite DB: `/Users/praneet/shiv-archive/data/shiv_opinions_v0.db`
- Master DB (immutable corpus): `/Users/praneet/shiv-archive/data/shiv_master.db`
- Analysis DB (tags + summaries + shifts): `/Users/praneet/shiv-archive/data/shiv_analysis.db`
- Master schema: `/Users/praneet/shiv-archive/db/master_schema.sql`
- Analysis schema: `/Users/praneet/shiv-archive/db/analysis_schema.sql`
- Bootstrap script: `/Users/praneet/shiv-archive/scripts/bootstrap_zero_db.py`
- Curated import script: `/Users/praneet/shiv-archive/scripts/import_curated_v1_json.py`
- URL enrichment script: `/Users/praneet/shiv-archive/scripts/enrich_urls_from_author_html.py`
- Batch URL backfill script: `/Users/praneet/shiv-archive/scripts/backfill_urls_in_batches.py`
- Batch verification promotion script: `/Users/praneet/shiv-archive/scripts/promote_verified_in_batches.py`
- Batch summary enrichment script: `/Users/praneet/shiv-archive/scripts/enrich_summaries_from_urls.py`
- Multi-source rebuild script: `/Users/praneet/shiv-archive/scripts/rebuild_multisource_archive.py`
- TNIE restoration merge script: `/Users/praneet/shiv-archive/scripts/merge_tnie_from_snapshot.py`
- Shift annotation generator script: `/Users/praneet/shiv-archive/scripts/generate_shift_annotations.py`
- Dual-db shift annotation generator script: `/Users/praneet/shiv-archive/scripts/generate_shift_annotations_dual.py`
- Legacy-to-dual migration script: `/Users/praneet/shiv-archive/scripts/migrate_to_dual_db.py`
- Full text backfill script (master DB): `/Users/praneet/shiv-archive/scripts/backfill_article_texts.py`
- Republic critical evidence generator (analysis DB): `/Users/praneet/shiv-archive/scripts/generate_republic_critical_evidence.py`
- DB snapshot script: `/Users/praneet/shiv-archive/scripts/snapshot_db.sh`
- Public data export script: `/Users/praneet/shiv-archive/scripts/export_public_json.py`
- Dual-db export script: `/Users/praneet/shiv-archive/scripts/export_public_json_dual.py`
- v0.1 build script: `/Users/praneet/shiv-archive/scripts/build_v01_site.sh`
- Website entrypoint: `/Users/praneet/shiv-archive/web/public/index.html`
- Next.js app entrypoint: `/Users/praneet/shiv-archive/src/app/page.tsx`

## Rebuild database from seed
```bash
/Users/praneet/shiv-archive/scripts/bootstrap_zero_db.py
```

## Enrich with real TNIE links from page source
1. Save the Shiv author page HTML as a local file, for example:
   `/Users/praneet/shiv-archive/data/raw/author_page.html`
2. Run:
```bash
/Users/praneet/shiv-archive/scripts/enrich_urls_from_author_html.py \
  --html-path /Users/praneet/shiv-archive/data/raw/author_page.html
```

## Import curated v1 JSON
```bash
/Users/praneet/shiv-archive/scripts/import_curated_v1_json.py \
  --json-path /Users/praneet/shiv-archive/data/seed/tnie_shiv_curated_v1_2026-02-22.json
```

## Initialize dual DB architecture (master + analysis)
```bash
/Users/praneet/shiv-archive/scripts/migrate_to_dual_db.py \
  --source-db-path /Users/praneet/shiv-archive/data/shiv_opinions_v0.db \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --analysis-db-path /Users/praneet/shiv-archive/data/shiv_analysis.db
```

If you need to rebuild dual DBs from legacy:
```bash
/Users/praneet/shiv-archive/scripts/migrate_to_dual_db.py \
  --source-db-path /Users/praneet/shiv-archive/data/shiv_opinions_v0.db \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --analysis-db-path /Users/praneet/shiv-archive/data/shiv_analysis.db \
  --force
```

## Build website data (dual DB mode)
```bash
/Users/praneet/shiv-archive/scripts/build_v01_site.sh
```

## Backfill all missing article URLs (5 at a time)
```bash
/Users/praneet/shiv-archive/scripts/backfill_urls_in_batches.py --batch-size 5
```

If you only want a preview:
```bash
/Users/praneet/shiv-archive/scripts/backfill_urls_in_batches.py --batch-size 5 --dry-run
```

## Promote draft articles to verified (5 at a time)
```bash
/Users/praneet/shiv-archive/scripts/promote_verified_in_batches.py --batch-size 5
```

Preview mode:
```bash
/Users/praneet/shiv-archive/scripts/promote_verified_in_batches.py --batch-size 5 --dry-run
```

## Replace heuristic summaries with page-derived summaries (5 at a time)
```bash
/Users/praneet/shiv-archive/scripts/enrich_summaries_from_urls.py \
  --batch-size 5 \
  --only-heuristic \
  --resolve-search
```

Preview mode:
```bash
/Users/praneet/shiv-archive/scripts/enrich_summaries_from_urls.py \
  --batch-size 5 \
  --only-heuristic \
  --resolve-search \
  --dry-run
```

## Generate reusable and auditable shift annotations (dual DB mode)
```bash
/Users/praneet/shiv-archive/scripts/generate_shift_annotations_dual.py \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --analysis-db-path /Users/praneet/shiv-archive/data/shiv_analysis.db \
  --shift-id all
```

Preview mode:
```bash
/Users/praneet/shiv-archive/scripts/generate_shift_annotations_dual.py \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --analysis-db-path /Users/praneet/shiv-archive/data/shiv_analysis.db \
  --shift-id all \
  --dry-run
```

## Generate full article text in master DB (5 at a time)
```bash
/Users/praneet/shiv-archive/scripts/backfill_article_texts.py \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --batch-size 5
```

Preview mode:
```bash
/Users/praneet/shiv-archive/scripts/backfill_article_texts.py \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --batch-size 5 \
  --dry-run
```

## Generate strict Republic shift picks with quote-backed rationale
```bash
/Users/praneet/shiv-archive/scripts/generate_republic_critical_evidence.py \
  --master-db-path /Users/praneet/shiv-archive/data/shiv_master.db \
  --analysis-db-path /Users/praneet/shiv-archive/data/shiv_analysis.db \
  --version critical_v1 \
  --max-per-phase 18 \
  --min-score 11
```

## Legacy single-db shift annotations (compatibility mode)
```bash
/Users/praneet/shiv-archive/scripts/generate_shift_annotations.py \
  --shift-id all
```

Preview mode:
```bash
/Users/praneet/shiv-archive/scripts/generate_shift_annotations.py \
  --shift-id all \
  --dry-run
```

## Rebuild from 61-article multi-source archive (TNIE + Scroll + EPW + Outlook)
```bash
/Users/praneet/shiv-archive/scripts/rebuild_multisource_archive.py \
  --batch-size 5
```

## Merge back complete TNIE archive from snapshot (batch size 5)
```bash
/Users/praneet/shiv-archive/scripts/merge_tnie_from_snapshot.py \
  --batch-size 5 \
  --snapshot-db-path /Users/praneet/shiv-archive/data/snapshots/shiv_opinions_v0_20260222T204026Z.db
```

## Create immutable DB snapshot before any bulk update
```bash
/Users/praneet/shiv-archive/scripts/snapshot_db.sh
```
Snapshots are stored under:
`/Users/praneet/shiv-archive/data/snapshots`

## Backend policy (static source of truth)
- Primary source of truth is split:
  - Master corpus DB: `/Users/praneet/shiv-archive/data/shiv_master.db`
  - Analysis DB: `/Users/praneet/shiv-archive/data/shiv_analysis.db`
- Legacy import source (read-only compatibility): `/Users/praneet/shiv-archive/data/shiv_opinions_v0.db`
- Do not mutate data manually.
- Apply changes only through scripts in `/Users/praneet/shiv-archive/scripts`.
- Create a snapshot before bulk operations.
- Every enrichment operation must write provenance and QA notes.
- Raw article metadata and article text are stored in master DB tables.
- Summaries, tags, and shift/view analysis are stored in analysis DB tables.
- Shift annotations are persisted in analysis DB `shift_annotations` with run-level audit in `shift_annotation_runs`.

## Run Shiv Archive (Next.js)
Install once:
```bash
cd /Users/praneet/shiv-archive && npm install
```

Local dev:
```bash
cd /Users/praneet/shiv-archive && npm run dev -- --port 5180
```
Open:
`http://localhost:5180`

Production build:
```bash
cd /Users/praneet/shiv-archive && npm run build
```
Static export output:
`/Users/praneet/shiv-archive/out`

Cloudflare Pages:
- Build command: `npm run build`
- Output directory: `out`

## Preview website locally
```bash
python3 -m http.server --directory /Users/praneet/shiv-archive/web/public 4173
```
Open:
`http://localhost:4173`

## Quick checks
```bash
sqlite3 /Users/praneet/shiv-archive/data/shiv_master.db \
  "SELECT COUNT(*) AS articles, MIN(published_at), MAX(published_at) FROM articles;"

sqlite3 /Users/praneet/shiv-archive/data/shiv_master.db \
  "SELECT section, COUNT(*) FROM articles GROUP BY section ORDER BY COUNT(*) DESC;"

sqlite3 /Users/praneet/shiv-archive/data/shiv_master.db \
  "SELECT COUNT(*) AS total, SUM(CASE WHEN status='verified' THEN 1 ELSE 0 END) AS verified FROM articles;"

sqlite3 /Users/praneet/shiv-archive/data/shiv_analysis.db \
  "SELECT COUNT(*) AS analysis_rows, SUM(CASE WHEN summary IS NOT NULL AND TRIM(summary) <> '' THEN 1 ELSE 0 END) AS with_summary FROM article_analysis;"

sqlite3 /Users/praneet/shiv-archive/data/shiv_analysis.db \
  "SELECT shift_id, COUNT(*) FROM shift_annotations GROUP BY shift_id ORDER BY shift_id;"
```
