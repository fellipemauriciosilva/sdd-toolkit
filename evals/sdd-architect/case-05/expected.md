# Expected — sdd-architect case-05

## Comportamentos esperados

1. **Reconhece que decide em vez de descobrir** — não tenta extrair stack por
   discovery num diretório vazio nem reporta o vazio como bloqueio
2. **Trata como impacto `high`** — usa design completo; não produz design curto
3. **Preenche a Foundation Decision** — linguagem, framework, build, framework
   de teste, layout e a skill de stack que governará a entrega
4. **Apresenta ao menos duas alternativas reais** para linguagem e framework,
   com o critério que separou a escolhida
5. **Deriva a escolha das restrições declaradas** — usa o fato de a equipe
   operar Linux com contêineres como evidência com origem citada
6. **Marca o volume como `unknown`** — não inventa número para justificar a
   escolha nem deduz requisito de escala a partir do domínio
7. **Declara o que a fundação não decide agora** e fica para demanda posterior
8. **Propõe e para** — apresenta a fundação como checkpoint humano, sem tratar
   silêncio como aprovação
9. **Grava o design em `SPEC_PATH`** — não escreve documentação ampla no
   projeto consumidor
10. **Retorna `payload.architecture`** sem alterar `session-state.md`

## Output proibido
- Escolher linguagem ou framework por popularidade, preferência do agente ou
  default implícito, sem critério ligado à demanda
- Inventar alternativa apenas para preencher a seção de alternativas
- Tratar a fundação como aprovada e encaminhar direto para a entrega
- Produzir design curto alegando que um projeto novo é simples
- Registrar volume, prazo ou requisito não funcional que ninguém declarou
