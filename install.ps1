# SDD Kit Installer - v3.0
# Compila agents/*.md -> dist/ e deploya agentes nos runtimes configurados.
#
# Uso:
#   powershell install.ps1 <PROJECT_DIR> [-Runtime copilot|claude|all] [-KitRoot PATH]
#
# Exemplos:
#   powershell install.ps1 ..\gcb-hr-api-gestao-meta
#   powershell install.ps1 ..\gcb-hr-api-gestao-meta -Runtime copilot
#   powershell install.ps1 ..\gcb-hr-api-gestao-meta -Runtime all

param(
  [Parameter(Mandatory=$true, Position=0)]
  [string]$ProjectDir,

  [ValidateSet("copilot", "claude", "all")]
  [string]$Runtime = "all",

  [string]$KitRoot = ""
)

$ErrorActionPreference = "Stop"

# -- Resolucao de caminhos ---------------------------------------------------
# Fallback para KitRoot quando PSScriptRoot nao esta disponivel
if (-not $KitRoot) {
  $KitRoot = Split-Path $MyInvocation.MyCommand.Path -Parent
  if (-not $KitRoot) { $KitRoot = (Get-Location).Path }
}

$projectAbs  = (Resolve-Path $ProjectDir).Path
$projectName = Split-Path $projectAbs -Leaf
$kitAbs      = (Resolve-Path $KitRoot).Path

# Compute relative path: Target relativo a Base (PS 5.1 compatible)
function Get-RelPath {
  param([string]$Base, [string]$Target)
  $baseParts   = $Base.TrimEnd('\').Split('\')
  $targetParts = $Target.TrimEnd('\').Split('\')
  $common = 0
  $minLen = [Math]::Min($baseParts.Length, $targetParts.Length)
  while ($common -lt $minLen -and $baseParts[$common] -ieq $targetParts[$common]) { $common++ }
  $parts = @()
  for ($i = $common; $i -lt $baseParts.Length; $i++) { $parts += '..' }
  for ($i = $common; $i -lt $targetParts.Length; $i++) { $parts += $targetParts[$i] }
  if ($parts.Length -eq 0) { return '.' }
  return ($parts -join '/')
}

$sddKitRelative = Get-RelPath -Base $projectAbs -Target $kitAbs

# -- Header ------------------------------------------------------------------
Write-Host ""
Write-Host "+===============================================+"
Write-Host "  SDD Kit Installer - v3.0"
Write-Host "+===============================================+"
Write-Host "  Projeto:   $projectName"
Write-Host "  Diretorio: $projectAbs"
Write-Host "  Kit root:  $kitAbs"
Write-Host "  sdd_kit:   $sddKitRelative"
Write-Host "  Runtime:   $Runtime"
Write-Host ""

# -- Compilador de Agentes ---------------------------------------------------
# Le agents/*.md, filtra secoes por runtime, injeta frontmatter, grava em dist/
# Formato das secoes: <!-- @all -->, <!-- @claude -->, <!-- @copilot -->, <!-- @end -->
function Compile-Agent {
  param(
    [string]$SrcFile,
    [string]$Target,
    [string]$OutDir
  )

  $content = Get-Content $SrcFile -Encoding UTF8

  # Extrair campos do frontmatter (entre os dois ---)
  $inFrontmatter = $false
  $fmEnd = $false
  $fmLines = @()
  foreach ($line in $content) {
    if ($line -eq '---' -and -not $fmEnd) {
      if (-not $inFrontmatter) { $inFrontmatter = $true; continue }
      else { $fmEnd = $true; continue }
    }
    if ($inFrontmatter -and -not $fmEnd) { $fmLines += $line }
  }

  $name        = ($fmLines | Where-Object { $_ -match '^name:\s*' } | Select-Object -First 1) -replace '^name:\s*', '' -replace '"', ''
  $description = ($fmLines | Where-Object { $_ -match '^description:\s*' } | Select-Object -First 1) -replace '^description:\s*', '' -replace '^"', '' -replace '"$', ''
  $version     = ($fmLines | Where-Object { $_ -match '^version:\s*' } | Select-Object -First 1) -replace '^version:\s*', '' -replace '"', ''

  if (-not $name) {
    Write-Host "  [WARN] sem campo name em $SrcFile - ignorado"
    return
  }

  $outFileName = if ($Target -eq "copilot") { "$name.agent.md" } else { "$name.md" }
  $outFile = Join-Path $OutDir $outFileName

  # Gerar frontmatter de runtime usando List<string>
  $lines = [System.Collections.Generic.List[string]]::new()
  if ($Target -eq "copilot") {
    $lines.Add('---')
    $lines.Add('mode: agent')
    $lines.Add('author: "Felipe Mauricio da Silva"')
    $lines.Add('description: "' + $description + '"')
    $lines.Add('model: "Claude Sonnet 4.6"')
    $lines.Add('tools:')
    $lines.Add('  - search/fileSearch')
    $lines.Add('  - search/textSearch')
    $lines.Add('  - edit/editFiles')
    $lines.Add('  - edit/createFile')
    $lines.Add('  - execute/runInTerminal')
    $lines.Add('  - execute/getTerminalOutput')
    $lines.Add('  - vscode/askQuestions')
    $lines.Add('version: "' + $version + '"')
    $lines.Add('---')
    $lines.Add('')
  } else {
    $lines.Add('---')
    $lines.Add('name: "' + $name + '"')
    $lines.Add('description: "' + $description + '"')
    $lines.Add('---')
    $lines.Add('')
  }

  # Processar corpo: filtrar secoes por target
  $inFm = $true
  $fmCount = 0
  $printing = $false

  foreach ($line in $content) {
    if ($inFm) {
      if ($line -eq '---') {
        $fmCount++
        if ($fmCount -eq 2) { $inFm = $false }
      }
      continue
    }

    if ($line -eq '<!-- @all -->') { $printing = $true; continue }
    if ($line -eq '<!-- @end -->') { $printing = $false; continue }
    if ($line -eq '<!-- @claude -->') {
      $printing = ($Target -eq "claude")
      continue
    }
    if ($line -eq '<!-- @copilot -->') {
      $printing = ($Target -eq "copilot")
      continue
    }

    if ($printing) { $lines.Add($line) }
  }

  [System.IO.File]::WriteAllLines($outFile, $lines, [System.Text.Encoding]::UTF8)
  Write-Host "  [OK] $name - $outFileName"
}

function Compile-All {
  param([string]$Target)

  $srcDir = Join-Path $kitAbs "agents"
  $outDir = Join-Path $kitAbs "dist\$Target"

  if (-not (Test-Path $srcDir)) {
    Write-Host "  [SKIP] agents/ nao encontrado - usando .github/agents/ (modo legado)"
    return $false
  }

  New-Item -ItemType Directory -Force $outDir | Out-Null
  Write-Host ""
  Write-Host "[Compiler] Compilando agents/ -> dist/$Target/ ..."

  $count = 0
  Get-ChildItem $srcDir -Filter "*.md" | ForEach-Object {
    Compile-Agent -SrcFile $_.FullName -Target $Target -OutDir $outDir
    $count++
  }

  Write-Host "  Total: $count agentes compilados para $Target"
  return $true
}

# -- Passo 1: workspace em sdd-history-implementations (raiz do usuário) -----
$historyDir = Join-Path $HOME "sdd-history-implementations"
$workspaceDir = Join-Path $historyDir "$projectName\specs"
New-Item -ItemType Directory -Force $workspaceDir | Out-Null
Write-Host "[OK] sdd-history-implementations/$projectName/specs/ criado"

# -- Passo 2: sdd.config.md no projeto ---------------------------------------
$githubDir = Join-Path $projectAbs ".github"
New-Item -ItemType Directory -Force $githubDir | Out-Null

$historyDirFwd = $historyDir -replace '\\', '/'
$sddConfigLines = @(
  '# SDD Config',
  '',
  "project: $projectName",
  "sdd_kit: $sddKitRelative",
  "sdd_workspace: $historyDirFwd",
  'version_required: "2.5.0"'
)
[System.IO.File]::WriteAllLines((Join-Path $githubDir "sdd.config.md"), $sddConfigLines, [System.Text.Encoding]::UTF8)
Write-Host "[OK] .github/sdd.config.md criado no projeto"

# -- Passo 3: estrutura de diretorios no projeto -----------------------------
@(
  ".github\agents",
  ".github\instructions",
  ".github\docs\project-context",
  ".github\docs\architecture",
  ".github\docs\testing",
  ".github\docs\operations"
) | ForEach-Object {
  New-Item -ItemType Directory -Force (Join-Path $projectAbs $_) | Out-Null
}
Write-Host "[OK] estrutura .github/ criada no projeto"

# -- Passo 4: sdd-gates.config.md (se nao existir) ---------------------------
$projectGates = Join-Path $githubDir "sdd-gates.config.md"
$kitGates     = Join-Path $kitAbs "templates\sdd-gates.config.md"
if (-not (Test-Path $projectGates)) {
  Copy-Item $kitGates $projectGates
  Write-Host "[OK] sdd-gates.config.md copiado do kit (defaults)"
} else {
  Write-Host "[--] sdd-gates.config.md ja existe - mantido"
}

# -- Passo 5: Compilar e deployar agentes ------------------------------------
$pipelineAgentsFallback = @(
  "sdd-bootstrap.agent.md",
  "sdd-create-spec.agent.md",
  "sdd-analyze-demand.agent.md",
  "sdd-implement-spec.agent.md",
  "sdd-generate-integration-tests.agent.md",
  "sdd-review-code.agent.md",
  "sdd-update-documentation.agent.md"
)

if ($Runtime -eq "copilot" -or $Runtime -eq "all") {
  $compiled = Compile-All -Target "copilot"

  if ($compiled) {
    Write-Host ""
    Write-Host "[Copilot] Deployando dist/copilot/ para .github/agents/ do projeto..."
    $distCopilot = Join-Path $kitAbs "dist\copilot"
    $projectAgentsDir = Join-Path $githubDir "agents"
    $copied = 0
    Get-ChildItem $distCopilot -Filter "*.agent.md" | ForEach-Object {
      Copy-Item $_.FullName (Join-Path $projectAgentsDir $_.Name) -Force
      Write-Host "  [OK] $($_.Name)"
      $copied++
    }
    Write-Host "  Total: $copied agentes deployados"
  } else {
    Write-Host ""
    Write-Host "[Copilot] Copiando agentes de .github/agents/ (fallback legado)..."
    $kitAgentsDir     = Join-Path $kitAbs ".github\agents"
    $projectAgentsDir = Join-Path $githubDir "agents"
    foreach ($agent in $pipelineAgentsFallback) {
      $src = Join-Path $kitAgentsDir $agent
      $dst = Join-Path $projectAgentsDir $agent
      if (Test-Path $src) {
        Copy-Item $src $dst -Force
        Write-Host "  [OK] $agent"
      } else {
        Write-Host "  [WARN] nao encontrado: $agent"
      }
    }
  }
}

if ($Runtime -eq "claude" -or $Runtime -eq "all") {
  Write-Host ""
  $claudeAgentsDir = Join-Path $env:USERPROFILE ".claude\agents"
  New-Item -ItemType Directory -Force $claudeAgentsDir | Out-Null

  $compiled = Compile-All -Target "claude"

  if ($compiled) {
    $distClaude = Join-Path $kitAbs "dist\claude"

    # Bootstrap global — disponivel em qualquer projeto via /sdd-bootstrap
    Write-Host "[Claude Code] Deployando sdd-bootstrap -> ~/.claude/agents/..."
    $bootstrapSrc = Join-Path $distClaude "sdd-bootstrap.md"
    if (Test-Path $bootstrapSrc) {
      Copy-Item $bootstrapSrc (Join-Path $claudeAgentsDir "sdd-bootstrap.md") -Force
      Write-Host "  [OK] sdd-bootstrap.md -> ~/.claude/agents/"
    } else {
      Write-Host "  [WARN] dist/claude/sdd-bootstrap.md nao encontrado"
    }

    # Demais agentes -> PROJECT/.claude/agents/ (sub-agentes invocados pelo bootstrap)
    $projClaudeDir = Join-Path $projectAbs ".claude\agents"
    New-Item -ItemType Directory -Force $projClaudeDir | Out-Null
    Write-Host "[Claude Code] Deployando dist/claude/ para .claude/agents/ do projeto..."
    $count = 0
    Get-ChildItem $distClaude -Filter "*.md" | ForEach-Object {
      Copy-Item $_.FullName (Join-Path $projClaudeDir $_.Name) -Force
      Write-Host "  [OK] $($_.Name)"
      $count++
    }
    Write-Host "  Total: $count agentes deployados"
  } else {
    $bootstrapDst = Join-Path $claudeAgentsDir "sdd-bootstrap.md"
    if (Test-Path $bootstrapDst) {
      Write-Host "[Claude Code] ~/.claude/agents/sdd-bootstrap.md ja existe - verifique se esta atualizado"
    } else {
      Write-Host "[Claude Code] [WARN] bootstrap nao encontrado - copie manualmente para ~/.claude/agents/"
    }
  }
}

# -- Resumo ------------------------------------------------------------------
Write-Host ""
Write-Host "+===============================================+"
Write-Host "  Instalacao concluida"
Write-Host "+===============================================+"
Write-Host ""
Write-Host "  dist/                       - agentes compilados por runtime"
Write-Host "  ~/sdd-history-implementations/ - specs e session-states dos projetos"
Write-Host ""
Write-Host "  Proximos passos:"
Write-Host "  1. Execute /sdd-setup-project $projectName para gerar docs de contexto"
Write-Host "  2. Execute /sdd-bootstrap $projectName TICKET para iniciar uma demanda"
Write-Host ""
Write-Host "  Para re-compilar e re-deployar (ex: apos atualizar agents/):"
Write-Host "  powershell install.ps1 $ProjectDir -Runtime $Runtime"
Write-Host ""
