#!/usr/bin/env bash
# Install bundle v22 into a bench, and PROVE it landed before touching the site.
#
# Why this script exists: `git update-ref refs/heads/<branch> refs/bundles/<branch>` moves the
# branch pointer only - it does not touch the working tree. The app then keeps running the old
# code while `git log` already shows the new commit, which is how an "installed" fix can still
# print the framework's default grid. This script does the working-tree step, verifies the new
# files are on disk, and stops if they are not.
set -euo pipefail

APP_DIR="${APP_DIR:-$HOME/frappe-bench/apps/murasalat_office}"
PACK_DIR="${PACK_DIR:-/tmp}"
BRANCH="${BRANCH:-feat/attachment-native-minimum}"
SITE="${SITE:-murasalat.localhost}"
BUNDLE="$PACK_DIR/murasalat_office-$(printf '%s' "$BRANCH" | tr '/' '-').bundle"
TEMPLATE="murasalat_office/murasalat_office/report/murasalat_management_summary/murasalat_management_summary.html"

cd "$APP_DIR"

echo "== 1/5  updating the working tree =="
[ -f "$BUNDLE" ] || { echo "FAIL: bundle not found at $BUNDLE"; exit 1; }
git fetch "$BUNDLE" "+refs/heads/$BRANCH:refs/bundles/$BRANCH"
git checkout -f -B "$BRANCH" "refs/bundles/$BRANCH"
git log --oneline -1

echo
echo "== 2/5  proving the new code is on disk =="
[ -f "$TEMPLATE" ] || { echo "FAIL: $TEMPLATE is missing - the tree is still stale, nothing installed"; exit 1; }
echo "layout file: present"
grep -q "def template_path" murasalat_office/setup/report_print_formats.py \
  || { echo "FAIL: the installer is still the old one"; exit 1; }
echo "installer: new version"
echo "working tree diff: $(git status --porcelain | wc -l) file(s)"

echo
echo "== 3/5  python syntax =="
python3 -m compileall -q murasalat_office/setup/report_print_formats.py && echo "ok"

if [ "${SKIP_BENCH:-0}" = "1" ]; then
  echo
  echo "== 4/5  bench steps skipped (SKIP_BENCH=1) =="
  echo "== 5/5  DONE - the tree is verified, the site was not touched =="
  exit 0
fi

echo
echo "== 4/5  refreshing the site =="
bench --site "$SITE" migrate
bench --site "$SITE" execute murasalat_office.setup.report_print_formats.plan
bench --site "$SITE" execute murasalat_office.setup.report_print_formats.install
bench --site "$SITE" clear-cache

echo
echo "== 5/5  DONE =="
cat <<'NOTE'
Open the report and hard-reload the page (Ctrl+Shift+R), then Print.
Leave "Print Format" empty and "Pick Columns" unticked - the report's own A4 layout is used.
plan must now print a "current" key for each format; the layout colours come from that file,
not from the Print Format rows, so even an empty dropdown prints correctly.
NOTE
