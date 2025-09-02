# 🔒 Security Policy

## 🛡️ **Reporting Security Vulnerabilities**

We take the security of RatCrawler seriously. If you discover a security vulnerability, please follow these steps:

### 📧 **How to Report**

**Email**: [theboringrats@gmail.com](mailto:theboringrats@gmail.com)

**Subject**: `[SECURITY] Brief description of the vulnerability`

**Please include**:

- Detailed description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Suggested fix (if available)
- Your contact information for follow-up

### ⏱️ **Response Timeline**

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Timeline**: Depends on severity (see below)
- **Public Disclosure**: After fix is released and users have time to update

---

## 🚨 **Severity Classification**

| Severity     | Description                                   | Response Time |
| ------------ | --------------------------------------------- | ------------- |
| **Critical** | Remote code execution, privilege escalation   | 24-48 hours   |
| **High**     | Data exposure, authentication bypass          | 3-7 days      |
| **Medium**   | Information disclosure, denial of service     | 7-14 days     |
| **Low**      | Configuration issues, minor information leaks | 14-30 days    |

---

## 🔐 **Security Features**

### 🎯 **Current Security Measures**

#### **Authentication & Authorization**

- **Dashboard Authentication**: Password-protected Streamlit dashboard
- **Environment-based Credentials**: Configurable via `DASHBOARD_PASSWORD`
- **Session Management**: Secure session handling with automatic cleanup
- **User Verification**: Username/password validation for dashboard access

#### **Database Security**

- **Encrypted Connections**: All database connections use secure protocols
- **Token-based Authentication**: Turso cloud databases use auth tokens
- **Connection Pooling**: Secure connection management with automatic cleanup
- **Credential Management**: Environment variable storage for sensitive data

#### **API Security**

- **CORS Configuration**: Properly configured cross-origin resource sharing
- **Input Validation**: Request validation for all API endpoints
- **Rate Limiting**: Built-in protection against abuse
- **Health Checks**: Secure monitoring endpoints

#### **Web Crawling Security**

- **Robots.txt Compliance**: Respects website crawling policies
- **Rate Limiting**: Intelligent request throttling
- **User-Agent Rotation**: Prevents detection and blocking
- **Spam Detection**: ML-based spam and malicious content detection

---

## 🔧 **Security Configuration**

### ⚙️ **Environment Variables**

**Required Security Variables:**

```bash
# Dashboard Authentication
DASHBOARD_PASSWORD="your-secure-password"

# Database Credentials (if using Turso)
TURSO_DATABASE_URL="libsql://your-database.turso.io"
TURSO_AUTH_TOKEN="your-auth-token"

# Optional Security Settings
ALLOWED_HOSTS="localhost,127.0.0.1"
API_RATE_LIMIT="100"  # requests per minute
```

### 🛠️ **Secure Installation**

1. **Use Virtual Environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

2. **Install from Requirements**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set Strong Passwords**

   ```bash
   export DASHBOARD_PASSWORD="your-very-secure-password-here"
   ```

4. **Secure File Permissions**
   ```bash
   chmod 600 .env  # If using .env file
   chmod 700 logs/  # Secure log directory
   ```

---

## ⚠️ **Security Best Practices**

### 🎯 **For Users**

#### **Password Security**

- ✅ Use strong, unique passwords (minimum 12 characters)
- ✅ Include uppercase, lowercase, numbers, and special characters
- ✅ Change default passwords immediately
- ✅ Use environment variables, never hardcode passwords

#### **Network Security**

- ✅ Run dashboard on localhost in development
- ✅ Use HTTPS in production environments
- ✅ Configure firewall rules for production deployments
- ✅ Limit access to monitoring ports (8000, 8501)

#### **Database Security**

- ✅ Rotate database tokens regularly
- ✅ Use separate databases for different environments
- ✅ Monitor database access logs
- ✅ Backup sensitive data securely

#### **File Security**

- ✅ Secure configuration files (chmod 600)
- ✅ Exclude sensitive files from version control
- ✅ Regular security updates for dependencies
- ✅ Monitor log files for suspicious activity

### 🎯 **For Developers**

#### **Code Security**

- ✅ Never commit secrets or passwords
- ✅ Use environment variables for all credentials
- ✅ Validate all user inputs
- ✅ Implement proper error handling
- ✅ Use parameterized database queries
- ✅ Regular dependency updates

#### **Testing Security**

- ✅ Include security tests in test suite
- ✅ Test authentication mechanisms
- ✅ Validate input sanitization
- ✅ Test rate limiting functionality

---

## 🚫 **Known Security Considerations**

### ⚠️ **Important Notes**

1. **Default Credentials**: Change the default dashboard password (`swadhin`)
2. **Local Development**: Dashboard runs on localhost by default
3. **Database Tokens**: Turso tokens are stored in configuration files
4. **Log Files**: May contain sensitive information, secure appropriately
5. **API Endpoints**: Some endpoints don't require authentication (monitoring)

### 🔄 **Planned Security Enhancements**

- [ ] **Multi-factor Authentication** for dashboard access
- [ ] **API Key Authentication** for REST endpoints
- [ ] **Encrypted Configuration** for sensitive settings
- [ ] **Audit Logging** for all security events
- [ ] **Rate Limiting** improvements
- [ ] **HTTPS Enforcement** for production deployments

---

## 📚 **Security Dependencies**

### 🔍 **Security-Related Packages**

| Package                | Purpose               | Security Notes                   |
| ---------------------- | --------------------- | -------------------------------- |
| `requests>=2.28.0`     | HTTP client           | Always update for security fixes |
| `fastapi>=0.100.0`     | Web framework         | Built-in security features       |
| `sqlalchemy>=2.0.0`    | Database ORM          | Prevents SQL injection           |
| `streamlit>=1.25.0`    | Dashboard framework   | Session management               |
| `python-dotenv>=1.0.0` | Environment variables | Secure credential loading        |

### 🔄 **Security Updates**

We recommend:

- **Regular Updates**: Update dependencies monthly
- **Security Patches**: Apply security updates immediately
- **Vulnerability Scanning**: Use `pip-audit` or similar tools
- **Monitoring**: Subscribe to security advisories for key dependencies

```bash
# Check for known vulnerabilities
pip install pip-audit
pip-audit

# Update all packages
pip install --upgrade -r requirements.txt
```

---

## 🔗 **Additional Resources**

### 📖 **Security Documentation**

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [SQLAlchemy Security](https://docs.sqlalchemy.org/en/20/core/security.html)
- [Streamlit Security](https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso)

### 🛡️ **Security Tools**

- [Bandit](https://bandit.readthedocs.io/) - Python security linter
- [Safety](https://pypi.org/project/safety/) - Dependency vulnerability scanner
- [pip-audit](https://pypi.org/project/pip-audit/) - Package vulnerability auditing

---

## 📜 **Security Policy Updates**

This security policy is reviewed and updated regularly. Last updated: **September 2, 2025**

### 📅 **Version History**

- **v1.0.0** (September 2, 2025): Initial security policy
- **v1.1.0** (TBD): Multi-database security enhancements
- **v1.2.0** (TBD): Enhanced authentication features

---

## 🤝 **Responsible Disclosure**

We appreciate security researchers and users who help keep RatCrawler secure. We commit to:

- ✅ **Prompt Response**: Acknowledge reports within 48 hours
- ✅ **Transparent Communication**: Keep you updated on fix progress
- ✅ **Credit**: Acknowledge your contribution (if desired)
- ✅ **Coordinated Disclosure**: Work together on disclosure timeline

**Thank you for helping keep RatCrawler secure! 🛡️**

---

_This document is part of the RatCrawler project security framework. For technical questions, see our [README.md](README.md) or contact the development team._
