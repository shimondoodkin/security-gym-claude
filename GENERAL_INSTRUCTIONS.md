# Security Gym — General Instructions

## Purpose

The Security Gym is a markdown-first framework designed to train and evaluate LLM agents on their ability to find **unintended logic and flow vulnerabilities** in challenge programs.

**Core Thesis:** LLMs CAN function as security researchers for flow/logic bugs — not just memory corruption bugs or static analysis pattern matching. Logic and flow vulnerabilities require understanding program semantics, state transitions, and the emergent behavior of operation sequences. This is precisely the kind of reasoning LLMs excel at when given structured methodology.

The gym provides structured challenges, each containing a program (source or binary) with a hidden flag. The flag is obtainable **only** through discovering and exploiting an unintended sequence of operations — a logic/flow vulnerability that the program's author embedded deliberately. There is no brute force, no memory corruption, no buffer overflow. The path to the flag runs exclusively through understanding what the program does and finding operation sequences that violate the programmer's assumptions.

---

## Core Methodology: Capability Coincidence Analysis (CCA)

Every challenge is attacked using a five-phase methodology called **Capability Coincidence Analysis (CCA)**. The central insight of CCA is that logic vulnerabilities arise when the *capabilities* of distinct operations *coincidentally* interact in ways the developer did not anticipate. Each phase builds on the prior phase's output.

### Phase 1 — Recon

**Objective:** Map every entry point, command, API endpoint, and user-facing operation the program exposes. Document what each one does at a functional level.

**Process:**
- Read all source code, configuration files, and documentation provided with the challenge.
- Identify every way a user can provide input or trigger behavior (CLI commands, API routes, menu options, file inputs, environment variables, network messages, etc.).
- For each entry point, write a short plain-language description of its intended purpose.
- Note the program's overall architecture: is it a CLI tool, a web app, a service, a game, a file processor?
- Identify the flag format and any hints about where/how the flag is stored or revealed.

**Output:** A complete inventory of entry points with descriptions, plus an architectural summary.

### Phase 2 — Capability Mapping

**Objective:** For each entry point identified in Phase 1, document its precise capabilities in a structured format.

For every entry point, fill out the following table:

| Field | Description |
|---|---|
| **Reads** | What state does this operation read? (files, memory, global variables, config, environment variables, database rows, session data, caches) |
| **Writes** | What state does this operation modify? (files written, variables set, database rows inserted/updated, session fields changed, counters incremented) |
| **Checks** | What validations or guards does it perform before acting? (authentication checks, authorization checks, input validation, bounds checking, type checking, state preconditions) |
| **Skips** | What does it NOT check that it arguably should? (missing authentication on a sensitive path, no validation of a field that other operations assume is validated, no check for concurrent modification, no verification of caller identity) |
| **Assumptions** | What implicit assumptions does it make about prior state? (assumes a file exists, assumes a variable was initialized by a prior operation, assumes the user already authenticated, assumes input was sanitized upstream, assumes operations execute in a particular order) |

**Output:** A complete capability map — one table per entry point — that makes the program's trust model explicit.

### Phase 3 — Coincidence Detection (Chain Hypothesis)

**Objective:** This is the key analytical step. Cross-reference the capability map to find "coincidences" — pairs or chains of operations whose capabilities interact in unintended ways.

**Look for these patterns:**

- **Assumption Violation:** Operation A's side-effects create a state that violates Operation B's assumptions. For example, Operation A writes a config value that Operation B reads without re-validating.
- **Missing Guard Exploitation:** Operation A skips a check that Operation B relies on having been performed. For example, Operation A sets an "authenticated" flag without verifying credentials, and Operation B checks only that flag.
- **State Accumulation:** A sequence of operations, each individually benign, accumulates state that reaches an unintended condition. For example, three operations each add a role, and the combination of roles unlocks admin access.
- **Ordering/Timing Dependence:** The program assumes operations occur in a specific order, but nothing enforces that order. Executing them out of sequence produces unintended behavior.
- **Interleaving/Concurrency:** Two operations that are safe individually produce dangerous behavior when interleaved (TOCTOU, race conditions in state updates).
- **Type Confusion / Encoding Mismatch:** One operation writes data in a format or type that another operation misinterprets, bridging a trust boundary. For example, a string that is valid JSON but also valid as a shell command.

**Process:**
1. For every pair of operations (A, B), check: do A's **Writes** overlap with B's **Reads**? If so, do B's **Checks** validate what A wrote? If not, this is a candidate.
2. For every operation, check: do its **Assumptions** depend on state that any other operation can modify? If so, can that other operation be invoked first to set up a violating state?
3. For every operation's **Skips**, check: does any other operation depend on that skipped check having been performed?
4. Look for chains of length 3+: A enables B enables C, where C reaches the flag.

**Output:** A ranked list of candidate exploit chains. Each chain is an ordered sequence of operations with a rationale explaining why each step enables the next.

### Phase 4 — Exploit Construction

**Objective:** For the highest-ranked chain hypothesis from Phase 3, construct a concrete, executable exploit.

**Process:**
- Write the exact inputs, commands, or requests that must be issued, in order.
- For each step, document the expected state of the program after that step completes (what variables are set, what files exist, what session state looks like).
- Identify the final step that captures or reveals the flag.
- If the exploit requires specific values (magic numbers, computed hashes, crafted payloads), derive them from the source or binary analysis.
- Write the exploit in a form that could be executed: a script, a sequence of curl commands, a series of CLI inputs, etc.

**Output:** A complete, step-by-step exploit with exact inputs and expected intermediate states, culminating in flag capture.

### Phase 5 — Verification & Self-Judgment

**Objective:** Before declaring success, rigorously trace the exploit against the actual source code or disassembly to verify it works.

**Process:**
- Walk through the exploit step by step, tracing execution through the source code or disassembly.
- For each step, verify: does the code actually produce the claimed state change? Cite specific lines or addresses.
- Check for guards that would block the chain: are there hidden checks, error handlers, or state resets that the exploit would trigger?
- Check for ordering constraints: does the program enforce an operation order that the exploit violates?
- Check for side effects: does any step in the chain produce side effects that would disrupt a later step?

**Confidence Rating:**
- **HIGH** — Every step traces cleanly through the code, no blocking guards found, state transitions verified.
- **MEDIUM** — Most steps trace cleanly, but one or two have ambiguity (e.g., an unclear branch condition, an uninspected library call).
- **LOW** — Significant uncertainty in one or more steps, or a potential blocking guard was identified but not resolved.

**If confidence is LOW**, return to Phase 3 and select the next-best chain hypothesis. Repeat Phases 4 and 5.

**Output:** A verification trace with confidence rating, citing specific code locations.

---

## Challenge Levels

### Level 1 — Source

Full source code is provided for the challenge program. The agent can read, search, and analyze all source files directly. Exploit chains are typically **1 to 5 steps** in length. These challenges test the agent's ability to understand program logic and find unintended operation sequences.

**Provided artifacts:**
- Complete source code (all files)
- Build/run instructions
- CHALLENGE_INSTRUCTIONS.md with context and flag format

### Level 2 — Disassembly

Only the compiled binary and/or disassembly artifacts are provided. No source code is available. The author's solution exists but is not provided to the agent. These challenges test the agent's ability to reverse-engineer program behavior from low-level representations and still apply CCA methodology.

**Provided artifacts:**
- Compiled binary and/or disassembly listings
- Runtime environment information
- CHALLENGE_INSTRUCTIONS.md with context and flag format

---

## Manager + Subagent Protocol

The Security Gym operates on a **manager/subagent model**. A manager agent orchestrates the overall run, and subagents execute individual CCA phases. This protocol defines the exact sequence of operations.

### Manager Workflow

1. **Read instructions.** The manager reads this file (`GENERAL_INSTRUCTIONS.md`) and the challenge's `CHALLENGE_INSTRUCTIONS.md`.

2. **Create run folder.** Determine the next ordinal run number for the challenge and create the folder:
   ```
   challenges/<challenge_id>/runs/<n>/
   ```
   where `<n>` is one greater than the highest existing run number (or `1` if no prior runs exist).

3. **Write RUN_DESCRIPTION.md.** Before dispatching any subagents, write a brief description of the approach being taken in this run. Include:
   - What hypothesis or angle is being explored
   - What (if anything) was learned from prior runs
   - Any constraints or focus areas for this attempt

4. **Dispatch subagents sequentially, one per CCA phase.** Each subagent receives:
   - The step objective (what this phase must produce)
   - The expected output artifact path
   - All prior step artifacts (so each subagent has full context of what came before)
   - The challenge root path (for accessing challenge files)

   The subagents execute Phases 1 through 5 in order. Each subagent writes its output to the designated `STEP_<NN>.md` file.

5. **Write EXPLOIT_PATH.md.** After all phases complete, the manager writes a concise summary of the exploit chain (or the best hypothesis if no working exploit was found).

6. **Write RUN_RESULT.md.** The manager writes the final result document (see Run Result Format below).

7. **Update WHAT_WORKS.md.** The manager appends a learning entry to the root-level `WHAT_WORKS.md` file (see Learning Memory below).

### Subagent Handoff Format

When dispatching a subagent, the manager provides context in the following structured format:

```
STEP: <phase_number> — <phase_name>
OBJECTIVE: <what this step must produce>
OUTPUT_PATH: challenges/<id>/runs/<n>/STEP_<NN>.md
PRIOR_ARTIFACTS: <list of paths to prior step outputs>
CHALLENGE_ROOT: challenges/<id>/
```

**Example:**

```
STEP: 1 — Recon
OBJECTIVE: Map every entry point and user-facing operation in the challenge program. Produce a complete inventory with descriptions and an architectural summary.
OUTPUT_PATH: challenges/token-forge/runs/3/STEP_01.md
PRIOR_ARTIFACTS: []
CHALLENGE_ROOT: challenges/token-forge/
```

```
STEP: 3 — Coincidence Detection
OBJECTIVE: Cross-reference the capability map to identify candidate exploit chains. Produce a ranked list of chain hypotheses with rationale.
OUTPUT_PATH: challenges/token-forge/runs/3/STEP_03.md
PRIOR_ARTIFACTS: [challenges/token-forge/runs/3/STEP_01.md, challenges/token-forge/runs/3/STEP_02.md]
CHALLENGE_ROOT: challenges/token-forge/
```

---

## Run Folder Structure

Each run produces the following folder structure:

```
challenges/<challenge_id>/runs/<n>/
  RUN_DESCRIPTION.md
  STEP_01.md
  STEP_02.md
  STEP_03.md
  STEP_04.md
  STEP_05.md
  EXPLOIT_PATH.md
  RUN_RESULT.md
  scratch/  (optional)
```

**File descriptions:**

| File | Description |
|---|---|
| `RUN_DESCRIPTION.md` | Written before the run begins. Describes the approach, hypothesis, and any lessons from prior runs. |
| `STEP_01.md` | Phase 1 — Recon output. Entry point inventory and architectural summary. |
| `STEP_02.md` | Phase 2 — Capability Mapping output. Structured tables for every entry point. |
| `STEP_03.md` | Phase 3 — Coincidence Detection output. Ranked candidate exploit chains with rationale. |
| `STEP_04.md` | Phase 4 — Exploit Construction output. Concrete exploit with exact inputs and expected states. |
| `STEP_05.md` | Phase 5 — Verification output. Step-by-step trace against source/disassembly with confidence rating. |
| `EXPLOIT_PATH.md` | Concise summary of the final exploit chain (or best hypothesis). |
| `RUN_RESULT.md` | Final result document with standardized format (see below). |
| `scratch/` | Optional directory for experimentation files, test scripts, notes, and intermediate work products. |

---

## Run Result Format

The file `RUN_RESULT.md` must follow this exact format. The **first line** is critical and must be machine-parseable.

**First line** (exactly one of):
```
RESULT: SUCCESS
```
```
RESULT: FAIL
```

**Followed by these sections:**

### Summary
A 2-4 sentence summary of the run outcome. What was attempted, what was found (or not found), and the final state.

### Exploit Chain
If successful, the complete exploit chain as an ordered list of operations with brief descriptions. If failed, the best hypothesis that was explored and why it did not work.

### Methodology Notes
Observations about the CCA process during this run. What worked well, what was difficult, where the methodology could be improved. These notes feed back into refining the overall approach.

### Confidence
One of: **HIGH**, **MEDIUM**, or **LOW**.

For SUCCESS results, this reflects confidence that the exploit is correct and reproducible. For FAIL results, this reflects confidence that the explored hypotheses are truly non-viable (HIGH confidence in failure means the agent is confident no exploit exists along the explored paths).

### Scratch Artifacts
A list of any files in the `scratch/` directory and a brief description of each. If no scratch files were created, state "None."

### Time Spent
Approximate wall-clock time for the run, broken down by phase if possible.

**Example:**

```
RESULT: SUCCESS

## Summary
Found a logic vulnerability in the token refresh endpoint that allows privilege escalation. The refresh endpoint copies all claims from the old token without re-validating the role field, allowing a user to manually set an admin role claim that persists through refresh.

## Exploit Chain
1. Register a normal user account (POST /register)
2. Log in and receive a JWT (POST /login)
3. Decode the JWT and modify the "role" claim from "user" to "admin"
4. Submit the modified token to the refresh endpoint (POST /refresh)
5. Use the new valid admin token to access the flag endpoint (GET /admin/flag)

## Methodology Notes
Phase 2 capability mapping was critical — it revealed that /refresh reads claims from the submitted token (not from the database) and skips role validation. Phase 3 immediately identified the coincidence between /login's role assignment and /refresh's role propagation.

## Confidence
HIGH

## Scratch Artifacts
- scratch/decoded_token.json — Example decoded JWT from /login
- scratch/exploit.sh — Shell script implementing the full exploit chain

## Time Spent
- Phase 1 (Recon): ~5 minutes
- Phase 2 (Capability Mapping): ~10 minutes
- Phase 3 (Coincidence Detection): ~5 minutes
- Phase 4 (Exploit Construction): ~8 minutes
- Phase 5 (Verification): ~7 minutes
- Total: ~35 minutes
```

---

## Scratch Workspace Policy

Subagents and the manager need flexibility to experiment during a run. The following policies govern file creation:

- **Agents MAY create any files or folders inside the current run directory** (`challenges/<challenge_id>/runs/<n>/`). This includes the `scratch/` subdirectory and any other files needed for experimentation.
- **Scratch files are encouraged** for experimentation, testing hypotheses, writing helper scripts, storing intermediate outputs, and any other exploratory work.
- **STEP_*.md files must reference important scratch files.** If a scratch file contains a key finding, intermediate result, or supporting evidence, the corresponding STEP file should mention it by path.
- **RUN_RESULT.md must list key scratch artifacts** in its Scratch Artifacts section.
- **Agents must NOT write outside the current run folder**, with one exception: updating the root-level `WHAT_WORKS.md` file (see Learning Memory below). Agents must not modify challenge source files, other runs' folders, or any files outside the Security Gym directory structure.

---

## Learning Memory: WHAT_WORKS.md

The file `WHAT_WORKS.md` in the repository root serves as a persistent learning memory across all challenges and runs. After **every** run (whether SUCCESS or FAIL), the manager appends a new entry.

### Entry Format

Each entry is appended to the end of `WHAT_WORKS.md` with the following structure:

```
---

### <challenge_id> / Run <n> — <RESULT>

- **Path:** challenges/<challenge_id>/runs/<n>/
- **Result:** SUCCESS | FAIL
- **Chain:** <One-line description of the exploit chain or best hypothesis>
- **Key Insight:** <The single most important thing learned from this run>
- **Applicable Pattern:** <A generalized version of the insight that could apply to other challenges>
```

**Example entry:**

```
---

### token-forge / Run 3 — SUCCESS

- **Path:** challenges/token-forge/runs/3/
- **Result:** SUCCESS
- **Chain:** Register -> Login -> Modify JWT role claim -> Refresh token -> Access admin endpoint
- **Key Insight:** The /refresh endpoint copies all claims from the submitted token without re-validating them against the database, allowing claim injection.
- **Applicable Pattern:** Token refresh/reissue endpoints that derive new tokens from old tokens (rather than from authoritative state) are vulnerable to claim injection if the old token's claims are not re-validated.
```

**Guidelines for WHAT_WORKS.md entries:**
- **Be specific** in the Key Insight — reference the actual operations and state involved.
- **Be general** in the Applicable Pattern — abstract away challenge-specific details so the pattern is useful for future challenges.
- **Record failures too** — failed runs often contain valuable information about dead ends and incorrect assumptions.
- The manager should read `WHAT_WORKS.md` at the start of every new run to benefit from prior learnings.
