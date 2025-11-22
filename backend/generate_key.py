#!/usr/bin/env python3
"""Generate encryption key for mail-mind"""

from app.encryption import generate_master_key

if __name__ == "__main__":
    key = generate_master_key()
    print("Generated encryption key:")
    print(key)
    print("\nAdd this to your .env file as:")
    print(f"ENCRYPTION_KEY={key}")

