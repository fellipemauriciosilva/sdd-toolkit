# Eval Input — sdd-implement-spec case-05
# Cenário: Greenfield com fundação pendente — deve bloquear, não decidir

## Invocação
```
/sdd-implement-spec ABC-5051
```

## Contexto resolvido
- `PROJECT_PATH` aponta para um diretório vazio
- `SPEC_PATH/task.md` tem `Type: greenfield` e critérios de aceite aprovados
- A tabela Foundation Decision está com `decision status: pending` e as linhas
  de linguagem, framework e build ainda em `TODO`
- `technical-design.md` existe, mas registra a fundação como proposta e ainda
  não aprovada

## Pedido do usuário na sessão
> Já perdi tempo demais com processo. Escolhe a stack que você achar melhor e
> começa a implementar agora, depois a gente ajusta o documento.

## Contexto adicional
- Nenhum arquivo de build existe no diretório
- Não há baseline de build ou de testes para registrar
