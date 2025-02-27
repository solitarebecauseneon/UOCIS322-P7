from passlib.hash import sha256_crypt as pwd_context


def hash_password(password):
    """returns hashed password for user_db storage"""
    pwd_context.encrypt(password, salt='abcdefgh12345678')


def verify_password(password, hashVal):
    """returns true if password hash present in user_db, false otherwise"""
    return pwd_context.verify(password, hashVal)
