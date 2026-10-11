#!/usr/bin/env bash
# scripts/dev-env.sh — audierne's env loader: one file per concern, in order.
# Source it (source scripts/dev-env.sh) or run a command through it:
#   bash scripts/dev-env.sh python3 scripts/export_contributions_to_md.py
# A missing layer STOPS: an unset key would otherwise reach a script as empty.
# A .env.<concern>.dev beside a layer overrides it (laptop only).
# CI loads nothing from here: Actions reads its own repository secrets.

_audierne_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
_audierne_layers=(config claude infra platforms)

_audierne_load() {
  local c f
  for c in "${_audierne_layers[@]}"; do
    f="${_audierne_root}/.env.${c}"
    [ -f "$f" ] || { echo "dev-env: STOP — ${f} missing (template: env-templates/env.${c}.example)" >&2; return 1; }
    set -a; . "$f"; set +a
    [ -f "${f}.dev" ] && { set -a; . "${f}.dev"; set +a; }
  done
  echo "dev-env: loaded ${#_audierne_layers[@]}/${#_audierne_layers[@]} layers" >&2
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  set -euo pipefail
  _audierne_load
  [ "$#" -gt 0 ] && exec "$@"
else
  _audierne_load
fi
