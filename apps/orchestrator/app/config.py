
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

class Settings:
    APP_NAME: str = "Block 2 - MCP Orchestrator"

@lru_cache
def get_settings() -> Settings:
    return Settings()
