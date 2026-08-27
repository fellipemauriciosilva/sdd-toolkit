param(
  [Parameter(Position=0)] [string]$ProjectDir = "",
  [ValidateSet("user", "organization")] [string]$Scope = "user",
  [ValidateSet("copilot", "claude", "codex", "cursor", "all", "detected")] [string]$Runtime = "detected",
  [string]$KitRoot = "",
  [string]$InstallRoot = "",
  [string]$ProfileRoot = "",
  [string]$RepositoryUrl = "",
  [ValidateSet("stable", "beta", "main")] [string]$Channel = "main",
  [string]$Ref = "",
  [switch]$DryRun,
  [switch]$NoPath
)

$ErrorActionPreference = "Stop"
if ($ProjectDir) { throw "Instalação por projeto foi removida. Execute install.ps1 sem ProjectDir." }
if ($Scope -eq "organization") { throw "Scope organization requer provider e policy gerenciada; operação bloqueada." }
if ($Scope -ne "user") { throw "O único scope local suportado é user." }
if (-not $KitRoot) { $KitRoot = Split-Path $MyInvocation.MyCommand.Path -Parent }
$kitAbs = (Resolve-Path -LiteralPath $KitRoot).Path
$cli = Join-Path $kitAbs "scripts\sdd.py"
if (-not (Test-Path -LiteralPath $cli) -or -not (Test-Path -LiteralPath (Join-Path $kitAbs "VERSION"))) { throw "Kit inválido: VERSION ou scripts\sdd.py ausente." }

$python = Get-Command python.exe -ErrorAction SilentlyContinue
$pythonArgs = @()
if (-not $python) { $python = Get-Command py.exe -ErrorAction SilentlyContinue; if ($python) { $pythonArgs = @("-3") } }
if (-not $python) { throw "Python 3.9+ é obrigatório." }
& $python.Source @pythonArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)"
if ($LASTEXITCODE -ne 0) { throw "Python 3.9+ é obrigatório." }

if (-not $InstallRoot) { $InstallRoot = Join-Path $env:LOCALAPPDATA "SDD-Toolkit" }
$installAbs = [IO.Path]::GetFullPath($InstallRoot)
$binDir = Join-Path $installAbs "bin"

if ($RepositoryUrl) {
  $sourceRoot = Join-Path $installAbs "kit"
  $sourceArgs = @($cli, "source", "install", "--repository-url", $RepositoryUrl, "--source-root", $sourceRoot, "--channel", $Channel, "--json")
  if ($Ref) { $sourceArgs += @("--ref", $Ref) }
  if (-not $DryRun) { $sourceArgs += "--apply" }
  & $python.Source @pythonArgs @sourceArgs
  if ($LASTEXITCODE -ne 0) { throw "A origem Git do toolkit não pode ser instalada." }
  if (-not $DryRun) { $kitAbs = (Resolve-Path -LiteralPath $sourceRoot).Path; $cli = Join-Path $kitAbs "scripts\sdd.py" }
}

$args = @($cli, "install", "--scope", "user", "--runtime", $Runtime, "--kit-root", $kitAbs, "--with-cli", "--install-root", $installAbs, "--bin-dir", $binDir, "--json")
if ($ProfileRoot) { $args += @("--profile-root", $ProfileRoot) }
if ($NoPath) { $args += "--no-path" }
if (-not $DryRun) { $args += "--apply" }
& $python.Source @pythonArgs @args
if ($LASTEXITCODE -ne 0) { throw "A instalação global dos assets falhou." }
if ($DryRun) { Write-Host "Preview concluído; nenhum arquivo foi alterado." }
else { Write-Host "SDD Toolkit instalado. Abra um novo terminal, execute 'sdd --version' e depois 'sdd activate' na raiz do projeto." }
