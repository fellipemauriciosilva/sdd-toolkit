# Eval Input — sdd-review-code case-01
# Cenário: SQL Injection encontrado → G5 achado 🔴, CHECKPOINT 2

## Código para revisar
```java
// MetaRepository.java
public List<Meta> findByFilter(String status) {
    String sql = "SELECT * FROM metas WHERE status = '" + status + "'";
    return jdbcTemplate.query(sql, rowMapper);
}
```

## Contexto
- Método chamado diretamente a partir de controller
- `status` vem de query parameter sem validação
