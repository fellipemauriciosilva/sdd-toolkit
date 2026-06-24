---
applyTo: "**/controller/**/*.java,**/service/**/*.java,**/repository/**/*.java,**/adapter/**/*.java,**/client/**/*.java,**/*Application.java,**/*Config.java"
---

# Spring Boot Instructions

## Controllers
- Keep controllers thin.
- Validate request inputs.
- Delegate to services/use cases.

## Services / Use Cases
- Keep orchestration here.
- Avoid mixing business logic with HTTP, DB or messaging details.
- Use transactions intentionally.

## Repositories
- Keep persistence logic isolated.
- Avoid business rules in repositories.
- Watch lazy loading and N+1 queries.

## Clients / External Integrations
- Isolate external APIs behind clients/adapters.
- Configure timeouts.
- Handle 4xx/5xx according to business rules.
- Preserve retry/fallback patterns.

## Configuration
- Use configuration properties.
- Do not hardcode environment values or secrets.
