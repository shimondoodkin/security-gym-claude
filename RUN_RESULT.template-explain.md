# RUN_RESULT.md Format Specification

Every completed run MUST produce a `RUN_RESULT.md` file in its run folder (e.g., `runs/0/RUN_RESULT.md`). This document explains the exact format.

---

## Format Rules

### First Line (MANDATORY)

The very first line of the file must be EXACTLY one of:

```
RESULT: SUCCESS
```

or

```
RESULT: FAIL
```

No leading/trailing whitespace. No variations. This line is machine-parsed.

### Required Sections

After the first line, the following sections must appear in order:

#### 1. Summary
- 1 to 3 sentences describing what happened during the run.
- What was attempted, what was the outcome.

#### 2. Exploit Chain
- Numbered list of operations that form the exploit, from initial access to flag extraction.
- If no exploit was found, write exactly: `No viable chain found.`

#### 3. Methodology Notes
- Which CCA (Contextualize, Constrain, Attack) phases were most useful.
- What signals or observations led to finding (or failing to find) the vulnerability.
- Any dead ends explored and why they were abandoned.

#### 4. Confidence
- One of: `HIGH`, `MEDIUM`, or `LOW`
- Followed by a brief justification (1-2 sentences).

#### 5. Scratch Artifacts
- Bulleted list of key scratch/intermediate files created during the run.
- Each entry should be a relative path from the run folder and a short description.

#### 6. Time Spent
- Approximate time spent in each CCA phase.
- Format: `Contextualize: Xm | Constrain: Xm | Attack: Xm`

---

## Complete Example: SUCCESS

```markdown
RESULT: SUCCESS

## Summary

Identified a hardcoded XOR key in the authentication routine of SOURCE.py. Used the key to decrypt the stored flag value. The flag was recoverable in a single decryption step.

## Exploit Chain

1. Read SOURCE.py and identified the `authenticate()` function.
2. Found hardcoded XOR key `0xDEADBEEF` on line 42.
3. Located encrypted flag blob in the `FLAG_ENC` constant on line 10.
4. Wrote `decrypt.py` to XOR `FLAG_ENC` with the key.
5. Executed `decrypt.py` and recovered the flag: `FLAG{example_flag_here}`.

## Methodology Notes

- **Contextualize**: Mapped all functions and data flow in SOURCE.py. Identified that authentication was the critical path.
- **Constrain**: Narrowed focus to the `authenticate()` function after noticing it handled both auth and flag storage. Eliminated the CLI parsing and logging code as non-exploitable.
- **Attack**: XOR with a static key is a classic weak-crypto pattern. Wrote a one-shot decryption script.

Signal that led to finding: The XOR key was stored as a named constant rather than derived from user input, indicating it was static and recoverable.

## Confidence

HIGH — The exploit is deterministic (static key, static ciphertext) and was verified by successful decryption.

## Scratch Artifacts

- `decrypt.py` — XOR decryption script used to recover the flag
- `notes.txt` — Initial analysis notes from the Contextualize phase
- `STEP_1.md` — Contextualize phase documentation

## Time Spent

Contextualize: 5m | Constrain: 3m | Attack: 2m
```

---

## Complete Example: FAIL

```markdown
RESULT: FAIL

## Summary

Analyzed SOURCE.py for 15 minutes but was unable to identify a viable exploit chain. The application uses bcrypt for password hashing and the flag is only returned after successful authentication with a password that is not stored in the source.

## Exploit Chain

No viable chain found.

## Methodology Notes

- **Contextualize**: Mapped all entry points. The application takes a username and password, hashes the password with bcrypt, and compares against a hash loaded from an external database file not provided in the challenge.
- **Constrain**: Focused on the authentication bypass possibilities — SQL injection in the username field, timing attacks on the comparison, and potential bcrypt implementation flaws. All were ruled out: username is parameterized, comparison uses `hmac.compare_digest`, and bcrypt is the standard library implementation.
- **Attack**: Attempted brute-force against the bcrypt hash but this is computationally infeasible within the time budget. No shortcut was found.

Dead ends: Spent time investigating whether the database path could be manipulated via environment variables, but the path is hardcoded as an absolute path.

## Confidence

LOW — Confident that the explored attack vectors are not viable, but there may be a flaw in an area not yet examined (e.g., a race condition or an import-time side effect).

## Scratch Artifacts

- `analysis.txt` — Full function-by-function notes
- `STEP_1.md` — Contextualize phase documentation
- `STEP_2.md` — Constrain phase documentation with ruled-out vectors

## Time Spent

Contextualize: 6m | Constrain: 5m | Attack: 4m
```

---

## Parsing Notes for Automation

- To extract the result programmatically, read only the first line and match against `RESULT: SUCCESS` or `RESULT: FAIL`.
- Section headers use `## ` (h2) markdown format.
- The Confidence value is always the first word on the line after the `## Confidence` header.
