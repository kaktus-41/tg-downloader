import os

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    API_ID: str = os.getenv("API_ID", "")
    API_HASH: str = os.getenv("API_HASH", "")
    LOCAL_BOT_API_URL: str = os.getenv("LOCAL_BOT_API_URL", "https://api.telegram.org")
    THROTTLING_RATE: int = int(os.getenv("THROTTLING_RATE", "3"))

settings = Settings()
