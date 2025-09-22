from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str = ""
    db_url: str = "sqlite:///database/monitor.db"

