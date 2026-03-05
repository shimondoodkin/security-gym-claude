# Phase 2 — Capability Mapping

**Challenge:** CLI Vault (l1-cli-vault-001)
**Source file:** `SOURCE.py`
**Prior artifact:** `STEP_01.md`

---

## Global State Overview

Before mapping individual commands, note the two mutable state containers every command interacts with:

| State Object | Type | Description |
|---|---|---|
| `db` | `dict` (in-memory, persisted to `vault.db.json`) | All user records and `_system` metadata including the flag |
| `session` | `Session` instance (in-memory only) | Tracks `username`, `role`, `authenticated` for the current login |

---

## 1. REPL Dispatcher (`main()`, lines 297-327)

| Field | Detail |
|---|---|
| **Reads** | `input()` from stdin (line 306); `COMMANDS` dict (line 318) |
| **Writes** | Nothing directly; delegates to handler |
| **Checks** | Strips and lowercases input (line 306); checks for `quit`/`exit` (line 311); checks for empty input (line 315); checks command exists in `COMMANDS` (line 318) |
| **Skips** | No command-argument parsing -- each handler does its own `input()` calls. No rate limiting. No session timeout. |
| **Assumptions** | All commands are single-word; `db` and `session` are shared mutable references across all handlers. |

---

## 2. `register` (`cmd_register`, lines 89-122)

| Field | Detail |
|---|---|
| **Reads** | `input()` for username (line 91), password (line 102), confirm (line 107); `db` keys to check existence (line 98) |
| **Writes** | `db[username]` -- creates full user record with `password_hash`, empty `secrets`, and `_meta` (lines 112-120); calls `save_db(db)` (line 121) |
| **Checks** | Username non-empty (line 92); username does not start with `_` (line 95); username not already in db (line 98); password >= 4 chars (line 103); password matches confirmation (line 108) |
| **Skips** | No upper-bound on username length. No character-set restriction on username beyond the `_` prefix rule. No password complexity requirements beyond length. No check that user is NOT already logged in (you can register while authenticated). |
| **Assumptions** | Role is always hardcoded to `"user"` (line 116) -- there is no mechanism to register an admin via this path. Assumes `save_db` will succeed (no error handling for disk I/O). |

---

## 3. `login` (`cmd_login`, lines 125-140)

| Field | Detail |
|---|---|
| **Reads** | `input()` for username (line 127) and password (line 132); `db[username]["password_hash"]` (line 133); `db[username]["_meta"]["role"]` via `.get()` chain (line 138) |
| **Writes** | `session.username`, `session.role`, `session.authenticated` via `session.login()` (line 139) |
| **Checks** | Username exists in db AND does not start with `_` (line 128); password hash matches stored hash (line 133) |
| **Skips** | No check for whether user is already logged in -- a second login silently replaces the session. No account lockout after failed attempts. No session token or nonce. |
| **Assumptions** | The `role` value stored in `db[username]["_meta"]["role"]` is trustworthy (line 138). Defaults to `"user"` if `_meta` or `role` key is missing. **This is critical**: the role is read directly from the database at login time with no validation that it is a legitimate value set by a trusted process. |

---

## 4. `store` (`cmd_store`, lines 143-156)

| Field | Detail |
|---|---|
| **Reads** | `session.authenticated` (via `require_auth`, line 145); `input()` for key (line 148) and value (line 153); `session.username` (line 154) |
| **Writes** | `db[session.username]["secrets"][key] = value` (line 154); calls `save_db(db)` (line 155) |
| **Checks** | Authentication required (line 145); key non-empty (line 149) |
| **Skips** | No restriction on key names (could overwrite existing keys silently). No restriction on value content or length. No check that the user record still exists in `db` (could fail if record was deleted externally). |
| **Assumptions** | `db[session.username]` exists and has a `"secrets"` dict. |

---

## 5. `retrieve` (`cmd_retrieve`, lines 159-170)

| Field | Detail |
|---|---|
| **Reads** | `session.authenticated` (via `require_auth`, line 161); `input()` for key (line 163); `db[session.username]["secrets"]` (line 165) |
| **Writes** | Nothing (read-only operation) |
| **Checks** | Authentication required (line 161); key exists in secrets (line 166) |
| **Skips** | No access control beyond "must be logged in" -- any authenticated user can only retrieve their own secrets (which is fine given the data model). |
| **Assumptions** | `db[session.username]` exists and has a `"secrets"` key. |

---

## 6. `export` (`cmd_export`, lines 173-196)

| Field | Detail |
|---|---|
| **Reads** | `session.authenticated` (via `require_auth`, line 179); `input()` for filename (line 182); `session.username` (line 186); entire `db[session.username]` record (line 186) |
| **Writes** | Creates/overwrites an arbitrary file on disk with the JSON backup (lines 194-195). The backup contains: `format_version`, `exported_at`, `username`, and `user_data` (the **complete** user record including `password_hash`, `secrets`, and `_meta` with `role`). |
| **Checks** | Authentication required (line 179) |
| **Skips** | **No integrity seal, MAC, or signature on the exported file.** No restriction on export filename (could overwrite any writable file, including `vault.db.json` itself). No sanitization of the path. Does not exclude sensitive fields from the export (e.g., `_meta.role` is exported in plaintext at line 191). |
| **Assumptions** | The exported file will only be read back by the `import` command and will not be tampered with. **This assumption is false** -- any user with filesystem access can edit the export file before re-importing. |

---

## 7. `import` (`cmd_import`, lines 199-236)

| Field | Detail |
|---|---|
| **Reads** | `session.authenticated` (via `require_auth`, line 206); `input()` for filename (line 209); file contents parsed as JSON (lines 217-218); `backup["format_version"]` (line 221); `backup["username"]` (line 225); `backup["user_data"]` (line 230); `db[session.username]["_meta"]["role"]` after overwrite (line 234) |
| **Writes** | **Overwrites the entire user record**: `db[session.username] = backup["user_data"]` (line 230); calls `save_db(db)` (line 231); **refreshes session role**: `session.role = new_role` (line 235) |
| **Checks** | Authentication required (line 206); file exists on disk (line 213); `format_version == 1` (line 221); `backup["username"] == session.username` (line 225) |
| **Skips** | **No integrity verification** of the imported data (no MAC, signature, or checksum). **No validation of `user_data` structure** -- does not check that `password_hash`, `secrets`, or `_meta` conform to expected schema. **No validation of the `role` field** -- accepts any value including `"admin"`. Does not verify that `user_data._meta.role` matches the original role. Does not check whether `user_data` contains unexpected/malicious keys. |
| **Assumptions** | The `user_data` blob in the backup file has not been tampered with. The `_meta.role` value is legitimate. **Both assumptions are violated by a trivial attack**: export, edit `_meta.role` to `"admin"`, re-import. The session role refresh at line 234-235 ensures the escalated role takes effect immediately without requiring a re-login. |

---

## 8. `admin-report` (`cmd_admin_report`, lines 239-262)

| Field | Detail |
|---|---|
| **Reads** | `session.authenticated` (via `require_auth`, line 241); `session.role` (line 244); `db["_system"]` (line 248); iterates all non-`_`-prefixed keys in `db` for counts (lines 249-252) |
| **Writes** | Nothing (read-only, prints to stdout) |
| **Checks** | Authentication required (line 241); `session.role == "admin"` (line 244) |
| **Skips** | Authorization check relies solely on the in-memory `session.role` string comparison. No secondary verification against a trusted source (e.g., re-reading the role from db and validating it against a whitelist of legitimate admin accounts). |
| **Assumptions** | If `session.role == "admin"`, the user is a legitimate administrator. **This assumption is breakable** because `session.role` can be set to `"admin"` via the import path (line 235) without any cryptographic or structural safeguard. |

---

## 9. `help` (`cmd_help`, lines 265-278)

| Field | Detail |
|---|---|
| **Reads** | Nothing (static output) |
| **Writes** | Nothing (prints to stdout) |
| **Checks** | None |
| **Skips** | N/A |
| **Assumptions** | N/A |

---

## 10. Persistence: `load_db` / `save_db` (lines 30-48)

| Field | Detail |
|---|---|
| **Reads** | `load_db`: reads `vault.db.json` from disk if it exists (lines 32-34); otherwise constructs a fresh db with `_system` and the flag (lines 36-42) |
| **Writes** | `save_db`: writes entire `db` dict to `vault.db.json` as indented JSON (lines 47-48) |
| **Checks** | `load_db`: checks whether file exists via `os.path.exists` (line 32) |
| **Skips** | No file locking (concurrent access could corrupt). No schema validation on load. No integrity verification (a hand-edited `vault.db.json` is trusted). `save_db` has no error handling. |
| **Assumptions** | The JSON file on disk is well-formed and trustworthy. |

---

## 11. `hash_password` (line 51-53)

| Field | Detail |
|---|---|
| **Reads** | Plaintext password string |
| **Writes** | Returns SHA-256 hex digest |
| **Checks** | None |
| **Skips** | No salt. No key stretching (e.g., bcrypt/scrypt). Vulnerable to rainbow table attacks, but not relevant to the logic vulnerability scope. |
| **Assumptions** | Plaintext password is a valid UTF-8 string. |

---

## 12. `Session` class (lines 60-82)

| Field | Detail |
|---|---|
| **Reads** | `self.authenticated` in `require_auth` (line 79) |
| **Writes** | `login()` sets `username`, `role`, `authenticated` (lines 69-71); `logout()` clears them (lines 74-76) |
| **Checks** | `require_auth()` only checks `self.authenticated` boolean (line 79) |
| **Skips** | No validation of role values passed to `login()`. No concept of session expiry. No method to verify session integrity against the database. `role` is a plain string with no enum constraint. |
| **Assumptions** | Callers will only pass legitimate role values. **This assumption is broken** when `cmd_import` refreshes the role from attacker-controlled data (line 235). |

---

## Critical Capability Observations

### Trust Boundary Violations

1. **Export leaks `_meta.role`** (line 191) -- the role field is written to an unprotected file the user controls.
2. **Import trusts `_meta.role`** (line 230) -- the entire `user_data` blob, including role, is loaded from the unprotected file without validation.
3. **Import refreshes session role** (lines 234-235) -- the escalated role takes effect immediately in the running session.

### The Capability Chain

```
export (reads role from db, writes to file)
   --> attacker edits file (changes _meta.role to "admin")
      --> import (reads file, writes role to db AND session)
         --> admin-report (reads session.role, prints flag)
```

Each individual operation behaves "correctly" in isolation. The vulnerability arises from the **combination** of export exposing the role, import trusting the role, and admin-report checking only the session role.
