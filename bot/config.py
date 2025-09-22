from dataclasses import dataclass

@dataclass
class Config:
    bot_token: str = "8472752376:AAG28MxpSCQPFltLYFQTJiatoBKitMGNEeo"
    db_url: str = "sqlite:///database/monitor.db"
