import os
from dataclasses import dataclass

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0"))
    api_id: str = os.getenv("API_ID", "")
    api_hash: str = os.getenv("API_HASH", "")

settings = Settings()
