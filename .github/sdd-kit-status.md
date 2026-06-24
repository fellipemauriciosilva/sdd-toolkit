# SDD Kit — Status de Projetos Instalados

> Atualizado em: 2026-06-23 — Kit v3.1

---

## Projetos com Kit Instalado

| Projeto | Caminho | Runtime | Versão do Kit | Agentes | Última Instalação |
|---------|---------|---------|:---:|:---:|:-----------------:|
| `gcb-hr-api-gestao-meta` | `C:\Users\felipe.silva\workspace-gcb\gcb-hr-api-gestao-meta` | all (copilot + claude) | v3.1 | 18 | 2026-06-22 |
| `sharepoint-legacy` | `C:\Users\felipe.silva\workspace-gcb\sharepoint-legacy` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |
| `procop-app` | `...sharepoint-legacy\projects\procop-app` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |
| `horas-app` | `...sharepoint-legacy\projects\horas-app` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |
| `credito-app` | `...sharepoint-legacy\projects\credito-app` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |
| `gt-app` | `...sharepoint-legacy\projects\gt-app` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |
| `compras-contratos-svc` | `...sharepoint-legacy\projects\compras-contratos-svc` | all (copilot + claude) | v3.1 | 18 | 2026-06-23 |

---

## Como Atualizar um Projeto

Quando o kit recebe novas versões de agentes ou templates, re-execute o install para recompilar e deployar:

```powershell
# Windows — re-compila e re-deploya todos os agentes
powershell install.ps1 <CAMINHO_DO_PROJETO> -Runtime all
```

```bash
# Linux/Mac
bash install.sh <CAMINHO_DO_PROJETO> --runtime all
```

---

## Estrutura Instalada por Projeto

Após o install, o projeto recebe:

```
<projeto>/
├── sdd-verify.sh / sdd-verify.ps1          # Script padronizado de build (G3)
├── .github/
│   ├── sdd.config.md                       # Referência ao kit (sdd_kit: + project:)
│   ├── sdd-gates.config.md                 # Políticas de gate (copiado de templates/)
│   ├── agents/                             # 18 agentes compilados para Copilot
│   └── docs/project-context/
│       └── decisions-log.md                # Log de decisões (copiado de templates/)
└── .claude/
    └── agents/                             # 18 agentes compilados para Claude Code

~/.claude/agents/
└── sdd-bootstrap.md                        # Bootstrap global (Claude Code)
```

---

## sdd.config.md — Resolução de Caminhos (v2.5+)

Todos os projetos instalados com v3.1 têm um `sdd.config.md` em `.github/`:

```markdown
sdd_kit: ../../workspace/SDD Toolkit/sdd-toolkit
project: gcb-hr-api-gestao-meta
```

O `sdd-bootstrap` usa este arquivo para resolver:
- `SPEC_PATH = {sdd_kit}/workspace/{project}/specs/<TICKET>/`
- `gates config = {sdd_kit}/templates/sdd-gates.config.md` (fallback)
