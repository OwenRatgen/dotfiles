#!/usr/bin/env python3
"""git textconv driver for Raycast .rayconfig files.

Decrypts a .rayconfig to pretty-printed JSON on stdout so `git diff`,
`git log -p`, etc. show meaningful changes. The encrypted file stays the
only thing committed; plaintext is never written to disk or to git.

Password resolution (first hit wins):
  1. $RAYCONFIG_PASSWORD
  2. macOS Keychain generic password, service "raycast-rayconfig"

File format (RAYCFG3):
  8 bytes   magic "RAYCFG3\n"
  4 bytes   little-endian uint32 = length N of the gzip'd metadata block
  N bytes   gzip(JSON metadata, includes encryption.iv / encryption.salt)
  rest      AES-256-GCM ciphertext + 16-byte tag
            key = scrypt(password, salt, N=16384, r=8, p=1, dklen=32)
            nonce = the 16-byte iv
            plaintext = gzip(JSON config)
"""
import sys, os, struct, gzip, json, binascii, subprocess, signal

# Don't traceback if the reader (e.g. a pager) closes the pipe early.
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

def get_password():
    pw = os.environ.get("RAYCONFIG_PASSWORD")
    if pw:
        return pw.encode()
    try:
        out = subprocess.run(
            ["security", "find-generic-password", "-s", "raycast-rayconfig", "-w"],
            capture_output=True, text=True, check=True,
        )
        return out.stdout.strip().encode()
    except Exception:
        sys.stderr.write(
            "rayconfig-textconv: no password. Set $RAYCONFIG_PASSWORD or add a "
            "Keychain item:\n  security add-generic-password -s raycast-rayconfig "
            "-a \"$USER\" -w\n"
        )
        sys.exit(1)

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: rayconfig-textconv.py <file.rayconfig>\n")
        sys.exit(2)
    data = open(sys.argv[1], "rb").read()
    if data[:8] != b"RAYCFG3\n":
        # Not a format we understand; emit raw so diff still shows *something*.
        sys.stdout.buffer.write(data)
        return
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import scrypt

    n = struct.unpack("<I", data[8:12])[0]
    meta = json.loads(gzip.decompress(data[12:12 + n]))
    enc = data[12 + n:]
    iv = binascii.unhexlify(meta["encryption"]["iv"])
    salt = binascii.unhexlify(meta["encryption"]["salt"])
    key = scrypt(get_password(), salt, 32, N=16384, r=8, p=1)
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    inner = cipher.decrypt_and_verify(enc[:-16], enc[-16:])
    obj = json.loads(gzip.decompress(inner))
    json.dump(obj, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")

if __name__ == "__main__":
    main()
