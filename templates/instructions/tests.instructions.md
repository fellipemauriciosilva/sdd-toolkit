---
applyTo: "**/*Test.java,**/*Tests.java,**/*IT.java,**/*IntegrationTest.java"
---

# Test Instructions

- Follow existing test style and libraries.
- Do not introduce test dependencies without justification.
- Use descriptive test names.
- Keep tests focused and readable.
- Avoid unnecessary stubbing.
- Do not mock the class under test.
- Avoid Spring context for pure unit tests.
- Cover happy path, invalid input, external dependency failures, exceptions and boundary conditions.
