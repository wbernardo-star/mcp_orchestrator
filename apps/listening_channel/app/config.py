
import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Block 1 - Listening Channel"
    ORCHESTRATOR_URL: str = os.getenv(
        "LISTENING_CHANNEL_ORCHESTRATOR_URL",
        "http://localhost:7002/orchestrate",  # default for local dev
    )

@lru_cache
def get_settings() -> Settings:
    return Settings()
