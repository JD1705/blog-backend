from pymongo import AsyncMongoClient, ASCENDING
from core.config import settings

class Database:
    def __init__(self):
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

    async def setup_database_indexes(self):
        """Configura todos los índices necesarios al iniciar la app"""
        database = self.database.get_collection("token_blacklist") # type: ignore 
    
        # TTL Index para token_blacklist
        await database.token_blacklist.create_index(
            [("expires_at", ASCENDING)],
            expireAfterSeconds=0,
            name="ttl_expires_at"
        )
        
        # Índices únicos para users
        await database.users.create_index(
            [("email", ASCENDING)], 
            unique=True,
            name="unique_email"
        )

        print("\033[32mINFO\033[0m:     Indexes Created")

db = Database()
