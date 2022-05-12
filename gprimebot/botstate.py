from dataclasses import dataclass
import hashlib

@dataclass
class BotState:
    next_filename: str
    next_post_time: int
    mode: str
    count: int
