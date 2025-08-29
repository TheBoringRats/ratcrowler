import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Turso Database Configuration
    TURSO_DATABASE_URL = os.getenv('TURSO_DATABASE_URL')
    TURSO_AUTH_TOKEN = os.getenv('TURSO_AUTH_TOKEN')

    # Fallback to local SQLite if Turso not configured
    USE_TURSO = bool(TURSO_DATABASE_URL and TURSO_AUTH_TOKEN)
    LOCAL_DB_PATH = os.getenv('LOCAL_DB_PATH', 'website_crawler.db')
    BACKLINK_DB_PATH = os.getenv('BACKLINK_DB_PATH', 'backlinks.db')

    MAX_CRAWL_DEPTH = int(os.getenv('MAX_CRAWL_DEPTH', 3))
    MAX_PAGES_PER_DOMAIN = int(os.getenv('MAX_PAGES_PER_DOMAIN', 100))
    USER_AGENT = os.getenv('USER_AGENT', 'ratcrowler/1.0 (+https://github.com/theboringrats/ratcrowler)')

    # Database update settings
    DB_UPDATE_INTERVAL = int(os.getenv('DB_UPDATE_INTERVAL', 3600))  # 1 hour
    ENABLE_AUTO_BACKUP = os.getenv('ENABLE_AUTO_BACKUP', 'true').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.getenv('BACKUP_RETENTION_DAYS', 7))


config = Config()