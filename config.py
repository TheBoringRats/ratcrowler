import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    MONGODB_URI = os.getenv('MONGODB_URI')
    MAX_CRAWL_DEPTH = int(os.getenv('MAX_CRAWL_DEPTH', 3))
    MAX_PAGES_PER_DOMAIN = int(os.getenv('MAX_PAGES_PER_DOMAIN', 100))
    USER_AGENT = os.getenv('USER_AGENT', 'ratcrowler/1.0 (+https://github.com/swadhinbiswas/ratcrowler)')






config = Config()