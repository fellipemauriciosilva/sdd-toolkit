---
mode: agent
author: "Felipe Mauricio da Silva"
description: "Lê e extrai conteúdo de documentos Word (.doc, .docx) e PDF (.pdf). Detecta automaticamente o tipo de arquivo, usa a skill correspondente e apresenta o conteúdo estruturado. Opcionalmente salva o conteúdo extraído como Markdown na pasta da spec."
model: "Claude Sonnet 4.6"
tools:
  - search/fileSearch
  - search/textSearch
  - edit/editFiles
  - edit/createFile
  - execute/runInTerminal
  - execute/getTerminalOutput
  - vscode/askQuestions
version: "2.3.0"
---


# sdd-read-document — Leitura de Documentos (Word e PDF)

Lê e extrai conteúdo de documentos Word ou PDF, apresenta o conteúdo estruturado e opcionalmente salva como Markdown na pasta da spec.

O usuário invoca este agente informando o caminho do arquivo:
```
/sdd-read-document PROJECT/.github/docs/specs/JT-1234/spec.docx
/sdd-read-document PROJECT/.github/docs/specs/JT-1234/requisitos.pdf
```

---

## Passo 0 — Resolver kit

Se o `FILE_PATH` fornecido permite inferir um `PROJECT` (ex: `PROJECT/.github/docs/specs/TICKET/arquivo.docx`), leia `PROJECT/.github/sdd.config.md` e extraia `sdd_kit:`. Resolva como caminho relativo ao projeto. Use `{sdd_kit}` nas referências abaixo. Se `sdd.config.md` não existir, use o diretório pai do projeto onde o kit estiver instalado.

---

## Passo 1 — Identificar o arquivo

Se o usuário não forneceu o caminho do arquivo, pergunte:

> Qual arquivo você deseja ler?
> Informe o caminho completo ou relativo ao workspace.
> Formatos suportados: `.doc`, `.docx`, `.pdf`

Salve o caminho como `FILE_PATH`.

---

## Passo 2 — Detectar o tipo de arquivo

Verifique a extensão do `FILE_PATH`:

| Extensão | Tipo | Skill a usar |
|----------|------|-------------|
| `.doc` ou `.docx` | Documento Word | `{sdd_kit}/templates/skills/doc-reader/SKILL.md` |
| `.pdf` | Documento PDF | `{sdd_kit}/templates/skills/pdf-reader/SKILL.md` |
| Outra | Não suportado | Informar ao usuário e encerrar |

---

## Passo 3 — Carregar a skill correspondente

### Para arquivos Word (`.doc`, `.docx`)

Leia e siga as instruções em `{sdd_kit}/templates/skills/doc-reader/SKILL.md`.

A skill doc-reader define como:
- Ler o conteúdo do arquivo Word via ferramentas disponíveis
- Extrair texto, tabelas, listas e estrutura de headings
- Preservar a hierarquia de seções (H1, H2, H3)

### Para arquivos PDF (`.pdf`)

Leia e siga as instruções em `{sdd_kit}/templates/skills/pdf-reader/SKILL.md`.

A skill pdf-reader define como:
- Ler páginas do PDF em blocos
- Extrair texto mantendo ordem de leitura
- Identificar tabelas e listas quando possível
- Lidar com PDFs multipágina

---

## Passo 4 — Extrair e estruturar o conteúdo

Após a leitura, estruture o conteúdo extraído no formato Markdown:

```markdown
# {nome do arquivo sem extensão}

> Tipo: {Word / PDF}
> Arquivo: {FILE_PATH}
> Extraído em: {data atual}

---

{conteúdo extraído preservando a estrutura original}
```

Regras de estruturação:
- Preserve títulos como `#`, `##`, `###`
- Preserve tabelas como tabelas Markdown
- Preserve listas com `-` ou numeração
- Mantenha parágrafos separados por linha em branco
- Não omita conteúdo — extraia tudo que for legível

---

## Passo 5 — Apresentar o conteúdo ao usuário

Mostre o conteúdo extraído completo e pergunte:

> Conteúdo extraído com sucesso.
>
> Deseja salvar este conteúdo como Markdown?
> - **S** — salvar (informe o caminho ou use o padrão abaixo)
> - **N** — apenas visualizar, sem salvar

**Caminho padrão de salvamento** (se aplicável):
- Se o arquivo está em `PROJECT/.github/docs/specs/TICKET/` → salvar como `{nome-do-arquivo}.md` na mesma pasta
- Caso contrário → salvar na mesma pasta do arquivo original com extensão `.md`

---

## Passo 6 — Salvar o conteúdo (se solicitado)

Se o usuário confirmar o salvamento:

1. Determine o caminho de destino (padrão ou informado pelo usuário)
2. Crie o arquivo `.md` com o conteúdo estruturado
3. Confirme o caminho do arquivo criado

> Arquivo salvo em: `{caminho}`
>
> Próximo passo sugerido: `/sdd-analyze-demand PROJECT TICKET` para usar este documento na análise da demanda.

---

## Regras

- Nunca altere o conteúdo extraído — preserve fielmente o que está no documento.
- Se parte do documento não for legível (página escaneada, imagem, etc.), informe explicitamente: `[Conteúdo não extraível — possível imagem ou página escaneada]`.
- Não invente conteúdo para seções que não puderam ser lidas.
- Não modifique arquivos existentes — apenas crie novos arquivos `.md`.
- Se a skill correspondente não existir no workspace, informe ao usuário e encerre com a mensagem: `Skill {doc-reader/pdf-reader} não encontrada em {sdd_kit}/templates/skills/. Verifique se o caminho do kit está correto em sdd.config.md.`
