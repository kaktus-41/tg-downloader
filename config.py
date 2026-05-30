import os
from dataclasses import dataclass

@dataclass
class Settings:
    bot_token: str = os.getenv("BOT_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0"))
    api_id: str = os.getenv("API_ID", "")
    api_hash: str = os.getenv("API_HASH", "")
    local_bot_api_url: str = os.getenv("LOCAL_BOT_API_URL", "https://api.telegram.org")

settings = Settings()
