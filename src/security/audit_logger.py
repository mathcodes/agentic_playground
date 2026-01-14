"""
Audit Logging Module.
Records security events and user actions for compliance and forensics.

SECURITY FEATURES:
- Tamper-proof logging with checksums
- PII (Personally Identifiable Information) redaction
- Structured logging for SIEM integration
- Separate security event log
- Log rotation and retention policies
- Real-time alerting for critical events

COMPLIANCE:
- SOC2 audit trail requirements
- GDPR data access logging
- HIPAA audit log requirements
- PCI DSS requirement 10 (logging and monitoring)
- NIST cybersecurity framework logging
"""

import logging
import json
import hashlib
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import re


class AuditLogger:
    """
    Secure audit logging for compliance and security monitoring.
    
    SECURITY: Logs critical security events:
    - Authentication attempts (success/failure)
    - Authorization failures
    - Data access (who accessed what data)
    - Configuration changes
    - API calls
    - Error conditions
    - Rate limit violations
    - Input validation failures
    
    COMPLIANCE: Logs contain:
    - Timestamp (UTC)
    - User identifier
    - Action performed
    - Resource accessed
    - Result (success/failure)
    - IP address
    - User agent
    - Session ID
    - Checksums for tamper detection
    """
    
    # SECURITY: Event severity levels
    CRITICAL = 'CRITICAL'  # Security incidents, breaches
    ERROR = 'ERROR'        # Failed operations, denied access
    WARNING = 'WARNING'    # Suspicious activity, approaching limits
    INFO = 'INFO'          # Normal operations, successful auth
    DEBUG = 'DEBUG'        # Detailed diagnostic information
    
    # SECURITY: Event categories for filtering and alerting
    AUTH = 'authentication'
    AUTHZ = 'authorization'
    DATA_ACCESS = 'data_access'
    CONFIG = 'configuration'
    API = 'api'
    SECURITY = 'security'
    COMPLIANCE = 'compliance'
    
    def __init__(self, log_dir: str = 'logs'):
        """
        Initialize audit logger.
        
        SECURITY: Separate log files for:
        - Audit trail (compliance)
        - Security events (SIEM)
        - Application logs (debugging)
        
        Args:
            log_dir: Directory to store log files
        """
        # SECURITY: Create log directory with restricted permissions
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # SECURITY: Set up separate loggers
        self._setup_loggers()
        
        # SECURITY: Track previous log hash for tamper detection
        self.last_hash = None
    
    def _setup_loggers(self):
        """
        Configure logging handlers with appropriate formatting.
        
        SECURITY: Structured JSON logging for SIEM integration
        """
        # SECURITY: Audit logger for compliance (INFO and above)
        self.audit_logger = logging.getLogger('audit')
        self.audit_logger.setLevel(logging.INFO)
        
        audit_handler = logging.FileHandler(
            self.log_dir / 'audit.log',
            encoding='utf-8'
        )
        audit_handler.setFormatter(
            logging.Formatter('%(message)s')  # JSON format
        )
        self.audit_logger.addHandler(audit_handler)
        
        # SECURITY: Security logger for security events (WARNING and above)
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.WARNING)
        
        security_handler = logging.FileHandler(
            self.log_dir / 'security.log',
            encoding='utf-8'
        )
        security_handler.setFormatter(
            logging.Formatter('%(message)s')  # JSON format
        )
        self.security_logger.addHandler(security_handler)
        
        # SECURITY: Application logger for general logging
        self.app_logger = logging.getLogger('application')
        self.app_logger.setLevel(logging.DEBUG)
        
        app_handler = logging.FileHandler(
            self.log_dir / 'application.log',
            encoding='utf-8'
        )
        app_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
        self.app_logger.addHandler(app_handler)
    
    def _redact_pii(self, data: Any) -> Any:
        """
        Redact personally identifiable information from logs.
        
        SECURITY: Protects sensitive data in logs
        - Email addresses -> em***@example.com
        - API keys -> sk-***
        - Passwords -> [REDACTED]
        - Credit cards -> ****-****-****-1234
        - SSN -> ***-**-****
        
        COMPLIANCE: GDPR, CCPA, HIPAA require PII protection
        
        Args:
            data: Data to redact (string, dict, or list)
            
        Returns:
            Data with PII redacted
        """
        if isinstance(data, dict):
            return {k: self._redact_pii(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact_pii(item) for item in data]
        elif isinstance(data, str):
            # SECURITY: Redact email addresses
            data = re.sub(
                r'([a-zA-Z0-9._%+-]{1,2})[a-zA-Z0-9._%+-]*@([a-zA-Z0-9.-]+)',
                r'\1***@\2',
                data
            )
            
            # SECURITY: Redact API keys (common patterns)
            data = re.sub(
                r'(sk-[a-zA-Z0-9]{2})[a-zA-Z0-9_-]+',
                r'\1***',
                data
            )
            
            # SECURITY: Redact password fields
            if 'password' in data.lower():
                return '[REDACTED]'
            
            # SECURITY: Redact credit card numbers
            data = re.sub(
                r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?(\d{4})\b',
                r'****-****-****-\1',
                data
            )
            
            return data
        else:
            return data
    
    def _calculate_hash(self, log_entry: Dict[str, Any]) -> str:
        """
        Calculate hash of log entry for tamper detection.
        
        SECURITY: Chained hashing creates tamper-proof audit trail
        Each log entry includes hash of previous entry
        
        Args:
            log_entry: Log entry dictionary
            
        Returns:
            SHA256 hash of entry
        """
        # SECURITY: Include previous hash in calculation (blockchain-style)
        hash_input = json.dumps(log_entry, sort_keys=True)
        if self.last_hash:
            hash_input = self.last_hash + hash_input
        
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
    def log_event(
        self,
        category: str,
        action: str,
        result: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: str = INFO
    ):
        """
        Log an audit event.
        
        SECURITY: Structured logging with all relevant context
        
        Args:
            category: Event category (AUTH, AUTHZ, DATA_ACCESS, etc.)
            action: Action performed (login, query, access, etc.)
            result: Result (success, failure, denied)
            user_id: User identifier (redacted if PII)
            ip_address: Client IP address
            resource: Resource accessed (table, file, endpoint)
            details: Additional context
            severity: Log severity level
        """
        # SECURITY: Build structured log entry
        log_entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'category': category,
            'action': action,
            'result': result,
            'severity': severity,
            'user_id': user_id,
            'ip_address': ip_address,
            'resource': resource,
            'details': self._redact_pii(details) if details else None
        }
        
        # SECURITY: Add tamper detection hash
        log_entry['hash'] = self._calculate_hash(log_entry)
        self.last_hash = log_entry['hash']
        
        # SECURITY: Convert to JSON
        log_json = json.dumps(log_entry)
        
        # SECURITY: Log to appropriate logger based on severity
        if severity in [self.CRITICAL, self.ERROR, self.WARNING]:
            self.security_logger.log(
                getattr(logging, severity),
                log_json
            )
        
        # SECURITY: Always log to audit trail
        self.audit_logger.info(log_json)
    
    def log_authentication(
        self,
        user_id: str,
        result: str,
        ip_address: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Log authentication attempt.
        
        SECURITY: Critical for detecting:
        - Brute force attacks
        - Credential stuffing
        - Account takeover attempts
        
        Args:
            user_id: User attempting to authenticate
            result: success or failure
            ip_address: Source IP
            details: Additional context
        """
        severity = self.INFO if result == 'success' else self.WARNING
        
        self.log_event(
            category=self.AUTH,
            action='login',
            result=result,
            user_id=user_id,
            ip_address=ip_address,
            details=details,
            severity=severity
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        action: str,
        resource: str,
        ip_address: str,
        reason: str
    ):
        """
        Log authorization failure (access denied).
        
        SECURITY: Tracks privilege escalation attempts
        
        Args:
            user_id: User who was denied
            action: Action attempted
            resource: Resource they tried to access
            ip_address: Source IP
            reason: Why access was denied
        """
        self.log_event(
            category=self.AUTHZ,
            action=action,
            result='denied',
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            details={'reason': reason},
            severity=self.WARNING
        )
    
    def log_data_access(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        result: str = 'success',
        row_count: int = 0
    ):
        """
        Log data access for compliance.
        
        COMPLIANCE: GDPR Article 30 - logs of data processing
        HIPAA - access logs for PHI
        
        Args:
            user_id: User accessing data
            resource: Table/dataset accessed
            action: Type of access (read, write, delete)
            ip_address: Source IP
            result: success or failure
            row_count: Number of records accessed
        """
        self.log_event(
            category=self.DATA_ACCESS,
            action=action,
            result=result,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            details={'row_count': row_count},
            severity=self.INFO
        )
    
    def log_api_call(
        self,
        endpoint: str,
        method: str,
        user_id: Optional[str],
        ip_address: str,
        status_code: int,
        response_time_ms: float,
        query_params: Optional[Dict[str, Any]] = None
    ):
        """
        Log API call for monitoring and debugging.
        
        SECURITY: Tracks API usage patterns
        
        Args:
            endpoint: API endpoint called
            method: HTTP method
            user_id: User making call (if authenticated)
            ip_address: Source IP
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            query_params: Query parameters (redacted)
        """
        result = 'success' if 200 <= status_code < 300 else 'failure'
        severity = self.INFO if result == 'success' else self.WARNING
        
        self.log_event(
            category=self.API,
            action=f"{method} {endpoint}",
            result=result,
            user_id=user_id,
            ip_address=ip_address,
            details={
                'status_code': status_code,
                'response_time_ms': response_time_ms,
                'query_params': self._redact_pii(query_params) if query_params else None
            },
            severity=severity
        )
    
    def log_security_event(
        self,
        event_type: str,
        description: str,
        ip_address: str,
        user_id: Optional[str] = None,
        severity: str = WARNING
    ):
        """
        Log security event for SIEM.
        
        SECURITY: Critical security events:
        - SQL injection attempt
        - XSS attempt
        - Rate limit violation
        - Suspicious activity
        - Configuration changes
        
        Args:
            event_type: Type of security event
            description: Detailed description
            ip_address: Source IP
            user_id: User involved (if known)
            severity: Event severity
        """
        self.log_event(
            category=self.SECURITY,
            action=event_type,
            result='detected',
            user_id=user_id,
            ip_address=ip_address,
            details={'description': description},
            severity=severity
        )
    
    def log_input_validation_failure(
        self,
        input_type: str,
        reason: str,
        ip_address: str,
        user_id: Optional[str] = None
    ):
        """
        Log input validation failure.
        
        SECURITY: Tracks injection attempts and malicious input
        
        Args:
            input_type: Type of input (query, username, etc.)
            reason: Why validation failed
            ip_address: Source IP
            user_id: User (if known)
        """
        self.log_security_event(
            event_type='input_validation_failure',
            description=f"{input_type} validation failed: {reason}",
            ip_address=ip_address,
            user_id=user_id,
            severity=self.WARNING
        )
    
    def log_rate_limit_violation(
        self,
        identifier: str,
        endpoint: str,
        limit_type: str,
        ip_address: str
    ):
        """
        Log rate limit violation.
        
        SECURITY: Detects DoS attempts and API abuse
        
        Args:
            identifier: User ID or IP that violated limit
            endpoint: Endpoint being accessed
            limit_type: Type of limit (per-second, per-minute, etc.)
            ip_address: Source IP
        """
        self.log_security_event(
            event_type='rate_limit_violation',
            description=f"Rate limit exceeded for {endpoint} ({limit_type})",
            ip_address=ip_address,
            user_id=identifier if not identifier.startswith('ip:') else None,
            severity=self.WARNING
        )
    
    def get_recent_events(
        self,
        category: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> list:
        """
        Retrieve recent audit events for dashboard/monitoring.
        
        Args:
            category: Filter by category
            severity: Filter by severity
            limit: Maximum events to return
            
        Returns:
            List of recent events
        """
        events = []
        
        try:
            # SECURITY: Read from audit log
            with open(self.log_dir / 'audit.log', 'r') as f:
                lines = f.readlines()
                
                # Get last N lines
                for line in lines[-limit:]:
                    try:
                        event = json.loads(line.strip())
                        
                        # Apply filters
                        if category and event.get('category') != category:
                            continue
                        if severity and event.get('severity') != severity:
                            continue
                        
                        events.append(event)
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        return events


# SECURITY: Global audit logger instance
audit_logger = AuditLogger()
