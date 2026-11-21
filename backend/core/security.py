import bcrypt

def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt with a generated salt.
    Truncates to 72 bytes as per bcrypt specification.
    """
    if not password:
        return ""
    pwd_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.
    Includes backward-compatible fallback for legacy plaintext passwords.
    """
    if not plain_password or not hashed_password:
        return False
    try:
        # Check if the stored string is a bcrypt hash
        if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
            plain_bytes = plain_password.encode("utf-8")[:72]
            return bcrypt.checkpw(plain_bytes, hashed_password.encode("utf-8"))
        # Fallback for unhashed legacy plaintext
        return plain_password.strip() == hashed_password.strip()
    except Exception:
        return False

