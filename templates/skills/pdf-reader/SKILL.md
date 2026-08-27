---
name: pdf-reader
description: >
  Skill para ler, extrair e interpretar conteúdo de arquivos PDF presentes no
  workspace (especificações, contratos, documentos de negócio, RFCs, manuais
  operacionais) e transformá-lo em contexto utilizável pelo Copilot durante
  tarefas de análise, criação de specs, geração de testes e implementação.
applyTo: "**/*.pdf"
triggers:
  - "ler pdf"
  - "extrair pdf"
  - "resumir pdf"
  - "analisar pdf"
  - "interpretar pdf"
---

# Skill: PDF Reader

## Objetivo
Permitir que o Copilot leia, extraia e interprete o conteúdo de arquivos PDF do
repositório (ou anexados) sem inventar informações, preservando fidelidade ao
documento original e respeitando as regras gerais definidas em
`.github/copilot-instructions.md`.

## Quando usar
Use esta skill sempre que:
- O usuário pedir para "ler", "resumir", "analisar", "extrair" ou "interpretar"
  um arquivo `.pdf`.
- Houver um PDF como anexo, no workspace da demanda ou em qualquer pasta do
  workspace que precise ser convertido em contexto textual.
- For necessário derivar regras de negócio, requisitos, critérios de aceitação,
  contratos de API ou modelos de dados a partir de um PDF.

## Quando NÃO usar
- Para arquivos que não são PDF (use leitura de arquivo padrão).
- Para criar conteúdo que não esteja no PDF (não inventar regras de negócio).
- Para PDFs com conteúdo sensível (PII, segredos, credenciais) — neste caso,
  alertar o usuário e não persistir o conteúdo em logs ou docs públicos.

## Entradas
- Caminho do arquivo PDF (relativo ao workspace) ou anexo enviado no chat.
- Objetivo da leitura: `resumo`, `extração estruturada`, `geração de spec`,
  `geração de testes`, `mapeamento de regras de negócio`.

## Saídas esperadas
Conforme o objetivo:
1. **Resumo**: bullets curtos com os pontos principais e seções.
2. **Extração estruturada** (preferida para specs):
   - Título / Identificador
   - Objetivo
   - Escopo (in / out)
   - Atores e papéis
   - Regras de negócio (lista numerada)
   - Requisitos funcionais
   - Requisitos não funcionais
   - Critérios de aceitação
   - Contratos (REST, mensageria, DB) se houver
   - Riscos e suposições
   - Trechos citados (com nº da página) que sustentam cada item
3. **Mapa de rastreabilidade**: cada item extraído deve referenciar a página
   do PDF de origem (`p. N`) para auditoria.

## Procedimento
1. Localize o PDF (usar `file_search` se necessário).
2. Tente extrair o texto:
   - Preferir ferramentas/utilitários já disponíveis no ambiente
     (ex.: `pdftotext`, `pdfminer`, bibliotecas Java como `Apache PDFBox` se já
     existirem no `pom.xml`).
   - **Não** adicionar dependências novas ao `pom.xml` apenas para esta skill,
     salvo solicitação explícita (regra geral do repositório).
   - Se o PDF for digitalizado (imagem), informar que é necessário OCR e
     pedir confirmação antes de prosseguir.
3. Normalize o texto (remover cabeçalhos/rodapés repetidos, hifenização de
   quebra de linha, numeração espúria).
4. Estruture a saída no formato solicitado.
5. Sempre cite a página de origem dos trechos relevantes.
6. Se algo estiver ambíguo no PDF, **liste como "Dúvida / Suposição"** em vez
   de inventar.

## Comando recomendado (Windows / PowerShell)
Caso `pdftotext` (Poppler) esteja instalado:

```powershell
pdftotext -layout "<caminho-do-arquivo>.pdf" "<caminho-do-arquivo>.txt"
```

Alternativa via Python (se disponível):

```powershell
python -c "from pdfminer.high_level import extract_text; print(extract_text(r'<caminho>.pdf'))"
```

> Não instalar pacotes globais sem confirmação do usuário.

## Integração com prompts existentes
Esta skill complementa os prompts em `.github/prompts/`:
- `create-spec.prompt.md` → use a saída estruturada como insumo da spec.
- `analyze-project.prompt.md` → use para incorporar PDFs de contexto.
- `generate-tests.prompt.md` → use os critérios de aceitação extraídos como
  base dos casos de teste.

## Regras de qualidade
- Não inventar conteúdo ausente no PDF.
- Não expor dados sensíveis em logs ou documentação pública.
- Manter fidelidade ao texto original; paráfrase apenas quando necessário e
  sempre com citação da página.
- Para PDFs longos, processar em seções e consolidar ao final.
- Preferir saída em Markdown válido, pronto para salvar em `SPEC_PATH`.

## Checklist final antes de entregar
- [ ] Origem (arquivo + páginas) citada em cada item relevante.
- [ ] Nada foi inventado; ambiguidades viraram "Dúvida / Suposição".
- [ ] Saída no formato pedido (resumo / extração estruturada).
- [ ] Sem dados sensíveis vazados.
- [ ] Pronto para alimentar specs, testes ou implementação.
