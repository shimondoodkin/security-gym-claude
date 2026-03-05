# Phase 1 — Recon: Entry Point Inventory and Architectural Summary

**Challenge:** CLI Vault (l1-cli-vault-001)
**Source file:** `SOURCE.py`

---

## Architectural Summary

CLI Vault is a single-file Python CLI application implementing a password vault. It uses a REPL (read-eval-print loop) that reads commands from stdin, dispatches them to handler functions, and persists all data to a flat JSON file (`vault.db.json`).

**Key components:**

| Component | Description |
|-----------|-------------|
| `vault.db.json` | Flat-file JSON database; holds a `_system` key (with version, creation date, and the flag) plus one key per registered user |
| `Session` class | In-memory object tracking the currently authenticated user's `username`, `role`, and `authenticated` status |
| `load_db()` / `save_db()` | Read/write the JSON database; on first run, initializes `_system` with the flag |
| `hash_password()` | SHA-256 hex digest of a plaintext password |
| `COMMANDS` dict | Maps command strings to handler functions; all handlers receive `(db, session)` |

**Data model per user (stored under `db[username]`):**

```
{
  "password_hash": "<sha256 hex>",
  "secrets": { "<key>": "<value>", ... },
  "_meta": {
    "role": "user",          # or "admin"
    "created_by": "self-register",
    "created_at": "<iso timestamp>"
  }
}
```

**Authentication model:** Password hashes are compared at login. The `role` field is read from `_meta.role` in the database and stored on the in-memory `Session` object. There is no cryptographic integrity protection on user records or exported files.

---

## Entry Point Inventory

### 1. REPL Input (`vault>` prompt)

- **Type:** Top-level command dispatcher
- **Input:** Free-text string from stdin, lowercased and stripped
- **Behavior:** Looks up the command in the `COMMANDS` dict; calls the matching handler or prints an error. Also accepts `quit`/`exit` to terminate.

### 2. `register`

- **Auth required:** No
- **Inputs:** Username, master password, confirm password (all via `input()`)
- **Purpose:** Creates a new user account with role `"user"` and empty secrets
- **Validation:** Username non-empty, must not start with `_`, must not already exist; password >= 4 chars and must match confirmation
- **Side effects:** Writes new user record to `db` and saves to disk

### 3. `login`

- **Auth required:** No
- **Inputs:** Username, password (via `input()`)
- **Purpose:** Authenticates a user and populates the `Session` with username and role
- **Validation:** Username must exist in db and not start with `_`; password hash must match
- **Key detail:** Role is read from `db[username]["_meta"]["role"]` at login time and set on the session

### 4. `store`

- **Auth required:** Yes
- **Inputs:** Secret name (key), secret value (via `input()`)
- **Purpose:** Saves a key-value secret under the authenticated user's record
- **Validation:** Key must be non-empty

### 5. `retrieve`

- **Auth required:** Yes
- **Inputs:** Secret name (key) (via `input()`)
- **Purpose:** Prints the value of a stored secret
- **Validation:** Key must exist in user's secrets dict

### 6. `export`

- **Auth required:** Yes
- **Inputs:** Export filename (via `input()`, defaults to `vault_backup.json`)
- **Purpose:** Writes the entire user record (password hash, secrets, and `_meta` including role) to a JSON file on disk
- **Key detail:** The exported file contains the full `user_data` blob with no integrity seal or signature. The `_meta.role` field is included in plaintext.

### 7. `import`

- **Auth required:** Yes
- **Inputs:** Import filename (via `input()`, defaults to `vault_backup.json`)
- **Purpose:** Restores a user's vault from a previously exported JSON backup file
- **Validation:** `format_version` must equal `1`; `username` in backup must match `session.username`
- **Key detail:** After overwriting `db[session.username]` with the backup's `user_data`, the session role is **refreshed** from the imported data: `session.role = db[session.username]["_meta"]["role"]`. No integrity check is performed on the imported data.

### 8. `admin-report`

- **Auth required:** Yes (and `session.role == "admin"`)
- **Inputs:** None
- **Purpose:** Prints a system health report including vault version, creation date, user/secret counts, and the **system flag**
- **Key detail:** The flag is read from `db["_system"]["flag"]` and printed directly. This is the only command that reveals the flag.

### 9. `help`

- **Auth required:** No
- **Inputs:** None
- **Purpose:** Prints the list of available commands

### 10. `quit` / `exit`

- **Auth required:** No
- **Inputs:** None
- **Purpose:** Exits the REPL loop

---

## Flag Information

- **Flag value:** Stored in the global constant `FLAG` and written into `db["_system"]["flag"]` on first-run initialization
- **Flag format:** `FLAG{...}`
- **Reveal mechanism:** The `admin-report` command prints `db["_system"]["flag"]` — but only if `session.role == "admin"`
- **No user is created with admin role by default.** The `register` command hardcodes `"role": "user"`.

---

## Summary of External I/O Surfaces

| Surface | Direction | Description |
|---------|-----------|-------------|
| `input()` (stdin) | In | All user interaction: commands, usernames, passwords, secret keys/values, filenames |
| `vault.db.json` | In/Out | Persistent database file; read at startup, written after mutations |
| Export file (arbitrary name) | Out | JSON backup of a user's full record including `_meta.role` |
| Import file (arbitrary name) | In | JSON backup read and loaded wholesale into the database without integrity verification |
