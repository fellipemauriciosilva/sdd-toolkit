---
name: doc-reader
description: ">"
---

# Skill: DOC / DOCX Reader

## Objetivo
Permitir que o Copilot leia, extraia e interprete o conteúdo de arquivos
Microsoft Word (`.doc` legado e `.docx` Open XML) do repositório (ou anexados)
sem inventar informações, preservando fidelidade ao documento original e
respeitando as regras gerais definidas em `.github/copilot-instructions.md`.

## Quando usar
Use esta skill sempre que:
- O usuário pedir para "ler", "resumir", "analisar", "extrair" ou "interpretar"
  um arquivo `.doc` ou `.docx`.
- Houver um documento Word como anexo, no workspace da demanda ou em
  qualquer pasta do workspace que precise ser convertido em contexto textual.
- For necessário derivar regras de negócio, requisitos, critérios de aceitação,
  contratos de API ou modelos de dados a partir de um documento Word.

## Quando NÃO usar
- Para arquivos que não são Word (use a skill apropriada — ex.: `pdf-reader`
  para PDFs, leitura padrão para Markdown/texto).
- Para criar conteúdo que não esteja no documento (não inventar regras de
  negócio).
- Para documentos com conteúdo sensível (PII, segredos, credenciais) — neste
  caso, alertar o usuário e não persistir o conteúdo em logs ou docs públicos.

## Entradas
- Caminho do arquivo `.doc`/`.docx` (relativo ao workspace) ou anexo enviado
  no chat.
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
   - Tabelas relevantes (preservar como Markdown)
   - Riscos e suposições
   - Trechos citados (com referência de seção/heading) que sustentam cada item
3. **Mapa de rastreabilidade**: cada item extraído deve referenciar a seção
   ou heading do documento de origem para auditoria.

## Procedimento
1. Localize o documento (usar `file_search` se necessário).
2. Tente extrair o texto:
   - **`.docx`** (formato Open XML, recomendado):
     - Preferir descompactação ZIP do `.docx` e leitura de `word/document.xml`
       quando ferramentas externas não estiverem disponíveis.
     - Ou usar `python-docx`, `pandoc`, `docx2txt` se já existirem no
       ambiente.
   - **`.doc`** (formato binário legado):
     - Usar `antiword`, `catdoc`, LibreOffice headless (`soffice --headless
       --convert-to txt`) ou `textract` se já existirem no ambiente.
     - Se não for possível extrair, recomendar ao usuário converter para
       `.docx` ou `.pdf` antes de prosseguir.
   - **Não** adicionar dependências novas ao `pom.xml` ou ao ambiente apenas
     para esta skill, salvo solicitação explícita (regra geral do
     repositório).
   - Se o arquivo contiver apenas imagens digitalizadas, informar que é
     necessário OCR e pedir confirmação antes de prosseguir.
3. Normalize o texto:
   - Remover cabeçalhos/rodapés repetidos.
   - Preservar estrutura de headings (H1/H2/H3) como seções Markdown.
   - Converter tabelas em Markdown.
   - Preservar listas numeradas e com marcadores.
4. Estruture a saída no formato solicitado.
5. Sempre cite a seção/heading de origem dos trechos relevantes.
6. Se algo estiver ambíguo, **liste como "Dúvida / Suposição"** em vez de
   inventar.

## Comandos recomendados (Windows / PowerShell)

### .docx — extração via descompactação (sem dependências extras)
```powershell
# .docx é um ZIP; o texto principal fica em word/document.xml
Expand-Archive -Path "<arquivo>.docx" -DestinationPath "<arquivo>_unzipped" -Force
Get-Content "<arquivo>_unzipped\word\document.xml"
```

### .docx — via Python (`python-docx`), se disponível
```powershell
python -c "from docx import Document; d = Document(r'<arquivo>.docx'); print('\n'.join(p.text for p in d.paragraphs))"
```

### .docx / .doc — via Pandoc, se disponível
```powershell
pandoc "<arquivo>.docx" -t gfm -o "<arquivo>.md"
pandoc "<arquivo>.doc"  -t gfm -o "<arquivo>.md"
```

### .doc / .docx — via LibreOffice headless, se disponível
```powershell
soffice --headless --convert-to txt "<arquivo>.doc"
soffice --headless --convert-to txt "<arquivo>.docx"
```

> Não instalar pacotes globais sem confirmação do usuário.

## Integração com prompts existentes
Esta skill complementa os prompts em `.github/prompts/`:
- `create-spec.prompt.md` → use a saída estruturada como insumo da spec.
- `analyze-project.prompt.md` → use para incorporar documentos Word de
  contexto.
- `generate-tests.prompt.md` → use os critérios de aceitação extraídos como
  base dos casos de teste.
- `read-pdf.prompt.md` / skill `pdf-reader` → fluxo análogo para PDFs.

## Regras de qualidade
- Não inventar conteúdo ausente no documento.
- Não expor dados sensíveis em logs ou documentação pública.
- Manter fidelidade ao texto original; paráfrase apenas quando necessário e
  sempre com citação da seção.
- Preservar tabelas e listas estruturadas (Markdown).
- Para documentos longos, processar em seções e consolidar ao final.
- Preferir saída em Markdown válido, pronto para salvar em `SPEC_PATH`.

## Checklist final antes de entregar
- [ ] Origem (arquivo + seção/heading) citada em cada item relevante.
- [ ] Nada foi inventado; ambiguidades viraram "Dúvida / Suposição".
- [ ] Saída no formato pedido (resumo / extração estruturada).
- [ ] Tabelas e listas preservadas em Markdown.
- [ ] Sem dados sensíveis vazados.
- [ ] Pronto para alimentar specs, testes ou implementação.
