---
name: sdd-install-sdd-kit
description: "Orienta a instalação global user-scoped do SDD Toolkit e valida os runtimes disponíveis. Uso: sdd-install-sdd-kit [runtime opcional]."
---

> **Autor:** Felipe Maurício da Silva · **E-mail:** fellipemauriciosilva@gmail.com · **LinkedIn:** https://www.linkedin.com/in/felipe-mauricio-06685735/

# Instalar o SDD Toolkit

Este agente orienta somente a instalação no perfil do usuário. Nunca copia
agentes, skills, manifestos ou configurações para o projeto consumidor.

## Fluxo

1. Verifique se `sdd doctor --scope user --json` já encontra uma instalação
   saudável. Se encontrar, informe os runtimes disponíveis e siga para ativação.
2. Se o toolkit ainda não estiver instalado, peça somente a localização do
   pacote/release quando ela não estiver disponível no contexto atual.
3. Execute primeiro o preview do wrapper adequado ao sistema operacional:

```powershell
.\install.ps1 -DryRun
```

```bash
bash install.sh --dry-run
```

4. Mostre os destinos, conflitos e runtimes detectados. Só depois da aprovação
   explícita do usuário, execute o mesmo wrapper sem `-DryRun`/`--dry-run`.
5. Valide com `sdd --version`, `sdd doctor --scope user --json` e
   `sdd context resolve --json` quando o projeto atual já estiver ativado.
6. Oriente o usuário a abrir o projeto desejado e executar `sdd activate`.

## Regras

- Runtime é opcional: o instalador detecta os harnesses disponíveis; solicite
  seleção apenas quando o usuário quiser limitar a instalação.
- Use `--profile-root`, `--install-root`, `--no-path`, JSON e source Git somente
  quando o usuário declarar ambiente isolado, gerenciado ou automatizado.
- Não peça `PROJECT_DIR` nem escreva arquivos de configuração no projeto,
  `.claude`, `.codex` ou `.cursor` no projeto.
- Se não houver runtime detectado, explique que o CLI pode ser instalado agora e
  o runtime poderá ser detectado/reinstalado depois.
