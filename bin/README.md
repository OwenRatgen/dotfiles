# Raycast config versioning

`Raycast.rayconfig` is Raycast's encrypted export (scrypt + AES-256-GCM, gzip'd
JSON inside). It's committed as-is — the encrypted blob is the single source of
truth. To get **readable JSON diffs** without ever committing plaintext:

- `bin/rayconfig-textconv.py` — decrypts to JSON on stdout (git textconv driver).
- `.gitattributes` — binds `Raycast.rayconfig` to that driver (`diff=rayconfig`).
- `bin/setup-rayconfig-diff.sh` — run once per clone to activate the driver
  locally and check the password / dependency.

Password comes from `$RAYCONFIG_PASSWORD` or the macOS Keychain item
`raycast-rayconfig` — never from the repo.

## Updating the config
Re-export from Raycast, replace `Raycast.rayconfig`, then `git diff` shows the
JSON changes. Commit as normal.

## ⚠️ Security
This repo is public and the export is only as strong as its password. Use a
strong export password (not a trivial one) so the committed blob can't be
brute-forced. Clipboard history and activity are included in the export.
