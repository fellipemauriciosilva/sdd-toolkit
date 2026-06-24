---
applyTo: "src/**/*.java,**/*.yml,**/*.yaml,**/*.properties"
---

# Security Instructions

- Never commit secrets, tokens, passwords or private keys.
- Do not log passwords, tokens, authorization headers or sensitive payloads.
- Validate external input.
- Preserve authentication and authorization patterns.
- Avoid exposing stack traces or infrastructure details in public responses.
- Prefer existing dependencies and avoid unmaintained libraries.
