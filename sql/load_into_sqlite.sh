#!/usr/bin/env bash
# Build a local SQLite database from data/*.csv and run every analysis query.
# Usage:  bash sql/load_into_sqlite.sh
# Output: ecommerce.db in the project root.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB="$ROOT/ecommerce.db"
rm -f "$DB"

sqlite3 "$DB" < "$ROOT/sql/00_schema.sql"

import_csv() { # table file
  sqlite3 "$DB" <<EOF
.mode csv
.import --skip 1 $ROOT/data/$2 $1
EOF
}

import_csv customers          customers.csv
import_csv orders             orders.csv
import_csv order_items        order_items.csv
import_csv payments           payments.csv
import_csv reviews            reviews.csv
import_csv products           products.csv
import_csv sellers            sellers.csv
import_csv category_translation category_translation.csv

echo "Loaded tables:"
sqlite3 "$DB" "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"

for f in "$ROOT"/sql/0[1-9]_*.sql "$ROOT"/sql/10_*.sql; do
  echo
  echo "================ $(basename "$f") ================"
  sqlite3 -header -column "$DB" < "$f" | head -25
done

echo
echo "Done. Database: $DB"
