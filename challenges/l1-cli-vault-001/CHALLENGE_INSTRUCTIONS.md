# Challenge: CLI Vault

## Level
L1 — Source

## Description
CLI Vault is a simple command-line password vault. Users can:
- **register** a new account with a username and master password
- **login** with credentials
- **store** a secret under a named key
- **retrieve** a secret by key
- **export** their vault to a JSON backup file
- **import** a vault from a JSON backup file
- **admin-report** view system health stats (admin only)

The vault stores data in a local JSON file. Each user has their own namespace.

## Files
- `SOURCE.py` — Complete application source

## Objective
Find the hidden flag. The flag format is `FLAG{...}`.

## Rules
- Analyze the source code to find an unintended sequence of operations that exposes the flag
- The flag cannot be obtained through normal intended use of the program
- Document your methodology and exploit chain
