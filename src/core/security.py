import bcrypt
from pydantic import SecretStr
from jwt import encode, decode, ExpiredSignatureError, InvalidTokenError
from datetime import timedelta, timezone, datetime
from core.config import settings
from fastapi import status, HTTPException


def hash_password(plain_pwd: SecretStr):
    salt = bcrypt.gensalt()
    pwd = plain_pwd.get_secret_value().encode()

    hashed_pwd = bcrypt.hashpw(pwd, salt)
    return hashed_pwd.decode()


def verify_password(plain_pwd: SecretStr, hashed_pwd: str) -> bool:
    pwd = plain_pwd.get_secret_value().encode()

    return bcrypt.checkpw(pwd, hashed_pwd.encode())


# JWT


def create_jwt_token(data: dict, expire_delta: None | timedelta = None) -> str:
    to_encode = data.copy()

    if expire_delta:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire_minutes = int(settings.jwt_expire_minutes)
        expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)

    to_encode.update({"exp": expire})
    secret_key = settings.jwt_secret_key
    if not secret_key:
        raise ValueError("SECRET_KEY is not configured in the environment variables")

    algorithm = settings.jwt_algorithm
    encoded_jwt = encode(to_encode, secret_key, algorithm)
    return encoded_jwt


def verify_token(token: str) -> dict:
    try:
        if token.startswith("Bearer "):
            token = token[7:]

        secret_key = settings.jwt_secret_key
        if not secret_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server Configuration Error",
            )

        algorithm = settings.jwt_algorithm
        payload = decode(token, secret_key, algorithms=[algorithm])

        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token Expired"
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Token"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could Not Verify The Credentials",
        )
