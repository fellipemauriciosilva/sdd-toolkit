#!/usr/bin/env bash
# SDD Kit Installer — v3.0
# Compila agents/*.md → dist/ e deploya agentes nos runtimes configurados.
#
# Uso:
#   bash install.sh <PROJECT_DIR> [--runtime=copilot|claude|all] [--kit-root=PATH]
#
# Exemplos:
#   bash install.sh ../gcb-hr-api-gestao-meta
#   bash install.sh ../gcb-hr-api-gestao-meta --runtime=copilot
#   bash install.sh ../gcb-hr-api-gestao-meta --runtime=all --kit-root=/abs/path/to/kit

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KIT_ROOT="$SCRIPT_DIR"
RUNTIME="all"
PROJECT_DIR=""

# ── Parse argumentos ─────────────────────────────────────────────────────────
for arg in "$@"; do
  case $arg in
    --runtime=*) RUNTIME="${arg#*=}" ;;
    --kit-root=*) KIT_ROOT="${arg#*=}" ;;
    --help|-h)
      echo "Uso: bash install.sh <PROJECT_DIR> [--runtime=copilot|claude|all]"
      exit 0 ;;
    -*)
      echo "Opção desconhecida: $arg"; exit 1 ;;
    *)
      PROJECT_DIR="$arg" ;;
  esac
done

if [[ -z "$PROJECT_DIR" ]]; then
  echo "Erro: PROJECT_DIR é obrigatório."
  echo "Uso: bash install.sh <PROJECT_DIR> [--runtime=copilot|claude|all]"
  exit 1
fi

PROJECT_ABS="$(cd "$PROJECT_DIR" && pwd)"
PROJECT_NAME="$(basename "$PROJECT_ABS")"

# Calcula o caminho relativo do projeto para o kit
if command -v python3 &>/dev/null; then
  SDD_KIT_RELATIVE="$(python3 -c "import os; print(os.path.relpath('$KIT_ROOT', '$PROJECT_ABS'))")"
elif command -v python &>/dev/null; then
  SDD_KIT_RELATIVE="$(python -c "import os; print(os.path.relpath('$KIT_ROOT', '$PROJECT_ABS'))")"
else
  SDD_KIT_RELATIVE="$(realpath --relative-to="$PROJECT_ABS" "$KIT_ROOT" 2>/dev/null || echo "REPLACE_WITH_RELATIVE_PATH_TO_KIT")"
fi

# ── Header ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "  SDD Kit Installer — v3.0"
echo "╚══════════════════════════════════════════════╝"
echo "  Projeto:  $PROJECT_NAME"
echo "  Diretório: $PROJECT_ABS"
echo "  Kit root:  $KIT_ROOT"
echo "  sdd_kit:   $SDD_KIT_RELATIVE"
echo "  Runtime:   $RUNTIME"
echo ""

# ── Compilador de Agentes ─────────────────────────────────────────────────────
# Lê agents/*.md, filtra seções por runtime, injeta frontmatter, grava em dist/
# Formato das seções: <!-- @all -->, <!-- @claude -->, <!-- @copilot -->, <!-- @end -->
compile_agent() {
  local src_file="$1"   # agents/sdd-bootstrap.md
  local target="$2"     # copilot | claude
  local out_dir="$3"    # dist/copilot | dist/claude

  # Extrair campos do frontmatter fonte
  local name description version
  name=$(awk 'BEGIN{f=0} /^---/{f++; next} f==1 && /^name:/{gsub(/^name:[[:space:]]*/,""); gsub(/"/,""); print; exit}' "$src_file")
  description=$(awk 'BEGIN{f=0} /^---/{f++; next} f==1 && /^description:/{gsub(/^description:[[:space:]]*/,""); gsub(/^"/,""); gsub(/"$/,""); print; exit}' "$src_file")
  version=$(awk 'BEGIN{f=0} /^---/{f++; next} f==1 && /^version:/{gsub(/^version:[[:space:]]*/,""); gsub(/"/,""); print; exit}' "$src_file")

  if [[ -z "$name" ]]; then
    echo "  [WARN] sem campo 'name' em $src_file — ignorado"
    return
  fi

  local out_file
  if [[ "$target" == "copilot" ]]; then
    out_file="$out_dir/${name}.agent.md"
  else
    out_file="$out_dir/${name}.md"
  fi

  # Escrever frontmatter de runtime
  if [[ "$target" == "copilot" ]]; then
    cat > "$out_file" << FRONTMATTER
---
mode: agent
author: "Felipe Mauricio da Silva"
description: "$description"
model: "Claude Sonnet 4.6"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - vscode/askQuestions
version: "$version"
---

FRONTMATTER
  else
    cat > "$out_file" << FRONTMATTER
---
name: "$name"
description: "$description"
---

FRONTMATTER
  fi

  # Processar corpo: filtrar seções por runtime usando awk
  # Regras: @all → sempre imprime | @claude/@copilot → só imprime se for o target
  awk -v target="$target" '
    BEGIN { in_hdr=1; hdr_end=0; printing=0 }
    in_hdr && /^---$/ { hdr_end++; if(hdr_end==2) { in_hdr=0 }; next }
    in_hdr { next }
    /^<!-- @all -->$/     { printing=1; next }
    /^<!-- @claude -->$/  { printing=(target=="claude") ? 1 : -1; next }
    /^<!-- @copilot -->$/ { printing=(target=="copilot") ? 1 : -1; next }
    /^<!-- @end -->$/     { printing=0; next }
    printing==1 { print }
  ' "$src_file" >> "$out_file"

  echo "  [OK] $name → $(basename "$out_file")"
}

compile_all() {
  local target="$1"     # copilot | claude
  local out_dir="$KIT_ROOT/dist/$target"
  local src_dir="$KIT_ROOT/agents"

  if [[ ! -d "$src_dir" ]]; then
    echo "  [SKIP] agents/ não encontrado — usando .github/agents/ (modo legado)"
    return 1
  fi

  mkdir -p "$out_dir"
  echo ""
  echo "[Compiler] Compilando agents/ → dist/$target/ ..."

  local count=0
  for src_file in "$src_dir"/*.md; do
    [[ -f "$src_file" ]] || continue
    compile_agent "$src_file" "$target" "$out_dir"
    ((count++)) || true
  done

  echo "  Total: $count agentes compilados para $target"
  return 0
}

# ── Passo 1: workspace em sdd-history-implementations (raiz do usuário) ──────
HISTORY_DIR="$HOME/sdd-history-implementations"
WORKSPACE_DIR="$HISTORY_DIR/$PROJECT_NAME/specs"
mkdir -p "$WORKSPACE_DIR"
echo "[OK] sdd-history-implementations/$PROJECT_NAME/specs/ criado"

# ── Passo 2: sdd.config.md no projeto ────────────────────────────────────────
mkdir -p "$PROJECT_ABS/.github"
cat > "$PROJECT_ABS/.github/sdd.config.md" << EOF
# SDD Config

project: $PROJECT_NAME
sdd_kit: $SDD_KIT_RELATIVE
sdd_workspace: $HISTORY_DIR
version_required: "2.5.0"
EOF
echo "[OK] .github/sdd.config.md criado no projeto"

# ── Passo 3: estrutura de diretórios no projeto ───────────────────────────────
mkdir -p \
  "$PROJECT_ABS/.github/agents" \
  "$PROJECT_ABS/.github/instructions" \
  "$PROJECT_ABS/.github/docs/project-context" \
  "$PROJECT_ABS/.github/docs/architecture" \
  "$PROJECT_ABS/.github/docs/testing" \
  "$PROJECT_ABS/.github/docs/operations"
echo "[OK] estrutura .github/ criada no projeto"

# ── Passo 4: sdd-gates.config.md (se não existir) ────────────────────────────
if [[ ! -f "$PROJECT_ABS/.github/sdd-gates.config.md" ]]; then
  cp "$KIT_ROOT/templates/sdd-gates.config.md" "$PROJECT_ABS/.github/sdd-gates.config.md"
  echo "[OK] sdd-gates.config.md copiado do kit (defaults)"
else
  echo "[--] sdd-gates.config.md já existe — mantido"
fi

# ── Passo 5: Compilar e deployar agentes ─────────────────────────────────────

# Pipeline agents esperados (para fallback legado)
PIPELINE_AGENTS=(
  "sdd-bootstrap.agent.md"
  "sdd-create-spec.agent.md"
  "sdd-analyze-demand.agent.md"
  "sdd-implement-spec.agent.md"
  "sdd-generate-integration-tests.agent.md"
  "sdd-review-code.agent.md"
  "sdd-update-documentation.agent.md"
)

if [[ "$RUNTIME" == "copilot" || "$RUNTIME" == "all" ]]; then
  echo ""
  if compile_all "copilot"; then
    # Deploya a partir de dist/copilot/
    echo "[Copilot] Deployando para .github/agents/ do projeto..."
    DIST_COPILOT="$KIT_ROOT/dist/copilot"
    copied=0
    for f in "$DIST_COPILOT"/*.agent.md; do
      [[ -f "$f" ]] || continue
      cp "$f" "$PROJECT_ABS/.github/agents/$(basename "$f")"
      echo "  [OK] $(basename "$f")"
      ((copied++)) || true
    done
    echo "  Total: $copied agentes deployados"
  else
    # Fallback: copia direto de .github/agents/
    echo "[Copilot] Copiando agentes de .github/agents/ (fallback legado)..."
    KIT_AGENTS_DIR="$KIT_ROOT/.github/agents"
    for agent in "${PIPELINE_AGENTS[@]}"; do
      if [[ -f "$KIT_AGENTS_DIR/$agent" ]]; then
        cp "$KIT_AGENTS_DIR/$agent" "$PROJECT_ABS/.github/agents/$agent"
        echo "  [OK] $agent"
      else
        echo "  [WARN] não encontrado: $agent"
      fi
    done
  fi
fi

if [[ "$RUNTIME" == "claude" || "$RUNTIME" == "all" ]]; then
  echo ""
  CLAUDE_AGENTS_DIR="$HOME/.claude/agents"
  mkdir -p "$CLAUDE_AGENTS_DIR"

  if compile_all "claude"; then
    DIST_CLAUDE="$KIT_ROOT/dist/claude"

    # Bootstrap global — disponível em qualquer projeto via /sdd-bootstrap
    echo "[Claude Code] Deployando sdd-bootstrap → ~/.claude/agents/..."
    if [[ -f "$DIST_CLAUDE/sdd-bootstrap.md" ]]; then
      cp "$DIST_CLAUDE/sdd-bootstrap.md" "$CLAUDE_AGENTS_DIR/sdd-bootstrap.md"
      echo "  [OK] sdd-bootstrap.md → ~/.claude/agents/"
    else
      echo "  [WARN] dist/claude/sdd-bootstrap.md não encontrado"
    fi

    # Demais agentes → PROJECT/.claude/agents/ (sub-agentes invocados pelo bootstrap)
    PROJ_CLAUDE_DIR="$PROJECT_DIR/.claude/agents"
    mkdir -p "$PROJ_CLAUDE_DIR"
    echo "[Claude Code] Deployando dist/claude/ para .claude/agents/ do projeto..."
    count=0
    for f in "$DIST_CLAUDE"/*.md; do
      [[ -f "$f" ]] || continue
      cp "$f" "$PROJ_CLAUDE_DIR/$(basename "$f")"
      echo "  [OK] $(basename "$f")"
      count=$((count + 1))
    done
    echo "  Total: $count agentes deployados"
  else
    # Fallback: usa o arquivo existente
    if [[ -f "$HOME/.claude/agents/sdd-bootstrap.md" ]]; then
      echo "[Claude Code] ~/.claude/agents/sdd-bootstrap.md já existe — verifique se está atualizado"
    else
      echo "[Claude Code] [WARN] bootstrap não encontrado — copie manualmente para ~/.claude/agents/"
    fi
  fi
fi

# ── Resumo ────────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════╗"
echo "  Instalação concluída"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "  dist/        → agentes compilados por runtime"
echo "  workspace/   → specs e session-states dos projetos"
echo ""
echo "  Próximos passos:"
echo "  1. Execute /sdd-setup-project $PROJECT_NAME para gerar docs de contexto"
echo "  2. Execute /sdd-bootstrap $PROJECT_NAME <TICKET> para iniciar uma demanda"
echo ""
echo "  Para re-compilar e re-deployar (ex: após atualizar agents/):"
echo "  bash install.sh $PROJECT_DIR --runtime=$RUNTIME"
echo ""
