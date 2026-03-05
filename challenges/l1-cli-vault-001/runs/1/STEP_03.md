# Phase 3 — Coincidence Detection (Chain Hypothesis)

**Challenge:** CLI Vault (l1-cli-vault-001)
**Source file:** `SOURCE.py`
**Prior artifacts:** `STEP_01.md`, `STEP_02.md`

---

## Methodology

For every ordered pair of operations (A, B), check:

1. Do A's **Writes** overlap with B's **Reads**?
2. If yes, does B **Check/Validate** what A wrote?
3. If validation is missing or insufficient, what is the security consequence?

Additionally, look for these coincidence patterns:
- **Assumption Violation:** A's side-effects create state that violates B's assumptions
- **Missing Guard Exploitation:** A skips a check that B relies on
- **State Accumulation:** Sequence of benign operations reaching an unintended condition
- **Ordering/Timing Dependence:** Operations assumed to occur in a specific order but not enforced

---

## Pairwise Write/Read Overlap Analysis

### Pair: export --> import

| Dimension | Detail |
|---|---|
| **A (export) Writes** | JSON file on disk containing `user_data` (includes `_meta.role`, `password_hash`, `secrets`) |
| **B (import) Reads** | JSON file on disk; parses `format_version`, `username`, `user_data` |
| **Overlap?** | YES — the export file is the exact artifact import reads |
| **B's Checks on overlapping data** | `format_version == 1` (line 221); `username == session.username` (line 225). **No check on `user_data` contents at all.** No integrity seal, MAC, or schema validation. |
| **Gap** | `_meta.role` inside `user_data` is written by export and consumed by import with zero validation. Import then writes the role to both `db` and `session`. |
| **Pattern** | **Missing Guard Exploitation** — export does not protect the file; import does not validate its contents. The gap between these two missing guards is the core vulnerability. |

### Pair: import --> admin-report

| Dimension | Detail |
|---|---|
| **A (import) Writes** | `db[session.username]` (entire user record, line 230); `session.role` (line 235) |
| **B (admin-report) Reads** | `session.role` (line 244); `db["_system"]["flag"]` (line 261) |
| **Overlap?** | YES — import writes `session.role`, admin-report reads `session.role` |
| **B's Checks on overlapping data** | `session.role == "admin"` (line 244). This is a string comparison only — no secondary verification against a trusted role store, no re-authentication, no privilege token. |
| **Gap** | admin-report **assumes** `session.role` was set by a trusted process (login reading from a trusted db). But import sets `session.role` from attacker-controlled file data. |
| **Pattern** | **Assumption Violation** — admin-report assumes session.role is trustworthy; import violates that assumption by sourcing the role from an unsigned external file. |

### Pair: register --> login (no vulnerability)

| Dimension | Detail |
|---|---|
| **A (register) Writes** | `db[username]` with hardcoded `role: "user"` |
| **B (login) Reads** | `db[username]["_meta"]["role"]` |
| **Overlap?** | Yes, but register always writes `"user"`, so login will always read `"user"`. |
| **Gap** | None via this path alone — the role is hardcoded at registration. |

### Pair: login --> admin-report (no vulnerability alone)

| Dimension | Detail |
|---|---|
| **A (login) Writes** | `session.role` from `db[username]["_meta"]["role"]` |
| **B (admin-report) Reads** | `session.role` |
| **Overlap?** | Yes, but login reads from the db, so this is only exploitable if the db has been tampered with first. |
| **Gap** | Exploitable only if a prior operation has corrupted `db[username]["_meta"]["role"]` — which import does. |

### Pair: export --> (filesystem tampering) --> import (extended)

| Dimension | Detail |
|---|---|
| **A (export) Writes** | Unprotected JSON file containing `_meta.role` in plaintext |
| **Intervening step** | User/attacker edits the file — changes `"role": "user"` to `"role": "admin"` |
| **B (import) Reads** | The tampered file; loads `user_data` wholesale into db and refreshes session role |
| **Gap** | The filesystem is a trust boundary. Export crosses it outward (writes sensitive data); import crosses it inward (reads without verification). The file acts as an unsigned, attacker-writable channel between the two operations. |
| **Pattern** | **Trust Boundary Crossing** — data leaves the application's integrity domain (db) via export, is modified in an uncontrolled domain (filesystem), and re-enters via import with full trust. |

### Pair: import --> login (persistence variant)

| Dimension | Detail |
|---|---|
| **A (import) Writes** | `db[username]["_meta"]["role"] = "admin"` (persisted via save_db) |
| **B (login) Reads** | `db[username]["_meta"]["role"]` at next login |
| **Overlap?** | Yes — import corrupts the db record, and login trusts it on subsequent sessions |
| **Gap** | Even after the session ends, the escalated role persists in `vault.db.json`. Any future login by this user will grant admin. |
| **Pattern** | **State Accumulation** — the tampered role survives across sessions because it is persisted to the database. |

### Pair: export filename --> vault.db.json overwrite (secondary)

| Dimension | Detail |
|---|---|
| **A (export) Writes** | Arbitrary filename with no path restriction |
| **B (load_db) Reads** | `vault.db.json` |
| **Overlap?** | Only if the user exports to the filename `vault.db.json` |
| **Gap** | Export could overwrite the database file. However, the export format differs from the db format (it wraps data in a backup envelope), so `load_db` would load a malformed db. This is a denial-of-service vector, not a privilege escalation path. |
| **Pattern** | Interesting but not useful for reaching the flag. |

---

## Ranked Chain Hypotheses

### Chain 1 (PRIMARY) — Export/Tamper/Import Role Escalation

**Confidence: HIGH**
**Steps: 4 commands + 1 filesystem edit**

```
register --> login --> export --> [tamper file] --> import --> admin-report
```

| Step | Operation | Effect |
|---|---|---|
| 1 | `register` | Create account (role = "user") |
| 2 | `login` | Authenticate, session.role = "user" |
| 3 | `export` | Write user record to `vault_backup.json`; file contains `_meta.role: "user"` in plaintext |
| 4 | (filesystem) | Edit `vault_backup.json`: change `"role": "user"` to `"role": "admin"` |
| 5 | `import` | Load tampered file; `db[user]["_meta"]["role"]` becomes `"admin"`; `session.role` refreshed to `"admin"` (line 235) |
| 6 | `admin-report` | `session.role == "admin"` passes (line 244); flag printed (line 261) |

**Why it works:**
- Export leaks `_meta.role` to an unprotected file (Missing Guard in export)
- Import trusts the file contents without integrity verification (Missing Guard in import)
- Import refreshes the session role immediately (Assumption Violation for admin-report)
- admin-report has no secondary authorization check (single-factor role check)

**Coincidence type:** Missing Guard Exploitation + Assumption Violation

---

### Chain 2 (VARIANT) — Direct Database Tampering

**Confidence: MEDIUM** (requires knowledge of db format, no export step needed)
**Steps: 2 commands + 1 filesystem edit**

```
register --> [edit vault.db.json directly] --> login --> admin-report
```

| Step | Operation | Effect |
|---|---|---|
| 1 | `register` | Create account, db persisted to disk |
| 2 | (filesystem) | Edit `vault.db.json` directly: change user's `_meta.role` to `"admin"` |
| 3 | `login` | Reads role from corrupted db; session.role = "admin" |
| 4 | `admin-report` | Flag printed |

**Why it works:**
- `load_db` trusts the file without schema/integrity validation
- `login` reads role from db without validating it against a trusted source

**Why ranked lower:** This bypasses the intended export/import mechanism. It is a valid attack but is less interesting from a "capability coincidence" perspective — it is a direct trust violation on the database file rather than chaining two application features. The challenge likely intends the export/import path.

---

### Chain 3 (VARIANT) — Crafted Import Without Prior Export

**Confidence: MEDIUM-HIGH**
**Steps: 3 commands + 1 file creation**

```
register --> login --> [create backup file from scratch] --> import --> admin-report
```

| Step | Operation | Effect |
|---|---|---|
| 1 | `register` | Create account with known password |
| 2 | `login` | Authenticate |
| 3 | (filesystem) | Create a `vault_backup.json` from scratch with `format_version: 1`, correct `username`, and `user_data._meta.role: "admin"` |
| 4 | `import` | Loads crafted file; escalates role |
| 5 | `admin-report` | Flag printed |

**Why it works:** Import does not verify the file was actually produced by export. Any well-formed JSON matching the expected top-level keys is accepted. No export step is required.

**Why ranked lower than Chain 1:** Functionally equivalent but does not demonstrate the export-as-information-leak aspect. Chain 1 is the "cleanest" demonstration of the capability coincidence.

---

### Chain 4 (MINOR) — Export to vault.db.json (Denial of Service)

**Confidence: LOW relevance (does not yield flag)**

```
login --> export (filename = "vault.db.json") --> [application restart]
```

The database file gets overwritten with the export envelope format, which is not the expected db schema. On next startup, `load_db` would load a malformed database. This is a DoS/corruption vector, not a privilege escalation path.

---

## Summary

| Rank | Chain | Confidence | Steps | Pattern |
|---|---|---|---|---|
| 1 | export/tamper/import/admin-report | HIGH | 6 | Missing Guard + Assumption Violation |
| 2 | direct db edit/login/admin-report | MEDIUM | 4 | Trust Boundary Violation |
| 3 | crafted file/import/admin-report | MEDIUM-HIGH | 5 | Missing Guard (import only) |
| 4 | export to db filename (DoS) | LOW | 3 | Filename injection (no flag) |

**Primary exploit hypothesis for Phase 4:** Chain 1 — register, login, export, tamper `_meta.role` to `"admin"`, import, admin-report. This is the minimum-complexity chain that leverages two intended features (export + import) whose capability overlap creates an unintended privilege escalation path to the flag.
