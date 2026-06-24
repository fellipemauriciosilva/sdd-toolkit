# Task: [BUG-XXXX — Bug Description]

## Identification

| Field | Value |
|-------|-------|
| Ticket | BUG-XXXX |
| Type | bugfix |
| Priority | TODO (P1/P2/P3) |
| Status | analysis |
| Severity | TODO (critical/high/medium/low) |
| Reported by | TODO |
| Environment | TODO (prod/staging/local) |

---

## Bug Description

TODO — one paragraph clearly describing what is failing.

## Steps to Reproduce

1. TODO
2. TODO
3. TODO

## Current (Buggy) Behavior

TODO — exactly what happens when the bug is triggered.

## Expected Behavior

TODO — exactly what should happen instead.

## Root Cause Analysis

TODO — fill after analyzing the code. Identify the exact class, method and line where the bug originates.

**Root cause file:** TODO
**Root cause line:** TODO
**Reason:** TODO

## Affected Files

| File | Layer | Change |
|------|-------|--------|
| `path/to/BuggyClass.java` | application | modify |

## Entry Point

TODO — which flow triggers this bug? (Kafka message, REST call, scheduler, etc.)

## Fix Plan

### Step 1 — TODO

## Tests to Add / Update

| Test class | Scenario |
|-----------|---------|
| `SomeServiceTest` | should not fail when [condition] |

## Regression Prevention

TODO — how will we ensure this bug doesn't come back?
(Unit test? Integration test? Input validation?)

## Risks

- RISK: TODO (could the fix affect other behaviors?)

## Decisions Made

<!-- Fill as decisions are taken during implementation -->
