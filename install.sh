#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kit_root="$script_dir"
runtime="detected"
scope="user"
install_root=""
profile_root=""
repository_url=""
channel="main"
ref=""
dry_run=false
no_path=false

usage() {
  echo "Uso: bash install.sh [--dry-run] [--runtime=detected|copilot|claude|codex|cursor|all]"
  echo "Avançado: --repository-url=URL --channel=stable|beta|main --ref=REF --install-root=PATH --profile-root=PATH --no-path"
}

for arg in "$@"; do
  case "$arg" in
    --runtime=*) runtime="${arg#*=}" ;;
    --scope=*) scope="${arg#*=}" ;;
    --kit-root=*) kit_root="${arg#*=}" ;;
    --install-root=*) install_root="${arg#*=}" ;;
    --profile-root=*) profile_root="${arg#*=}" ;;
    --repository-url=*) repository_url="${arg#*=}" ;;
    --channel=*) channel="${arg#*=}" ;;
    --ref=*) ref="${arg#*=}" ;;
    --dry-run) dry_run=true ;;
    --no-path) no_path=true ;;
    --help|-h) usage; exit 0 ;;
    -*) echo "Opção desconhecida: $arg" >&2; exit 2 ;;
    *) echo "Instalação por projeto foi removida. Execute o instalador sem caminho de projeto." >&2; exit 2 ;;
  esac
done

if [[ "$scope" == "organization" ]]; then
  echo "Scope organization requer provider e policy gerenciada; operação bloqueada." >&2
  exit 2
fi
if [[ "$scope" != "user" ]]; then
  echo "Scope inválido: $scope. O único scope local suportado é user." >&2
  exit 2
fi
case "$runtime" in detected|copilot|claude|codex|cursor|all) ;; *) echo "Runtime inválido: $runtime" >&2; exit 2;; esac
case "$channel" in stable|beta|main) ;; *) echo "Channel inválido: $channel" >&2; exit 2;; esac

if command -v python3 >/dev/null 2>&1; then python_cmd="$(command -v python3)";
elif command -v python >/dev/null 2>&1; then python_cmd="$(command -v python)";
else echo "Python 3.9+ é obrigatório." >&2; exit 2; fi
"$python_cmd" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,9) else 1)' || { echo "Python 3.9+ é obrigatório." >&2; exit 2; }

kit_root="$(cd "$kit_root" && pwd)"
cli="$kit_root/scripts/sdd.py"
[[ -f "$cli" && -f "$kit_root/VERSION" ]] || { echo "Kit inválido: VERSION ou scripts/sdd.py ausente." >&2; exit 2; }

if [[ -z "$install_root" ]]; then
  case "$(uname -s)" in Darwin) install_root="$HOME/Library/Application Support/sdd-toolkit";; *) install_root="${XDG_DATA_HOME:-$HOME/.local/share}/sdd-toolkit";; esac
fi
bin_dir="${SDD_TOOLKIT_BIN_DIR:-$HOME/.local/bin}"
[[ -n "${install_root:-}" ]] && bin_dir="$install_root/bin"

if [[ -n "$repository_url" ]]; then
  source_root="$install_root/kit"
  source_args=(source install --repository-url "$repository_url" --source-root "$source_root" --channel "$channel" --json)
  [[ -n "$ref" ]] && source_args+=(--ref "$ref")
  [[ "$dry_run" == false ]] && source_args+=(--apply)
  "$python_cmd" "$cli" "${source_args[@]}"
  if [[ "$dry_run" == false ]]; then kit_root="$source_root"; cli="$kit_root/scripts/sdd.py"; fi
fi

args=(install --scope user --runtime "$runtime" --kit-root "$kit_root" --with-cli --install-root "$install_root" --bin-dir "$bin_dir" --json)
[[ -n "$profile_root" ]] && args+=(--profile-root "$profile_root")
[[ "$no_path" == true ]] && args+=(--no-path)
[[ "$dry_run" == false ]] && args+=(--apply)
"$python_cmd" "$cli" "${args[@]}"

if [[ "$dry_run" == true ]]; then
  echo "Preview concluído; nenhum arquivo foi alterado."
else
  echo "SDD Toolkit instalado. Abra um novo terminal, execute 'sdd --version' e depois 'sdd activate' na raiz do projeto."
fi
