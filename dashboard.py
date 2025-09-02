"""
Enhanced Streamlit Dashboard for RatCrawler Monitoring
Real-time monitoring with authentication, beautiful visuals, and comprehensive analytics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import threading
from typing import Dict, List, Any
import json
import logging
from pathlib import Path
import requests
import os
import sys
import psutil
import hashlib
import hmac

# Import RatCrawler components
from rat.logger import log_manager
from rat.healthcheck import Health
from rat.dblist import DBList
from rat.config import config

# Custom CSS for enhanced styling
CUSTOM_CSS = """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 2rem;
    }

    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
    }

    .status-healthy {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }

    .status-warning {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }

    .status-critical {
        background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
    }

    .sidebar-logo {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        color: #4ECDC4;
        margin-bottom: 2rem;
    }

    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
"""

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        username = st.session_state["username"]
        password = st.session_state["password"]

        # Get credentials from environment
        correct_username = os.getenv("DASHBOARD_PASSWORD", "swadhin")
        correct_password = os.getenv("DASHBOARD_PASSWORD", "swadhin")

        # Check credentials
        if username == correct_username and password == correct_password:
            st.session_state["password_correct"] = True
            st.session_state["authenticated_user"] = username
            del st.session_state["password"]  # Don't store password
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show login form
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        st.markdown('<div class="main-header">🕷️ RatCrawler Dashboard</div>', unsafe_allow_html=True)

        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="login-container">', unsafe_allow_html=True)
                st.markdown("### 🔐 Login Required")
                st.text_input("Username", key="username")
                st.text_input("Password", type="password", key="password")
                st.button("Login", on_click=password_entered)
                st.markdown('</div>', unsafe_allow_html=True)
        return False
    elif not st.session_state["password_correct"]:
        # Password incorrect, show error and login form again
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        st.markdown('<div class="main-header">🕷️ RatCrawler Dashboard</div>', unsafe_allow_html=True)

        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown('<div class="login-container">', unsafe_allow_html=True)
                st.error("❌ Invalid username or password")
                st.markdown("### 🔐 Login Required")
                st.text_input("Username", key="username")
                st.text_input("Password", type="password", key="password")
                st.button("Login", on_click=password_entered)
                st.markdown('</div>', unsafe_allow_html=True)
        return False
    else:
        # Password correct
        return True


class EnhancedDashboardManager:
    """Enhanced dashboard with better visuals and analytics"""

    def __init__(self):
        self.health = Health()
        self.db_list = DBList()
        self.last_update = datetime.now()
        self.update_interval = 5  # seconds

    def get_system_metrics(self) -> Dict:
        """Get comprehensive system metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_percent': (disk.used / disk.total) * 100,
                'disk_used_gb': disk.used / (1024**3),
                'disk_total_gb': disk.total / (1024**3),
            }
        except Exception as e:
            st.error(f"Error getting system metrics: {e}")
            return {}

    def get_database_health(self) -> List[Dict]:
        """Get comprehensive database health information"""
        try:
            self.health.useabledbdata()

            all_databases = []

            # Process crawler databases
            for i, db in enumerate(self.health.crawler_databases):
                if not db:
                    continue

                try:
                    usage = self.health.current_limit(
                        db['name'],
                        db['organization'],
                        db['apikey']
                    )

                    if usage:
                        storage_used = usage.get('storage_bytes', 0)
                        writes_used = usage.get('rows_written', 0)
                        storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                        write_limit = db.get('monthly_write_limit', 10000000)

                        storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                        write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                        # Determine status
                        if storage_percent >= 90 or write_percent >= 90:
                            status = "critical"
                        elif storage_percent >= 75 or write_percent >= 75:
                            status = "warning"
                        else:
                            status = "healthy"

                        all_databases.append({
                            'name': db['name'],
                            'type': 'crawler',
                            'organization': db['organization'],
                            'status': status,
                            'storage_used_gb': storage_used / (1024**3),
                            'storage_limit_gb': db.get('storage_quota_gb', 5),
                            'storage_percent': storage_percent,
                            'writes_used': writes_used,
                            'write_limit': write_limit,
                            'write_percent': write_percent,
                            'useable': self.health.useable_databases_crawler[i] is not None if i < len(self.health.useable_databases_crawler) else False
                        })
                except Exception as e:
                    all_databases.append({
                        'name': db['name'],
                        'type': 'crawler',
                        'organization': db['organization'],
                        'status': 'error',
                        'error': str(e),
                        'useable': False
                    })

            # Process backlink databases
            for i, db in enumerate(self.health.backlink_databases):
                if not db:
                    continue

                try:
                    usage = self.health.current_limit(
                        db['name'],
                        db['organization'],
                        db['apikey']
                    )

                    if usage:
                        storage_used = usage.get('storage_bytes', 0)
                        writes_used = usage.get('rows_written', 0)
                        storage_limit = db.get('storage_quota_gb', 5) * 1024**3
                        write_limit = db.get('monthly_write_limit', 10000000)

                        storage_percent = (storage_used / storage_limit) * 100 if storage_limit > 0 else 0
                        write_percent = (writes_used / write_limit) * 100 if write_limit > 0 else 0

                        # Determine status
                        if storage_percent >= 90 or write_percent >= 90:
                            status = "critical"
                        elif storage_percent >= 75 or write_percent >= 75:
                            status = "warning"
                        else:
                            status = "healthy"

                        all_databases.append({
                            'name': db['name'],
                            'type': 'backlink',
                            'organization': db['organization'],
                            'status': status,
                            'storage_used_gb': storage_used / (1024**3),
                            'storage_limit_gb': db.get('storage_quota_gb', 5),
                            'storage_percent': storage_percent,
                            'writes_used': writes_used,
                            'write_limit': write_limit,
                            'write_percent': write_percent,
                            'useable': self.health.useable_databases_backlink[i] is not None if i < len(self.health.useable_databases_backlink) else False
                        })
                except Exception as e:
                    all_databases.append({
                        'name': db['name'],
                        'type': 'backlink',
                        'organization': db['organization'],
                        'status': 'error',
                        'error': str(e),
                        'useable': False
                    })

            return all_databases
        except Exception as e:
            st.error(f"Error getting database health: {e}")
            return []

    def get_recent_logs(self, limit: int = 50) -> List[Dict]:
        """Get recent logs from the log manager"""
        try:
            if hasattr(log_manager, 'queue_handler'):
                return log_manager.queue_handler.get_recent_logs(limit)
            else:
                return []
        except Exception as e:
            st.error(f"Error getting logs: {e}")
            return []


def create_system_metrics_chart(metrics: Dict):
    """Create beautiful system metrics visualization"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('CPU Usage', 'Memory Usage', 'Disk Usage', 'System Health'),
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "pie"}]]
    )

    # CPU gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=metrics.get('cpu_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "CPU %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=1, col=1
    )

    # Memory gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=metrics.get('memory_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Memory %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=1, col=2
    )

    # Disk gauge
    fig.add_trace(
        go.Indicator(
            mode="gauge+number+delta",
            value=metrics.get('disk_percent', 0),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Disk %"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkorange"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ),
        row=2, col=1
    )

    # System health pie chart
    health_data = []
    health_labels = []
    health_colors = []

    if metrics.get('cpu_percent', 0) < 70:
        health_data.append(1)
        health_labels.append('CPU OK')
        health_colors.append('#00ff00')
    else:
        health_data.append(1)
        health_labels.append('CPU High')
        health_colors.append('#ff0000')

    if metrics.get('memory_percent', 0) < 80:
        health_data.append(1)
        health_labels.append('Memory OK')
        health_colors.append('#00ff00')
    else:
        health_data.append(1)
        health_labels.append('Memory High')
        health_colors.append('#ff0000')

    if metrics.get('disk_percent', 0) < 85:
        health_data.append(1)
        health_labels.append('Disk OK')
        health_colors.append('#00ff00')
    else:
        health_data.append(1)
        health_labels.append('Disk Full')
        health_colors.append('#ff0000')

    fig.add_trace(
        go.Pie(
            labels=health_labels,
            values=health_data,
            marker_colors=health_colors,
            title="System Health"
        ),
        row=2, col=2
    )

    fig.update_layout(height=600, title="System Metrics Dashboard")
    return fig


def main():
    """Main dashboard application"""
    # Check authentication
    if not check_password():
        return

    # Apply custom CSS
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # Main header
    st.markdown('<div class="main-header">🕷️ RatCrawler Dashboard</div>', unsafe_allow_html=True)

    # Initialize dashboard manager
    dashboard = EnhancedDashboardManager()

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-logo">🕷️ RatCrawler</div>', unsafe_allow_html=True)
        st.markdown(f"**Welcome:** {st.session_state.get('authenticated_user', 'Admin')}")

        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto Refresh (5s)", value=True)

        # Manual refresh button
        if st.button("🔄 Refresh Now"):
            st.rerun()

        # Logout button
        if st.button("🔓 Logout"):
            for key in st.session_state.keys():
                del st.session_state[key]
            st.rerun()

        st.markdown("---")
        st.markdown("### 📊 Quick Stats")

        # Quick system info
        try:
            cpu = psutil.cpu_percent()
            memory = psutil.virtual_memory().percent
            st.metric("CPU", f"{cpu:.1f}%")
            st.metric("Memory", f"{memory:.1f}%")
        except:
            st.error("System metrics unavailable")

    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "🗄️ Databases", "📝 Logs", "⚙️ System"])

    with tab1:
        st.header("📊 System Overview")

        # Get metrics
        metrics = dashboard.get_system_metrics()
        db_health = dashboard.get_database_health()

        if metrics:
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "🖥️ CPU Usage",
                    f"{metrics['cpu_percent']:.1f}%",
                    delta=None
                )

            with col2:
                st.metric(
                    "💾 Memory Usage",
                    f"{metrics['memory_percent']:.1f}%",
                    delta=f"{metrics['memory_used_gb']:.1f}GB used"
                )

            with col3:
                st.metric(
                    "💿 Disk Usage",
                    f"{metrics['disk_percent']:.1f}%",
                    delta=f"{metrics['disk_used_gb']:.1f}GB used"
                )

            with col4:
                healthy_dbs = len([db for db in db_health if db.get('status') == 'healthy'])
                total_dbs = len(db_health)
                st.metric(
                    "🗄️ Healthy DBs",
                    f"{healthy_dbs}/{total_dbs}",
                    delta=f"{(healthy_dbs/total_dbs*100):.1f}%" if total_dbs > 0 else "0%"
                )

            # System metrics chart
            if metrics:
                fig = create_system_metrics_chart(metrics)
                st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.header("🗄️ Database Health Monitor")

        db_health = dashboard.get_database_health()

        if db_health:
            # Database details table
            st.subheader("📋 Database Details")

            df = pd.DataFrame(db_health)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No database information available")

    with tab3:
        st.header("📝 Real-time Logs")

        # Log level filter
        log_level = st.selectbox("🔍 Filter by Level", ["ALL", "INFO", "WARNING", "ERROR"])

        # Get logs
        if log_level == "ALL":
            logs = dashboard.get_recent_logs(100)
        else:
            logs = log_manager.get_recent_logs(100, level=log_level)

        if logs:
            # Display logs in a nice format
            for log in reversed(logs[-20:]):  # Show latest 20 logs
                level = log.get('level', 'INFO')
                timestamp = log.get('timestamp', '')
                message = log.get('message', '')
                logger = log.get('logger', '')

                # Color code based on level
                if level == 'ERROR':
                    st.error(f"**{timestamp}** [{logger}] {message}")
                elif level == 'WARNING':
                    st.warning(f"**{timestamp}** [{logger}] {message}")
                else:
                    st.info(f"**{timestamp}** [{logger}] {message}")
        else:
            st.info("No logs available")

    with tab4:
        st.header("⚙️ System Information")

        try:
            # System information
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("🖥️ Hardware Info")
                st.write(f"**CPU Cores:** {psutil.cpu_count()}")
                st.write(f"**CPU Frequency:** {psutil.cpu_freq().current:.2f} MHz" if psutil.cpu_freq() else "N/A")

                memory = psutil.virtual_memory()
                st.write(f"**Total Memory:** {memory.total / (1024**3):.2f} GB")
                st.write(f"**Available Memory:** {memory.available / (1024**3):.2f} GB")

                disk = psutil.disk_usage('/')
                st.write(f"**Total Disk:** {disk.total / (1024**3):.2f} GB")
                st.write(f"**Free Disk:** {disk.free / (1024**3):.2f} GB")

            with col2:
                st.subheader("🔧 Process Info")
                st.write(f"**Python Version:** {sys.version}")
                st.write(f"**Platform:** {os.name}")
                st.write(f"**Current Directory:** {os.getcwd()}")

                # Environment variables
                st.write(f"**Environment Variables:**")
                env_vars = ["JSONPATH", "DASHBOARD_PASSWORD"]
                for var in env_vars:
                    value = os.getenv(var, "Not set")
                    if "PASSWORD" in var:
                        value = "***" if value != "Not set" else "Not set"
                    st.write(f"  - {var}: {value}")
        except Exception as e:
            st.error(f"Error getting system information: {e}")

    # Auto-refresh
    if auto_refresh:
        time.sleep(5)
        st.rerun()


if __name__ == "__main__":
    st.set_page_config(
        page_title="RatCrawler Dashboard",
        page_icon="🕷️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
