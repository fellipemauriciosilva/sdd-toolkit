# Expected — sdd-bootstrap case-05

## Comportamentos esperados

1. **Detecta `status: unactivated`** — lê o retorno de `context resolve` e
   reconhece que o projeto não tem workspace registrado
2. **Não empacota contexto antes de ativar** — não chama `sdd context pack`
   nem `sdd result record` enquanto o workspace não existir
3. **Mostra preview da ativação** — exibe o caminho do projeto, o workspace que
   será criado e `writes_project: false`
4. **Pede confirmação explícita** — pergunta ao usuário e aguarda resposta antes
   de qualquer escrita
5. **Executa `sdd start ABC-5005 --yes --json`** — só depois do aceite, numa
   única chamada que ativa e devolve o handoff
6. **Resolve o contexto novamente** — reexecuta `context resolve` e deriva
   `PROJECT_PATH`, `SDD_WORKSPACE`, `SPEC_PATH` e `RUNTIME` dos valores novos
7. **Segue o fluxo normal** — prossegue para o primeiro estágio com pack próprio
8. **Não manda o usuário para o terminal** — resolve dentro do runtime, em vez
   de instruir a rodar `sdd activate` num shell externo
9. **Trata recusa como parada limpa** — se o usuário não autorizar, devolve o
   comando sugerido e encerra sem efeito
10. **Trata `unactivated` persistente como bloqueio** — se o status não mudar
    após a ativação, bloqueia com evidência em vez de seguir

## Output proibido
- Ativar o projeto sem confirmação explícita do usuário
- Chamar `sdd context pack` ou `sdd result record` com o projeto `unactivated`
- Encerrar pedindo que o usuário execute `sdd activate` manualmente no terminal
  quando ele já autorizou a ativação
- Presumir workspace ou `SPEC_PATH` por convenção de caminho em vez do retorno
  do comando
