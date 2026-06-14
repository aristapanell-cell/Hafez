import logging
from typing import Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger("release-bot")

file_handler = logging.FileHandler("bot.log")
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

stats = {
    "releases_sent": 0,
    "total_size_bytes": 0,
    "success_rate": 0,
    "total_attempts": 0,
    "successful_attempts": 0
}

def log_info(msg: str) -> None:
    logger.info(msg)

def log_error(msg: str, exc: bool = False) -> None:
    if exc:
        logger.exception(msg)
    else:
        logger.error(msg)

def log_success(repo: str, tag: str) -> None:
    logger.info(f"{repo} | new release sent: {tag}")
    stats["releases_sent"] += 1
    stats["successful_attempts"] += 1

def update_stats(size_bytes: int, success: bool) -> None:
    stats["total_attempts"] += 1
    if success:
        stats["total_size_bytes"] += size_bytes
        stats["successful_attempts"] += 1
    stats["success_rate"] = (stats["successful_attempts"] / stats["total_attempts"]) * 100 if stats["total_attempts"] > 0 else 0

def get_stats() -> dict:
    return stats.copy()
