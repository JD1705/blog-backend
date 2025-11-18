from pydantic_settings import BaseSettings
from pydantic import Field
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # MongoDB configuration
    mongodb_url: str = Field(alias="MONGODB_URL")
    database_name: str = Field("blog_db", alias="DATABASE_NAME")

    # JWT configuration
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(30, alias="JWT_EXPIRE_MINUTES")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings() # type: ignore
