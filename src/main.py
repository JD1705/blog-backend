from core.config import settings
from fastapi import FastAPI, status
from core.database import db
from services.utility import lifespan
from api.routes import auth, users

app = FastAPI(title="Blog API", lifespan=lifespan)

# routers
app.include_router(auth.router)
app.include_router(users.router)

@app.get("/")
async def root():
    return {"message": "Blog API Running",
            "status": "OK"}
