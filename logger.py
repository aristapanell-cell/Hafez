import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("release-bot")

def log_info(msg):
    logger.info(msg)

def log_error(msg, exc=False):
    if exc:
        logger.exception(msg)
    else:
        logger.error(msg)

def log_success(repo, tag):
    logger.info(f"{repo} | new release sent: {tag}")
