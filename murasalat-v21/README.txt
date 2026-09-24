Murasalat Office - five branches, all verified
==============================================

  1. fix/seal-integrity                    3896cdd
  2. chore/ci-and-verification             a98d172
  3. fix/arabic-labels                     df1521b
  4. fix/referral-cancellation             662c291
  5. fix/verification-and-workflow-tasks   ec3f0aa

Chain: fix/div12-repair -> ... -> feat/professional-reports -> 1 -> 2 -> 3 -> 4 -> 5.

RECOMMENDED - bundles, fetching into temporary refs
---------------------------------------------------
Fetching straight into a branch fails with "refusing to fetch into branch ...
checked out" when that branch happens to be the current one. Fetching into a
throwaway ref and then moving the branch avoids that entirely.

  cd ~/frappe-bench/apps/murasalat_office
  D=~/murasalat-branches
  git fetch origin
  git checkout --detach

  while read -r file branch; do
    git fetch "$D/$file" "+refs/heads/$branch:refs/bundles/$branch" || break
    git update-ref "refs/heads/$branch" "refs/bundles/$branch"
    echo "$branch -> $(git rev-parse --short "refs/heads/$branch")"
  done <<'LIST'
murasalat_office-fix-seal-integrity.bundle fix/seal-integrity
murasalat_office-chore-ci-verification.bundle chore/ci-and-verification
murasalat_office-fix-arabic-labels.bundle fix/arabic-labels
murasalat_office-fix-referral-cancellation.bundle fix/referral-cancellation
murasalat_office-fix-verification-workflow-tasks.bundle fix/verification-and-workflow-tasks
LIST

  git push origin fix/seal-integrity chore/ci-and-verification fix/arabic-labels
  git push origin fix/referral-cancellation fix/verification-and-workflow-tasks

Expected short SHAs, in the order printed above:
  3896cdd  a98d172  df1521b  662c291  ec3f0aa

ALTERNATIVE - patches
---------------------
  git checkout -B chore/ci-and-verification fix/seal-integrity
  git am "$D/chore-ci-verification.patch"
  # parent of each branch is the previous one in the list above

THEN, on the site
-----------------
  git checkout fix/verification-and-workflow-tasks
  bench --site murasalat.localhost execute murasalat_office.setup.report_access.apply_report_roles
  bench --site murasalat.localhost execute murasalat_office.setup.workflow_tasks.plan
  bench --site murasalat.localhost execute murasalat_office.verification.site_smoke.run

If an earlier run of the role script rewrote report definitions:
  git checkout -- murasalat_office/murasalat_office/report/
