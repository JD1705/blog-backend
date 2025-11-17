import bcrypt
from pydantic import SecretStr

def hash_password(plain_pwd: SecretStr):
    salt = bcrypt.gensalt()
    pwd = plain_pwd.get_secret_value().encode()

    hashed_pwd = bcrypt.hashpw(pwd, salt)
    return hashed_pwd

def verify_password(plain_pwd: SecretStr, hashed_pwd: bytes):
    pwd = plain_pwd.get_secret_value().encode()

    verified = bcrypt.checkpw(pwd, hashed_pwd)
    return verified
