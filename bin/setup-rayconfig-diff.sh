#!/usr/bin/env bash
# One-time per clone: activate the readable-JSON diff driver for Raycast.rayconfig.
# The driver itself (bin/rayconfig-textconv.py) and the .gitattributes binding are
# committed; only this local git config and the Keychain password are per-machine.
set -euo pipefail
repo="$(cd "$(dirname "$0")/.." && pwd)"

git -C "$repo" config diff.rayconfig.textconv "$repo/bin/rayconfig-textconv.py"
git -C "$repo" config diff.rayconfig.cachetextconv false
echo "✓ git diff driver 'rayconfig' activated"

if security find-generic-password -s raycast-rayconfig -w >/dev/null 2>&1; then
  echo "✓ Keychain item 'raycast-rayconfig' already present"
else
  echo "→ Add the export password to your login Keychain:"
  echo "    security add-generic-password -s raycast-rayconfig -a \"\$USER\" -w"
  echo "  (or set \$RAYCONFIG_PASSWORD in your shell)"
fi

# Requires pycryptodome for scrypt + AES-GCM.
if ! python3 -c 'import Crypto' >/dev/null 2>&1; then
  echo "→ Install the crypto dependency:  python3 -m pip install --user pycryptodome"
fi
