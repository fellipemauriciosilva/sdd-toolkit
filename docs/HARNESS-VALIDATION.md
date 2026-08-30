# Validação externa dos harnesses

Esta matriz é executada manualmente porque requer os produtos reais instalados
e, em alguns casos, conta/autorização do usuário.

| Runtime | Evidência mínima | Comando de diagnóstico | Resultado esperado |
|---|---|---|---|
| Claude Code | cliente real instalado e versão capturada | `sdd runtime detect --runtime claude --mode full --redact-paths --json` | CLI, extensão e Desktop não são confundidos |
| GitHub Copilot | cliente/harness real e perfil isolado | `sdd runtime detect --runtime copilot --mode full --redact-paths --json` | CLI e extensões Copilot/Copilot Chat são componentes distintos |
| Codex | cliente real e agentes TOML descobertos | `sdd runtime detect --runtime codex --mode full --redact-paths --json` | extensão, CLI standalone e binário embarcado são diferenciados |
| Cursor | cliente/CLI real e agentes Markdown descobertos | `sdd runtime detect --runtime cursor --mode full --redact-paths --json` | `cursor-agent`, editor e assets são reportados separadamente |

## Níveis de evidência

| Nível | O que comprova | Pode rodar sem conta do runtime |
|---|---|---|
| L0 | inventário passivo: PATH, editor, extensão, package e app | sim |
| L1 | versão/capability por probe local limitado | sim, quando a CLI existir |
| L2 | install, doctor, ownership e uninstall em perfil isolado | sim |
| L3 | o harness descobre e invoca `sdd-orchestrator` em uma demanda inofensiva | não |
| L4 | lifecycle real completo: start, resume, gates e rollback | não |

Registre L0/L1 antes de preparar o perfil isolado e execute L2 para assets do
SDD. L3 e L4 requerem a interface real, autenticação e aprovação do usuário;
não devem ser simulados como sucesso. Quando houver runner privado confiável,
um canary manual poderá ser reintroduzido sem expor perfis reais a PRs.

Para cada runtime, executar em perfil isolado: install preview/apply, doctor,
uma task low/medium/high, update preview/apply, crash-recovery simulado e
uninstall. Anexar JSON redigido e versão do cliente à issue/release. Não
registrar tokens, prompts, specs ou paths pessoais.

Para reproduzir L0 em um profile ou instalação portátil sem iniciar o editor,
use `sdd runtime detect --profile-root <perfil> --extensions-dir <diretório>`
ou `--portable-root <raiz-portable>`. Isso permite exercitar a mesma matriz em
fixtures locais antes de depender de um runner com conta autenticada.
