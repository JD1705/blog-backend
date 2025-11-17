from core.config import settings
from fastapi import FastAPI
from core.database import db
from services.utility import lifespan

app = FastAPI(title="Blog API", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Blog API Running",
            "status": "OK"}
