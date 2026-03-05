# Level 2 — Disassembly Challenge Creation Guide

## Overview

L2 challenges provide participants with disassembly artifacts instead of source code. The participant must reverse-engineer the binary to understand the program's logic, then discover and exploit a chain of flaws to reach the hidden flag. L2 challenges are inherently harder than L1 because the participant must first reconstruct the program's behavior from low-level representations.

## Input

A completed `CREATE_REQUEST.template.md` with the following fields set:

- **level**: L2
- **language**: C or C++ (restricted to compiled languages)
- **target_arch**: Target architecture (e.g., x86_64)
- **difficulty**: 1 to 5
- **code_poorness**: 1 to 5
- **chain_steps_min** and **chain_steps_max**: defining the exploit chain length range
- **flaw_types**: list of flaw types to incorporate
- **narrative**: description of what kind of program this should be

Note: The language is restricted to C or C++ because L2 challenges require compilation to a native binary. Python and Rust are not supported at this level. Rust may be considered in the future but its debug info and decompilation characteristics require separate handling.

## Construction Steps

### Step 1: Build as L1 First, Verify Exploit

Before creating the disassembly artifacts, build the challenge as a fully working L1 challenge:

1. Follow all steps in `LEVEL_1_SOURCE_CREATION.md` (Steps 1 through 6).
2. Write the complete source code in C or C++.
3. Verify the exploit chain works at the source level.
4. Confirm all validation checks pass.

This ensures the underlying challenge is sound before adding the reverse-engineering layer. The L1 source and solution serve as the ground truth for the L2 challenge.

### Step 2: Compile and Extract Artifacts

Compile the source code and generate the disassembly artifacts that participants will receive.

#### Compilation

Compile the program with settings appropriate to the difficulty level:

```bash
# Basic compilation (difficulty 1-2): minimal optimization, some debug symbols stripped
gcc -O0 -o challenge challenge.c
strip --strip-debug challenge

# Moderate compilation (difficulty 3): optimization enabled, fully stripped
gcc -O2 -o challenge challenge.c
strip --strip-all challenge

# Hard compilation (difficulty 4-5): high optimization, LTO, fully stripped
gcc -O2 -flto -o challenge challenge.c
strip --strip-all challenge
```

Adjust compiler flags based on the challenge. Higher optimization levels make decompilation harder because the compiler may reorder, inline, or eliminate code.

#### Extract Disassembly Artifacts

Generate the following artifacts from the compiled binary:

1. **Stripped binary** — The compiled executable with symbols removed.

   ```bash
   cp challenge challenge.stripped
   ```

2. **Objdump disassembly** — Full disassembly listing from objdump.

   ```bash
   objdump -d -M intel challenge.stripped > disasm.txt
   ```

3. **Decompiler pseudo-code** — Pseudo-C output from a decompiler (Ghidra, IDA, or similar). This gives participants a higher-level view but with decompiler artifacts (generated variable names, reconstructed control flow, etc.).

   ```bash
   # Using Ghidra headless analyzer (example)
   analyzeHeadless /tmp/ghidra_project project_name \
     -import challenge.stripped \
     -postScript ExportDecompiled.java \
     -scriptPath /path/to/scripts
   ```

   If a decompiler is not available, this artifact may be omitted, but its inclusion is strongly recommended for difficulty levels 1-3.

4. **Strings output** — Extracted strings from the binary.

   ```bash
   strings challenge.stripped > strings.txt
   ```

### Step 3: Package in Challenge Directory

Organize the challenge artifacts in the following directory structure:

```
challenges/<challenge_id>/
    CHALLENGE_INSTRUCTIONS.md
    SOLUTION.md
    disasm/
        challenge.stripped          # The stripped binary
        disasm.txt                 # objdump disassembly
        decompiled.c               # Decompiler pseudo-code (if available)
        strings.txt                # Extracted strings
    runs/
```

Note that for L2 challenges, the `disasm/` directory replaces the `source/` directory used in L1 challenges. The original source code is NOT provided to participants — it is kept only in SOLUTION.md for reference.

### Step 4: Write CHALLENGE_INSTRUCTIONS.md

Create the participant-facing instructions file specifying this is an L2 challenge:

```markdown
# <Challenge Name>

## Level
L2 — Disassembly Analysis

## Architecture
<target_arch, e.g., x86_64>

## Description
<2-3 paragraphs describing what the program does and how it is used. Written as if this
is documentation for the program. Do not hint at vulnerabilities. The description should
give enough context for the participant to understand the program's purpose without
having source code.>

## Objective
A flag is hidden somewhere in this program's logic. It cannot be found through normal
usage. Your goal is to reverse-engineer the binary, identify the chain of flaws, and
demonstrate how to extract the flag.

## Provided Artifacts
- `disasm/challenge.stripped` — Stripped ELF binary (<target_arch>)
- `disasm/disasm.txt` — Objdump disassembly (Intel syntax)
- `disasm/decompiled.c` — Decompiler pseudo-code output (if provided)
- `disasm/strings.txt` — Extracted strings

## Running the Program
<Instructions for how to run the binary, including any dependencies or environment
setup needed.>

## Submission
Provide:
1. The flag value.
2. The exact sequence of operations (with inputs) to extract it.
3. An explanation of each flaw in the chain, referencing specific addresses or
   decompiled functions.
```

### Step 5: Write SOLUTION.md

The SOLUTION.md for L2 challenges includes everything from an L1 solution plus additional reverse-engineering context:

```markdown
# Solution: <Challenge Name>

## Flag
<exact flag value>

## Original Source Code
<The complete original C/C++ source code used to build the binary. This is the ground
truth that participants do not have access to.>

## Compiler Flags
<Exact compiler command used, e.g.:>
```
gcc -O2 -o challenge challenge.c
strip --strip-all challenge
```

## Exploit Chain Summary
<One-sentence summary of the full chain.>

## Chain Steps

### Step 1: <Flaw Type>
- **Operation**: <which operation/function>
- **Flaw**: <what the flaw is>
- **Action**: <exact input/command to exploit it>
- **Result**: <what this step achieves>
- **Why it works**: <why this flaw exists>

### Step 2: <Flaw Type>
...

### Step N: <Flaw Type>
...

## Key Addresses and Symbols

| Symbol / Function     | Address (in stripped binary) | Purpose                     |
|-----------------------|-----------------------------|-----------------------------|
| main                  | 0x<addr>                    | Entry point                 |
| <function_name>       | 0x<addr>                    | <brief description>         |
| <flag_location>       | 0x<addr>                    | Where the flag is stored    |
| ...                   | ...                         | ...                         |

## Source-to-Disassembly Mapping

For each critical section of the exploit chain, provide the mapping between the original
source code and the corresponding disassembly or decompiled output:

### Chain Step 1: <Flaw Type>

**Original source (lines X-Y):**
```c
<relevant source snippet>
```

**Corresponding disassembly (addresses 0xAAAA-0xBBBB):**
```asm
<relevant disassembly snippet>
```

**Decompiler output:**
```c
<relevant decompiler pseudo-code>
```

**Notes**: <Any observations about how the compiler transformed the code, optimizations
that obscure the flaw, or decompiler artifacts that might mislead the participant.>

### Chain Step 2: <Flaw Type>
...

## Flaw Type Summary
| Step | Flaw Type         | Source Location   | Binary Address |
|------|-------------------|-------------------|----------------|
| 1    | <flaw_type>       | <file:line>       | 0x<addr>       |
| ...  | ...               | ...               | ...            |

## Verification
- **Normal use does not expose flag**: <explanation>
- **No shorter chain exists**: <explanation>
- **Difficulty assessment**: <justification, including reverse-engineering overhead>
```

## Additional Considerations for L2 Challenges

### Difficulty Adjustment

L2 challenges are inherently harder than their L1 equivalents because participants must reverse-engineer the binary before they can even begin to analyze the logic. Account for this when setting the difficulty:

- An L1 challenge rated difficulty 3 might become difficulty 4 or 5 at L2 depending on optimization level and binary complexity.
- Consider providing the decompiler pseudo-code for lower difficulty L2 challenges (1-3) to reduce the reverse-engineering barrier.
- For higher difficulty L2 challenges (4-5), consider omitting the decompiler output or using higher optimization levels.

### Anti-Shortcut Measures

Ensure participants cannot bypass the reverse-engineering step:

- The flag should not appear in the strings output. Use runtime construction, encoding, or derivation to build the flag value.
- Avoid hardcoded flag strings that would be visible with a simple `strings` command.
- Consider deriving the flag from program state so that static analysis alone is insufficient — the participant must understand the dynamic behavior.

### Compiler Optimization Awareness

Be aware of how compiler optimizations can affect the challenge:

- Dead code elimination may remove code paths you intended to keep.
- Function inlining may merge functions that were separate in the source, changing the challenge structure.
- Constant folding may pre-compute values you wanted to remain as runtime computations.
- Always verify the compiled binary still contains the full exploit chain by testing the exploit against the binary, not just the source.
