import asyncio
from typing import Type

from pymongo import AsyncMongoClient

from core.config import settings
from models.base import MongoModel


async def create_indexes_for_model(model_class: Type[MongoModel], database):
    """
    Crea todos los índices para un modelo específico.
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
    Crea índices para todos los modelos registrados.
    """
    # from models.comment import Comment  # Futuro
    from models.token import TokenBlacklist

    from models.post import Post
    from models.user import User

    models = [User, Post, TokenBlacklist]  # Agregar más modelos aquí

    print("\033[32mINFO\033[0m:     Creating database indexes...")

    tasks = [create_indexes_for_model(model, database) for model in models]
    await asyncio.gather(*tasks)

    print("\033[32mINFO\033[0m:     Indexes Created")


class Database:
    def __init__(self) -> None:
        self.client = None
        self.database = None

    async def connect(self):
        self.client = AsyncMongoClient(settings.mongodb_url)
        self.database = self.client[settings.database_name]

        await self.client.aconnect()
        print("\033[32mINFO\033[0m:     Connected to MongoDB")

    async def close(self):
        if self.client:
            await self.client.close()
        print("\033[32mINFO\033[0m:     Connection Closed")

    # to DELETE
    # async def setup_database_indexes(self):
    #     """Configura todos los índices necesarios al iniciar la app"""
    #     database = self.database.get_collection("token_blacklist")  # type: ignore
    #
    #     # TTL Index para token_blacklist
    #     await database.token_blacklist.create_index(
    #         [("expires_at", ASCENDING)], expireAfterSeconds=0, name="ttl_expires_at"
    #     )
    #
    #     # Índices únicos para users
    #     await database.users.create_index(
    #         [("email", ASCENDING)], unique=True, name="unique_email"
    #     )
    #
    #     print("\033[32mINFO\033[0m:     Indexes Created")


db = Database()
