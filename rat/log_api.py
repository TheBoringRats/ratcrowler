"""
Enhanced Log API for RatCrawler
Provides real-time log streaming and monitoring capabilities
"""

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import secrets
from pathlib import Path
import psutil
import logging

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rat.logger import log_manager
from rat.healthcheck import Health
from rat.dblist import DBList

# Initialize FastAPI app
app = FastAPI(
    title="RatCrawler Log API",
    description="Real-time monitoring and logging API for RatCrawler",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security setup
security = HTTPBasic()

# Initialize components
health_checker = Health()
db_list = DBList()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate API access"""
    correct_username = os.getenv("RAT_DASH_USER", "admin")
    correct_password = os.getenv("RAT_DASH_PASSWORD", "password")

    is_correct_username = secrets.compare_digest(credentials.username, correct_username)
    is_correct_password = secrets.compare_digest(credentials.password, correct_password)

    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "RatCrawler Log API",
        "version": "1.0.0",
        "endpoints": {
            "logs": "/logs",
            "logs/recent": "/logs/recent",
            "logs/stream": "/logs/stream",
            "health": "/health",
            "system": "/system",
            "databases": "/databases"
        }
    }

@app.get("/logs/recent")
async def get_recent_logs(
    limit: int = 100,
    level: Optional[str] = None,
    current_user: str = Depends(get_current_user)
):
    """Get recent logs with optional filtering"""
    try:
        if hasattr(log_manager, 'queue_handler'):
            if level:
                logs = log_manager.queue_handler.get_logs_by_level(level, limit)
            else:
                logs = log_manager.queue_handler.get_recent_logs(limit)

            return {
                "status": "success",
                "count": len(logs),
                "logs": logs,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "message": "Log queue handler not available",
                "logs": [],
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "logs": [],
            "timestamp": datetime.now().isoformat()
        }

@app.get("/logs/stream")
async def stream_logs(current_user: str = Depends(get_current_user)):
    """Stream logs in real-time using Server-Sent Events"""
    async def log_generator():
        last_count = 0
        while True:
            try:
                if hasattr(log_manager, 'queue_handler'):
                    current_logs = log_manager.queue_handler.get_recent_logs(10)
                    current_count = len(log_manager.queue_handler.log_queue)

                    if current_count > last_count:
                        # New logs available
                        new_logs = list(log_manager.queue_handler.log_queue)[last_count:]
                        for log in new_logs:
                            yield f"data: {json.dumps(log)}\n\n"
                        last_count = current_count

                await asyncio.sleep(1)  # Check for new logs every second
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        log_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
    )

@app.get("/health")
async def get_health_status(current_user: str = Depends(get_current_user)):
    """Get comprehensive health status"""
    try:
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Database health
        health_checker.useabledbdata()
        useable_crawler = len([db for db in health_checker.useable_databases_crawler if db is not None])
        useable_backlink = len([db for db in health_checker.useable_databases_backlink if db is not None])

        total_crawler = len(health_checker.crawler_databases)
        total_backlink = len(health_checker.backlink_databases)

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": (disk.used / disk.total) * 100,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3)
            },
            "databases": {
                "crawler": {
                    "total": total_crawler,
                    "useable": useable_crawler,
                    "health_percent": (useable_crawler / total_crawler * 100) if total_crawler > 0 else 0
                },
                "backlink": {
                    "total": total_backlink,
                    "useable": useable_backlink,
                    "health_percent": (useable_backlink / total_backlink * 100) if total_backlink > 0 else 0
                }
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/databases")
async def get_database_status(current_user: str = Depends(get_current_user)):
    """Get detailed database status information"""
    try:
        all_databases = []

        # Get crawler databases
        crawler_dbs = db_list.crowldbgrab()
        for db in crawler_dbs:
            try:
                usage = health_checker.current_limit(
                    db['name'],
                    db['organization'],
                    db['apikey']
                )

                storage_used = usage.get('storage_bytes', 0) if usage else 0
                writes_used = usage.get('rows_written', 0) if usage else 0

                all_databases.append({
                    "name": db['name'],
                    "type": "crawler",
                    "organization": db['organization'],
                    "storage_used_gb": storage_used / (1024**3),
                    "storage_limit_gb": db.get('storage_quota_gb', 5),
                    "storage_percent": (storage_used / (db.get('storage_quota_gb', 5) * 1024**3)) * 100,
                    "writes_used": writes_used,
                    "write_limit": db.get('monthly_write_limit', 10000000),
                    "write_percent": (writes_used / db.get('monthly_write_limit', 10000000)) * 100,
                    "status": "healthy" if storage_used < (db.get('storage_quota_gb', 5) * 1024**3 * 0.8) else "warning"
                })
            except Exception as e:
                all_databases.append({
                    "name": db['name'],
                    "type": "crawler",
                    "organization": db['organization'],
                    "status": "error",
                    "error": str(e)
                })

        # Get backlink databases
        backlink_dbs = db_list.backlinkdbgrab()
        for db in backlink_dbs:
            try:
                usage = health_checker.current_limit(
                    db['name'],
                    db['organization'],
                    db['apikey']
                )

                storage_used = usage.get('storage_bytes', 0) if usage else 0
                writes_used = usage.get('rows_written', 0) if usage else 0

                all_databases.append({
                    "name": db['name'],
                    "type": "backlink",
                    "organization": db['organization'],
                    "storage_used_gb": storage_used / (1024**3),
                    "storage_limit_gb": db.get('storage_quota_gb', 5),
                    "storage_percent": (storage_used / (db.get('storage_quota_gb', 5) * 1024**3)) * 100,
                    "writes_used": writes_used,
                    "write_limit": db.get('monthly_write_limit', 10000000),
                    "write_percent": (writes_used / db.get('monthly_write_limit', 10000000)) * 100,
                    "status": "healthy" if storage_used < (db.get('storage_quota_gb', 5) * 1024**3 * 0.8) else "warning"
                })
            except Exception as e:
                all_databases.append({
                    "name": db['name'],
                    "type": "backlink",
                    "organization": db['organization'],
                    "status": "error",
                    "error": str(e)
                })

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "databases": all_databases,
            "summary": {
                "total": len(all_databases),
                "healthy": len([db for db in all_databases if db.get('status') == 'healthy']),
                "warning": len([db for db in all_databases if db.get('status') == 'warning']),
                "error": len([db for db in all_databases if db.get('status') == 'error'])
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/system")
async def get_system_info(current_user: str = Depends(get_current_user)):
    """Get detailed system information"""
    try:
        # Get system information
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "system": {
                "platform": os.name,
                "boot_time": boot_time.isoformat(),
                "uptime_seconds": uptime.total_seconds(),
                "cpu_count": psutil.cpu_count(),
                "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
                "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
            },
            "processes": {
                "total": len(psutil.pids()),
                "running": len([p for p in psutil.process_iter(['status']) if p.info['status'] == 'running'])
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)