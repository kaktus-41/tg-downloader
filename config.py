import os

class Settings:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
    API_ID: str = os.getenv("API_ID", "")
    API_HASH: str = os.getenv("API_HASH", "")
    THROTTLING_RATE: int = int(os.getenv("THROTTLING_RATE", "3"))
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50 МБ
    PLAYLIST_LIMIT: int = 10

settings = Settings()
