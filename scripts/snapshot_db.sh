#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/praneet/shiv-archive"
DB="$ROOT/data/shiv_opinions_v0.db"
SNAP_DIR="$ROOT/data/snapshots"
LOG_FILE="$SNAP_DIR/SNAPSHOTS.log"

mkdir -p "$SNAP_DIR"

stamp="$(date -u +"%Y%m%dT%H%M%SZ")"
snap="$SNAP_DIR/shiv_opinions_v0_${stamp}.db"

cp "$DB" "$snap"
hash="$(shasum -a 256 "$snap" | awk '{print $1}')"

{
  echo "${stamp}  ${hash}  ${snap}"
} >> "$LOG_FILE"

echo "Snapshot created: $snap"
echo "SHA256: $hash"
echo "Logged: $LOG_FILE"
