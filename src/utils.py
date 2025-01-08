from datetime import datetime
import json
import logging
from types import SimpleNamespace
import re
import os

class Config(SimpleNamespace):
    @classmethod
    def from_json(cls):
        with open('./config.json', 'r') as config_file:
            data = json.load(config_file)
        return cls(**data)

def format_time_difference(start_time:datetime, end_time:datetime) -> str:
    time_difference = end_time - start_time
    total_seconds = int(time_difference.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def convert_to_mb(size:float, unit:str) -> float:
    match unit.lower():
        case 'b':
            return size / 1024 / 1024
        case 'kb':
            return size / 1024
        case 'mb':
            return size
        case 'gb':
            return size * 1024
        case 'tb':
            return size * 1024 * 1024
        case _:
            raise ValueError(f"Unknown unit: {unit}")

def get_safe_guild_name(guild_name:str | None) -> str:
    if guild_name is None:
        raise ValueError("guild_name was not found")
    safe_name = re.sub(r'[<>:"/\\|?* ]', '_', guild_name).lower()
    if not os.path.exists(f'./files/{safe_name}/'):
        os.makedirs(f'./files/{safe_name}/')
    return safe_name

def get_logger() -> logging.Logger:
    logger = logging.getLogger('float')
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        file_handler = logging.FileHandler('./log.log')
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger

