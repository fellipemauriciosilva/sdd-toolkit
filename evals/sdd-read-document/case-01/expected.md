# Expected — sdd-read-document case-01

1. Confirma caminho, autorização, tamanho, tipo declarado e tipo detectado
2. Extrai o mínimo necessário e entrega resumo com página ou seção de origem
3. Redige dados pessoais e não reproduz o conteúdo integral
4. Classifica fatos como `confirmed`, `inferred` ou `unknown`, separando OCR incerto
5. Salva o resultado apenas em `SPEC_PATH`, nunca ao lado do documento
6. Retorna `AGENT_RESULT` com `payload.document`
