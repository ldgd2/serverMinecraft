import bcrypt

password = "123456"
# Hash from the log
stored_hash = "$2b$12$arx8Bra72WwDKERrJrBO4uuiAbqFdNlPR02Id4RxdoMY4yTliUp3S"

result = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
print(f"Match: {result}")

# Generate new hash for 123456
new_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(f"New Hash: {new_hash}")
