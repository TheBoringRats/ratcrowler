# RatCrawler Enhanced Monitoring & Dashboard

## Overview

This enhanced monitoring system provides comprehensive logging, real-time dashboard, and improved database monitoring for the RatCrawler project.

## Features

### 🪵 Enhanced Logging System (`rat/logger.py`)

- **Centralized Logging**: All components use a unified logging system
- **Real-time Log Queue**: Logs are stored in memory for real-time access
- **Multiple Handlers**: File, console, and queue handlers
- **Database Operation Logging**: Automatic logging of all database operations
- **Crawler Activity Logging**: Detailed logging of crawling activities
- **Log Export**: Export logs to JSON format
- **Log Statistics**: Real-time log analysis and statistics

### 📊 Streamlit Dashboard (`dashboard.py`)

- **Real-time Monitoring**: Live updates of system status
- **Database Status**: Comprehensive database health monitoring
- **Log Viewer**: Real-time log viewing with filtering
- **System Health**: Overall system health metrics
- **Interactive Charts**: Visual representation of data
- **Configuration Viewer**: View system configuration

### 🔍 Enhanced Database Monitoring (`monitor_databases.py`)

- **Health Checks**: Automated database health monitoring
- **Usage Tracking**: Storage and write usage monitoring
- **Rotation Recommendations**: Smart database rotation suggestions
- **Status Reports**: Export detailed health reports
- **Integrated Logging**: All monitoring activities are logged

## Installation

### Prerequisites

```bash
pip install -r requirements.txt
```

### Additional Dependencies

```bash
pip install streamlit plotly pandas
```

## Usage

### 1. Start the Dashboard

```bash
python run_dashboard.py
```

The dashboard will be available at: http://localhost:8501

### 2. Run Database Monitoring

```bash
python monitor_databases.py
```

### 3. View Logs

Logs are automatically stored in the `logs/` directory:

- `ratcrawler.log`: All logs
- `errors.log`: Error logs only

## Dashboard Features

### Overview Page

- System metrics (total databases, healthy databases, etc.)
- Database status summary
- Recent activity feed

### Database Status Page

- Individual database selection
- Storage and write usage charts
- Detailed database information
- Health status indicators

### Real-time Logs Page

- Live log streaming
- Log level filtering
- Log statistics
- Export functionality

### System Health Page

- Recent errors and warnings
- Log level distribution
- System uptime information

### Configuration Page

- Database configuration viewer
- System settings
- Environment information

## Logging Integration

### Automatic Logging

The system automatically logs:

- Database operations (insert, update, delete, commit)
- Crawler activities (page crawling, session management)
- System events (startup, shutdown, errors)
- Monitoring activities

### Log Format

```
timestamp - logger - level - module:line - message
```

### Log Levels

- `DEBUG`: Detailed debugging information
- `INFO`: General information
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical errors

## Database Monitoring

### Health Status

- **Healthy**: < 75% usage
- **Warning**: 75-89% usage
- **Critical**: ≥ 90% usage

### Automatic Recommendations

- Database rotation suggestions
- Usage optimization tips
- Health improvement recommendations

## API Reference

### Logger Functions

```python
from rat.logger import get_logger, log_db_operation, log_crawl_start

# Get a logger instance
logger = get_logger("my_module")

# Log database operations
log_db_operation("insert", "database_name", "table_name", record_count=1)

# Log crawler activities
log_crawl_start(session_id, seed_urls, config)
```

### Dashboard Manager

```python
from dashboard import DashboardManager

dashboard = DashboardManager()
db_status = dashboard.get_database_status()
logs = dashboard.get_recent_logs(limit=50)
```

## Configuration

### Logging Configuration

- Log directory: `logs/`
- Max log file size: 10MB
- Backup count: 5 files
- Queue size: 2000 entries

### Dashboard Configuration

- Auto-refresh interval: 5 seconds
- Port: 8501
- Host: 0.0.0.0

## Troubleshooting

### Common Issues

1. **Dashboard not loading**

   - Check if port 8501 is available
   - Ensure all dependencies are installed
   - Check firewall settings

2. **Logs not appearing**

   - Verify `logs/` directory exists
   - Check file permissions
   - Ensure logger is properly initialized

3. **Database monitoring errors**
   - Verify database credentials
   - Check network connectivity
   - Validate API keys

### Log Files

- Check `logs/ratcrawler.log` for general logs
- Check `logs/errors.log` for error details
- Use dashboard log viewer for real-time monitoring

## Development

### Adding New Loggers

```python
from rat.logger import get_logger

class MyComponent:
    def __init__(self):
        self.logger = get_logger("my_component")

    def my_method(self):
        self.logger.info("Method called")
```

### Extending Dashboard

Add new pages to the `dashboard.py` file:

```python
def show_custom_page(dashboard: DashboardManager):
    st.header("Custom Page")
    # Add your custom content here
```

## Performance

### Logging Performance

- In-memory queue for fast access
- Asynchronous file writing
- Minimal overhead for log operations

### Dashboard Performance

- Auto-refresh every 5 seconds
- Efficient data caching
- Optimized chart rendering

### Monitoring Performance

- Lightweight health checks
- Cached database status
- Minimal API calls

## Security

### Log Security

- Sensitive data is not logged
- Log files have appropriate permissions
- Log rotation prevents disk space issues

### Dashboard Security

- Local access by default
- No external API exposure
- Secure credential handling

## Contributing

1. Follow the existing logging patterns
2. Add appropriate log messages
3. Update dashboard for new features
4. Test monitoring functionality

## License

This monitoring system is part of the RatCrawler project and follows the same MIT license.
