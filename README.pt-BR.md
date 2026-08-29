<div align="center">
    <h1>🧭 SDD Toolkit</h1>
    <h3><em>Transforme um ticket em entrega verificada — dentro do agente de IA que você já usa.</em></h3>
</div>

<p align="center">
    <strong>Toolkit open source de Spec-Driven Development: agentes especializados, templates e skills que conduzem uma demanda da análise à documentação, com evidência explícita e gates humanos em cada etapa.</strong>
</p>

<p align="center">
    <a href="https://github.com/fellipemauriciosilva/sdd-toolkit/actions/workflows/verify.yml"><img src="https://github.com/fellipemauriciosilva/sdd-toolkit/actions/workflows/verify.yml/badge.svg" alt="verify"/></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="Licença MIT"/></a>
</p>

<p align="center">
    <a href="./README.md">English</a> ·
    <strong>Português&nbsp;(BR)</strong>
</p>

> [!NOTE]
> O toolkit orienta o trabalho do agente. Ele não substitui a revisão humana,
> os controles do runtime nem a validação do seu projeto.

---

## Índice

- [💡 O que é o SDD Toolkit?](#-o-que-é-o-sdd-toolkit)
- [⚡ Instalar](#-instalar)
- [🚀 Início rápido: trabalhar um ticket](#-início-rápido-trabalhar-um-ticket)
- [🏗️ Início rápido: criar um projeto do zero](#-início-rápido-criar-um-projeto-do-zero)
- [🐞 Início rápido: investigar um bug](#-início-rápido-investigar-um-bug)
- [🤖 Runtimes suportados](#-runtimes-suportados)
- [📋 Tipos de demanda](#-tipos-de-demanda)
- [🔧 CLI](#-cli)
- [🧭 O que ler depois](#-o-que-ler-depois)
- [📦 O que o pacote contém](#-o-que-o-pacote-contém)
- [🔒 Segurança, contribuição e suporte](#-segurança-contribuição-e-suporte)
- [🛠️ Desenvolvimento](#️-desenvolvimento)

## 💡 O que é o SDD Toolkit?

A maioria das sessões de IA começa num prompt e termina num diff que ninguém
consegue rastrear. O SDD Toolkit coloca um **processo** entre os dois: você
entrega um ticket, e ele conduz análise → arquitetura → entrega → testes →
review → documentação, parando em cada gate para **você** decidir.

Três coisas o diferenciam:

- **Nada é escrito no seu repositório.** Specs, estado e evidências ficam no
  seu perfil de usuário. Seu projeto continua limpo.
- **Evidência, não afirmação.** Teste que não rodou é registrado como
  `not-run`, nunca como sucesso. Falhas preexistentes são separadas do que a
  entrega introduziu.
- **Os mesmos agentes em quatro runtimes.** Instale uma vez e use em Claude
  Code, GitHub Copilot, Cursor ou Codex sem copiar nada por projeto.

## ⚡ Instalar

Requer **Python 3.9+**, **Git** e pelo menos um runtime suportado.

Primeiro veja o que será instalado — isso não escreve nada:

```powershell
.\install.ps1 -DryRun
```

```bash
bash install.sh --dry-run
```

> [!IMPORTANT]
> `-DryRun` / `--dry-run` só mostra o plano. Para instalar de fato o comando
> `sdd` e os agentes, rode o instalador **de novo, sem essa opção**:

```powershell
.\install.ps1 -Runtime all
```

```bash
bash install.sh --runtime=all
```

Abra um novo terminal e valide:

```bash
sdd --version
sdd doctor --scope user --json
```

> [!TIP]
> Para instalar só um runtime, use `-Runtime codex` (Windows) ou
> `--runtime=codex` (Unix). Veja [docs/USER-SCOPE.md](docs/USER-SCOPE.md) para
> instalação offline, raízes customizadas e recuperação.

## 🚀 Início rápido: trabalhar um ticket

Abra seu projeto no agente de IA e escreva, em linguagem natural:

```text
Use sdd-bootstrap para iniciar o ticket PAY-142 neste projeto.
O endpoint de cobrança precisa ser idempotente: uma requisição repetida com
a mesma chave devolve o resultado original em vez de cobrar duas vezes.
```

É toda a configuração. Nenhum comando para decorar, nenhum arquivo para
copiar, nenhuma configuração comitada no seu repositório.

Uma sessão típica:

```text
Você       Use sdd-bootstrap para iniciar o ticket PAY-142 neste projeto.

Bootstrap  Este projeto ainda não está ativo.
             projeto:   /caminho/do-seu-projeto
             workspace: ~/sdd-history-implementations/seu-projeto-a1b2/.../specs
             nada será escrito no repositório
           Posso ativar?

Você       sim

Bootstrap  Ativado. Analisando a demanda...
           G1 (demanda compreendida): passou
           Delivery Strategy: application, verificação [unit]
           Próximo: arquitetura. Confirma a estratégia?
```

O bootstrap conduz o pipeline e **para em cada gate** para sua decisão. Ele
nunca faz commit, push ou publicação por conta própria.

Para retomar uma demanda, troque o verbo:

```text
Use sdd-bootstrap para retomar o ticket PAY-142 neste projeto.
```

## 🏗️ Início rápido: criar um projeto do zero

Um repositório vazio não tem evidência a descobrir, então alguém precisa
*decidir* a stack. Numa demanda `greenfield` essa decisão tem dono e gate:

```text
Use sdd-bootstrap para iniciar o ticket PAY-001, tipo greenfield.
Criar um serviço que recebe pedidos de cobrança e devolve o status de
processamento. Nossa equipe opera Linux com contêineres.
```

O arquiteto preenche a **Foundation Decision** — linguagem, framework, build,
framework de teste, layout e a skill de stack que governará a entrega —
apresentando alternativas reais com o critério que separou a escolhida.

> [!IMPORTANT]
> Uma fundação não é revertida na prática, então `greenfield` é sempre
> classificado como impacto alto: nunca recebe design curto e **sempre** exige
> aprovação humana antes de qualquer código. Se a fundação estiver pendente, o
> implementador bloqueia em vez de escolher a stack sozinho.

## 🐞 Início rápido: investigar um bug

Para diagnosticar antes de mudar qualquer coisa, chame o investigador direto:

```text
Use sdd-investigate-bug para investigar o ticket PAY-207.
O checkout devolve 500 de forma intermitente depois que o provedor de
pagamento estoura o timeout.
```

Ele produz hipóteses, evidências, reprodução e plano mínimo de correção —
**sem tocar em código**. Você decide se vira uma entrega.

Qualquer agente pode ser chamado assim quando você quer uma etapa só, em vez
do pipeline inteiro:

```text
Use sdd-review-code para revisar a entrega do ticket PAY-142.
Use sdd-generate-tests para cobrir a entrega do ticket PAY-142.
```

O catálogo completo está em [docs/AGENTS.md](docs/AGENTS.md).

## 🤖 Runtimes suportados

O prompt é idêntico nos quatro — os agentes ficam no seu perfil de usuário,
não no projeto.

| Runtime | Onde escrever | Assets instalados em |
|---|---|---|
| **Claude Code** | chat do Claude Code, na raiz do projeto | `~/.claude/agents`, `~/.claude/skills` |
| **GitHub Copilot** | chat do Copilot no VS Code | `~/.copilot/agents`, `~/.copilot/skills` |
| **Cursor** | chat do Cursor | `~/.cursor/agents`, `~/.agents/skills` |
| **Codex** | sessão do Codex na raiz do projeto | `~/.codex/agents`, `~/.agents/skills` |

> [!NOTE]
> Alguns runtimes também deixam escolher o agente por menu ou com `@`. A
> sintaxe exata depende da versão do cliente — o pedido em linguagem natural
> acima funciona em todos. Veja
> [docs/QUICKSTART.pt-BR.md](docs/QUICKSTART.pt-BR.md#uso-em-cada-runtime).

Nunca copie agentes para `.github`, `.claude`, `.codex` ou `.cursor` dentro do
seu projeto.

## 📋 Tipos de demanda

Informe o tipo junto com o ticket quando não for uma feature comum:

| Tipo | Quando usar |
|---|---|
| `feature` | comportamento novo num projeto existente |
| `bugfix` | corrigir defeito |
| `greenfield` | **criar um projeto do zero** |
| `refactor` | mudar estrutura preservando comportamento |
| `migration` | migrar plataforma, versão ou tecnologia |
| `test-e2e` | a suíte E2E é a própria entrega |

O tipo decide o contrato de entrega, o agente de entrega e o impacto
arquitetural inicial — veja [docs/PIPELINE.md](docs/PIPELINE.md).

## 🔧 CLI

O caminho por terminal, útil para automação e CI:

```bash
cd /caminho/do-seu-projeto
sdd activate          # uma vez por projeto
sdd start PAY-142     # devolve workspace, spec e handoff
sdd status            # onde a demanda parou
sdd doctor --scope user --json
```

Referência completa em [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md).

## 🧭 O que ler depois

| Quero… | Leia |
|---|---|
| Começar em cinco minutos | [docs/QUICKSTART.pt-BR.md](docs/QUICKSTART.pt-BR.md) |
| Entender a arquitetura | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Entender gates e pipeline | [docs/PIPELINE.md](docs/PIPELINE.md) |
| Escrever ou alterar um agente | [docs/AGENT-CONTRACT.md](docs/AGENT-CONTRACT.md) |
| Ver o catálogo de agentes | [docs/AGENTS.md](docs/AGENTS.md) |
| Ver as skills disponíveis | [docs/SKILLS.md](docs/SKILLS.md) |
| Consultar um comando da CLI | [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md) |
| Instalar, atualizar, recuperar, desinstalar | [docs/USER-SCOPE.md](docs/USER-SCOPE.md) |
| Saber onde cada arquivo vive | [docs/FILES-AND-LIFECYCLE.md](docs/FILES-AND-LIFECYCLE.md) |
| Avaliar o comportamento dos agentes | [docs/EVALUATIONS.md](docs/EVALUATIONS.md) |
| Revisar limites de segurança | [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md) |
| Publicar uma release | [docs/RELEASE.md](docs/RELEASE.md) |

> [!NOTE]
> A documentação de referência em `docs/` está em português, com exceção do
> README em inglês e do Quickstart. Traduções são bem-vindas — veja
> [CONTRIBUTING.md](CONTRIBUTING.md).

## 📦 O que o pacote contém

| Área | Finalidade |
|---|---|
| `agents/` | Fonte dos agentes especializados. |
| `templates/` | Templates de spec, sessão, verificadores e skills. |
| `dist/` | Artefatos compilados para cada runtime. |
| `scripts/` | CLI, compilador, lifecycle, validação e release. |
| `schemas/` | Contratos versionados para estado, instalação e entrega. |
| `evals/` | Casos e rubricas para avaliar o comportamento dos agentes. |

## 🔒 Segurança, contribuição e suporte

- Vulnerabilidades: [SECURITY.md](SECURITY.md). Nunca publique secrets, dados
  de clientes ou detalhes exploráveis numa issue.
- Contribuições: [CONTRIBUTING.md](CONTRIBUTING.md), incluindo DCO.
- Conduta: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Suporte: [SUPPORT.md](SUPPORT.md).
- Governança: [docs/GOVERNANCE.md](docs/GOVERNANCE.md) e
  [docs/MAINTAINERS.md](docs/MAINTAINERS.md).
- Proveniência e terceiros: [docs/PROVENANCE.md](docs/PROVENANCE.md) e
  [docs/THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).

## 🛠️ Desenvolvimento

```bash
python scripts/sdd_compile.py --runtime all
python scripts/build_inventory.py --write dist/build-manifest.json
python scripts/sdd_lint.py --json
python scripts/public_content_check.py
python -m unittest discover -s tests
```

O compilador não regenera o `dist/build-manifest.json` — é passo separado, e o
`tests/test_dist_sync.py` falha quando os dois divergem.

Antes de uma release, siga [docs/RELEASE.md](docs/RELEASE.md). A publicação só
deve ocorrer após revisão de segurança, proveniência e evidências externas dos
runtimes suportados.

A licença é [MIT](LICENSE). O mantenedor inicial é
[Felipe Maurício da Silva](docs/MAINTAINERS.md).
