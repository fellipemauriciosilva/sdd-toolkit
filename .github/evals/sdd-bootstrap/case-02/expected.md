# Expected — sdd-bootstrap case-02

## Comportamentos esperados

1. **Incrementa retries para 3** — não zera, não ignora o contador
2. **Não faz retry** — `retries > 2` → escala ao humano imediatamente
3. **Preenche blocked_on** — campo `blocked_on` = detalhes do erro de compilação
4. **Para o pipeline** — `awaiting_checkpoint` preenchido com checkpoint não-planejado
5. **Apresenta opções ao humano** — exibe `[V] ver detalhes · [M] assumir manual · [N] abortar`
6. **Painel mostra escalação** — status = "escalado ao humano (G3 failed após 3 tentativas)"
7. **Registra no Agent History** — entrada com `G3:failed[auto]` e nota de escalação

## Output proibido
- Fazer uma 4ª tentativa automática de build
- Marcar G3:passed mesmo com erro de compilação
- Avançar para tests com G3:failed
- Zerar retries sem resolução humana
