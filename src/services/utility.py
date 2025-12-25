from fastapi import FastAPI
from core.database import db, create_all_indexes
from contextlib import asynccontextmanager
from unidecode import unidecode
import re


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    await create_all_indexes(db.database)
    yield
    await db.close()


def generate_slug(text: str) -> str:
    """
    convert text into a slug URL friendly
    example: "My Title" -> "my-title"
    """
    # transform to ascii (handle accents)
    text = unidecode(text)

    # make it lowercase
    text = text.lower()

    # replace alphanumeric characters for "-"
    text = re.sub(r"[^a-z0-9\s-]", "", text)

    # replace multiple blank spaces with "-"
    text = re.sub(r"[\s-]+", "-", text)

    # delete "-" at start and end
    text = text.strip("-")

    return text


def verify_unique_slug(slug: str) -> str:
    if not await db.database.posts.find_one({"slug": slug}):
        return slug
    else:
        counter = 1
        while True:
            candidate = f"{slug}-{counter}"
            if not await db.database.posts.find_one({"slug": candidate}):
                return candidate

            counter += 1
