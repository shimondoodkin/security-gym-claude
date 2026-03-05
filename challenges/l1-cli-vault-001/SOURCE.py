#!/usr/bin/env python3
"""
CLI Vault — A simple command-line password vault.

Features:
  register      Create a new account
  login         Authenticate with username and master password
  store         Save a secret under a named key
  retrieve      Fetch a secret by key
  export        Export your vault to a JSON backup file
  import        Restore your vault from a JSON backup file
  admin-report  View system health stats (admin only)
  help          Show available commands
  quit          Exit the program
"""

import json
import hashlib
import os
from datetime import datetime, timezone

DB_FILE = "vault.db.json"
FLAG = "FLAG{export_import_role_escalation_ftw}"


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def load_db():
    """Load the vault database from disk, or initialize a fresh one."""
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    # First-run initialization
    return {
        "_system": {
            "version": "1.0.0",
            "created": datetime.now(timezone.utc).isoformat(),
            "flag": FLAG,
        }
    }


def save_db(db):
    """Persist the vault database to disk."""
    with open(DB_FILE, "w") as f:
        json.dump(db, f, indent=2)


def hash_password(password):
    """Return the SHA-256 hex digest of *password*."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------

class Session:
    """Tracks the currently authenticated user."""

    def __init__(self):
        self.username = None
        self.role = None
        self.authenticated = False

    def login(self, username, role):
        self.username = username
        self.role = role
        self.authenticated = True

    def logout(self):
        self.username = None
        self.role = None
        self.authenticated = False

    def require_auth(self):
        if not self.authenticated:
            print("[!] You must be logged in to do that.")
            return False
        return True


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_register(db, _session):
    """Create a new user account."""
    username = input("  Username: ").strip()
    if not username:
        print("[!] Username cannot be empty.")
        return
    if username.startswith("_"):
        print("[!] Usernames starting with '_' are reserved.")
        return
    if username in db:
        print("[!] Username already exists.")
        return

    password = input("  Master password: ").strip()
    if len(password) < 4:
        print("[!] Password must be at least 4 characters.")
        return

    confirm = input("  Confirm password: ").strip()
    if password != confirm:
        print("[!] Passwords do not match.")
        return

    db[username] = {
        "password_hash": hash_password(password),
        "secrets": {},
        "_meta": {
            "role": "user",
            "created_by": "self-register",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    }
    save_db(db)
    print(f"[+] Account '{username}' created successfully.")


def cmd_login(db, session):
    """Authenticate an existing user."""
    username = input("  Username: ").strip()
    if username not in db or username.startswith("_"):
        print("[!] Invalid username or password.")
        return

    password = input("  Password: ").strip()
    if db[username]["password_hash"] != hash_password(password):
        print("[!] Invalid username or password.")
        return

    # Set session role from the user's metadata
    role = db[username].get("_meta", {}).get("role", "user")
    session.login(username, role)
    print(f"[+] Welcome back, {username}! (role: {role})")


def cmd_store(db, session):
    """Store a secret under a named key."""
    if not session.require_auth():
        return

    key = input("  Secret name: ").strip()
    if not key:
        print("[!] Key cannot be empty.")
        return

    value = input("  Secret value: ").strip()
    db[session.username]["secrets"][key] = value
    save_db(db)
    print(f"[+] Secret '{key}' stored.")


def cmd_retrieve(db, session):
    """Retrieve a secret by key."""
    if not session.require_auth():
        return

    key = input("  Secret name: ").strip()
    secrets = db[session.username].get("secrets", {})
    if key not in secrets:
        print(f"[!] No secret named '{key}' found.")
        return

    print(f"  {key} = {secrets[key]}")


def cmd_export(db, session):
    """Export the current user's vault to a JSON backup file.

    The export includes the full user record so that a faithful restore is
    possible — passwords, secrets, and account metadata are all preserved.
    """
    if not session.require_auth():
        return

    filename = input("  Export filename [vault_backup.json]: ").strip()
    if not filename:
        filename = "vault_backup.json"

    user_data = db[session.username]
    backup = {
        "format_version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "username": session.username,
        "user_data": user_data,  # full record for faithful backup
    }

    with open(filename, "w") as f:
        json.dump(backup, f, indent=2)
    print(f"[+] Vault exported to '{filename}'.")


def cmd_import(db, session):
    """Import a vault from a JSON backup file.

    The backup must have the correct format_version and the username inside
    the backup must match the currently logged-in user (to prevent one user
    from overwriting another user's data).
    """
    if not session.require_auth():
        return

    filename = input("  Import filename [vault_backup.json]: ").strip()
    if not filename:
        filename = "vault_backup.json"

    if not os.path.exists(filename):
        print(f"[!] File '{filename}' not found.")
        return

    with open(filename, "r") as f:
        backup = json.load(f)

    # Validate backup structure
    if backup.get("format_version") != 1:
        print("[!] Unsupported backup format version.")
        return

    if backup.get("username") != session.username:
        print("[!] Backup username does not match current session.")
        return

    # Restore the full user record from backup
    db[session.username] = backup["user_data"]
    save_db(db)

    # Refresh session role from the (possibly updated) metadata
    new_role = db[session.username].get("_meta", {}).get("role", "user")
    session.role = new_role
    print(f"[+] Vault imported from '{filename}'. Session refreshed (role: {new_role}).")


def cmd_admin_report(db, session):
    """View system health stats. Requires admin privileges."""
    if not session.require_auth():
        return

    if session.role != "admin":
        print("[!] Access denied. Admin privileges required.")
        return

    system_info = db.get("_system", {})
    total_users = sum(1 for k in db if not k.startswith("_"))
    total_secrets = sum(
        len(db[k].get("secrets", {})) for k in db if not k.startswith("_")
    )

    print("=" * 50)
    print("          ADMIN — System Health Report")
    print("=" * 50)
    print(f"  Vault version  : {system_info.get('version', 'unknown')}")
    print(f"  Created        : {system_info.get('created', 'unknown')}")
    print(f"  Total users    : {total_users}")
    print(f"  Total secrets  : {total_secrets}")
    print(f"  System flag    : {system_info.get('flag', 'N/A')}")
    print("=" * 50)


def cmd_help(*_):
    """Show available commands."""
    print()
    print("Available commands:")
    print("  register       Create a new account")
    print("  login          Authenticate with username and master password")
    print("  store          Save a secret under a named key")
    print("  retrieve       Fetch a secret by key")
    print("  export         Export your vault to a JSON backup file")
    print("  import         Restore your vault from a JSON backup file")
    print("  admin-report   View system health stats (admin only)")
    print("  help           Show this help message")
    print("  quit           Exit the program")
    print()


# ---------------------------------------------------------------------------
# REPL
# ---------------------------------------------------------------------------

COMMANDS = {
    "register": cmd_register,
    "login": cmd_login,
    "store": cmd_store,
    "retrieve": cmd_retrieve,
    "export": cmd_export,
    "import": cmd_import,
    "admin-report": cmd_admin_report,
    "help": cmd_help,
}


def main():
    print("=== CLI Vault v1.0 ===")
    print("Type 'help' for available commands.\n")

    db = load_db()
    session = Session()

    while True:
        try:
            command = input("vault> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if command in ("quit", "exit"):
            print("Goodbye!")
            break

        if command == "":
            continue

        handler = COMMANDS.get(command)
        if handler is None:
            print(f"[!] Unknown command: '{command}'. Type 'help' for options.")
            continue

        handler(db, session)


if __name__ == "__main__":
    main()
