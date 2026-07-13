"""
Password hashing / verification helpers.

The old login flow compared plaintext fields directly (roll number +
DOB, email + name) which isn't real authentication. Moving to
email + password means the `students` and `teachers` tables need a
`password_hash` column (bcrypt hash), e.g.:

    ALTER TABLE teachers ADD COLUMN password_hash TEXT;
    ALTER TABLE students ADD COLUMN password_hash TEXT;

and existing rows need to be backfilled with a hashed password
(e.g. hash_password("temporary123")) before this login will work for them.

Requires: pip install bcrypt
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
