# Turso Database Integration Guide

This guide shows how to seamlessly integrate Turso databases with automatic rotation into your existing RatCrawler.

## 🚀 Quick Start

### 1. Replace Database Imports

**Before (SQLite):**

```python
from crawlerdb import WebsiteCrawlerDatabase
from backlinkdb import BacklinkDatabase
```

**After (Turso with auto-rotation):**

```python
from turso_database_adapter import TursoWebsiteCrawlerDatabase, TursoBacklinkDatabase
```

### 2. Update Database Initialization

**Before:**

```python
crawler_db = WebsiteCrawlerDatabase("website_crawler.db")
backlinks_db = BacklinkDatabase("backlinks.db")
```

**After:**

```python
crawler_db = TursoWebsiteCrawlerDatabase()  # No file path needed!
backlinks_db = TursoBacklinkDatabase()
```

## 📊 Features

- ✅ **Automatic Rotation**: Switches databases when approaching 10M monthly write limits
- ✅ **Drop-in Replacement**: Same API as your existing SQLite databases
- ✅ **Real-time Monitoring**: Web dashboard at http://localhost:8000
- ✅ **Background Health Checks**: Automatic database health monitoring
- ✅ **Write Tracking**: Tracks monthly writes per database
- ✅ **Seamless Migration**: Migrate existing SQLite data to Turso

## 🔧 Setup Steps

### Step 1: Configure Turso Databases

Edit `turso_monitoring_dashboard.py` and add your Turso database configurations:

```python
# Add your databases here
monitor.add_database(
    name="crawler_db_1",
    url="your-turso-db-url-1",
    auth_token="your-auth-token-1",
    monthly_write_limit=10000000  # 10M writes
)

monitor.add_database(
    name="crawler_db_2",
    url="your-turso-db-url-2",
    auth_token="your-auth-token-2",
    monthly_write_limit=10000000
)
```

### Step 2: Start Monitoring Dashboard

```bash
python turso_monitoring_dashboard.py
```

This starts the web dashboard at http://localhost:8000

### Step 3: Update Your Crawler Code

Replace your database imports and initialization as shown above.

### Step 4: Migrate Existing Data (Optional)

```python
from turso_database_adapter import migrate_to_turso

# Run once to migrate your existing SQLite data
migrate_to_turso()
```

## 📈 Monitoring

### Web Dashboard

- Visit http://localhost:8000 for real-time monitoring
- View database usage, write counts, and rotation status
- See alerts when databases approach capacity limits

### Programmatic Monitoring

```python
from turso_rotation_utility import check_database_health, get_current_database

# Get current active database
current = get_current_database()
print(f"Active database: {current}")

# Check all database health
health = check_database_health()
for db_name, stats in health.items():
    print(f"{db_name}: {stats['monthly_writes']}/{stats['write_limit']} writes")
```

## 🔄 How Rotation Works

1. **Write Tracking**: Every database write is tracked
2. **Capacity Monitoring**: System monitors when databases approach 85% capacity
3. **Automatic Rotation**: When limit is reached, automatically switches to next available database
4. **Seamless Operation**: Your crawler code continues working without interruption

## 🛠️ API Reference

### TursoWebsiteCrawlerDatabase

Same methods as your existing `WebsiteCrawlerDatabase`:

- `create_crawl_session(seed_urls, config)`
- `store_crawled_page(page_data, session_id)`
- `log_crawl_error(session_id, url, error_type, error_msg)`
- `get_all_crawled_urls()`
- `get_all_content_hashes()`
- `finish_crawl_session(session_id, status)`

### TursoBacklinkDatabase

Same methods as your existing `BacklinkDatabase`:

- `store_backlinks(backlinks_list)`
- `store_domain_scores(domain_scores)`
- `store_pagerank_scores(pagerank_scores)`
- `get_backlinks_for_url(target_url)`

## 🚨 Alerts & Notifications

The system automatically alerts you when:

- Database reaches 70% of monthly write limit
- Database reaches 85% capacity (triggers rotation)
- No available databases with capacity
- Database connection failures

## 📝 Example Integration

See `integration_example.py` for complete working examples of how to integrate Turso into your crawler.

## 🔍 Troubleshooting

### Common Issues

1. **"No available databases"**

   - Check your Turso database configurations
   - Ensure auth tokens are valid
   - Verify database URLs are correct

2. **"Write failed" errors**

   - System will automatically rotate to another database
   - Check monitoring dashboard for database status

3. **Migration fails**
   - Ensure your existing SQLite databases exist
   - Check file permissions
   - Verify Turso databases are accessible

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎯 Best Practices

1. **Monitor Regularly**: Check the web dashboard daily
2. **Plan Capacity**: Add new databases before existing ones are full
3. **Backup Data**: Regularly backup your Turso databases
4. **Test Rotation**: Test with small datasets first
5. **Update Tokens**: Keep auth tokens current

## 📞 Support

If you encounter issues:

1. Check the monitoring dashboard for error messages
2. Review the logs in your terminal
3. Verify your Turso database configurations
4. Test with the integration examples

## 🚀 Next Steps

1. Configure your Turso databases
2. Update your crawler imports
3. Start the monitoring dashboard
4. Test with a small crawl
5. Monitor the dashboard as you scale up

Your crawler will now automatically handle database rotation while maintaining the same simple API you're used to!
