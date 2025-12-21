#!/usr/bin/env bash
set -euo pipefail

# Script to serve the site locally with clean rebuild and optional broken link check
# Serves at http://127.0.0.1:4000/ (root) for easier local testing (--baseurl '')

if ! command -v bundle >/dev/null 2>&1; then
  echo "Bundler is not installed. Run: gem install bundler"
  exit 2
fi

# Fix SSL certificate verification on macOS (for remote theme fetch)
if [[ -f "$(brew --prefix)/etc/ca-certificates/cert.pem" ]]; then
  export SSL_CERT_FILE="$(brew --prefix)/etc/ca-certificates/cert.pem"
  echo "✓ SSL certificates configured"
fi

echo "Cleaning old build artifacts..."
rm -rf _site .jekyll-cache .jekyll-metadata .sass-cache

echo "Installing dependencies..."
bundle config set --local path vendor/bundle
bundle install --jobs 4 --retry 3

echo "Building site..."
bundle exec jekyll build --baseurl ''

# echo "Checking for broken links..."
# bundle exec htmlproofer ./_site \
#   --assume-extension \
#   --allow-hash-href \
#   --ignore-urls "/framaforms.org/,/tags/#,/categories/#" \
#   --disable-external \
#   --ignore-status-codes "0,200,301,302,403,999" \
#   --ignore-missing-alt \
#   --no-enforce-https \
#   --ignore-files "/.+\.(js|css|json)$/i" \
#   || echo "⚠️  Some htmlproofer checks failed (non-blocking for local dev)"

echo "Starting Jekyll server at http://127.0.0.1:4000/ (root for local dev)"
bundle exec jekyll serve --livereload --verbose --trace --host 127.0.0.1 --port 4000 --baseurl ''