from fastapi import FastAPI
from core.database import db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await db.setup_database_indexes()
    yield
    await db.close()
