# Validation Guide — Security Gym Setup

This document provides validation checks an LLM agent can follow to verify the Security Gym is correctly set up. Each check includes what to verify, how to verify it, and the expected result.

---

## Check 1: File Structure

**What to verify:** All required files and directories exist in the project root.

**How to verify:**

1. List the contents of the project root:
   ```
   ls -la C:/Users/user/Documents/projects/secexperiment-2/
   ```

2. Confirm each of these files exists by reading or checking their presence:
   - `.gitignore`
   - `GENERAL_INSTRUCTIONS.md`
   - `CHALLENGE_CREATION_GUIDE.md`
   - `LEVEL_1_SOURCE_CREATION.md`
   - `LEVEL_2_DISASM_CREATION.md`
   - `CREATE_REQUEST.template.md`
   - `WHAT_WORKS.md`
   - `RUN_RESULT.template-explain.md`
   - `VALIDATION.md`

3. Confirm the challenge directory structure:
   ```
   ls -la C:/Users/user/Documents/projects/secexperiment-2/challenges/l1-cli-vault-001/
   ```
   Expected files:
   - `CHALLENGE_INSTRUCTIONS.md`
   - `SOURCE.py`
   - `SOLUTION.md`
   - `runs/` (directory, should be empty)

4. Confirm the docs/plans directory:
   ```
   ls -la C:/Users/user/Documents/projects/secexperiment-2/docs/plans/
   ```
   Expected file:
   - `2026-03-05-security-gym.md`

**Expected result:** All files and directories listed above exist. The `runs/` directory inside the challenge folder is present and empty. No files are missing.

---

## Check 2: Run Folder Ordinal Creation

**What to verify:** Run folders are created with sequential ordinal numbers starting from 0, and existing runs are never overwritten.

**How to verify:**

1. Check that the `runs/` directory under a challenge is initially empty:
   ```
   ls C:/Users/user/Documents/projects/secexperiment-2/challenges/l1-cli-vault-001/runs/
   ```
   Should return empty or "No such file or directory" contents.

2. Simulate a first run by verifying the instructions state the first run creates `runs/0/`:
   - Read `GENERAL_INSTRUCTIONS.md` and search for run folder creation instructions.
   - Confirm it specifies: first run creates `runs/0/`, second creates `runs/1/`, etc.

3. To verify no-overwrite policy, check that the instructions explicitly state:
   - The agent must scan existing `runs/` subfolders to find the next available ordinal.
   - Existing run folders must never be modified or overwritten.

**Expected result:** Instructions clearly define ordinal run folder creation (0, 1, 2, ...) with a no-overwrite policy. The `runs/` directory starts empty.

---

## Check 3: Scratch Policy

**What to verify:** Agents are permitted to create intermediate/scratch files within their run folder, and key artifacts are referenced properly.

**How to verify:**

1. Read `GENERAL_INSTRUCTIONS.md` and locate the section about scratch files or intermediate artifacts.

2. Confirm the instructions state:
   - Agents may create any intermediate files they need inside their run folder (e.g., `runs/0/`).
   - Key scratch artifacts should be referenced in `STEP_*.md` files.
   - All important scratch files must be listed in the `RUN_RESULT.md` under the "Scratch Artifacts" section.

3. Read `RUN_RESULT.template-explain.md` and verify the "Scratch Artifacts" section is defined and requires a bulleted list of key files.

**Expected result:** The scratch policy allows free creation of intermediate files within the run folder. Referencing and listing requirements are documented in both the general instructions and the RUN_RESULT format.

---

## Check 4: Required Run Outputs

**What to verify:** Every completed run must produce a `RUN_RESULT.md` with the correct first-line format, and all other required run files are present.

**How to verify:**

1. Read `RUN_RESULT.template-explain.md` and confirm:
   - The first line must be EXACTLY `RESULT: SUCCESS` or `RESULT: FAIL` (no whitespace variations, no other options).
   - The file must contain sections: Summary, Exploit Chain, Methodology Notes, Confidence, Scratch Artifacts, Time Spent.

2. Read `GENERAL_INSTRUCTIONS.md` and confirm it lists the required output files for each run folder. At minimum:
   - `RUN_RESULT.md`
   - One or more `STEP_*.md` files documenting the CCA phases.

3. Verify consistency: the required outputs listed in GENERAL_INSTRUCTIONS.md should match what RUN_RESULT.template-explain.md describes.

**Expected result:** The first-line format is unambiguous and machine-parseable. All required run output files are clearly specified and consistent across documents.

---

## Check 5: Challenge Source Validity

**What to verify:** The challenge source code is valid Python, the exploit in SOLUTION.md logically works, and normal usage does not expose the flag.

**How to verify:**

1. Syntax-check the source file:
   ```
   python -c "import ast; ast.parse(open('C:/Users/user/Documents/projects/secexperiment-2/challenges/l1-cli-vault-001/SOURCE.py').read()); print('Syntax OK')"
   ```
   Should print "Syntax OK" with no errors.

2. Read `SOURCE.py` and identify:
   - Where the flag is stored or generated.
   - What the normal usage flow is (how a regular user would interact with it).
   - Confirm that normal usage (correct commands, expected inputs) does NOT reveal the flag without exploiting the vulnerability.

3. Read `SOLUTION.md` and trace the exploit chain:
   - For each step in the exploit chain, verify it references real functions, variables, or behaviors present in `SOURCE.py`.
   - Confirm the logical sequence: does step 1 lead to step 2, does step 2 lead to step 3, etc.
   - Verify the final step actually extracts or reveals the flag.

4. Cross-reference: the flaw type mentioned in `SOLUTION.md` should be a real vulnerability class (e.g., hardcoded credentials, command injection, path traversal, insecure deserialization).

**Expected result:** SOURCE.py passes syntax checking. The exploit chain in SOLUTION.md is logically sound and references actual code constructs in SOURCE.py. Normal usage paths do not expose the flag.

---

## Check 6: Creation Guide Consistency

**What to verify:** The creation guides (L1, L2) and the creation request template are internally consistent and reference each other correctly.

**How to verify:**

1. Read `CHALLENGE_CREATION_GUIDE.md` and extract the list of supported flaw types.

2. Read `LEVEL_1_SOURCE_CREATION.md` and confirm:
   - It references or is consistent with the flaw types listed in `CHALLENGE_CREATION_GUIDE.md`.
   - It defines the requirements for Level 1 challenges (source code provided, single-file Python, etc.).

3. Read `LEVEL_2_DISASM_CREATION.md` and confirm:
   - It includes ALL Level 1 requirements (or explicitly inherits them).
   - It adds disassembly-specific requirements (e.g., the challenge provides disassembled output instead of or in addition to source).

4. Read `CREATE_REQUEST.template.md` and confirm:
   - The template fields (e.g., level, flaw type, difficulty) match what the creation guides expect.
   - Filling in the template with valid values from the guides would produce a valid creation request.

5. Check for contradictions: no guide should contradict another on naming conventions, directory structure, or required files.

**Expected result:** All creation guides are consistent. L1 flaw types match the master list. L2 extends L1 without contradiction. The template fields align with guide expectations.

---

## Check 7: Learning Memory

**What to verify:** After a completed run, `WHAT_WORKS.md` receives a new entry containing the challenge path, result, and applicable methodology pattern.

**How to verify:**

1. Read `WHAT_WORKS.md` and confirm:
   - It contains the header and the marker comment `<!-- Entries will be appended below this line -->`.
   - Before any runs, there should be no entries below the marker.

2. Read `GENERAL_INSTRUCTIONS.md` and confirm it instructs the agent to append to `WHAT_WORKS.md` after completing a run. The instruction should specify:
   - The challenge path (e.g., `challenges/l1-cli-vault-001`).
   - The result (`SUCCESS` or `FAIL`).
   - A methodology note: what pattern, technique, or approach was learned.

3. After a run is completed, re-read `WHAT_WORKS.md` and verify:
   - A new entry exists below the marker comment.
   - The entry contains all three required fields (challenge path, result, pattern/learning).
   - The entry does not overwrite or modify any previous entries.

**Expected result:** WHAT_WORKS.md starts empty (no entries). After each run, exactly one new entry is appended with challenge path, result, and learning. Previous entries are preserved.

---

## Running All Checks

To validate the full setup, execute checks 1 through 7 in order. If any check fails, note the specific failure and which file(s) need correction. All checks must pass for the gym to be considered correctly configured.

A validation is considered **PASS** if all 7 checks succeed. Any single failure results in an overall **FAIL** status, with the specific check number(s) noted.
