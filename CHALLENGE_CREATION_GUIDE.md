# Challenge Creation Guide

## Overview

This guide describes how to create security challenges for the secexperiment framework. Each challenge presents a program with a hidden flag that can only be reached by discovering and exploiting a chain of subtle flaws in the code.

## Challenge Structure

Every challenge lives in its own directory under `challenges/` and follows this layout:

```
challenges/<challenge_id>/
    CHALLENGE_INSTRUCTIONS.md   # What the participant sees
    source/                     # Source code files (L1) or binary artifacts (L2)
    SOLUTION.md                 # Full exploit chain and rationale (hidden from participants)
    runs/                       # Directory for participant attempt logs and outputs
```

- **CHALLENGE_INSTRUCTIONS.md** — The participant-facing description. It explains what the program does, how to interact with it, and states that a hidden flag exists somewhere. It must not hint at the exploit chain.
- **source/** — Contains the program source code (for L1 challenges) or disassembly artifacts (for L2 challenges). This is the material the participant analyzes.
- **SOLUTION.md** — The full solution write-up. Documents the exact exploit chain, each flaw involved, why the chain works, and the flag value. This file is never shown to participants.
- **runs/** — A directory where outputs from participant attempts are stored for later evaluation.

## Design Principles

### 1. Each operation must look correct in isolation

Every function, endpoint, or code block in the challenge should appear to work correctly when examined on its own. The vulnerability arises only from the combination of multiple operations interacting in unintended ways. A reviewer looking at any single piece should think "this looks fine."

### 2. Flag must be unreachable through intended use

Normal, expected usage of the program must never expose the flag. The flag should only be accessible through a specific sequence of operations that exploits the interaction between flaws. If a user can stumble onto the flag by accident during normal use, the challenge is broken.

### 3. Chain length determines difficulty

The number of steps in the exploit chain is the primary difficulty lever:

- **1 step** — Easy. A single flaw leads directly to the flag.
- **2-3 steps** — Medium. Two or three flaws must be chained together.
- **4-5 steps** — Hard to very hard. Multiple flaws interact across different parts of the program.

Longer chains are harder because the participant must discover each flaw independently and then figure out how they connect.

### 4. Flaw types should be combinable

Challenges should draw from the following flaw types, and the best challenges combine multiple types:

- **auth_bypass** — Circumventing authentication or authorization checks.
- **state_confusion** — Exploiting inconsistent or shared mutable state.
- **toctou** — Time-of-check to time-of-use race conditions.
- **type_juggling** — Exploiting loose type comparisons or implicit type conversions.
- **encoding_mismatch** — Exploiting differences in how data is encoded, decoded, or interpreted.
- **implicit_trust** — Trusting data, headers, or inputs that can be controlled by the attacker.
- **config_manipulation** — Altering configuration values, environment variables, or settings to change program behavior.
- **privilege_escalation** — Moving from a lower privilege level to a higher one through unintended means.
- **info_leak** — Extracting information (keys, internal state, memory contents) that enables further exploitation.
- **race_condition** — Exploiting concurrent operations that lack proper synchronization.

Combining flaw types (e.g., an info_leak that reveals data needed for an auth_bypass) creates more realistic and interesting challenges.

### 5. Code poorness is a dial

The `code_poorness` setting controls how obvious the flaws are at the source level:

- **1 (clean)** — Well-structured, well-commented code with subtle gaps in logic. The flaws are hidden in reasonable-looking design decisions.
- **2** — Mostly clean code with occasional shortcuts or slightly unclear variable naming.
- **3** — Average quality code with some inconsistencies, mixed patterns, and a few questionable practices.
- **4** — Messy code with poor naming, inconsistent error handling, and tangled control flow that makes analysis harder.
- **5 (messy)** — Deliberately hard to read. Buried assumptions, misleading comments, dead code, and convoluted logic. The flaws hide in the noise.

Higher code poorness makes challenges harder to analyze but does not change the underlying exploit chain. It is an orthogonal difficulty axis to chain length.

## Creation Process

1. **Fill the template** — Start by filling out `CREATE_REQUEST.template.md` with the desired parameters: level, language, difficulty, code poorness, chain steps, flaw types, and narrative description.

2. **Follow the level guide** — Use the appropriate level-specific guide:
   - For L1 (source code) challenges: follow `LEVEL_1_SOURCE_CREATION.md`
   - For L2 (disassembly) challenges: follow `LEVEL_2_DISASM_CREATION.md`

3. **Write SOLUTION.md** — Document the complete exploit chain, including each step, the flaw type at each step, why the flaw exists, and the exact commands or inputs needed to reach the flag.

4. **Verify the challenge** — Confirm that:
   - Normal use of the program never exposes the flag.
   - The documented exploit chain works exactly as described.
   - No shorter exploit chain exists that also reaches the flag.
   - The difficulty rating matches the actual chain complexity.

5. **Place in challenges/** — Move the completed challenge into `challenges/<challenge_id>/` with the correct directory structure.
