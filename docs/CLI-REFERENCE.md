# Referência curta da CLI

## Contexto incremental de agentes

No uso diário, `sdd-bootstrap` executa estes comandos automaticamente. Eles
existem também para diagnóstico e para `sdd run` avulso:

```bash
sdd context pack --ticket ABC-123 --agent sdd-implement-spec --apply --json
sdd context validate --file <pack.json> --json
sdd context explain --file <pack.json> --json
sdd context expand --ticket ABC-123 --parent-file <pack.json> --request-file <result.json> --apply --json
sdd result record --ticket ABC-123 --file <result.json> --context-file <pack.json> --apply --json
sdd context state --ticket ABC-123 --json
sdd run sdd-review-code --ticket ABC-123 --apply --json
```

`context pack` e `run` usam preview por padrão. `--apply` persiste apenas dados
no workspace pessoal da demanda, nunca no projeto consumidor. `result record`
rejeita resultado, ticket, agente, hash ou pack incompatíveis.

Todos os comandos mutáveis usam preview por padrão; `--apply` confirma a ação.

| Objetivo | Comando |
|---|---|
| Ver versão | `sdd --version` |
| Ver identidade e contato público | `sdd about --json` |
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
| Propor delivery por tipo | `sdd delivery propose --type greenfield --json` |
| Validar delivery | `sdd delivery validate --task /caminho/task.md --json` |
| Validar arquitetura | `sdd architecture validate --task /caminho/task.md --json` |
| Validar resultado de agente | `sdd result validate --file /caminho/result.json --json` |
| Lint dos contratos de agente | `sdd lint --json` |

Use `sdd <comando> --help` para parâmetros completos. Consulte
[USER-SCOPE.md](USER-SCOPE.md) para ownership, source, cache offline e conflitos
e [AGENT-CONTRACT.md](AGENT-CONTRACT.md) para o envelope `AGENT_RESULT` validado
por `sdd result validate`.

`--type` aceita `feature`, `bugfix`, `greenfield`, `refactor`, `migration` e
`test-e2e`. `e2e` e `playwright` normalizam para `test-e2e`; `new-project` e
`novo-projeto` normalizam para `greenfield`. O tipo define o `delivery_kind`, o
agente de entrega e o impacto arquitetural inicial — veja
[PIPELINE.md](PIPELINE.md).

`sdd lint` roda sobre uma árvore-fonte do toolkit e verifica contexto canônico,
capabilities versus efeitos, política comum injetada, equivalência entre os
quatro runtimes, ausência de artefatos legados, cobertura de evals e o conteúdo
que os evals exigem: posse do estado, posse dos gates e neutralidade de stack.
Sai com código 1 quando encontra qualquer finding.

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
