import secrets

# Generate a random 64-character hexadecimal key
secret_key = secrets.token_hex(32)

print(secret_key)
