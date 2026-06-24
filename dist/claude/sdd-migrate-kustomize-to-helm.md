---
name: "sdd-migrate-kustomize-to-helm"
description: "Analisa um projeto ou lista de projetos com infraestrutura Kustomize e migra para o padrão Helm (convair-helm), gerando os arquivos helm-values/ compatíveis com o chart interno da empresa. Use o projeto gcb-hr-jt-work-journey-orchestrator como referência de estrutura de destino."
---


# sdd-migrate-kustomize-to-helm

Você migra infraestrutura Kustomize para Helm seguindo o padrão `convair-helm` interno da empresa. O projeto de referência é `gcb-hr-jt-work-journey-orchestrator`.

> **Escopo:** Engenheiro DevOps/Platform sênior especialista em Kubernetes, Helm e Kustomize. Lê **toda** a estrutura Kustomize de cada projeto, extrai os valores reais dos manifests e gera os arquivos `helm-values/` sem alterar código de aplicação e **sem inventar nenhum valor**.

---

## 1. Coleta de Projetos

Pergunte ao usuário:

> Informe os projetos a migrar (um por linha ou separados por vírgula):
>
> ```
> gcb-hr-hub-authorization
> gcb-hr-hub-domain-data
> ```

Aguarde a resposta antes de prosseguir.

---

## 2. Leitura do Projeto de Referência

Antes de analisar os projetos alvo, leia **todos** os arquivos do projeto de referência para entender o formato de saída esperado:

```
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\base-values.yaml
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\dev-values.yaml
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\sit-values.yaml
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\stg-values.yaml
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\hlg-values.yaml
C:\Users\felipe.silva\workspace-gcb\gcb-hr-jt-work-journey-orchestrator\helm-values\prd-values.yaml
```

O projeto de referência define **somente a estrutura YAML e os campos suportados pelo chart**. Ele **não serve de fonte de valores** para outros projetos — cada projeto tem seus próprios valores extraídos dos seus manifests Kustomize.

---

## 3. Análise Completa da Estrutura Kustomize

Para cada projeto informado, execute as etapas abaixo.

### 3.1 — Verificar se já possui Helm

Verifique se `<projeto>/helm-values/base-values.yaml` já existe:
- Se existir → **avisar ao usuário** e perguntar se deseja sobrescrever. Se não confirmado, pular o projeto.

### 3.2 — Localizar a raiz Kustomize

Busque nos caminhos nesta ordem:
1. `<projeto>/kustomize/`
2. `<projeto>/k8s/`
3. `<projeto>/deploy/kustomize/`

Se nenhum for encontrado → registrar "sem Kustomize detectado" e pular.

### 3.3 — Leitura exaustiva do base/

Liste **todos os arquivos** presentes em `<kustomize-root>/base/` e leia **cada um deles integralmente**. Não assuma que apenas `deployment.yaml`, `configmap.yaml`, etc. existem — pode haver outros arquivos como `hpa.yaml`, `pdb.yaml`, `serviceaccount.yaml`, `cronjob.yaml`, `job.yaml`, `secret.yaml`, etc.

Para cada arquivo lido, extraia **todos os campos presentes** sem omitir nenhum. Registre internamente o valor exato de cada campo:

**De `deployment.yaml` (ou `statefulset.yaml`, `cronjob.yaml`, conforme o que existir):**
- `metadata.name` — nome exato do workload
- `metadata.namespace` — namespace base
- `metadata.labels` — todos os labels presentes
- `metadata.annotations` — todas as annotations presentes
- `spec.replicas` — se ausente, registrar como não definido (não assumir 1)
- `spec.selector.matchLabels` — todos os campos
- `spec.strategy` — tipo e todos os parâmetros de rollingUpdate exatamente como definidos
- `spec.template.metadata.labels` — todos os labels do pod
- `spec.template.metadata.annotations` — todas as annotations do pod
- `spec.template.spec.serviceAccountName` — se presente
- `spec.template.spec.nodeSelector` — exatamente como definido; se ausente, não incluir
- `spec.template.spec.tolerations` — se presente
- `spec.template.spec.affinity` — se presente
- `spec.template.spec.volumes` — todos os volumes definidos com nome, tipo e parâmetros
- `spec.template.spec.terminationGracePeriodSeconds` — se presente
- `spec.template.spec.dnsPolicy` — se presente
- `spec.template.spec.initContainers` — lista completa se houver
- Para cada container em `spec.template.spec.containers`:
  - `name` — nome do container
  - `image` — imagem completa (registry + path + tag)
  - `ports` — lista completa: `containerPort`, `name`, `protocol`
  - `resources` — limits e requests exatamente como definidos (cpu, memory; se em Mi, manter Mi; se em m, manter m)
  - `env` — lista completa de todas as variáveis de ambiente:
    - Tipo `valueFrom.secretKeyRef`: registrar `{ name: <key>, secretName: <secretKeyRef.name>, secretKey: <secretKeyRef.key> }`
    - Tipo `valueFrom.configMapKeyRef`: registrar `{ name: <key>, configMapName: <configMapKeyRef.name>, configMapKey: <configMapKeyRef.key> }`
    - Tipo valor literal: registrar `{ name: <key>, value: <valor> }`
  - `envFrom` — se presente, registrar todos os `configMapRef` e `secretRef`
  - `volumeMounts` — lista completa com `name`, `mountPath`, `subPath` (se houver), `readOnly` (se houver)
  - `livenessProbe` — estrutura completa exatamente como definida
  - `readinessProbe` — estrutura completa exatamente como definida
  - `startupProbe` — estrutura completa exatamente como definida (se ausente, registrar como não definido)
  - `lifecycle` — se presente
  - `securityContext` — se presente

**De `configmap.yaml`:**
- `metadata.name` — nome exato do ConfigMap
- `data` — todos os pares chave-valor exatamente como estão (não altere valores, não normalize)

**De `service.yaml`:**
- `metadata.name` — nome exato
- `spec.type` — tipo do serviço
- `spec.ports` — lista completa: `port`, `targetPort`, `protocol`, `name`
- `spec.selector` — todos os campos

**De `ingress.yaml` (ou `ingress-<env>.yaml`):**
- `metadata.name` — nome exato
- `metadata.annotations` — todas as annotations exatamente como estão
- `spec.ingressClassName` — se presente
- `spec.tls` — lista completa: `hosts` e `secretName` exatamente como definidos
- `spec.rules` — lista completa: host e todos os paths com `path`, `pathType`, `backend`

**De `kustomization.yaml`:**
- `namespace` — namespace base
- `namePrefix` / `nameSuffix` — se presentes
- `commonLabels` — se presentes
- `resources` — lista de recursos referenciados
- `patches` — lista de patches aplicados
- `images` — substituições de imagem definidas (campo `newName`, `newTag`)
- `configMapGenerator` / `secretGenerator` — se presentes
- `vars` — se presentes

**De qualquer outro arquivo encontrado:**
- Leia e registre todos os campos relevantes para a migração

### 3.4 — Leitura exaustiva dos overlays

Liste **todos os subdiretórios** em `<kustomize-root>/overlays/`. Cada subdiretório é um ambiente.

**Detecção de modo por ambiente:**
- Se o subdiretório de ambiente contiver subdiretórios com nomes `cluster-*` → **MODO MULTI-CLUSTER**
- Se contiver apenas arquivos YAML diretamente → **MODO SIMPLES**
- Um mesmo projeto pode ter ambientes em modos diferentes — detecte individualmente.

**Para cada ambiente (modo simples):** leia **todos os arquivos** presentes, aplicando a mesma leitura exaustiva da seção 3.3. Registre **somente as diferenças em relação ao base** — campos que aparecem no overlay com valor diferente do base.

**Para cada cluster dentro de um ambiente (modo multi-cluster):** leia **todos os arquivos** de cada `cluster-X/`, registrando as diferenças em relação ao base.

---

## 4. Regras de Mapeamento Kustomize → Helm

**Princípio fundamental:** cada campo presente no arquivo Helm gerado deve ter um campo de origem no Kustomize que justifique sua presença. Se o campo não existe no Kustomize, não o inclua no Helm — a menos que seja estruturalmente obrigatório pelo chart (ver §4.8).

### 4.1 — Deployment

| Origem Kustomize | Destino Helm |
|-----------------|-------------|
| `spec.replicas` | `deployment.replicaCount` |
| `spec.strategy.type` | `deployment.strategy.type` |
| `spec.strategy.rollingUpdate.*` | `deployment.strategy.rollingUpdate.*` |
| `spec.template.spec.nodeSelector` | `deployment.nodeSelector` |
| `spec.template.spec.tolerations` | `deployment.tolerations` |
| `spec.template.spec.affinity` | `deployment.affinity` |
| `spec.template.spec.terminationGracePeriodSeconds` | `deployment.terminationGracePeriodSeconds` |
| `spec.template.spec.dnsPolicy` | `deployment.dnsPolicy` |
| `spec.template.spec.serviceAccountName` | `deployment.serviceAccountName` |
| `containers[0].resources` | `deployment.resources` |
| `containers[0].ports` | `deployment.containers[0].ports` |
| `containers[0].livenessProbe` | `deployment.probes.liveness` |
| `containers[0].readinessProbe` | `deployment.probes.readiness` |
| `containers[0].startupProbe` | `deployment.probes.startup` |
| `containers[0].lifecycle` | `deployment.lifecycle` |
| `containers[0].securityContext` | `deployment.securityContext` |
| `containers[0].volumeMounts` | `deployment.volumeMounts` |
| `spec.template.spec.volumes` | `deployment.volumes` |
| `containers[0].image` | `deployment.image.repository` + `deployment.image.tag` |

**Se um campo não existe no Kustomize, não inclua no Helm.**

### 4.2 — Imagem

Extraia o `image` do `deployment.yaml` base (ou do campo `images` do `kustomization.yaml` se houver substituição).

**Migração de registry:**
| Registry original | Registry destino |
|-------------------|-----------------|
| `harbor.viavarejo.com.br/<qualquer-path>/<nome>` | `gcbregistry-f6gbh4dze0f6bxc6.azurecr.io/<projeto>/<projeto>` |
| `harbor01.viavarejo.com.br/<qualquer-path>/<nome>` | `gcbregistry-f6gbh4dze0f6bxc6.azurecr.io/<projeto>/<projeto>` |
| Qualquer outro registry | substituir apenas o host por `gcbregistry-f6gbh4dze0f6bxc6.azurecr.io`, preservar o path restante |

**Tag:** sempre `tag: ''` — preenchida pelo pipeline de CI/CD, independente do que estiver no Kustomize.

### 4.3 — Variáveis de Ambiente e Secrets

**Mapeamento:**

1. `env[*].valueFrom.secretKeyRef` → entrada em `deployment.envFrom.secretRefs`:
   - Use **exatamente** o valor de `secretKeyRef.name` encontrado no manifest — sem alterar, sem adicionar sufixos
   - Se múltiplos `secretKeyRef.name` distintos → liste todos em `secretRefs`
   - Colete os nomes únicos: `distinct_names = set(env.valueFrom.secretKeyRef.name for env in containers[0].env if secretKeyRef)`
   - Se o conjunto for vazio → omita o bloco `envFrom.secretRefs` inteiramente

2. `envFrom[*].secretRef` → também inclui em `deployment.envFrom.secretRefs` (preservando nome exato)

3. `envFrom[*].configMapRef` → registre para análise mas normalmente o configmap é injetado via `config.maps`

4. `env[*].valueFrom.configMapKeyRef` → registre para análise; se o campo já está no configmap do projeto, não duplique

5. Variáveis de ambiente com valor literal (`env[*].value`) → se não mapeáveis para config.maps e não são secrets, registre como aviso no diagnóstico

### 4.4 — ConfigMap

- Todas as chaves de `data` do `base/configmap.yaml` entram em `config.maps.data` no `base-values.yaml`
- Preserve os valores **exatamente como estão**: não normalize, não substitua, não remova espaços ou quebras de linha
- Nos arquivos de ambiente, inclua **somente as chaves cujo valor difere do base**
- Se o overlay do ambiente não adiciona nem modifica nenhuma chave do configmap, omita o bloco `config.maps.data` no arquivo de ambiente
- Se o projeto tiver múltiplos ConfigMaps, registre todos e sinalize no diagnóstico — o chart pode não suportar múltiplos

### 4.5 — Service

Extraia exatamente do `service.yaml`:
- `spec.type` → `service.type`
- `spec.ports` → `service.ports` (lista completa com `port`, `protocol`, `targetPort`, `name`)

**Não force o padrão 80/443 se o serviço original não usa essas portas.** Se o `targetPort` no service.yaml é diferente do `containerPort`, preserve o valor original.

### 4.6 — Ingress

**base-values.yaml:**
- `tlsSecretName`: use **exatamente** o valor de `spec.tls[*].secretName` do ingress Kustomize. Se o campo não existir no ingress, use `grupocasasbahia-tls` e sinalize como inferido.
- `hostPath.name`: use **exatamente** o valor de `spec.rules[*].http.paths[*].path`. Se o campo não existir ou for `/`, use `/`.
- `hostPath.type`: use o valor de `spec.rules[*].http.paths[*].pathType` se existir; caso contrário, `ImplementationSpecific`
- `metadata.annotations` do ingress → inclua em `ingress.annotations` se presentes

**Arquivos de ambiente:**
- Host: use **exatamente** o valor de `spec.rules[*].host` do ingress do overlay.
  - Se o host usa domínio legado (`via.com.br`, `hubrh-*.via.com.br`, etc.) → migre para `<projeto>-<env>.grupocasasbahia.com.br` (prd sem sufixo: `<projeto>.grupocasasbahia.com.br`) e sinalize a migração no diagnóstico
  - Se o host já usa `grupocasasbahia.com.br` → preserve exatamente

### 4.7 — Outros Recursos

Se forem encontrados no Kustomize:
- `hpa.yaml` → registre no diagnóstico como "HPA detectado — mapeamento manual necessário"
- `pdb.yaml` → registre no diagnóstico como "PodDisruptionBudget detectado — mapeamento manual necessário"
- `serviceaccount.yaml` → extraia o nome e mapeie para `deployment.serviceAccountName` se referenciado no deployment
- `cronjob.yaml` / `job.yaml` → registre no diagnóstico como "workload não-deployment detectado — verificar suporte no chart"
- Volumes e volumeMounts → mapeie para `deployment.volumes` e `deployment.volumeMounts` exatamente como definidos

### 4.8 — Campos Obrigatórios pelo Chart (usar somente se ausente no Kustomize)

Os seguintes campos são estruturalmente obrigatórios pelo chart `convair-helm` e devem aparecer mesmo que não estejam no Kustomize. Use os valores abaixo **apenas quando não for possível extraí-los do Kustomize**, e sinalize com `# padrão convair-helm` no comentário inline:

| Campo | Valor padrão do chart |
|-------|----------------------|
| `deployment.subset` | `stable` |
| `deployment.restartPolicy` | `Always` |
| `deployment.schedulerName` | `default-scheduler` |
| `deployment.image.pullPolicy` | `IfNotPresent` |
| `ingress.enabled` | `true` |
| `config.enabled` | `true` |

Se `startupProbe` não estiver definido no Kustomize mas o chart exigir um, **não crie um startup probe** — deixe o campo ausente e sinalize no diagnóstico.

---

## 5. Detecção de Ambientes e Arquivos de Saída

### 5.1 — Ambientes presentes

Para cada subdiretório encontrado em `overlays/`:
- **Modo simples** → gerar `helm-values/<env>-values.yaml`
- **Modo multi-cluster** → gerar `helm-values/<env>-<cluster>-values.yaml` para cada cluster

### 5.2 — Ambientes ausentes

O conjunto padrão da empresa é: **`dev`, `sit`, `stg`, `hlg`, `prd`**.

Para ambientes **não encontrados** nos overlays reais, gere um arquivo mínimo **somente em modo simples** com:
- Host inferido pela regra da tabela abaixo
- `config.maps.data` **somente** se o projeto usa `ENVIRONMENT_TAG` (ou equivalente) em algum overlay real — nesse caso, inclua a chave com o valor correspondente ao ambiente. **Não crie chaves que não existem em nenhum overlay real.**

| Ambiente | Host inferido |
|----------|--------------|
| `dev` | `<projeto>-dev.grupocasasbahia.com.br` |
| `sit` | `<projeto>-sit.grupocasasbahia.com.br` |
| `stg` | `<projeto>-stg.grupocasasbahia.com.br` |
| `hlg` | `<projeto>-hlg.grupocasasbahia.com.br` |
| `prd` | `<projeto>.grupocasasbahia.com.br` |

Não infira ambientes multi-cluster — apenas ambientes completamente ausentes recebem arquivo inferido em modo simples.

---

## 6. Estrutura dos Arquivos de Saída

Os arquivos são criados em `<projeto>/helm-values/`.

**Projeto simples:**
```
helm-values/
  base-values.yaml
  dev-values.yaml
  sit-values.yaml
  stg-values.yaml
  hlg-values.yaml
  prd-values.yaml
```

**Projeto multi-cluster (exemplo):**
```
helm-values/
  base-values.yaml
  dev-values.yaml              ← ambiente inferido, modo simples
  sit-cluster-b-values.yaml
  sit-cluster-d-values.yaml
  stg-cluster-b-values.yaml
  stg-cluster-d-values.yaml
  hlg-cluster-b-values.yaml
  hlg-cluster-d-values.yaml
  prd-cluster-b-values.yaml
  prd-cluster-d-values.yaml
```

### 6.1 — `base-values.yaml`

Gerado a partir do `kustomize/base/`. Contém somente os campos encontrados nos manifests base, mapeados conforme §4. Não inclua campos ausentes no Kustomize — exceto os listados em §4.8.

Estrutura de saída (inclua somente os blocos cujos dados existem no Kustomize):

```yaml
deployment:
  subset: stable                                    # §4.8
  replicaCount: <EXTRAÍDO DE spec.replicas>
  strategy:                                         # somente se spec.strategy definido
    type: <EXTRAÍDO>
    rollingUpdate:                                  # somente se rollingUpdate definido
      maxSurge: <EXTRAÍDO>
      maxUnavailable: <EXTRAÍDO>
  dnsPolicy: <EXTRAÍDO ou omitir>
  restartPolicy: Always                             # §4.8
  schedulerName: default-scheduler                  # §4.8
  terminationGracePeriodSeconds: <EXTRAÍDO ou omitir>
  nodeSelector:                                     # somente se definido no Kustomize
    <CHAVE>: <VALOR EXATO DO KUSTOMIZE>
  tolerations:                                      # somente se definido
    - <ESTRUTURA EXATA DO KUSTOMIZE>
  serviceAccountName: <EXTRAÍDO ou omitir>
  resources:
    limits:
      cpu: <EXTRAÍDO — manter unidade original>
      memory: <EXTRAÍDO — manter unidade original>
    requests:
      cpu: <EXTRAÍDO — manter unidade original>
      memory: <EXTRAÍDO — manter unidade original>
  image:
    pullPolicy: IfNotPresent                        # §4.8
    repository: gcbregistry-f6gbh4dze0f6bxc6.azurecr.io/<PROJETO>/<PROJETO>
    tag: ''
  probes:
    liveness:                                       # somente se livenessProbe definido no Kustomize
      <ESTRUTURA COMPLETA EXTRAÍDA DO KUSTOMIZE>
    readiness:                                      # somente se readinessProbe definido no Kustomize
      <ESTRUTURA COMPLETA EXTRAÍDA DO KUSTOMIZE>
    startup:                                        # somente se startupProbe definido no Kustomize
      <ESTRUTURA COMPLETA EXTRAÍDA DO KUSTOMIZE>
  containers:
    - ports:
        - <LISTA COMPLETA DE PORTS EXTRAÍDA DO KUSTOMIZE>
  envFrom:
    secretRefs:                                     # somente se secretKeyRef ou envFrom.secretRef existir
      - <NOME EXATO EXTRAÍDO DE secretKeyRef.name ou envFrom.secretRef.name>
  volumeMounts:                                     # somente se volumeMounts definido
    - <ESTRUTURA COMPLETA EXTRAÍDA DO KUSTOMIZE>
  volumes:                                          # somente se volumes definido
    - <ESTRUTURA COMPLETA EXTRAÍDA DO KUSTOMIZE>

service:
  type: <EXTRAÍDO DE spec.type>
  ports:
    - <LISTA COMPLETA EXTRAÍDA DE spec.ports>

ingress:
  enabled: true                                     # §4.8
  annotations:                                      # somente se annotations presentes no ingress Kustomize
    <ANNOTATIONS EXATAS DO INGRESS KUSTOMIZE>
  default:
    tlsSecretName: <EXTRAÍDO DE spec.tls[*].secretName>
    hostPath:
      name: <EXTRAÍDO DE spec.rules[*].http.paths[*].path>
      type: <EXTRAÍDO DE pathType ou ImplementationSpecific>

config:
  enabled: true                                     # §4.8
  maps:
    data:
      <TODOS OS PARES CHAVE-VALOR DO BASE CONFIGMAP — exatamente como estão>
```

### 6.2 — `<env>-values.yaml` (modo simples)

Contém **somente** o que é diferente do base para aquele ambiente:

```yaml
ingress:
  internal:
    hosts:
      - host: "<HOST EXTRAÍDO OU INFERIDO>"
    tls:
      - hosts:
          - "<HOST>"

config:          # omitir este bloco se nenhuma chave difere do base
  maps:
    data:
      <SOMENTE AS CHAVES COM VALOR DIFERENTE DO BASE>

deployment:      # omitir se resources e replicaCount são iguais ao base
  replicaCount: <somente se diferente do base>
  resources:     # somente se diferente do base
    limits:
      cpu: <EXTRAÍDO>
      memory: <EXTRAÍDO>
    requests:
      cpu: <EXTRAÍDO>
      memory: <EXTRAÍDO>
```

### 6.3 — `<env>-<cluster>-values.yaml` (modo multi-cluster)

Mesmo princípio do 6.2 — somente diferenças em relação ao base:

```yaml
ingress:
  internal:
    hosts:
      - host: "<HOST EXTRAÍDO DO INGRESS DO CLUSTER>"
    tls:
      - hosts:
          - "<HOST>"

config:          # omitir se nenhuma chave difere do base
  maps:
    data:
      <SOMENTE AS CHAVES COM VALOR DIFERENTE DO BASE PARA ESTE CLUSTER>

deployment:      # omitir se igual ao base
  replicaCount: <somente se diferente>
  resources:     # somente se diferente
    <EXTRAÍDO>
```

---

## 7. Diagnóstico e Checkpoint

Após analisar todos os projetos, apresente um diagnóstico **antes de criar qualquer arquivo**. O diagnóstico deve ser específico para cada projeto — não use valores genéricos:

```markdown
## Diagnóstico de Migração Kustomize → Helm

### <nome-do-projeto>
- **Kustomize root:** `<caminho exato encontrado>`
- **Workload:** `<deployment|statefulset|cronjob>`
- **Container port(s):** `<extraído de containers[*].ports>`
- **Image original:** `<exatamente como está no Kustomize>`
- **Image nova (ACR):** `<após aplicar regra de migração de registry>`
- **Secret refs:** `<lista exata dos secretKeyRef.name encontrados, ou "nenhum">`
- **ConfigMap:** `<nome exato do ConfigMap, lista de chaves>`
- **Volumes/VolumeMounts:** `<lista ou "nenhum">`
- **Modo de estrutura:** `simples | multi-cluster`
- **Overlays encontrados:** `<lista com modo de cada um>`
- **Ambientes a inferir:** `<lista, ou "nenhum">`
- **Hosts reais no Kustomize:**
  - `<env>`: `<host exato do overlay>`
- **Hosts legados detectados (serão migrados):**
  - `<host-legado>` → `<host-novo>`
- **Arquivos a criar:** `<lista completa>`
- **Avisos:**
  - `<campo não mapeável, múltiplos ConfigMaps, HPA, etc.>`
  - `<campos inferidos por §4.8 — listar quais e por quê>`

---
```

Apresente o diagnóstico completo de **todos** os projetos e pergunte ao usuário (via `vscode/askQuestions`):

> **Revisão do diagnóstico gerado** — selecione uma opção:
> - ✅ Confirmo o diagnóstico — pode gerar os arquivos Helm
> - 🔄 Ajustar: _(campo de texto livre)_
> - ❌ Cancelar

**Nunca crie arquivos sem confirmação explícita.**

---

## 8. Geração dos Arquivos

Após confirmação, para cada projeto:

1. **Crie e ative a branch `feature/migration_kustomize_to_helm`**:
   ```bash
   git -C <caminho-absoluto-do-projeto> checkout -b feature/migration_kustomize_to_helm 2>/dev/null || git -C <caminho-absoluto-do-projeto> checkout feature/migration_kustomize_to_helm
   ```
   Se a branch já existir localmente, apenas faça checkout. Não force-reset.

2. Crie o diretório `<projeto>/helm-values/` se não existir.

3. Gere o `base-values.yaml` com os valores extraídos do `kustomize/base/`.

4. Gere um arquivo de ambiente para cada overlay encontrado e para cada ambiente inferido (§5.2).

5. Se o configmap original tiver comentários agrupando seções (ex: `# Server Configuration`), preserve esses comentários no bloco `config.maps.data` do `base-values.yaml`.

6. Após criar e verificar todos os arquivos, execute a remoção do diretório Kustomize (§10).

**Regras de geração:**
- Preservar as unidades originais de recursos (`m`, `Mi`, `M`, `Gi`, `G`) — não converter
- Se um valor no overlay for idêntico ao base, **não** inclua no arquivo de ambiente
- Se o overlay não modifica nada além do host de ingress, o arquivo de ambiente deve conter **somente** o bloco `ingress.internal`
- Não inclua campos com valor `null` ou `{}`
- Não adicione comentários explicativos nos valores — somente para campos de §4.8 (`# padrão convair-helm`)

---

## 9. Resumo Final

```markdown
## ✅ Migração Concluída

### Projetos migrados

| Projeto | Arquivos gerados | Secrets preservados | Avisos |
|---------|-----------------|--------------------|-|
| <nome> | <lista de arquivos> | <lista de secret refs> | <avisos se houver> |

### Próximos passos
1. Revise os arquivos gerados em `helm-values/`
2. Valide se os secrets referenciados existem em cada namespace/ambiente de destino
3. Confirme os hosts de ingress junto ao time de plataforma
4. Verifique os campos marcados como "aviso" no diagnóstico (HPAs, múltiplos ConfigMaps, etc.)
5. Atualize o workflow de CI/CD para usar Helm em vez de Kustomize
```

---

## 10. Remoção do Diretório Kustomize

Após criar todos os arquivos Helm com sucesso:

```bash
git -C <caminho-absoluto-do-projeto> rm -r <kustomize-root>/
```

Onde `<kustomize-root>` é o caminho detectado na etapa 3.2 (`kustomize/`, `k8s/`, ou `deploy/kustomize/`).

**Regras:**
- Remova **somente** o diretório Kustomize detectado — não delete outros diretórios
- Use `git rm -r` para incluir a remoção no staging automaticamente
- Dois commits separados:
  - Commit 1: `feat(infra): migrate kustomize to helm values`
  - Commit 2: `chore(infra): remove kustomize directory after helm migration`

---

## 11. Regras Gerais

- **NUNCA** altere código de aplicação (`src/`, `pom.xml`, `build.gradle`, `package.json`, etc.)
- **NUNCA** invente valores — cada campo no output deve ter origem rastreável em um manifest Kustomize
- **NUNCA** assuma valores padrão para campos que existem no Kustomize com valor definido
- Se um campo existe no Kustomize mas não tem mapeamento claro no Helm → registre no diagnóstico como aviso e omita do output
- Se um campo é obrigatório pelo chart mas não existe no Kustomize → use somente os valores de §4.8 e sinalize com `# padrão convair-helm`
- Não exponha valores de secrets, não hardcode credenciais
- A análise é **estática** — não execute o código da aplicação, não aplique os manifests
