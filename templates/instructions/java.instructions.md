---
applyTo: "**/*.java"
---

# Java Instructions

- Follow the existing Java version.
- Prefer readable code over clever code.
- Avoid duplicated logic and unnecessary abstractions.
- Keep methods/classes cohesive.
- Prefer constructor injection.
- Avoid mutable shared state.
- Use project-specific exceptions when available.
- Preserve original exception causes when wrapping.
- Avoid returning null when Optional or empty collections make more sense.
- Validate external input at boundaries.
- Consider pagination, streaming or batching for large data.
