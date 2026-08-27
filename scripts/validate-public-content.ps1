$ErrorActionPreference = "Stop"

# Public-release guardrail for known internal names, domains, paths, and keys.
$blocked = 'casas\s*bahia|via\s*varejo|casasbahia\.com|grupocasasbahia|viavarejo\.com|workspace-gcb|convair-helm|saas-enterprise|felipe\.silva|gcb-hr-|gcb-project|gcb-example|gcb-other|organization-helm|gcbregistry|grupoexample'
$secrets = 'sk-[A-Za-z0-9]{10,}|ghp_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+|BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY'
$extensions = @('.md', '.txt', '.yaml', '.yml', '.json', '.sh', '.ps1', '.py', '.toml', '.xml', '.html')
$root = (Get-Location).Path
$files = Get-ChildItem -LiteralPath $root -Recurse -File | Where-Object {
  $_.FullName -notmatch '\\.git\\' -and
  $_.Name -notlike 'validate-public-content.*' -and
  $_.Name -ne 'public_content_check.py' -and
  $extensions -contains $_.Extension.ToLowerInvariant()
}

$blockedMatches = @()
$secretMatches = @()
foreach ($file in $files) {
  $text = [IO.File]::ReadAllText($file.FullName)
  if ($text -match $blocked) { $blockedMatches += $file.FullName }
  if ($text -match $secrets) { $secretMatches += $file.FullName }
}

if ($blockedMatches.Count -gt 0) {
  $blockedMatches | ForEach-Object { Write-Error "Blocked internal reference found: $_" }
  exit 1
}
if ($secretMatches.Count -gt 0) {
  $secretMatches | ForEach-Object { Write-Error "Credential or private-key pattern found: $_" }
  exit 1
}

python scripts/public_content_check.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Public-content validation passed."
