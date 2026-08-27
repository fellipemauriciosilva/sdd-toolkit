# Referência curta da CLI

Todos os comandos mutáveis usam preview por padrão; `--apply` confirma a ação.

| Objetivo | Comando |
|---|---|
| Ver versão | `sdd --version` |
| Ativar projeto atual | `sdd activate` |
| Pré-visualizar ativação | `sdd activate --dry-run` |
| Iniciar demanda | `sdd start ABC-123` |
| Retomar demanda | `sdd resume ABC-123` |
| Ver demanda/projeto atual | `sdd status` |
| Listar ativações locais | `sdd activation list` |
| Descobrir runtimes sem executar binários | `sdd runtime detect --mode quick --json` |
| Verificar versões, extensões e packages locais | `sdd runtime detect --mode full --redact-paths --json` |
| Diagnosticar perfil | `sdd doctor --scope user --json` |
| Instalar assets | `sdd install --scope user --runtime all --apply --json` |
| Atualizar assets | `sdd update --scope user --runtime all --apply --json` |
| Remover assets owned | `sdd uninstall --scope user --apply --json` |
| Ver transações | `sdd transaction status --scope user --active-only --json` |
| Recuperar transação | `sdd transaction recover --scope user --apply --json` |
| Resolver contexto | `sdd context resolve --ticket ABC-123 --json` |
| Validar delivery | `sdd delivery validate --task /caminho/task.md --json` |
| Validar arquitetura | `sdd architecture validate --task /caminho/task.md --json` |

Use `sdd <comando> --help` para parâmetros completos. Consulte
[USER-SCOPE.md](USER-SCOPE.md) para ownership, source, cache offline e conflitos.

## Descoberta de runtimes

`quick` é o padrão: somente lê metadados locais, `PATH`, manifests de extensões
e registros públicos do sistema. Não inicia aplicativos, não acessa a rede e não
lê tokens, sessões ou configurações do usuário.

`full` é uma ação explícita: além do scan passivo, executa apenas argumentos
fixos de versão nos candidatos de CLI e comandos de inventário nos editores e
gerenciadores de pacotes disponíveis. Cada resultado informa evidência,
componente, host, versão, conflito e remediação. Use `--redact-paths` ao anexar
um relatório a uma issue.

Para perfis isolados ou editores portáteis, informe o diretório efetivo das
extensões sem alterar a configuração do editor:

```bash
sdd runtime detect --extensions-dir /caminho/extensions --mode quick --json
sdd runtime detect --portable-root /caminho/vscode-portable --mode quick --json
```

`--cache` grava apenas o snapshot do scan `quick` no estado local por até cinco
minutos. O cache é invalidado por mudanças no PATH, no catálogo, nos binários,
nos diretórios de extensões e nos manifests de cada extensão; `full` nunca usa
cache.
