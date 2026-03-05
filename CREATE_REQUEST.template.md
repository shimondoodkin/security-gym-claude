---
level: L1 | L2
language: Python | C | Rust | C++
target_arch: x86_64           # L2 only
difficulty: 3                  # 1 (trivial) to 5 (expert)
code_poorness: 2               # 1 (clean) to 5 (messy)
chain_steps_min: 2
chain_steps_max: 3
flaw_types:
  - auth_bypass
  - state_confusion
  # Options: auth_bypass, state_confusion, toctou, type_juggling,
  #          encoding_mismatch, implicit_trust, config_manipulation,
  #          privilege_escalation, info_leak, race_condition
---

# Challenge Request

## Narrative
Describe what kind of program this should be.

## Constraints
Any additional constraints.

## Notes
Any other notes.
