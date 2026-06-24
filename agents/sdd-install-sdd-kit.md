---
name: sdd-install-sdd-kit
description: "Instala o SDD Kit em um projeto. Wrapper do script install.sh/install.ps1 — detecta o OS e executa o instalador CLI. Uso: /sdd-install-sdd-kit [PROJECT_DIR] [--runtime=copilot|claude|all]"
version: "3.1.0"
---

<!-- @all -->
# sdd-install-sdd-kit — Instalador do SDD Kit (v2.5)

Este agente é um **thin wrapper** em torno dos scripts CLI `install.sh` (Linux/Mac/Git Bash) e `install.ps1` (Windows/PowerShell). Toda a lógica de instalação vive nos scripts — o agente apenas detecta o ambiente e os executa.

---

## Passo 1 — Coletar argumentos

Se o usuário não forneceu o projeto e o runtime, pergunte:

> **Qual projeto você quer instalar o SDD Kit?**
> Informe o caminho relativo ou absoluto para o diretório do projeto.
> (ex: `../gcb-hr-api-gestao-meta` ou `C:\Users\...\workspace-gcb\gcb-hr-api-gestao-meta`)

> **Para qual runtime?** `[copilot / claude / all]`
> - `copilot` — copia agentes para `.github/agents/` do projeto
> - `claude` — instala bootstrap em `~/.claude/agents/`
> - `all` — ambos (recomendado)

---

## Passo 2 — Identificar o diretório do kit

Se `{PROJECT_DIR}/.github/sdd.config.md` existir, leia o campo `sdd_kit:` e resolva como caminho relativo à raiz do projeto para obter `KIT_ROOT` absoluto.

Se não existir (primeira instalação), o usuário deve informar o caminho do kit, ou infira como o diretório-pai que contém `install.ps1` / `install.sh`.

Identifique `KIT_ROOT` de forma absoluta antes de executar o script.

---

## Passo 3 — Executar o instalador CLI

<!-- @end -->
<!-- @claude -->
Detecte o OS (verifique se `WINDIR` ou `C:\` existe, ou use `uname`). Execute via bash:

**Linux / Mac:**
```bash
bash "{KIT_ROOT}/install.sh" "{PROJECT_DIR}" --runtime={runtime}
```

**Windows (Git Bash / WSL):**
```bash
powershell -File "{KIT_ROOT}/install.ps1" "{PROJECT_DIR}" -Runtime {runtime}
```

Use a ferramenta bash para executar. Leia a saída completa — o script reporta cada passo com `[OK]`, `[--]` ou `[WARN]`.
<!-- @end -->
<!-- @copilot -->
Use `execute/runInTerminal` para executar e `execute/getTerminalOutput` para ler a saída.

**Windows (padrão Copilot):**
```powershell
powershell -File "{KIT_ROOT}/install.ps1" "{PROJECT_DIR}" -Runtime {runtime}
```

**Linux / Mac:**
```bash
bash "{KIT_ROOT}/install.sh" "{PROJECT_DIR}" --runtime={runtime}
```

Aguarde a conclusão do terminal antes de ler a saída. O script reporta cada passo com `[OK]`, `[--]` ou `[WARN]`.
<!-- @end -->
<!-- @all -->

---

## Passo 4 — Pós-instalação

Após o script concluir com sucesso:

1. Verifique se `.github/copilot-instructions.md` já existe no projeto.
   - Se não existir, oriente: "Execute `/sdd-setup-project {PROJECT}` para gerar o contexto do projeto (copilot-instructions, AGENTS.md, project-context/)."

2. Atualize `.github/sdd-kit-status.md` no kit:

```markdown
# SDD Kit Status

| Project | Status | Installed at | Runtime | Version |
|---------|--------|--------------|---------|---------|
| {project} | ✅ installed | {today} | {runtime} | v3.1 |
```

3. Exiba um resumo:
```
╔══════════════════════════════════════════════╗
  SDD Kit instalado em {project}
╚══════════════════════════════════════════════╝
  Kit:      {KIT_ROOT}
  sdd_kit:  {relative path calculado pelo script}
  Runtime:  {runtime}
  Workspace: {sdd_workspace}/{project}/specs/

  Próximos passos:
  ▸ /sdd-setup-project {project}   — gera contexto do projeto
  ▸ /sdd-bootstrap {project} <TICKET> --run   — inicia primeira demanda
```

---

## Regras

- Nunca edite código de produção ou testes.
- Se o script falhar (exit != 0), exiba a saída do erro e oriente o usuário a corrigir antes de continuar.
- Se `install.sh`/`install.ps1` não existir, oriente o usuário a atualizar o kit: o script está em `{KIT_ROOT}/install.sh`.
- Não recriar arquivos que o script já criou — verifique o output antes de qualquer ação manual.
<!-- @end -->
