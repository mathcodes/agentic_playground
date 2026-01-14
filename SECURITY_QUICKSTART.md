# Security Features - Quick Start Guide

## 🚀 Getting Started with Security

This guide will help you quickly enable and configure the security features in your Voice-to-SQL application.

---

## 📋 Quick Setup (5 Minutes)

### Step 1: Generate Security Keys

```bash
# Generate JWT Secret Key (copy the output)
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate Encryption Key (copy the output)
python -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"
```

### Step 2: Create .env File

Create a `.env` file in your project root:

```env
# Essential Configuration
ANTHROPIC_API_KEY=sk-ant-your-api-key-here
DATABASE_URL=postgresql://localhost:5432/voice_sql_test

# Security Keys (paste from Step 1)
JWT_SECRET_KEY=your-generated-key-from-step-1
ENCRYPTION_KEY=your-generated-key-from-step-1

# Enable Security Features
REQUIRE_AUTH=true
RATE_LIMIT_ENABLED=true
AUDIT_LOGGING_ENABLED=true

# Change Default Passwords!
DEFAULT_ADMIN_PASSWORD=YourStrongPassword123!
DEFAULT_VIEWER_PASSWORD=ViewerPassword123!
```

### Step 3: Install Dependencies

```bash
# Install security dependencies
pip install PyJWT==2.8.0 bcrypt==4.1.2 cryptography==41.0.7
```

### Step 4: Start the Application

```bash
python web_ui.py
```

---

## 🔐 Authentication Usage

### Login

```bash
# Login to get access token
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YourStrongPassword123!"}'

# Response includes access_token
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "role": "admin"
}
```

### Use Token for Queries

```bash
# Use the access_token from login
export TOKEN="your-access-token-here"

curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query":"Show me all products"}'
```

---

## 👥 User Management

### Creating Users

```python
# Create a new user via Python
from src.security.auth import auth_manager

# Create analyst user
auth_manager.create_user(
    username='analyst1',
    password='SecurePassword123!',
    role='analyst',
    metadata={'email': 'analyst@company.com'}
)

# Create viewer user (read-only)
auth_manager.create_user(
    username='viewer1',
    password='SecurePassword123!',
    role='viewer',
    metadata={'email': 'viewer@company.com'}
)

# Create developer user (code examples access)
auth_manager.create_user(
    username='dev1',
    password='SecurePassword123!',
    role='developer',
    metadata={'email': 'dev@company.com'}
)
```

### User Roles

| Role | Can Query | Can Access Code | Can Modify Data |
|------|-----------|-----------------|-----------------|
| **viewer** | ✅ Yes | ❌ No | ❌ No |
| **analyst** | ✅ Yes | ❌ No | ❌ No |
| **developer** | ✅ Yes | ✅ Yes | ❌ No |
| **admin** | ✅ Yes | ✅ Yes | ✅ Yes* |

*Only if `ALLOW_WRITE_QUERIES=true` in config

---

## 🛡️ Security Features Overview

### ✅ What's Protected

1. **Authentication** (JWT tokens)
   - Secure login with password hashing
   - Token expiration (1 hour)
   - Role-based access control

2. **Input Validation**
   - SQL injection prevention
   - XSS protection
   - Command injection prevention
   - Path traversal prevention

3. **Rate Limiting**
   - Prevents brute force attacks
   - Prevents API abuse
   - Prevents DoS attacks

4. **Audit Logging**
   - All authentication attempts logged
   - All queries logged
   - All security events logged
   - Logs stored in `logs/` directory

5. **Data Encryption**
   - Sensitive data encrypted at rest
   - Passwords hashed with bcrypt
   - API keys can be encrypted

6. **Secure Headers**
   - Content Security Policy (CSP)
   - XSS protection headers
   - Clickjacking prevention
   - MIME sniffing prevention

---

## 🔍 Monitoring Security

### View Logs

```bash
# View audit logs
tail -f logs/audit.log

# View security-specific events
tail -f logs/security.log

# View data access logs
tail -f logs/access.log
```

### Check Security Status

```bash
# View configuration
python -c "from config import Config; Config.print_config()"

# Test security features
python main.py --test
```

### Monitor Failed Login Attempts

```bash
# Check for failed authentication attempts
grep "login_attempt.*failure" logs/audit.log

# Check for rate limit violations
grep "rate_limit" logs/security.log

# Check for SQL injection attempts
grep "SQL_INJECTION" logs/security.log
```

---

## ⚙️ Configuration Reference

### Essential Security Settings

```env
# Authentication
REQUIRE_AUTH=true                # Enable authentication requirement
JWT_SECRET_KEY=<32+ char secret> # JWT signing key
JWT_ACCESS_TOKEN_EXPIRE=3600     # Token expiration (seconds)

# Encryption
ENCRYPTION_KEY=<fernet key>      # Data encryption key

# Query Safety
ALLOW_WRITE_QUERIES=false        # Block INSERT/UPDATE/DELETE
MAX_RESULTS=100                  # Limit result set size
MAX_QUERY_TIME=30                # Query timeout (seconds)

# Rate Limiting
RATE_LIMIT_ENABLED=true          # Enable rate limiting
RATE_LIMIT_PER_MINUTE=60         # Requests per minute
RATE_LIMIT_PER_HOUR=1000         # Requests per hour

# Logging
AUDIT_LOGGING_ENABLED=true       # Enable audit logging
LOG_LEVEL=INFO                   # Logging verbosity
```

### Development vs Production

**Development:**
```env
ENVIRONMENT=development
DEBUG=true
REQUIRE_AUTH=false  # Optional for easier testing
LOG_LEVEL=DEBUG
ENABLE_HSTS=false
```

**Production:**
```env
ENVIRONMENT=production
DEBUG=false
REQUIRE_AUTH=true
LOG_LEVEL=WARNING
ENABLE_HSTS=true  # Only with valid SSL
CORS_ALLOWED_ORIGINS=https://yourdomain.com
```

---

## 🚨 Common Issues & Solutions

### Issue: "JWT_SECRET_KEY not set"

**Solution:**
```bash
# Generate a strong secret
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add to .env file
```

### Issue: "Invalid or expired token"

**Solution:**
- Token expired (default 1 hour)
- Login again to get new token
- Or use refresh token to get new access token

### Issue: "Rate limit exceeded"

**Solution:**
- Wait for rate limit window to reset
- Check `Retry-After` header
- Increase rate limits in config if legitimate use

### Issue: "Database connection error"

**Solution:**
```bash
# Test database connection
psql $DATABASE_URL

# Check if PostgreSQL is running
pg_isready

# Verify DATABASE_URL in .env
```

### Issue: "Authentication required" but you want demo mode

**Solution:**
```env
# In .env file
REQUIRE_AUTH=false
```

---

## 📚 Additional Resources

- **Full Security Documentation**: `SECURITY.md`
- **Configuration Guide**: `config.py` (inline documentation)
- **Multi-Agent Guide**: `MULTI_AGENT_ARCHITECTURE.md`
- **Collaboration Guide**: `COLLABORATION_GUIDE.md`

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

### Critical
- [ ] Change all default passwords
- [ ] Generate and set strong JWT_SECRET_KEY (32+ chars)
- [ ] Generate and set ENCRYPTION_KEY
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `DEBUG=false`
- [ ] Set `REQUIRE_AUTH=true`
- [ ] Install SSL certificate
- [ ] Enable HSTS (after SSL is working)

### Important
- [ ] Configure firewall rules
- [ ] Set up database connection pooling
- [ ] Configure CORS allowed origins
- [ ] Set up log aggregation
- [ ] Configure monitoring and alerts
- [ ] Implement backup strategy
- [ ] Document incident response plan

### Recommended
- [ ] Use WSGI server (gunicorn)
- [ ] Set up Redis for rate limiting
- [ ] Enable error tracking (Sentry)
- [ ] Configure CDN
- [ ] Run penetration testing
- [ ] Set up automated security scanning

---

## 🔒 Security Best Practices

### DO:
✅ Use strong, unique passwords (12+ characters)  
✅ Rotate secrets regularly (annually minimum)  
✅ Monitor audit logs regularly  
✅ Keep dependencies updated  
✅ Use HTTPS in production  
✅ Limit rate limits appropriately  
✅ Test security features regularly  
✅ Document your security procedures  

### DON'T:
❌ Hardcode secrets in code  
❌ Commit .env files to git  
❌ Use DEBUG=true in production  
❌ Expose detailed errors to users  
❌ Use default passwords in production  
❌ Disable authentication in production  
❌ Allow write queries without careful consideration  
❌ Ignore failed authentication attempts  

---

## 🆘 Getting Help

### Issues?
1. Check logs in `logs/` directory
2. Run `python main.py --test` to verify setup
3. Check `SECURITY.md` for detailed documentation
4. Open an issue on GitHub

### Security Vulnerabilities?
**DO NOT** create public issues for security vulnerabilities.  
Email security concerns to: [your-security-email]

---

## 📈 Next Steps

Once security is configured:

1. **Create Additional Users**
   ```python
   from src.security.auth import auth_manager
   auth_manager.create_user('username', 'password', 'role')
   ```

2. **Test Authentication**
   ```bash
   # Try login with different users
   curl -X POST http://localhost:5000/api/login \
     -H "Content-Type: application/json" \
     -d '{"username":"viewer","password":"..."}'
   ```

3. **Monitor Logs**
   ```bash
   tail -f logs/audit.log
   ```

4. **Set Up Monitoring**
   - Configure alerts for failed logins
   - Monitor rate limit violations
   - Track query performance
   - Watch for security events

5. **Regular Maintenance**
   - Review audit logs weekly
   - Update dependencies monthly
   - Rotate secrets annually
   - Review user access quarterly

---

## ⭐ Quick Reference

```bash
# Start application
python web_ui.py

# View configuration
python -c "from config import Config; Config.print_config()"

# Run tests
python main.py --test

# Check logs
tail -f logs/audit.log

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate encryption key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Create user
python -c "from src.security.auth import auth_manager; auth_manager.create_user('user', 'pass', 'role')"
```

---

**Ready to go! 🚀**

Your Voice-to-SQL application is now secured with enterprise-grade security features.
