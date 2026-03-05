RESULT: SUCCESS

## Summary
Found a logic vulnerability in the export/import flow that enables privilege escalation. The export command leaks the user's `_meta.role` field to an unprotected JSON file. The import command restores the full user record from that file without validating the role, and refreshes the session role from the imported data. Tampering the exported file to set `role: "admin"` grants admin access, and the admin-report command reveals the flag.

## Exploit Chain
1. Register a new account (register)
2. Log in with credentials (login)
3. Export vault to JSON file (export) — leaks `_meta.role`
4. Tamper exported file: change `_meta.role` from `"user"` to `"admin"`
5. Import tampered file (import) — overwrites db record, refreshes session role to admin
6. Run admin-report — passes admin check, prints `FLAG{export_import_role_escalation_ftw}`

## Methodology Notes
CCA methodology worked cleanly on this challenge. Phase 2 capability mapping was the critical step — documenting the Skips and Assumptions for export/import immediately revealed that export leaks role data and import trusts it blindly. Phase 3 coincidence detection was almost mechanical once the capability map was complete. The Missing Guard Exploitation pattern (export skips integrity protection, import skips role validation) combined with Assumption Violation (admin-report assumes session.role was set only by login) made the chain obvious.

## Confidence
HIGH

## Scratch Artifacts
- scratch/exploit_inputs.txt — Pre-tamper stdin inputs (register, login, export)
- scratch/exploit_inputs_post_tamper.txt — Post-tamper stdin inputs (import, admin-report, quit)
- scratch/tamper_backup.py — Python script to tamper the exported backup file

## Time Spent
- Phase 1 (Recon): ~55s
- Phase 2 (Capability Mapping): ~80s
- Phase 3 (Coincidence Detection): ~83s
- Phase 4 (Exploit Construction): ~85s
- Phase 5 (Verification): ~89s
- Total: ~6.5 minutes
