---
name: "sdd-inspect-infra"
description: "Inspeção de infraestrutura com três modos: (1) mapeamento de credenciais em Helm/Kustomize/application.yaml, (2) extração de ConfigMaps e Secrets via kubectl, (3) criação de ambiente GDA sandbox para Casas Bahia. Selecione o modo ao invocar."
version: "2.3.0"
---

<!-- @all -->

# sdd-inspect-infra — Inspeção de Infraestrutura

Agente unificado de inspeção de infraestrutura com três modos de operação.

O usuário invoca este agente com um dos modos:

```
/sdd-inspect-infra --credentials PROJECT    → Mapear credenciais (Helm, Kustomize, application.yaml)
/sdd-inspect-infra --kubectl NAMESPACE      → Extrair ConfigMaps e Secrets do cluster via kubectl
/sdd-inspect-infra --sandbox PROJECT        → Criar ambiente GDA sandbox (Casas Bahia apenas)
```

Se o modo não for informado, apresente o menu:

> **sdd-inspect-infra — Selecione o modo:**
>
> **1. `--credentials`** — Mapear credenciais e referências de configuração em arquivos Helm/Kustomize/application.yaml de um projeto. Gera relatório em `maped-infra/docs/`.
>
> **2. `--kubectl`** — Extrair ConfigMaps e Secrets de um namespace Kubernetes via kubectl. Gera relatório em `maped-infra/kubectl-inspector/<namespace>/`.
>
> **3. `--sandbox`** — Criar ambiente GDA (sandbox/pre-prod) para projetos Casas Bahia. Gera arquivos Helm/Kustomize para o ambiente GDA e abre PR na esteira.
>
> Qual modo deseja usar? (1/2/3 ou --credentials/--kubectl/--sandbox)

---

## MODO 1 — `--credentials` — Mapeamento de Credenciais

### Etapa 0 — Coletar projetos

Pergunte ao usuário:

> Informe os projetos a mapear (um por linha ou separados por vírgula).
> Deixe em branco para mapear todos os projetos com SDD Kit instalado no workspace.

Salve a lista como `PROJECTS`. Se vazia, escaneie todos os diretórios do workspace com `.github/copilot-instructions.md`.

### Etapa 1 — Discovery de padrões de infra

Para cada projeto em `PROJECTS`, leia **em paralelo**:

- `PROJECT/pom.xml` → dependências de infra (vault, keyvault, AWS Secrets Manager)
- `PROJECT/helm-values/*.yaml` → ConfigMaps, Secrets, referências de vault
- `PROJECT/kustomize/` ou `PROJECT/overlays/` → patches de configuração
- `PROJECT/src/main/resources/application.yml` e `application-*.yml` → propriedades com placeholders
- `PROJECT/src/main/resources/bootstrap.yml` (se existir) → configuração de Vault/Config Server

### Etapa 2 — Leitura de arquivos de configuração

Para cada arquivo identificado na Etapa 1, extraia:

1. **Referências a segredos externos:**
   - `${vault:secret/...}` → HashiCorp Vault
   - `${azure-keyvault:...}` → Azure Key Vault
   - `secretKeyRef:` em YAML Kubernetes → Kubernetes Secret
   - `configMapKeyRef:` → Kubernetes ConfigMap

2. **Credenciais hardcoded** (verificar com regex — são achados 🔴 Crítico):
   - `password: [^${]` → valor não é referência
   - `secret: [^${]` → valor direto
   - `api-key: [^${]` → API key em texto plano

3. **Variáveis de ambiente esperadas** (`${ENV_VAR:default}`)

4. **URLs e endpoints de infra:**
   - Bancos de dados (`jdbc:`, `spring.datasource.url`)
   - Brokers Kafka (`spring.kafka.bootstrap-servers`)
   - Serviços externos (Feign clients, `feign.client.config`)

### Etapa 3 — Inferir propósito de cada credencial

Para cada credencial/configuração identificada, classifique:

| Tipo | Exemplos | Classificação |
|------|---------|---------------|
| Banco de dados | `DB_PASSWORD`, `datasource.password` | Crítico — nunca hardcoded |
| API externa | `EXTERNAL_API_KEY`, `feign.client.*.key` | Alto — via Vault/KeyVault |
| Kafka | `KAFKA_SASL_PASSWORD` | Alto — via Secret |
| Configuração não sensível | `SERVER_PORT`, `LOG_LEVEL` | Baixo — pode ser ConfigMap |
| Segredo genérico | qualquer `*_SECRET`, `*_TOKEN` | Crítico — via Vault/KeyVault |

### Etapa 4 — Gerar relatório por projeto

Para cada projeto, gere `maped-infra/docs/credenciais-{PROJECT}.md`:

```markdown
# Mapeamento de Credenciais — {PROJECT}

> Gerado em: {data}

## Sumário

| Classificação | Quantidade |
|---------------|-----------|
| 🔴 Hardcoded (CRÍTICO) | N |
| 🔑 Vault / KeyVault | N |
| 📦 Kubernetes Secret | N |
| ⚙️ ConfigMap / Env Var | N |

## Detalhamento

| Credencial/Config | Arquivo | Linha | Tipo | Classificação | Recomendação |
|------------------|---------|-------|------|---------------|-------------|
| DB_PASSWORD | application-hlg.yml | 12 | hardcoded | 🔴 Crítico | Migrar para Kubernetes Secret ou Azure KeyVault |
| API_KEY | helm-values/hlg.yaml | 34 | secretKeyRef | 📦 Kubernetes Secret | OK |

## Itens Críticos (ação imediata)

{listar apenas os itens 🔴 Hardcoded com arquivo e linha exata}

## Recomendações

{recomendações por projeto para migrar credenciais para Vault/KeyVault}
```

### Etapa 5 — Apresentar resumo consolidado

Exiba um resumo consolidado de todos os projetos mapeados e informe o caminho dos relatórios gerados.

---

## MODO 2 — `--kubectl` — Extração via kubectl

### Etapa 0 — Coletar parâmetros

Pergunte ao usuário (se não fornecidos na invocação):

> Informe:
> - **Namespace** do Kubernetes a inspecionar (ex: `gcb-hr-work-journey-hlg`)
> - **Kubeconfig** a usar (deixe em branco para usar o context atual)

Salve como `NAMESPACE` e `KUBECONFIG` (opcional).

### Etapa 1 — Verificar kubectl

```bash
kubectl version --client
kubectl config current-context
```

Se `kubectl` não estiver disponível, informe e encerre.

### Etapa 2 — Extrair ConfigMaps

```bash
kubectl get configmaps -n NAMESPACE -o json
```

Para cada ConfigMap retornado, extraia:
- Nome
- Chaves presentes em `data`
- Valores (omitir se o tamanho for > 1KB — registrar como `[truncado]`)

Salve em `maped-infra/kubectl-inspector/NAMESPACE/configmaps.md`.

### Etapa 3 — Extrair e decodificar Secrets

```bash
kubectl get secrets -n NAMESPACE -o json
```

Para cada Secret do tipo `Opaque` ou `kubernetes.io/tls`:
- Extraia o nome e as chaves presentes em `data`
- Decodifique os valores com base64:

**PowerShell:**
```powershell
[System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{valor-base64}"))
```

**Bash:**
```bash
echo "{valor-base64}" | base64 --decode
```

> ⚠️ **SEGURANÇA:** Os valores decodificados dos Secrets **NUNCA devem ser commitados** no repositório.

Salve em `maped-infra/kubectl-inspector/NAMESPACE/secrets.md` com os valores **mascarados**:
- Mostrar apenas os primeiros 4 caracteres seguidos de `****`
- Exemplo: `ghp_****` para tokens, `admin****` para senhas

### Etapa 4 — Atualizar .gitignore

Verifique se `.gitignore` na raiz do workspace contém:

```
maped-infra/kubectl-inspector/
```

Se não contiver, adicione automaticamente. Esta é uma **regra de segurança obrigatória**.

### Etapa 5 — Gerar sumário

Salve em `maped-infra/kubectl-inspector/NAMESPACE/summary.md`:

```markdown
# kubectl Inspector — {NAMESPACE}

> Extraído em: {data} | Context: {kubectl-context}

## ConfigMaps

| Nome | Chaves |
|------|--------|
| {nome} | {chave1}, {chave2} |

## Secrets

| Nome | Tipo | Chaves | Valores (mascarados) |
|------|------|--------|---------------------|
| {nome} | Opaque | {chave} | {primeiros-4}**** |

## Avisos de Segurança

- ⚠️ Este diretório está no `.gitignore` — nunca commitar
- ⚠️ Os valores de Secrets são mascarados neste arquivo
- ⚠️ Para valores completos, acesse diretamente via `kubectl get secret {nome} -n {namespace} -o jsonpath='{.data.{chave}}' | base64 --decode`
```

---

## MODO 3 — `--sandbox` — Criação de Ambiente GDA (Casas Bahia)

> **Atenção:** Este modo é exclusivo para projetos da Casas Bahia com ambientes GDA (sandbox/pre-prod).
> Não use para outros contextos.

### Etapa 0 — Coletar parâmetros

Pergunte ao usuário (se não fornecidos):

> Informe:
> - **Projeto** a criar ambiente GDA (ex: `gcb-hr-jt-work-journey-back`)
> - **Variant** de infra: `kustomize`, `helm-remote` ou `helm-local`
> - **Número do ticket** Jira para rastreabilidade (ex: `GDAS-999`)

### Etapa 1 — Ler configuração de homologação como base

Para o projeto informado, leia os arquivos do ambiente `hlg`:

- `helm-values/hlg.yaml` (variant Helm)
- `kustomize/overlays/hlg/` (variant Kustomize)
- `src/main/resources/application-hlg.yml`

### Checkpoint 1 (obrigatório antes de gerar arquivos)

Apresente ao usuário:

> **Checkpoint 1 — Revisão antes de gerar arquivos GDA**
>
> Projeto: {PROJECT}
> Variant: {VARIANT}
> Ticket: {TICKET}
> Base: ambiente hlg
>
> Substituições que serão aplicadas:
> - `hlg` → `gda` em nomes de recursos
> - Namespace: `{namespace-hlg}` → `{namespace-gda}`
> - Hosts: `-hlg` → `-preprd` em URLs
>
> Confirma? (S/N)

Aguarde confirmação antes de prosseguir.

### Etapa 2 — Gerar arquivos GDA

Aplique as seguintes substituições nos arquivos lidos:

| Origem (hlg) | Destino (gda) | Regra |
|-------------|--------------|-------|
| `namespace: gcb-hr-...-hlg` | `namespace: gcb-hr-...-gda` | Substituir sufixo `-hlg` por `-gda` |
| `host: servico-hlg.casasbahia.com` | `host: servico-preprd.casasbahia.com` | Substituir `-hlg` por `-preprd` |
| `hlg` no nome de ConfigMaps/Secrets | `gda` | Substituir literalmente |
| Réplicas | Reduzir para 1 (sandbox) | Mínimo para ambiente GDA |
| Resources (CPU/Memory) | Reduzir em 50% se > limites GDA | Sandbox com recursos menores |

**Variant Kustomize** — gere em `kustomize/overlays/gda/`:
- `kustomization.yaml`
- `deployment-patch.yaml`
- `service-patch.yaml` (se necessário)
- `ingress-patch.yaml` (se houver ingress)

**Variant Helm Remote** — gere em `helm-values/gda.yaml`

**Variant Helm Local** — gere em `helm-values/gda.yaml` com referência ao chart local

### Etapa 3 — Criar tarefa no Jira GDA

Registre o seguinte no checkpoint:

> Criação de tarefa Jira no projeto GDA:
> - **Projeto:** GDAS
> - **Tipo:** Task
> - **Título:** "Ambiente GDA — {PROJECT} — {TICKET}"
> - **Descrição:** "Arquivos de ambiente GDA gerados pelo sdd-inspect-infra. Revisar e abrir PR."
> - **Vinculado a:** {TICKET}

> ℹ️ Execute manualmente no Jira — este agente não tem acesso à API Jira.

### Checkpoint 2 (obrigatório antes de criar PR)

Apresente ao usuário:

> **Checkpoint 2 — Revisão antes de abrir PR**
>
> Arquivos gerados:
> {lista de arquivos criados}
>
> Branch a criar: `feature/gda-{PROJECT}-{TICKET}`
>
> Revisite os arquivos gerados e confirme que:
> - [ ] Namespace está correto (sufixo `-gda`)
> - [ ] Hosts usam `-preprd` (não `-hlg`)
> - [ ] Réplicas reduzidas para sandbox
> - [ ] Nenhuma credencial hardcoded foi introduzida
>
> Confirma abertura do PR? (S/N)

### Etapa 4 — Criar branch e abrir PR

Se o usuário confirmar:

```bash
git checkout -b feature/gda-{PROJECT}-{TICKET}
git add kustomize/overlays/gda/ helm-values/gda.yaml
git commit -m "feat(gda): ambiente sandbox para {PROJECT} — {TICKET}"
git push origin feature/gda-{PROJECT}-{TICKET}
```

Apresente o link do PR para o usuário abrir manualmente (ou via `gh pr create` se disponível).

---

## Regras Gerais

- **Modo `--credentials`**: nunca commitar `maped-infra/docs/` sem revisar itens 🔴 Crítico primeiro.
- **Modo `--kubectl`**: `maped-infra/kubectl-inspector/` é sempre adicionado ao `.gitignore` — nunca commitar valores decodificados de Secrets.
- **Modo `--sandbox`**: use exclusivamente para Casas Bahia / ambientes GDA. Os dois Checkpoints são obrigatórios.
- Nenhum modo modifica código de produção ou arquivos de teste.
- Credenciais hardcoded identificadas no modo `--credentials` são sempre classificadas como 🔴 Crítico — nunca ignore.
<!-- @end -->
