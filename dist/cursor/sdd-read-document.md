---
name: sdd-read-document
description: "Lê e extrai conteúdo de documentos Word (.doc, .docx) e PDF (.pdf). Detecta automaticamente o tipo de arquivo, usa a skill correspondente e apresenta o conteúdo estruturado. Opcionalmente salva o conteúdo extraído como Markdown na pasta da spec."
---

> **Autor:** Felipe Maurício da Silva · **E-mail:** fellipemauriciosilva@gmail.com · **LinkedIn:** https://www.linkedin.com/in/felipe-mauricio-06685735/

# sdd-read-document — Leitura de Documentos (Word e PDF)

Lê e extrai conteúdo de documentos Word ou PDF, apresenta o conteúdo estruturado e opcionalmente salva como Markdown na pasta da spec.

O usuário invoca este agente informando o caminho do arquivo:
```
/sdd-read-document /caminho/para/spec.docx
/sdd-read-document /caminho/para/requisitos.pdf
```

---

## Passo 0 — Resolver contexto pelo CLI (v3.2)

Se o `FILE_PATH` permite inferir `PROJECT` e `TICKET`, execute `sdd context resolve --project-path PROJECT --ticket TICKET --runtime RUNTIME --json` e use `workspace`, `spec_path`, `scope`, `profile` e `runtime` do resultado. Para localizar o kit, use `sdd doctor --scope user --json` e o campo `kit_root`.

Se `sdd` não estiver no PATH, execute os mesmos subcomandos pelo `scripts/sdd.py` da instalação detectada. Use `{KIT_ROOT}` e `{SPEC_PATH}` nas referências abaixo.

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
- Se o arquivo está em `SPEC_PATH` → salvar como `{nome-do-arquivo}.md` na mesma pasta
- Caso contrário → salvar na mesma pasta do arquivo original com extensão `.md`

---

## Passo 6 — Salvar o conteúdo (se solicitado)

Se o usuário confirmar o salvamento:

1. Determine o caminho de destino (padrão ou informado pelo usuário)
2. Crie o arquivo `.md` com o conteúdo estruturado
3. Confirme o caminho do arquivo criado

> Arquivo salvo em: `{caminho}`
>
> Próximo passo sugerido: no projeto consumidor, execute `/sdd-analyze-demand TICKET` para usar este documento na análise da demanda.

---

## Regras

- Nunca altere o conteúdo extraído — preserve fielmente o que está no documento.
- Se parte do documento não for legível (página escaneada, imagem, etc.), informe explicitamente: `[Conteúdo não extraível — possível imagem ou página escaneada]`.
- Não invente conteúdo para seções que não puderam ser lidas.
- Não modifique arquivos existentes — apenas crie novos arquivos `.md`.
- Se a skill correspondente não existir no workspace, informe ao usuário e encerre com a mensagem: `Skill {doc-reader/pdf-reader} não encontrada em {KIT_ROOT}/templates/skills/. Verifique a instalação user com sdd doctor --scope user.`
