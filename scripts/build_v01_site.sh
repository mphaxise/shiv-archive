#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/praneet/shiv-archive"
LEGACY_DB="$ROOT/data/shiv_opinions_v0.db"
MASTER_DB="$ROOT/data/shiv_master.db"
ANALYSIS_DB="$ROOT/data/shiv_analysis.db"

if [ ! -f "$MASTER_DB" ] || [ ! -f "$ANALYSIS_DB" ]; then
  echo "Dual DBs not found. Migrating from legacy DB..."
  "$ROOT/scripts/migrate_to_dual_db.py" \
    --source-db-path "$LEGACY_DB" \
    --master-db-path "$MASTER_DB" \
    --analysis-db-path "$ANALYSIS_DB"
fi

"$ROOT/scripts/generate_shift_annotations_dual.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --shift-id all \
  --annotation-version rule_based_v1_multisource

"$ROOT/scripts/generate_republic_critical_evidence.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --version critical_v3 \
  --max-per-phase 12 \
  --min-score 14 \
  --min-anchor-hits 3 \
  --min-group-hits 2

python3 "$ROOT/scripts/generate_republic_shift_research_packet.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --output-json "$ROOT/src/data/republic_shift_story_2026-02-26.json" \
  --output-md "$ROOT/docs/research/republic-shift-brief-2026-02-26.md"

cp "$ROOT/src/data/republic_shift_story_2026-02-26.json" \
  "$ROOT/docs/research/republic-shift-evidence-2026-02-26.json"

python3 "$ROOT/scripts/generate_science_shift_research_packet.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --output-json "$ROOT/src/data/science_shift_story_2026-02-26.json" \
  --output-md "$ROOT/docs/research/science-shift-brief-2026-02-26.md"

cp "$ROOT/src/data/science_shift_story_2026-02-26.json" \
  "$ROOT/docs/research/science-shift-evidence-2026-02-26.json"

"$ROOT/scripts/export_public_json_dual.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --output-path "$ROOT/web/public/data/articles.json"

"$ROOT/scripts/export_public_json_dual.py" \
  --master-db-path "$MASTER_DB" \
  --analysis-db-path "$ANALYSIS_DB" \
  --output-path "$ROOT/src/data/articles.json"

echo "v0.1 data build complete (dual DB mode)."
echo "Preview: python3 -m http.server --directory $ROOT/web/public 4173"
