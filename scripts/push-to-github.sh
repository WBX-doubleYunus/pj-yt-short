#!/usr/bin/env bash
set -e
if [ -z "$(git remote)" ]; then
  echo "No git remote found. Run 'git remote add origin <git-url>' first."
  exit 1
fi
git add .
msg=${1:-"chore: update project"}
git commit -m "$msg" || true
git push origin HEAD

echo "Push complete. The GitHub Actions workflow will run automatically to execute tests and demo."