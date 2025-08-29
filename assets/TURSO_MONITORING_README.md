# Turso Database Monitoring & Rotation System

A comprehensive FastAPI-based monitoring system for multiple Turso databases with automatic rotation capabilities.

## Features

- 🗄️ **Multi-Database Monitoring**: Monitor up to 20+ Turso databases simultaneously
- 📊 **Real-Time Dashboard**: Web-based dashboard with live updates
- 🔄 **Automatic Rotation**: Automatically rotate between databases when limits are approached
- 🚨 **Smart Alerts**: Warnings at 70% capacity, critical alerts at 90%
- 📈 **Usage Tracking**: Track storage and monthly write limits (10M per month)
- 🔧 **API Endpoints**: RESTful API for integration with your applications
- 🎯 **Production Ready**: Background monitoring, health checks, and error handling

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements_turso.txt
```

### 2. Run the Monitoring Dashboard

```bash
python turso_monitoring_dashboard.py
```

The dashboard will be available at: http://localhost:8000

### 3. Add Your First Database

Use the web interface or API to add your Turso databases:

```bash
curl -X POST "http://localhost:8000/api/database" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "db1",
    "url": "https://your-database.turso.io",
    "auth_token": "your-auth-token",
    "monthly_write_limit": 10000000,
    "storage_quota_gb": 5.0
  }'
```

## API Endpoints

### Database Management

- `GET /api/databases` - List all databases
- `POST /api/database` - Add new database
- `DELETE /api/database/{name}` - Remove database
- `GET /api/database/{name}` - Get database details

### Monitoring

- `GET /api/dashboard` - Get dashboard data
- `GET /api/available-database` - Get best database for writing
- `POST /api/record-writes/{db_name}` - Record write operations

### Health

- `GET /health` - Health check endpoint

## Integration with Your Crawler

### Basic Integration

```python
from turso_rotation_utility import get_current_database, record_writes

class YourCrawler:
    def save_data(self, data):
        # Get current database for writing
        db_name = get_current_database()

        # Your database operations here
        # ...

        # Record the write operation
        record_writes(db_name, 1)
```

### Advanced Integration

```python
from turso_rotation_utility import TursoIntegratedCrawler

class YourEnhancedCrawler(TursoIntegratedCrawler):
    def crawl_and_save(self, urls):
        for url in urls:
            data = self.crawl_page(url)
            self.perform_write_operation(data)
```

## Database Rotation Logic

The system automatically rotates databases based on:

1. **Storage Usage**: Rotate when >85% of 5GB quota used
2. **Write Limits**: Rotate when >85% of 10M monthly writes used
3. **Health Status**: Prioritize healthy databases

### Rotation Example

```python
# System automatically handles rotation
crawler = TursoIntegratedCrawler()

# This will automatically use the best available database
for i in range(100):
    crawler.perform_write_operation(f"data_{i}")
    # System rotates databases automatically when needed
```

## Configuration

### Environment Variables

```bash
# Database monitoring settings
TURSO_LOCAL_DB=turso_monitor.db
MONITORING_INTERVAL=300  # 5 minutes
AUTO_BACKUP=true
BACKUP_RETENTION_DAYS=7
```

### Database Limits

- **Storage**: 5GB per database (free tier)
- **Monthly Writes**: 10M per database
- **Rotation Threshold**: 85% capacity
- **Warning Threshold**: 70% capacity
- **Critical Threshold**: 90% capacity

## Monitoring Dashboard

### Features

- **Real-time Updates**: Auto-refresh every 30 seconds
- **Visual Indicators**: Color-coded status (Green/Yellow/Red)
- **Progress Bars**: Storage and write usage visualization
- **Alert System**: Active alerts for capacity issues
- **Database Management**: Add/remove databases via web interface

### Dashboard Sections

1. **System Overview**: Total databases, active/warning/critical counts
2. **Database List**: Individual database status and usage
3. **Active Alerts**: Current capacity warnings and critical issues
4. **Management**: Add new databases and manage existing ones

## Production Deployment

### 1. System Requirements

```bash
# Python 3.8+
pip install fastapi uvicorn requests pydantic

# Optional: For production server
pip install gunicorn
```

### 2. Production Server

```bash
# Using Uvicorn
uvicorn turso_monitoring_dashboard:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn
gunicorn turso_monitoring_dashboard:app -w 4 -k uvicorn.workers.UvicornWorker
```

### 3. Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements_turso.txt .
RUN pip install -r requirements_turso.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "turso_monitoring_dashboard:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Health Monitoring

```bash
# Health check
curl http://localhost:8000/health

# System status
curl http://localhost:8000/api/dashboard
```

## Troubleshooting

### Common Issues

1. **No Available Databases**

   ```
   Solution: Add more databases or check existing database capacity
   ```

2. **API Connection Errors**

   ```
   Solution: Verify Turso API tokens and database URLs
   ```

3. **High Memory Usage**

   ```
   Solution: Adjust monitoring interval or reduce database count
   ```

4. **Rotation Not Working**
   ```
   Solution: Check database limits and ensure proper write recording
   ```

### Logs and Debugging

```python
import logging
logging.basicConfig(level=logging.INFO)

# Enable debug mode
app = FastAPI(debug=True)
```

## Performance Optimization

### Database Optimization

- **Connection Pooling**: Automatic connection management
- **Background Monitoring**: Non-blocking health checks
- **Caching**: Usage data cached for 5 minutes
- **Cleanup**: Automatic old data removal

### Scaling Considerations

- **Multiple Workers**: Use Gunicorn with multiple workers
- **Load Balancing**: Distribute across multiple instances
- **Database Sharding**: Add more databases as needed
- **Monitoring**: Use external monitoring tools

## Security Best Practices

1. **API Tokens**: Store in environment variables
2. **HTTPS**: Use HTTPS in production
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Authentication**: Add authentication for sensitive endpoints
5. **Data Validation**: Validate all input data

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:

- Check the troubleshooting section
- Review the API documentation
- Create an issue on GitHub

---

**Happy Monitoring! 🎉**
