"""
Log API Server for RatCrawler
Provides REST endpoints for accessing logs programmatically
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import uvicorn
from pathlib import Path
import json
import os
from datetime import datetime
from rat.logger import log_manager

app = FastAPI(title="RatCrawler Log API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def read_logs_from_file(limit: int = 100) -> List[Dict]:
    """Read recent logs from the rotating log file on disk"""
    log_file = Path('logs') / 'ratcrawler.log'
    if not log_file.exists():
        return []

    try:
        # Read last N lines efficiently
        with open(log_file, 'rb') as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 1024
            data = b''
            while size > 0 and data.count(b'\n') <= limit:
                read_size = min(block, size)
                f.seek(size - read_size)
                data = f.read(read_size) + data
                size -= read_size

        lines = data.decode('utf-8', errors='ignore').splitlines()[-limit:]
        parsed = []
        for line in lines:
            try:
                # Parse log line format: timestamp - logger - level - module:lineno - message
                parts = line.split(' - ', 4)
                if len(parts) >= 4:
                    timestamp = parts[0].strip()
                    logger_name = parts[1].strip()
                    level = parts[2].strip()
                    message = parts[-1].strip()
                else:
                    timestamp = ''
                    logger_name = ''
                    level = 'INFO'
                    message = line

                parsed.append({
                    'timestamp': timestamp,
                    'logger': logger_name,
                    'level': level,
                    'message': message,
                    'module': '',
                    'function': '',
                    'line': None
                })
            except Exception:
                parsed.append({'timestamp': '', 'logger': '', 'level': 'INFO', 'message': line})

        return parsed
    except Exception:
        return []

@app.get("/logs", response_model=List[Dict])
async def get_logs(
    limit: int = Query(100, description="Number of logs to return", ge=1, le=1000),
    level: Optional[str] = Query(None, description="Filter by log level (DEBUG, INFO, WARNING, ERROR)"),
    source: str = Query("auto", description="Log source: 'memory' for in-memory logs, 'file' for file logs, 'auto' for automatic selection")
):
    """
    Get recent logs from the system.

    - **limit**: Number of logs to return (1-1000)
    - **level**: Filter by specific log level
    - **source**: Which log source to use
    """
    try:
        if source == "memory":
            # Get logs from memory
            if level and level.upper() != "ALL":
                logs = log_manager.get_logs_by_level(level.upper(), limit)
            else:
                logs = log_manager.get_recent_logs(limit)
        elif source == "file":
            # Get logs from file
            logs = read_logs_from_file(limit)
            if level and level.upper() != "ALL":
                logs = [log for log in logs if log['level'] == level.upper()]
        else:
            # Auto mode: try memory first, fall back to file
            if level and level.upper() != "ALL":
                logs = log_manager.get_logs_by_level(level.upper(), limit)
            else:
                logs = log_manager.get_recent_logs(limit)

            # If no logs in memory, try file
            if not logs:
                logs = read_logs_from_file(limit)
                if level and level.upper() != "ALL":
                    logs = [log for log in logs if log['level'] == level.upper()]

        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving logs: {str(e)}")

@app.get("/logs/stats")
async def get_log_stats():
    """Get log statistics"""
    try:
        # Try to get stats from log manager
        try:
            stats = log_manager.get_log_stats()
        except Exception:
            stats = {'total_logs': 0, 'logs_by_level': {}, 'recent_errors': [], 'recent_warnings': []}

        # If no stats from memory, try to get from file
        if stats.get('total_logs', 0) == 0:
            file_logs = read_logs_from_file(1000)
            logs_by_level = {}
            recent_errors = []
            recent_warnings = []

            for entry in file_logs:
                lvl = entry.get('level', 'INFO')
                logs_by_level[lvl] = logs_by_level.get(lvl, 0) + 1
                if lvl == 'ERROR':
                    recent_errors.append(entry)
                if lvl == 'WARNING':
                    recent_warnings.append(entry)

            stats = {
                'total_logs': len(file_logs),
                'logs_by_level': logs_by_level,
                'recent_errors': recent_errors[-10:],
                'recent_warnings': recent_warnings[-10:]
            }

        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving log stats: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "RatCrawler Log API"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
