# Phase 5 -- Verification & Self-Judgment

**Challenge:** CLI Vault (l1-cli-vault-001)
**Source file:** `SOURCE.py`
**Prior artifacts:** `STEP_01.md`, `STEP_02.md`, `STEP_03.md`, `STEP_04.md`
**Exploit under verification:** Chain 1 -- register -> login -> export -> tamper -> import -> admin-report

---

## Verification Method

For each exploit step, I trace execution through the source code line by line, verifying:
- The exact code path taken
- The state change produced
- Whether any guard or check blocks the operation
- Whether any side effect disrupts a later step

---

## Step 1: `register` with username=`attacker`, password=`pass1234`

**Entry:** `cmd_register(db, session)` at line 89.

| Line | Code | Verification |
|---|---|---|
| 91 | `username = input("  Username: ").strip()` | Receives `"attacker"`. Non-empty string. |
| 92-93 | `if not username:` | `"attacker"` is truthy. Check passes (not empty). |
| 95-96 | `if username.startswith("_"):` | `"attacker"` does not start with `_`. Check passes. |
| 98-99 | `if username in db:` | On a clean run, `db` contains only `"_system"`. `"attacker"` is not in `db`. Check passes. |
| 102 | `password = input(...)` | Receives `"pass1234"`. |
| 103-104 | `if len(password) < 4:` | `len("pass1234") == 8 >= 4`. Check passes. |
| 107 | `confirm = input(...)` | Receives `"pass1234"`. |
| 108-109 | `if password != confirm:` | Both are `"pass1234"`. Check passes. |
| 112-120 | `db[username] = { ... }` | Creates `db["attacker"]` with `password_hash = sha256("pass1234")`, `secrets = {}`, `_meta.role = "user"`. |
| 121 | `save_db(db)` | Persists to `vault.db.json`. |
| 122 | `print(...)` | Prints success message. |

**Result: PASS.** User record created. `_meta.role` is `"user"`. Database persisted. No side effects that disrupt later steps. Session remains unauthenticated (`session.authenticated = False`).

---

## Step 2: `login` with username=`attacker`, password=`pass1234`

**Entry:** `cmd_login(db, session)` at line 125.

| Line | Code | Verification |
|---|---|---|
| 127 | `username = input(...)` | Receives `"attacker"`. |
| 128 | `if username not in db or username.startswith("_"):` | `"attacker"` IS in `db` (created in Step 1). Does NOT start with `_`. Both conditions are `False`. Check passes. |
| 132 | `password = input(...)` | Receives `"pass1234"`. |
| 133 | `if db[username]["password_hash"] != hash_password(password):` | `db["attacker"]["password_hash"]` is `sha256("pass1234")`. `hash_password("pass1234")` returns the same digest. They are equal. Check passes. |
| 138 | `role = db[username].get("_meta", {}).get("role", "user")` | `db["attacker"]["_meta"]["role"]` is `"user"`. So `role = "user"`. |
| 139 | `session.login(username, role)` | Sets `session.username = "attacker"`, `session.role = "user"`, `session.authenticated = True`. |
| 140 | `print(...)` | Prints `[+] Welcome back, attacker! (role: user)`. |

**Result: PASS.** Session is now authenticated with `role = "user"`. No side effects that disrupt later steps.

---

## Step 3: `export` with filename=`vault_backup.json`

**Entry:** `cmd_export(db, session)` at line 173.

| Line | Code | Verification |
|---|---|---|
| 179 | `if not session.require_auth():` | `session.authenticated = True`. `require_auth()` returns `True`. Check passes. |
| 182 | `filename = input(...)` | Receives `"vault_backup.json"` (or empty for default, same result). |
| 183-184 | `if not filename: filename = "vault_backup.json"` | Filename is set either way. |
| 186 | `user_data = db[session.username]` | `user_data = db["attacker"]` -- the full user record including `_meta.role = "user"`. |
| 187-192 | `backup = { "format_version": 1, ... "user_data": user_data }` | Constructs the backup dict. `user_data` contains `_meta.role: "user"`. |
| 194-195 | `json.dump(backup, f, indent=2)` | Writes the backup to `vault_backup.json`. |
| 196 | `print(...)` | Prints success message. |

**Result: PASS.** File `vault_backup.json` now exists on disk containing the full user record with `_meta.role = "user"` in plaintext. No integrity seal. No side effects on `db` or `session`.

**Critical detail verified:** Line 191 includes `"user_data": user_data` which is a direct reference to `db["attacker"]`. This dict includes the nested `_meta` dict with the `role` field. The JSON serialization writes it all out in plaintext.

---

## Step 4: Tamper with `vault_backup.json` (filesystem operation)

**Operation:** Edit the file to change `"role": "user"` to `"role": "admin"` within `user_data._meta`.

**Verification:** This is a filesystem operation outside the program. The file is a plain JSON text file with no MAC, signature, checksum, or encryption. Any text editor or command-line tool can make this change.

**Guards that could prevent this:**
- None. The file is a regular file on disk. The program performs no integrity verification on import (confirmed in Step 5 below).

**Side effects on running program:** None. The in-memory `db` and `session` objects are not affected by external file changes. The tampered data only enters the program when `import` reads the file.

**Result: PASS.** The file now contains `"role": "admin"`.

---

## Step 5: `import` with filename=`vault_backup.json`

**Entry:** `cmd_import(db, session)` at line 199.

| Line | Code | Verification |
|---|---|---|
| 206 | `if not session.require_auth():` | `session.authenticated = True` (still logged in from Step 2). Check passes. |
| 209 | `filename = input(...)` | Receives `"vault_backup.json"`. |
| 210-211 | `if not filename: filename = "vault_backup.json"` | Filename set. |
| 213-214 | `if not os.path.exists(filename):` | File was created in Step 3 (and tampered in Step 4). Exists. Check passes. |
| 217-218 | `backup = json.load(f)` | Parses the tampered JSON file. `backup["user_data"]["_meta"]["role"]` is now `"admin"`. |
| 221-222 | `if backup.get("format_version") != 1:` | The export wrote `format_version: 1` and we did not change it. `1 == 1`. Check passes. |
| 225-226 | `if backup.get("username") != session.username:` | The export wrote `username: "attacker"` and we did not change it. `session.username` is `"attacker"`. `"attacker" == "attacker"`. Check passes. |
| 230 | `db[session.username] = backup["user_data"]` | **CRITICAL LINE.** Overwrites `db["attacker"]` with the tampered `user_data`. `db["attacker"]["_meta"]["role"]` is now `"admin"`. |
| 231 | `save_db(db)` | Persists the tampered record to `vault.db.json`. The escalated role is now durable. |
| 234 | `new_role = db[session.username].get("_meta", {}).get("role", "user")` | Reads `db["attacker"]["_meta"]["role"]` which is `"admin"`. So `new_role = "admin"`. |
| 235 | `session.role = new_role` | **CRITICAL LINE.** Sets `session.role = "admin"`. The in-memory session now has admin privileges. |
| 236 | `print(...)` | Prints `[+] Vault imported from 'vault_backup.json'. Session refreshed (role: admin).` |

**Result: PASS.** Both the database and the session now reflect `role = "admin"`. No re-authentication was required. No integrity check was performed on the file contents. The only validations were `format_version` and `username` match -- neither protects the `role` field.

**Guards checked:**
- `format_version == 1`: Satisfied (we kept it as-is).
- `username == session.username`: Satisfied (we kept it as-is).
- No other validation exists on the `user_data` contents.

---

## Step 6: `admin-report`

**Entry:** `cmd_admin_report(db, session)` at line 239.

| Line | Code | Verification |
|---|---|---|
| 241 | `if not session.require_auth():` | `session.authenticated = True`. Check passes. |
| 244-245 | `if session.role != "admin":` | `session.role` is `"admin"` (set in Step 5, line 235). `"admin" != "admin"` is `False`. Check passes. |
| 248 | `system_info = db.get("_system", {})` | `db["_system"]` exists (created by `load_db` on first run, line 36-42). Contains `"flag": "FLAG{export_import_role_escalation_ftw}"`. |
| 249-252 | Counts users and secrets. | Informational output, no security relevance. |
| 254-262 | Print report. | Prints the report including line 261: `print(f"  System flag    : {system_info.get('flag', 'N/A')}")` |
| 261 | `system_info.get('flag', 'N/A')` | `system_info["flag"]` is `"FLAG{export_import_role_escalation_ftw}"`. This value is printed. |

**Result: PASS.** The flag `FLAG{export_import_role_escalation_ftw}` is printed to stdout.

---

## Guard/Blocker Analysis

### Could any hidden check block the chain?

| Potential Blocker | Analysis | Verdict |
|---|---|---|
| Session timeout or expiry | The `Session` class has no timeout mechanism. Once `authenticated = True`, it stays true until `logout()` is called or the program exits. | No blocker. |
| Role validation on import | Lines 220-226 validate only `format_version` and `username`. No validation of `_meta.role` value (no whitelist, no enum check). | No blocker. |
| Schema validation on import | Line 230 does `db[session.username] = backup["user_data"]` with no structural validation. Any dict is accepted. | No blocker. |
| Re-authentication on import | Import only calls `require_auth()` which checks `session.authenticated` (a boolean). No password re-verification. | No blocker. |
| Re-authentication on admin-report | Only checks `session.role == "admin"` (line 244). No secondary verification, no re-read from db, no challenge. | No blocker. |
| File integrity check | No MAC, HMAC, signature, or checksum on the export file. | No blocker. |
| Error handler resetting state | No try/except blocks in `cmd_import` that would reset `session.role` on partial failure. The role refresh (line 235) happens after `save_db` (line 231), so even a late exception would leave the db corrupted. | No blocker. |

### Could any ordering constraint prevent the chain?

| Constraint | Analysis | Verdict |
|---|---|---|
| Must register before login | Login checks `username in db` (line 128). Registration creates the db entry. Order is respected in the exploit. | Satisfied. |
| Must login before export | Export calls `require_auth()` (line 179). Login sets `authenticated = True`. Order is respected. | Satisfied. |
| Must export before tamper | The tamper step edits the file created by export. Order is respected. (Note: the exploit would also work with a crafted file from scratch, but the presented chain uses export first.) | Satisfied. |
| Must tamper before import | Import reads the file. If tamper happens after import, the role change would not be loaded. The exploit tampers before import. | Satisfied. |
| Must import before admin-report | Admin-report checks `session.role`. Import sets it to `"admin"`. Order is respected. | Satisfied. |
| No enforced command ordering | The REPL loop (lines 304-323) accepts any command at any time. There is no state machine enforcing command order. | No constraint. |

### Could any side effect disrupt a later step?

| Side Effect | Analysis | Verdict |
|---|---|---|
| `save_db` after register (line 121) | Writes the clean user record. Does not interfere with later steps; the record is needed for login. | No disruption. |
| `save_db` after import (line 231) | Persists the tampered record. This is desirable for the exploit and does not disrupt admin-report. | No disruption. |
| Export writing to disk | Creates `vault_backup.json`. Does not modify `db` or `session`. | No disruption. |
| Import overwriting `db[username]` (line 230) | Replaces the user record. The `password_hash` in the tampered file is the same as the original (we only changed `role`), so if a re-login were required it would still work. | No disruption. |

---

## Confidence Assessment

**Rating: HIGH**

**Justification:**

1. **Every line of code in the exploit path has been traced.** Each operation produces the claimed state change at the cited line numbers.

2. **Every validation check has been enumerated and shown to be satisfied.** The only checks on import are `format_version` (trivially satisfied) and `username` match (trivially satisfied). No check exists on `_meta.role`.

3. **No hidden guards, error handlers, or state resets exist** that would block the chain.

4. **No ordering constraints are enforced** beyond what the exploit naturally satisfies (register before login, login before authenticated commands).

5. **No side effects disrupt subsequent steps.** Each step's state changes are either neutral or directly enabling for the next step.

6. **The flag revelation mechanism is verified.** Line 261 reads from `db["_system"]["flag"]` which is set to `FLAG{export_import_role_escalation_ftw}` at line 40 during `load_db` initialization.

7. **The exploit requires no race conditions, no timing dependencies, and no brute force.** It is a deterministic sequence of 6 operations (4 REPL commands + 1 filesystem edit + 1 REPL command).

---

## Verified Flag

```
FLAG{export_import_role_escalation_ftw}
```

---

## Summary

The exploit chain is **verified to work**. The vulnerability is a classic trust boundary violation: the `export` command writes security-sensitive metadata (`_meta.role`) to an unprotected file on disk, and the `import` command reads it back without integrity verification, then promotes the role to the live session. The `admin-report` command trusts `session.role` as the sole authorization check, completing the privilege escalation path to the flag.

| Step | Command | Key Line(s) | State Change |
|---|---|---|---|
| 1 | `register` | 112-121 | `db["attacker"]` created, `role = "user"` |
| 2 | `login` | 138-139 | `session.role = "user"`, `authenticated = True` |
| 3 | `export` | 186-195 | `vault_backup.json` written with `role: "user"` in plaintext |
| 4 | (tamper) | N/A | File edited: `role: "user"` -> `role: "admin"` |
| 5 | `import` | 230, 231, 234-235 | `db` and `session.role` both set to `"admin"` |
| 6 | `admin-report` | 244, 261 | Role check passes; flag printed |

**Confidence: HIGH** -- No ambiguity remains. The exploit succeeds as described.
