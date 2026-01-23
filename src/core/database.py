import asyncio
from typing import Type

from pymongo import AsyncMongoClient

from core.config import settings
from models.base import MongoModel


async def create_indexes_for_model(model_class: Type[MongoModel], database):
    """
    Create all the indexes for an especific model.
    """
    collection_name = model_class.get_collection_name()
    indexes = model_class.get_indexes()

    if not indexes:
        print(f"⚠️  No indexes defined for {collection_name}")
        return

    try:
        collection = database[collection_name]

        # Verificar índices existentes
        existing_indexes = await collection.index_information()
        existing_names = set(existing_indexes.keys())

        # Crear nuevos índices
        created_count = 0
        for index in indexes:
            # El índice '_id' siempre existe, lo saltamos
            if index.document.get("name") == "_id_":
                continue

            if index.document.get("name") not in existing_names:
                await collection.create_indexes([index])
                created_count += 1

        if created_count > 0:
            print(
                f"\033[32mINFO\033[0m:     Created {created_count} indexes for {collection_name}"
            )
        else:
            print(
                f"\033[32mINFO\033[0m:     All indexes already exist for {collection_name}"
            )

    except Exception as e:
        print(
            f"\033[32mINFO\033[0m:     Error creating indexes for {collection_name}: {e}"
        )


async def create_all_indexes(database):
    """
    Create indexes for all the registered models.
    """
    from models.comment import Comment
    from models.token import TokenBlacklist

    from models.post import Post
    from models.user import User

    models = [User, Post, TokenBlacklist, Comment]  # Add more models here

    print("\033[32mINFO\033[0m:     Creating database indexes...")

    tasks = [create_indexes_for_model(model, database) for model in models]
    await asyncio.gather(*tasks)

    print("\033[32mINFO\033[0m:     Indexes Created")


class Database:
    def __init__(self) -> None:
        self.client = None
        self.database = None
        self.users = None
        self.posts = None
        self.comments = None
        self.token_blacklist = None

    async def connect(self):
        self.client = AsyncMongoClient(settings.mongodb_url)
        self.database = self.client[settings.database_name]
        self.users = self.database.users
        self.posts = self.database.posts
        self.comments = self.database.comments
        self.token_blacklist = self.database.token_blacklist

        await self.client.aconnect()
        print("\033[32mINFO\033[0m:     Connected to MongoDB")

    async def close(self):
        if self.client:
            await self.client.close()
        print("\033[32mINFO\033[0m:     Connection Closed")


db = Database()
