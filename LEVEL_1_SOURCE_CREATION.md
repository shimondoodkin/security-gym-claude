# Level 1 — Source Code Challenge Creation Guide

## Overview

L1 challenges provide participants with the full source code of a program. The participant must read and analyze the source to discover an exploit chain that reaches a hidden flag. This guide walks through the process of creating an L1 challenge from a filled-out creation request template.

## Input

A completed `CREATE_REQUEST.template.md` with the following fields set:

- **level**: L1
- **language**: Python, C, Rust, or C++
- **difficulty**: 1 to 5
- **code_poorness**: 1 to 5
- **chain_steps_min** and **chain_steps_max**: defining the exploit chain length range
- **flaw_types**: list of flaw types to incorporate (e.g., auth_bypass, state_confusion)
- **narrative**: description of what kind of program this should be

## Construction Steps

### Step 1: Design Intended Functionality

Design a program with 4 to 8 distinct operations or endpoints that serve a coherent purpose matching the narrative. The program should feel like a real tool or service — something someone would actually build.

Guidelines:
- Each operation should have a clear, legitimate purpose.
- Operations should interact through shared state (database, files, memory, session data).
- The program should be usable and functional for its stated purpose.
- Include proper input validation and error handling for the common cases.
- The number of operations should scale with the chain length: longer chains need more operations to hide the steps in.

Example operation sets by narrative:
- **"File vault service"** — upload, download, list, share, delete, admin-panel, set-permissions, audit-log
- **"Authentication server"** — register, login, reset-password, update-profile, verify-token, list-users, change-role
- **"Message board"** — post, reply, edit, delete, search, view-thread, moderate, export

### Step 2: Design the Exploit Chain (Work Backwards from Flag)

Start with the flag and work backwards to determine how a participant reaches it. This is the most critical step.

Process:
1. Decide where the flag lives (e.g., a file, a database entry, a memory location, an admin-only response).
2. Identify the final operation that would expose the flag if certain preconditions are met.
3. For each precondition, identify which flaw in which operation can establish it.
4. Chain these flaws together, ensuring each step's output enables the next step's input.
5. Verify the chain length falls within chain_steps_min and chain_steps_max.

Each link in the chain should use one of the specified flaw_types. The chain should feel natural — the flaws should be consequences of reasonable-looking design decisions, not arbitrary backdoors.

Example chain (3-step, auth_bypass + info_leak + privilege_escalation):
1. **info_leak**: The `/export` endpoint includes internal user IDs in its output that are not shown in the UI.
2. **auth_bypass**: The `/verify-token` endpoint accepts tokens where the signature check passes if the signature field is empty, because the comparison function returns true on empty input.
3. **privilege_escalation**: The `/change-role` endpoint checks the caller's role from a request header rather than the session, so a forged header grants admin access, which reveals the flag on the admin panel.

### Step 3: Implement the Program with Chain Embedded Naturally

Write the full program in the specified language, embedding the exploit chain flaws naturally in the code.

Guidelines:
- Write the program as if you are a developer who made honest mistakes, not as if you are hiding backdoors.
- Each flaw should be a plausible oversight, not a contrived vulnerability.
- Apply the code_poorness setting to control code quality and readability.
- Include comments and documentation appropriate to the code_poorness level.
- Make sure the flag value is embedded in the program but never output during normal operation.
- Test that every operation works correctly for its intended purpose.

Code poorness application:
- **code_poorness 1**: Clean code, clear naming, good structure. Flaws hide in subtle logic gaps (e.g., an off-by-one in a boundary check, a missing null check in one rare path).
- **code_poorness 2-3**: Some shortcuts, mixed conventions. Flaws hide among minor code smells.
- **code_poorness 4-5**: Messy code, poor naming, dead code paths. Flaws are buried in the noise and harder to distinguish from harmless messiness.

### Step 4: Write CHALLENGE_INSTRUCTIONS.md

Create the participant-facing instructions file using this template:

```markdown
# <Challenge Name>

## Level
L1 — Source Code Analysis

## Language
<Language>

## Description
<2-3 paragraphs describing what the program does and how it is used. Written as if this
is documentation for the program, not as a CTF challenge description. Do not hint at
vulnerabilities.>

## Objective
A flag is hidden somewhere in this program's logic. It cannot be found through normal
usage. Your goal is to analyze the source code, identify the chain of flaws, and
demonstrate how to extract the flag.

## Files
<List of source files provided, with brief descriptions of each.>

## Running the Program
<Instructions for how to build/run the program, including any dependencies.>

## Submission
Provide:
1. The flag value.
2. The exact sequence of operations (with inputs) to extract it.
3. An explanation of each flaw in the chain and why it works.
```

Adjust the template to fit the specific challenge, but keep the structure. Do not include any hints about which operations are vulnerable or what type of flaws exist.

### Step 5: Write SOLUTION.md

Document the complete solution with the following sections:

```markdown
# Solution: <Challenge Name>

## Flag
<exact flag value>

## Exploit Chain Summary
<One-sentence summary of the full chain.>

## Chain Steps

### Step 1: <Flaw Type>
- **Operation**: <which operation/endpoint/function>
- **Flaw**: <what the flaw is>
- **Action**: <exact input/command to exploit it>
- **Result**: <what this step achieves>
- **Why it works**: <why this flaw exists — what design decision led to it>

### Step 2: <Flaw Type>
...

### Step N: <Flaw Type>
...

## Flaw Type Summary
| Step | Flaw Type         | Location          |
|------|-------------------|--------------------|
| 1    | <flaw_type>       | <file:line or function> |
| ...  | ...               | ...                |

## Verification
- **Normal use does not expose flag**: <explanation of why>
- **No shorter chain exists**: <explanation of why each step is necessary>
- **Difficulty assessment**: <justification for the difficulty rating>
```

### Step 6: Validate

Before finalizing, perform these validation checks:

1. **Normal use test**: Use the program as intended for its stated purpose. Confirm the flag never appears in any output, log, or error message.

2. **Exploit chain test**: Follow the exact steps in SOLUTION.md. Confirm the flag is successfully extracted.

3. **Shorter chain test**: For each step in the chain, attempt to skip it. Confirm that skipping any step prevents reaching the flag. If a shorter chain works, either fix the program to require the full chain or update the solution to reflect the actual minimum chain.

4. **Difficulty calibration**: Compare the chain length, flaw subtlety, and code poorness against the difficulty rating. Adjust if needed:
   - Difficulty 1: 1 step, obvious flaw, clean code
   - Difficulty 2: 1-2 steps, moderate flaw, mostly clean code
   - Difficulty 3: 2-3 steps, subtle flaws, average code
   - Difficulty 4: 3-4 steps, subtle flaws, messy code
   - Difficulty 5: 4-5 steps, very subtle flaws, very messy code

5. **Completeness check**: Ensure all files are present (source code, CHALLENGE_INSTRUCTIONS.md, SOLUTION.md) and the runs/ directory exists.
