"""
Enhanced Logging System for RatCrawler
Provides centralized logging with multiple handlers and real-time monitoring
"""

import logging
import logging.handlers
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import queue
import threading
from collections import deque


class LogQueueHandler(logging.Handler):
    """Custom handler that stores logs in a queue for real-time access"""

    def __init__(self, max_logs: int = 1000):
        super().__init__()
        self.log_queue = deque(maxlen=max_logs)
        self.lock = threading.Lock()

    def emit(self, record):
        try:
            # Create a comprehensive log entry
            log_entry = {
                'timestamp': datetime.fromtimestamp(record.created).isoformat(),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'thread': record.thread,
                'thread_name': record.threadName,
                'process': record.process
            }

            # Add any extra attributes
            if hasattr(record, '__dict__'):
                extra_attrs = {k: v for k, v in record.__dict__.items()
                             if k not in ['name', 'msg', 'args', 'levelname', 'levelno',
                                        'pathname', 'filename', 'module', 'lineno',
                                        'funcName', 'created', 'msecs', 'relativeCreated',
                                        'thread', 'threadName', 'processName', 'process']}
                if extra_attrs:
                    log_entry['extra'] = extra_attrs

            with self.lock:
                self.log_queue.append(log_entry)
        except Exception:
            self.handleError(record)

    def get_recent_logs(self, limit: int = 100) -> list:
        """Get recent logs from the queue"""
        with self.lock:
            return list(self.log_queue)[-limit:]

    def get_logs_by_level(self, level: str, limit: int = 100) -> list:
        """Get logs filtered by level"""
        with self.lock:
            filtered_logs = [log for log in self.log_queue if log['level'] == level.upper()]
            return filtered_logs[-limit:]

    def get_logs_by_logger(self, logger_name: str, limit: int = 100) -> list:
        """Get logs filtered by logger name"""
        with self.lock:
            filtered_logs = [log for log in self.log_queue if log['logger'] == logger_name]
            return filtered_logs[-limit:]

    def clear_logs(self):
        """Clear all logs from the queue"""
        with self.lock:
            self.log_queue.clear()


class DatabaseActivityLogger:
    """Logger for database operations"""

    def __init__(self, logger_name: str = "database"):
        self.logger = logging.getLogger(logger_name)

    def log_db_operation(self, operation: str, db_name: str, table: Optional[str] = None,
                        record_count: Optional[int] = None, duration: Optional[float] = None,
                        success: bool = True, error: Optional[str] = None):
        """Log database operations"""
        extra = {
            'db_name': db_name,
            'operation': operation,
            'table': table,
            'record_count': record_count,
            'duration': duration,
            'success': success,
            'category': 'database'
        }

        if success:
            message = f"DB Operation: {operation} on {db_name}"
            if table:
                message += f" table {table}"
            if record_count:
                message += f" ({record_count} records)"
            if duration:
                message += f" in {duration:.2f}s"
            self.logger.info(message, extra=extra)
        else:
            message = f"DB Error: {operation} on {db_name} failed"
            if error:
                message += f" - {error}"
            extra['error_message'] = error
            self.logger.error(message, extra=extra)


class CrawlerActivityLogger:
    """Logger for crawler operations"""

    def __init__(self, logger_name: str = "crawler"):
        self.logger = logging.getLogger(logger_name)

    def log_crawl_start(self, session_id: str, seed_urls: list, config: dict):
        """Log crawl session start"""
        extra = {
            'session_id': session_id,
            'seed_urls': seed_urls,
            'config': config,
            'category': 'crawl_session'
        }

        message = f"Crawl Started: Session {session_id} with {len(seed_urls)} seed URLs"
        self.logger.info(message, extra=extra)

    def log_page_crawl(self, url: str, status_code: int, response_time: float,
                      word_count: Optional[int] = None, success: bool = True, error: Optional[str] = None):
        """Log individual page crawl"""
        extra = {
            'url': url,
            'status_code': status_code,
            'response_time': response_time,
            'word_count': word_count,
            'success': success,
            'category': 'page_crawl'
        }

        if error:
            extra['error_message'] = error

        message = f"Page {'Crawled' if success else 'Failed'}: {url} - {status_code} ({response_time:.2f}s)"
        if word_count:
            message += f" - {word_count} words"

        if success:
            self.logger.info(message, extra=extra)
        else:
            self.logger.warning(message, extra=extra)


class SystemLogger:
    """Logger for system-level events"""

    def __init__(self, logger_name: str = "system"):
        self.logger = logging.getLogger(logger_name)

    def log_service_start(self, service_name: str, port: Optional[int] = None):
        """Log service start"""
        extra = {
            'service_name': service_name,
            'port': port,
            'category': 'service'
        }

        message = f"Service Started: {service_name}"
        if port:
            message += f" on port {port}"

        self.logger.info(message, extra=extra)


class EnhancedLogManager:
    """Enhanced centralized log manager"""

    def __init__(self, log_dir: str = "logs", max_bytes: int = 10485760, backup_count: int = 5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Create queue handler for real-time access
        self.queue_handler = LogQueueHandler(max_logs=2000)

        # Setup logging configuration
        self._setup_logging(max_bytes, backup_count)

        # Initialize specialized loggers
        self.db_logger = DatabaseActivityLogger()
        self.crawler_logger = CrawlerActivityLogger()
        self.system_logger = SystemLogger()

    def _setup_logging(self, max_bytes: int, backup_count: int):
        """Setup comprehensive logging configuration"""
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )

        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        root_logger.addHandler(console_handler)

        # File handlers
        main_file_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "ratcrawler.log",
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        main_file_handler.setLevel(logging.INFO)
        main_file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(main_file_handler)

        # Add queue handler for real-time monitoring
        self.queue_handler.setLevel(logging.INFO)
        self.queue_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(self.queue_handler)

    def get_recent_logs(self, limit: int = 100, level: Optional[str] = None, logger_name: Optional[str] = None):
        """Get recent logs with optional filtering"""
        if logger_name:
            return self.queue_handler.get_logs_by_logger(logger_name, limit)
        elif level:
            return self.queue_handler.get_logs_by_level(level, limit)
        else:
            return self.queue_handler.get_recent_logs(limit)

    def log_startup(self):
        """Log system startup"""
        self.system_logger.log_service_start("RatCrawler")
        logging.getLogger("system").info("RatCrawler logging system initialized")


# Initialize global log manager
log_manager = EnhancedLogManager()

# Initialize logging on import
log_manager.log_startup()
