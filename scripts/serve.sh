#!/usr/bin/env bash
set -euo pipefail

# Script to serve the site locally for reviewers
# Usage: ./scripts/serve.sh

if ! command -v bundle >/dev/null 2>&1; then
  echo "Bundler is not installed. Run: gem install bundler"
  exit 2
fi

echo "Installing dependencies (may be skipped if already done)..."
bundle config set --local path vendor/bundle
bundle install --jobs 4 --retry 3

echo "Starting Jekyll server at http://127.0.0.1:4000/participons"
bundle exec jekyll serve --livereload --host 127.0.0.1 --port 4000
