from pymongo import AsyncMongoClient
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

db = Database()
