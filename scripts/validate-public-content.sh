#!/usr/bin/env bash
set -euo pipefail

# Public-release guardrail for known internal names, domains, paths, and keys.
blocked='casas[[:space:]]*bahia|via[[:space:]]*varejo|casasbahia\.com|grupocasasbahia|viavarejo\.com|workspace-gcb|convair-helm|saas-enterprise|felipe\.silva|gcb-hr-|gcb-project|gcb-example|gcb-other|organization-helm|gcbregistry|grupoexample'
secrets='sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY'
scan_args=(--hidden -n -i -g '!.git/**' -g '!scripts/validate-public-content.sh' -g '!scripts/validate-public-content.ps1' -g '!scripts/public_content_check.py' -g '!*.png' -g '!*.jpg' -g '!*.jpeg' -g '!*.gif' -g '!*.webp' -g '!*.zip' -g '!*.pdf')

if rg "${scan_args[@]}" "$blocked" .; then
  echo "Public-content validation failed: blocked internal reference found." >&2
  exit 1
fi
if rg "${scan_args[@]}" "$secrets" .; then
  echo "Public-content validation failed: credential or private-key pattern found." >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  python3 scripts/public_content_check.py
else
  python scripts/public_content_check.py
fi

echo "Public-content validation passed."
