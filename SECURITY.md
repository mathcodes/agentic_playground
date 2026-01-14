# Security & Compliance Guide

## 🔒 Security Overview

This document outlines the comprehensive security measures implemented in the Voice-to-SQL Multi-Agent System to protect your company's AI experience and ensure compliance with industry standards.

## Table of Contents

- [Security Architecture](#security-architecture)
- [Authentication & Authorization](#authentication--authorization)
- [Input Validation & Sanitization](#input-validation--sanitization)
- [SQL Injection Prevention](#sql-injection-prevention)
- [Rate Limiting & DDoS Protection](#rate-limiting--ddos-protection)
- [Audit Logging & Compliance](#audit-logging--compliance)
- [Data Protection](#data-protection)
- [Network Security](#network-security)
- [Compliance Standards](#compliance-standards)
- [Deployment Best Practices](#deployment-best-practices)
- [Incident Response](#incident-response)

---

## Security Architecture

### Defense in Depth

The application implements multiple layers of security:

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Layer                             │
│  • HTTPS/TLS encryption                                     │
│  • Firewall rules                                           │
│  • DDoS protection (rate limiting)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                            │
│  • Authentication (JWT)                                      │
│  • Authorization (RBAC)                                      │
│  • Input validation                                          │
│  • Security headers                                          │
│  • CORS protection                                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  • Parameterized queries                                     │
│  • Read-only transactions                                    │
│  • Result set limits                                         │
│  • Query timeouts                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Audit Layer                                │
│  • Comprehensive logging                                     │
│  • Tamper-proof audit trail                                  │
│  • PII redaction                                             │
│  • Real-time alerting                                        │
└─────────────────────────────────────────────────────────────┘
```

### Security Modules

All security functionality is centralized in the `/src/security/` module:

- **`auth.py`** - Authentication and authorization
- **`rate_limiter.py`** - Rate limiting and abuse prevention
- **`input_validator.py`** - Input validation and sanitization
- **`audit_logger.py`** - Comprehensive audit logging

---

## Authentication & Authorization

### JWT-Based Authentication

The system uses JWT (JSON Web Tokens) for stateless authentication:

**Features:**
- Access tokens (1 hour expiration)
- Refresh tokens (7 days expiration)
- Cryptographic signing (HMAC-SHA256)
- Token revocation support
- Automatic session timeout

**Configuration:**
```bash
# Set in environment variables or .env file
JWT_SECRET_KEY=your-secure-random-key-here  # REQUIRED for production
REQUIRE_AUTH=true                           # Enforce authentication
SESSION_TIMEOUT=60                          # Minutes
```

**Generating a secure JWT secret:**
```bash
# Generate 32-byte random key
openssl rand -hex 32
```

### Role-Based Access Control (RBAC)

Four role levels with granular permissions:

| Role | Permissions | Use Case |
|------|-------------|----------|
| **admin** | Full access to all operations | System administrators |
| **user** | Query, read, AI assistance | Regular users |
| **readonly** | View-only access | Auditors, read-only users |
| **api** | Programmatic access | API integrations |

**Protecting endpoints:**
```python
from src.security.auth import require_auth

@app.route('/api/sensitive')
@require_auth('admin')  # Requires admin role
def sensitive_endpoint():
    return {'data': 'sensitive'}
```

### Password Security

**NIST-compliant password requirements:**
- Minimum 12 characters (16+ recommended)
- bcrypt hashing with cost factor 12
- Automatic salt generation
- Constant-time comparison (timing attack protection)

**Account Lockout:**
- 5 failed attempts trigger 15-minute lockout
- Prevents brute force attacks
- IP-based and user-based tracking

---

## Input Validation & Sanitization

### Multi-Layer Validation

All user inputs undergo comprehensive validation:

#### 1. Length Validation
- Query: 5,000 characters max
- Username: 100 characters max
- Email: 254 characters max (RFC 5321)
- API Key: 256 characters max

#### 2. Format Validation
- Email: RFC 5322 compliant
- Username: Alphanumeric + underscore/hyphen
- URLs: HTTP/HTTPS only, no internal IPs

#### 3. Content Validation

**Detects and blocks:**
- SQL injection patterns
- XSS (Cross-Site Scripting)
- Command injection
- LLM prompt injection
- Path traversal
- Control characters
- Zero-width characters

**Example validation:**
```python
from src.security.input_validator import input_validator

# Validate user query
is_valid, error = input_validator.validate_query(user_query)
if not is_valid:
    return {'error': error}, 400

# Sanitize for safe display
safe_text = input_validator.sanitize_for_html(user_input)
```

### LLM Prompt Injection Detection

Specialized detection for LLM-specific attacks:

**Blocked patterns:**
- "Ignore previous instructions"
- "You are now in roleplay mode"
- "Forget everything above"
- "System prompt override"
- Jailbreak attempts

---

## SQL Injection Prevention

### Defense Layers

#### 1. Parameterized Queries
**ALWAYS** use parameterized queries:
```python
# ✅ SECURE - Parameterized query
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# ❌ INSECURE - String concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

#### 2. Query Validation

Comprehensive SQL safety checks:
- Keyword blacklist (INSERT, UPDATE, DELETE, DROP, etc.)
- Multiple statement detection
- Comment detection (`--`, `/* */`)
- UNION-based injection detection
- Time-based attack detection (SLEEP, pg_sleep)
- Boolean-based injection patterns
- Hexadecimal obfuscation
- Information schema access prevention

#### 3. Read-Only Transactions

By default, all SELECT queries run in read-only mode:
```python
# Database enforces read-only at transaction level
conn.set_session(readonly=True, autocommit=False)
```

#### 4. Write Query Control

Write operations disabled by default:
```bash
# Configuration
ALLOW_WRITE_QUERIES=false  # Keep false in production
```

If write queries are needed, implement strict authorization:
```python
if user_role != 'admin':
    return {'error': 'Permission denied'}, 403
```

### Query Timeouts

Prevents DoS through complex queries:
- Default: 30 seconds per query
- Configurable: `MAX_QUERY_TIME`
- Enforced at database level

### Result Set Limits

Prevents memory exhaustion:
- Default: 100 rows
- Configurable: `MAX_RESULTS`
- Uses `fetchmany()` for efficiency

---

## Rate Limiting & DDoS Protection

### Sliding Window Rate Limiting

Multi-tier rate limits:

| Tier | Per Second | Per Minute | Per Hour | Per Day |
|------|------------|------------|----------|---------|
| **Default** | 5 | 60 | 1,000 | 10,000 |
| **Authenticated** | 10 | 300 | 5,000 | 50,000 |
| **Premium** | 20 | 1,000 | 20,000 | 200,000 |
| **Admin** | 50 | 5,000 | 100,000 | 1,000,000 |

**Configuration:**
```bash
ENABLE_RATE_LIMITING=true
```

**Applying to endpoints:**
```python
from src.security.rate_limiter import rate_limit

@app.route('/api/query')
@rate_limit('authenticated')
def query_endpoint():
    return {'result': 'data'}
```

### Features

- **Sliding window** - More accurate than fixed window
- **IP-based** - Tracks unauthenticated users by IP
- **User-based** - Tracks authenticated users by ID
- **Automatic cleanup** - Prevents memory growth
- **Standard headers** - X-RateLimit-* headers

### Response Format

When rate limit exceeded:
```json
{
  "error": "Rate limit exceeded",
  "message": "60/60 requests per minute",
  "retry_after": 45
}
```

**Headers:**
```
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640995200
```

---

## Audit Logging & Compliance

### Comprehensive Audit Trail

All security-relevant events are logged:

**Logged Events:**
- Authentication attempts (success/failure)
- Authorization failures
- Data access (who, what, when)
- API calls
- Input validation failures
- Rate limit violations
- Security events
- Configuration changes
- Error conditions

### Log Structure

**Structured JSON logging for SIEM integration:**
```json
{
  "timestamp": "2024-01-14T10:30:00.000Z",
  "category": "authentication",
  "action": "login",
  "result": "success",
  "severity": "INFO",
  "user_id": "user123",
  "ip_address": "192.168.1.100",
  "resource": "api/login",
  "details": {"method": "jwt"},
  "hash": "abc123..."
}
```

### Tamper Detection

**Blockchain-style chained hashing:**
- Each log entry includes hash of previous entry
- Detects tampering or deletion
- Cryptographic integrity verification

### PII Redaction

**Automatic redaction of sensitive data:**
- Email addresses → `em***@example.com`
- API keys → `sk-***`
- Passwords → `[REDACTED]`
- Credit cards → `****-****-****-1234`
- IP addresses → `[IP]` (in error messages)

### Log Files

Three separate log files:

1. **`logs/audit.log`** - All events (compliance)
2. **`logs/security.log`** - Security events only (SIEM)
3. **`logs/application.log`** - Application debug logs

**Configuration:**
```bash
ENABLE_AUDIT_LOGGING=true
```

---

## Data Protection

### Encryption

#### In Transit
- **HTTPS/TLS 1.2+** enforced in production
- Certificate validation
- Strong cipher suites
- HSTS header (force HTTPS)

**Configuration:**
```bash
HTTPS_ONLY=true  # Required for production
```

#### At Rest
- Database encryption (PostgreSQL native encryption)
- Encrypted backups
- Key management (separate from application)

### Database Security

**Connection Security:**
```bash
# Production database URL with SSL
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
DB_SSL_REQUIRED=true
```

**Best Practices:**
- Use strong database passwords (16+ random characters)
- Limit database user privileges (SELECT only if possible)
- Enable SSL/TLS for connections
- Regular database backups
- Encrypted backup storage

### Secrets Management

**NEVER commit secrets to version control:**

**`.gitignore` includes:**
```
.env
*.key
*.pem
secrets/
```

**Use environment variables:**
```bash
# .env file (NEVER commit this)
ANTHROPIC_API_KEY=sk-ant-api03-xxx
JWT_SECRET_KEY=your-secure-key
DATABASE_URL=postgresql://user:pass@host/db
```

**Production secrets management:**
- Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
- Rotate secrets regularly (every 90 days)
- Use separate secrets per environment

---

## Network Security

### Security Headers

**All responses include security headers:**

```http
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), microphone=(), camera=()
```

**Protection against:**
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME sniffing
- Protocol downgrade attacks
- Information disclosure

### CORS Configuration

**Controlled cross-origin access:**
```bash
# Only allow specific origins
CORS_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

**Default (development):**
```bash
CORS_ORIGINS=http://localhost:*,http://127.0.0.1:*
```

### Firewall Rules

**Recommended firewall configuration:**

**Ingress (incoming):**
- Port 443 (HTTPS) - Allow from trusted IPs only
- Port 5432 (PostgreSQL) - Allow from application servers only
- All other ports - Deny

**Egress (outgoing):**
- Port 443 (HTTPS) - Allow (for API calls)
- Port 5432 (PostgreSQL) - Allow to database
- All other ports - Deny unless required

---

## Compliance Standards

### SOC 2 Type II

**Controls implemented:**
- Access controls (authentication/authorization)
- Encryption in transit and at rest
- Audit logging (comprehensive trail)
- Change management (configuration validation)
- Availability (rate limiting, timeouts)
- Monitoring and alerting

### GDPR (EU Data Protection)

**Data protection measures:**
- User consent mechanisms
- Data access logging (Article 30)
- Right to erasure support
- PII encryption
- Data minimization
- Privacy by design

### HIPAA (Healthcare)

**If handling PHI (Protected Health Information):**
- Access controls (RBAC)
- Audit trails (all data access logged)
- Encryption (in transit and at rest)
- Automatic logoff (session timeout)
- Unique user identification (JWT)
- Emergency access procedures

### PCI DSS (Payment Card Data)

**If handling payment data:**
- Requirement 6.5.1: Injection flaws (comprehensive prevention)
- Requirement 8: Unique IDs and strong authentication
- Requirement 10: Logging and monitoring (audit trail)
- Requirement 11: Regular security testing

### NIST Cybersecurity Framework

**Core functions implemented:**
- **Identify**: Asset inventory, risk assessment
- **Protect**: Access control, data security
- **Detect**: Security monitoring, audit logging
- **Respond**: Incident response procedures
- **Recover**: Backup and restore capabilities

---

## Deployment Best Practices

### Production Checklist

#### Before Deployment

- [ ] Generate strong JWT_SECRET_KEY (32+ bytes)
- [ ] Generate strong database password (16+ chars)
- [ ] Set ENVIRONMENT=production
- [ ] Set DEBUG=false
- [ ] Set HTTPS_ONLY=true
- [ ] Set REQUIRE_AUTH=true
- [ ] Configure CORS_ORIGINS to specific domains
- [ ] Enable SSL for database (DB_SSL_REQUIRED=true)
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review and test incident response plan
- [ ] Scan dependencies for vulnerabilities
- [ ] Run security tests
- [ ] Document all secrets locations

#### Production Server

**Use production WSGI server (not Flask development server):**

```bash
# Install gunicorn
pip install gunicorn gevent

# Run with 4 workers
gunicorn -w 4 -b 127.0.0.1:5000 --timeout 60 web_ui:app

# Or with gevent for async support
gunicorn -w 4 -k gevent -b 127.0.0.1:5000 web_ui:app
```

**Systemd service example:**
```ini
[Unit]
Description=Voice-to-SQL Web UI
After=network.target postgresql.service

[Service]
Type=notify
User=voicesql
WorkingDirectory=/opt/voice-to-sql
Environment="PATH=/opt/voice-to-sql/venv/bin"
ExecStart=/opt/voice-to-sql/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 web_ui:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Reverse Proxy (Nginx)

**Use Nginx for SSL termination:**

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Monitoring

**Set up monitoring for:**
- Failed authentication attempts (> 10/minute)
- Rate limit violations (> 100/hour)
- Database connection errors
- API error rates (> 5%)
- Slow queries (> 5 seconds)
- Disk space (< 20% free)
- Memory usage (> 80%)

**Tools:**
- Prometheus + Grafana
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Splunk
- DataDog
- New Relic

---

## Incident Response

### Security Incident Procedure

#### 1. Detection
- Monitor security logs
- Set up alerts for suspicious activity
- Regular security audits

#### 2. Containment
```bash
# Immediately revoke compromised tokens/keys
# Block suspicious IP addresses
# Isolate affected systems
```

#### 3. Investigation
- Review audit logs
- Identify attack vector
- Assess scope of breach
- Preserve evidence

#### 4. Remediation
- Patch vulnerabilities
- Rotate all secrets
- Update security rules
- Deploy fixes

#### 5. Recovery
- Restore from clean backups if needed
- Verify system integrity
- Resume normal operations

#### 6. Post-Incident
- Document incident
- Update security procedures
- Notify affected parties (if required)
- Conduct lessons learned review

### Emergency Contacts

**Maintain emergency contact list:**
- Security team lead
- Database administrator
- Cloud/infrastructure team
- Legal/compliance team
- Executive sponsor

---

## Security Testing

### Regular Security Audits

#### Dependency Scanning
```bash
# Check for known vulnerabilities
pip install safety
safety check --json

# Audit npm packages (if using frontend)
npm audit
```

#### Static Code Analysis
```bash
# Security linting
pip install bandit
bandit -r src/

# General linting
flake8 src/
pylint src/
```

#### Dynamic Testing

**SQL Injection testing:**
```bash
# Test with sqlmap
sqlmap -u "http://localhost:5000/api/query" --data='{"query":"test"}' --batch
```

**Web application scanning:**
```bash
# OWASP ZAP or Burp Suite
# Test for: XSS, CSRF, injection flaws, misconfigurations
```

### Penetration Testing

**Annual penetration testing by qualified professionals:**
- Web application testing
- API security testing
- Infrastructure testing
- Social engineering testing

---

## Security Updates

### Keeping Dependencies Updated

```bash
# Check for outdated packages
pip list --outdated

# Update specific package
pip install --upgrade package-name

# Update all packages (test thoroughly!)
pip install --upgrade -r requirements.txt
```

### Security Patch Policy

- **Critical vulnerabilities**: Patch within 24 hours
- **High vulnerabilities**: Patch within 7 days
- **Medium vulnerabilities**: Patch within 30 days
- **Low vulnerabilities**: Patch in next release

---

## Additional Resources

### Documentation
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CWE Top 25](https://cwe.mitre.org/top25/)

### Security Training
- OWASP Web Security Testing Guide
- SANS Security Training
- Certified Information Systems Security Professional (CISSP)

### Tools
- **Static Analysis**: Bandit, SonarQube
- **Dependency Scanning**: Safety, Snyk
- **Web Scanning**: OWASP ZAP, Burp Suite
- **Monitoring**: Splunk, ELK Stack, Prometheus

---

## Contact

For security concerns or to report vulnerabilities:

**Email**: security@yourcompany.com  
**PGP Key**: [Link to public key]  
**Bug Bounty**: [Link to program if applicable]

**Response Time:**
- Critical: 4 hours
- High: 24 hours
- Medium: 72 hours
- Low: 1 week

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-14  
**Next Review**: 2026-04-14

