# SDD Gates — Configuração Padrão do Kit (v2.5)

> Fallback de configuração para o pipeline `sdd-bootstrap --run`.
> Cascata (mais específico vence): flag na invocação > session-state da demanda > `{project}/.github/sdd-gates.config.md` > **este arquivo** > default do bootstrap.

## Profile padrão

```
profile: safe
```

Perfis disponíveis:

| Perfil | G1 | G2 plano | G3 build | G4 tests | G5 review | G6 PR |
|--------|----|----|----|----|----|----|
| `safe` *(default)* | auto | confirm | auto | auto | confirm¹ | confirm |
| `fast`             | auto | auto    | auto | auto | confirm¹ | confirm |
| `paranoid`         | confirm | confirm | confirm | confirm | confirm | confirm |
| `yolo`             | auto | auto    | auto | auto | auto    | auto |

¹ G5 só pausa se houver achado 🔴 Crítico.

## Overrides por gate (opcional)

Sobrescreve o profile para gates específicos. Descomente e ajuste conforme a necessidade do projeto.

```
# G3: confirm    # este projeto sempre inspeciona o build manualmente
# G4: skip       # este projeto não usa testes de integração no pipeline
```

## Etapas habilitadas (opcional)

Define quais etapas toggleable rodam por padrão. Etapas core (`analyze`, `implement`) sempre rodam.

```
tests:  enabled
review: enabled
docs:   enabled
```

## Regras de segurança

- `G2`, `G5` e `G6` só podem ir para `auto`/`skip` com flag nominal explícita na invocação (`--auto=G6`) ou via `--profile=yolo`.
- `skip` em `G6` (abrir PR sem confirmação) exige `--force-skip=G6`.
- `--profile=yolo` exibe aviso e registra no Agent History que rodou sem supervisão.
