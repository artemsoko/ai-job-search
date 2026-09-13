#!/usr/bin/env bash
# One scrape round over LinkedIn with PAGINATION and generic titles.
#
# Two gaps this closes, both found on 2026-08-14 when NVIDIA reqs turned out to be
# absent from a 371-entry seen_jobs.json:
#   1. LinkedIn's page size is fixed at 10. Passing --limit 20 does NOT fetch page 2,
#      so every earlier round only ever saw the top 10 hits per query.
#   2. Every query carried the word Python or Backend. Titles like "Senior Software
#      Developer" or "Senior Software Engineer" never matched, so whole employers
#      (NVIDIA among them) were invisible regardless of what the body said.
#
# Usage: ./scripts/scrape_round.sh <jobage-days> <output.jsonl>
set -uo pipefail
CLI=".agents/skills/linkedin-search/cli/src/cli.ts"
AGE="${1:-30}"
OUT="${2:-/tmp/scrape_round.jsonl}"
: > "$OUT"

# Generic titles first — these are the ones that were missing.
QUERIES_NL=(
  "Senior Software Engineer"
  "Senior Software Developer"
  "Senior Python Engineer"
  "Senior Backend Engineer"
  "Python Developer"
  "Staff Software Engineer"
  "Lead Software Engineer"
)
QUERIES_UK=(
  "Senior Software Engineer Python"
  "Senior Backend Engineer"
  "Senior Python Developer"
  "Staff Software Engineer Python"
)

run() {  # run <query> <location> <page>
  bun run "$CLI" search -q "$1" -l "$2" --jobage "$AGE" --page "$3" --format json 2>/dev/null \
  | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit()
for r in d.get('results',[]):
    r['_q']=sys.argv[1]; r['_loc']=sys.argv[2]; r['_page']=sys.argv[3]
    print(json.dumps(r,ensure_ascii=False))
" "$1" "$2" "$3" >> "$OUT"
}

for q in "${QUERIES_NL[@]}"; do
  for page in 1 2; do
    run "$q" "Netherlands" "$page"
  done
done
for q in "${QUERIES_UK[@]}"; do
  for page in 1 2; do
    run "$q" "London, United Kingdom" "$page"
  done
done

echo "rows: $(wc -l < "$OUT")  unique ids: $(python3 -c "
import json,sys
ids={json.loads(l)['id'] for l in open('$OUT')}
print(len(ids))
")"
