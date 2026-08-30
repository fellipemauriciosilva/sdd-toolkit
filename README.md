<div align="center">
    <h1>🧭 SDD Toolkit</h1>
    <h3><em>Turn a ticket into a verified delivery — in the AI agent you already use.</em></h3>
</div>

<p align="center">
    <strong>An open-source Spec-Driven Development toolkit: specialized agents, templates and skills that carry a demand from analysis to documentation, with explicit evidence and human gates at every step.</strong>
</p>

<p align="center">
    <a href="https://github.com/fellipemauriciosilva/sdd-toolkit/actions/workflows/verify.yml"><img src="https://github.com/fellipemauriciosilva/sdd-toolkit/actions/workflows/verify.yml/badge.svg" alt="verify"/></a>
    <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License"/></a>
</p>

<p align="center">
    <strong>English</strong> ·
    <a href="./README.pt-BR.md">Português&nbsp;(BR)</a>
</p>

> [!NOTE]
> The toolkit guides the agent's work. It does not replace human review, the
> runtime's own controls, or your project's validation.

---

## Table of Contents

- [💡 What is the SDD Toolkit?](#-what-is-the-sdd-toolkit)
- [⚡ Install](#-install)
- [🚀 Quickstart: work a ticket](#-quickstart-work-a-ticket)
- [🏗️ Quickstart: start a project from scratch](#-quickstart-start-a-project-from-scratch)
- [🐞 Quickstart: investigate a bug](#-quickstart-investigate-a-bug)
- [🤖 Supported runtimes](#-supported-runtimes)
- [📋 Demand types](#-demand-types)
- [🔧 CLI](#-cli)
- [🧭 What to read next](#-what-to-read-next)
- [📦 What the package contains](#-what-the-package-contains)
- [🔒 Security, contributing and support](#-security-contributing-and-support)
- [🛠️ Development](#️-development)

## 💡 What is the SDD Toolkit?

Most AI coding sessions start from a prompt and end with a diff nobody can
trace. The SDD Toolkit puts a **process** between the two: you give it a
ticket, and it runs analysis → architecture → delivery → tests → review →
documentation, stopping at each gate so **you** decide.

Three things make it different:

- **Nothing is written to your repository.** Specs, state and evidence live in
  your user profile. Your project stays clean.
- **Evidence, not claims.** A test that did not run is recorded as `not-run`,
  never as success. Pre-existing failures are separated from what the delivery
  introduced.
- **The same agents in four runtimes.** Install once; use it in Claude Code,
  GitHub Copilot, Cursor or Codex without copying anything per project.

## ⚡ Install

Requires **Python 3.9+**, **Git**, and at least one supported runtime.

First preview what will be installed — this writes nothing:

```powershell
.\install.ps1 -DryRun
```

```bash
bash install.sh --dry-run
```

> [!IMPORTANT]
> `-DryRun` / `--dry-run` only prints the plan. To actually install the `sdd`
> command and the agents, run the installer **again without that flag**:

```powershell
.\install.ps1 -Runtime all
```

```bash
bash install.sh --runtime=all
```

Open a new terminal and check:

```bash
sdd --version
sdd doctor --scope user --json
```

> [!TIP]
> To install for a single runtime, use `-Runtime codex` (Windows) or
> `--runtime=codex` (Unix). See [docs/USER-SCOPE.md](docs/USER-SCOPE.md) for
> offline installs, custom roots and recovery.

## 🚀 Quickstart: work a ticket

Open your project in your AI agent and type, in plain language:

```text
Use sdd-orchestrator to start ticket PAY-142 in this project.
The charge endpoint must be idempotent: a repeated request with the same
key returns the original result instead of charging twice.
```

That is the whole setup. No command to memorize, no file to copy, no
configuration committed to your repository.

A typical session:

```text
You          Use sdd-orchestrator to start ticket PAY-142 in this project.

Orchestrator This project is not active yet.
               project:   /path/to/your-project
               workspace: ~/sdd-history-implementations/your-project-a1b2/.../specs
               nothing will be written to the repository
             May I activate it?

You          yes

Orchestrator Activated. Analyzing the demand...
             G1 (demand understood): passed
             Delivery Strategy: application, verification [unit]
             Next: architecture. Confirm the strategy?
```

The orchestrator runs the pipeline and **stops at every gate** for your decision.
It never commits, pushes or publishes on its own.

To pick a demand back up, swap the verb:

```text
Use sdd-orchestrator to resume ticket PAY-142 in this project.
```

## 🏗️ Quickstart: start a project from scratch

An empty repository has no evidence to discover, so somebody has to *decide*
the stack. In a `greenfield` demand that decision has an owner and a gate:

```text
Use sdd-orchestrator to start ticket PAY-001, type greenfield.
Create a service that receives billing requests and returns processing status.
Our team runs Linux with containers.
```

The architect fills in the **Foundation Decision** — language, framework, build
tool, test framework, layout, and the stack skill that will govern the
delivery — presenting real alternatives with the criterion that separated the
chosen one.

> [!IMPORTANT]
> A foundation is not reverted in practice, so `greenfield` is always classified
> as high impact: it never gets a short design and **always** requires human
> approval before any code. If the foundation is still pending, the
> implementer blocks instead of picking a stack on its own.

## 🐞 Quickstart: investigate a bug

To diagnose before changing anything, call the investigator directly:

```text
Use sdd-investigate-bug to investigate ticket PAY-207.
Checkout intermittently returns 500 after the payment provider times out.
```

It produces hypotheses, evidence, a reproduction and a minimal fix plan —
**without touching code**. You decide whether to turn it into a delivery.

Every agent can be called this way when you want a single step instead of the
whole pipeline:

```text
Use sdd-review-code to review the delivery for ticket PAY-142.
Use sdd-generate-tests to cover the delivery for ticket PAY-142.
```

The full catalog is in [docs/AGENTS.md](docs/AGENTS.md).

## 🤖 Supported runtimes

The prompt is identical in all four — the agents live in your user profile, not
in the project.

| Runtime | Where to type | Assets installed in |
|---|---|---|
| **Claude Code** | Claude Code chat, at the project root | `~/.claude/agents`, `~/.claude/skills` |
| **GitHub Copilot** | Copilot chat in VS Code | `~/.copilot/agents`, `~/.copilot/skills` |
| **Cursor** | Cursor chat | `~/.cursor/agents`, `~/.agents/skills` |
| **Codex** | Codex session at the project root | `~/.codex/agents`, `~/.agents/skills` |

> [!NOTE]
> Some runtimes also let you pick the agent from a menu or with `@`. The exact
> selection syntax depends on the client version — the plain-language request
> above works everywhere. See
> [docs/QUICKSTART.md](docs/QUICKSTART.md#usage-in-each-runtime).

Never copy agents into `.github`, `.claude`, `.codex` or `.cursor` inside your
project.

## 📋 Demand types

State the type together with the ticket when it is not an ordinary feature:

| Type | When to use it |
|---|---|
| `feature` | new behavior in an existing project |
| `bugfix` | fix a defect |
| `greenfield` | **create a project from scratch** |
| `refactor` | change structure, preserve behavior |
| `migration` | migrate platform, version or technology |
| `test-e2e` | the E2E suite is the deliverable itself |

The type decides the delivery contract, the delivery agent and the initial
architectural impact — see [docs/PIPELINE.md](docs/PIPELINE.md).

## 🔧 CLI

The terminal path, useful for automation and CI:

```bash
cd /path/to/your-project
sdd activate          # once per project
sdd start PAY-142     # returns workspace, spec path and handoff
sdd status            # where the demand stopped
sdd doctor --scope user --json
```

Full reference in [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md).

## 🧭 What to read next

| I want to… | Read |
|---|---|
| Get started in five minutes | [docs/QUICKSTART.md](docs/QUICKSTART.md) |
| Understand the architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Understand gates and the pipeline | [docs/PIPELINE.md](docs/PIPELINE.md) |
| Write or change an agent | [docs/AGENT-CONTRACT.md](docs/AGENT-CONTRACT.md) |
| Browse the agent catalog | [docs/AGENTS.md](docs/AGENTS.md) |
| Browse the available skills | [docs/SKILLS.md](docs/SKILLS.md) |
| Look up a CLI command | [docs/CLI-REFERENCE.md](docs/CLI-REFERENCE.md) |
| Install, update, recover, uninstall | [docs/USER-SCOPE.md](docs/USER-SCOPE.md) |
| Find where each file lives | [docs/FILES-AND-LIFECYCLE.md](docs/FILES-AND-LIFECYCLE.md) |
| Evaluate agent behavior | [docs/EVALUATIONS.md](docs/EVALUATIONS.md) |
| Review security limits | [docs/THREAT-MODEL.md](docs/THREAT-MODEL.md) |
| Publish a release | [docs/RELEASE.md](docs/RELEASE.md) |

> [!NOTE]
> The reference documentation under `docs/` is currently written in Portuguese,
> except for this README and the Quickstart. Translations are welcome — see
> [CONTRIBUTING.md](CONTRIBUTING.md).

## 📦 What the package contains

| Area | Purpose |
|---|---|
| `agents/` | Source of the specialized agents. |
| `templates/` | Spec, session, verifier and skill templates. |
| `dist/` | Compiled artifacts for each runtime. |
| `scripts/` | CLI, compiler, lifecycle, validation and release. |
| `schemas/` | Versioned contracts for state, installation and delivery. |
| `evals/` | Cases and rubrics for evaluating agent behavior. |

## 🔒 Security, contributing and support

- Vulnerabilities: [SECURITY.md](SECURITY.md). Never post secrets, customer
  data or exploitable detail in an issue.
- Contributions: [CONTRIBUTING.md](CONTRIBUTING.md), including DCO sign-off.
- Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
- Support: [SUPPORT.md](SUPPORT.md).
- Governance: [docs/GOVERNANCE.md](docs/GOVERNANCE.md) and
  [docs/MAINTAINERS.md](docs/MAINTAINERS.md).
- Provenance and third parties: [docs/PROVENANCE.md](docs/PROVENANCE.md) and
  [docs/THIRD_PARTY_NOTICES.md](docs/THIRD_PARTY_NOTICES.md).

## 🛠️ Development

```bash
python scripts/sdd_compile.py --runtime all
python scripts/build_inventory.py --write dist/build-manifest.json
python scripts/sdd_lint.py --json
python scripts/public_content_check.py
python -m unittest discover -s tests
```

The compiler does not regenerate `dist/build-manifest.json` — that is a
separate step, and `tests/test_dist_sync.py` fails when the two drift apart.

Before a release, follow [docs/RELEASE.md](docs/RELEASE.md). Publishing should
only happen after security review, provenance and external evidence from the
supported runtimes.

The license is [MIT](LICENSE). The initial maintainer is
[Felipe Maurício da Silva](docs/MAINTAINERS.md).
