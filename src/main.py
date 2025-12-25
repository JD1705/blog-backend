from fastapi import FastAPI
from services.utility import lifespan
from api.routes import auth, users, posts

app = FastAPI(title="Blog API", lifespan=lifespan)

# routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(posts.router)


@app.get("/")
async def root():
    return {"message": "Blog API Running", "status": "OK"}
