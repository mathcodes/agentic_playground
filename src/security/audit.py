"""
Audit Logging Module

Implements comprehensive audit logging for security and compliance.

Logs all security-relevant events including:
- Authentication attempts (success/failure)
- Authorization failures
- Query executions
- Data access
- Configuration changes
- Security violations

Compliance Standards:
- SOC 2: Requires audit logs for all security events
- GDPR: Requires tracking of personal data access
- HIPAA: Requires comprehensive audit trails
- PCI DSS: Requires logging of all access to cardholder data
"""

import logging
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any
from functools import wraps
from flask import request
import os
import sys

# Configure logging directory
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


class AuditLogger:
    """
    Centralized audit logging system.
    
    Provides structured logging of all security-relevant events.
    Logs are written to both file and console for redundancy.
    
    Log Format:
    - Timestamp (ISO 8601)
    - Event type
    - User/IP
    - Action
    - Result (success/failure)
    - Additional context
    """
    
    # Event types for categorization
    EVENT_TYPES = {
        'AUTH': 'Authentication',
        'AUTHZ': 'Authorization',
        'QUERY': 'Query Execution',
        'ACCESS': 'Data Access',
        'CONFIG': 'Configuration Change',
        'SECURITY': 'Security Event',
        'ERROR': 'Error',
        'ADMIN': 'Administrative Action'
    }
    
    def __init__(self, log_file: str = 'audit.log'):
        """
        Initialize the audit logger.
        
        Creates separate log files for:
        - audit.log: All audit events
        - security.log: Security-specific events
        - access.log: Data access events
        
        Args:
            log_file: Primary audit log file name
        """
        self.log_file = os.path.join(LOG_DIR, log_file)
        self.security_log = os.path.join(LOG_DIR, 'security.log')
        self.access_log = os.path.join(LOG_DIR, 'access.log')
        
        # Configure main audit logger
        self.logger = logging.getLogger('audit')
        self.logger.setLevel(logging.INFO)
        
        # File handler with rotation (production should use RotatingFileHandler)
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)  # Only warnings+ to console
        
        # JSON formatter for structured logs
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Configure security logger
        self.security_logger = logging.getLogger('security')
        self.security_logger.setLevel(logging.WARNING)
        security_handler = logging.FileHandler(self.security_log)
        security_handler.setFormatter(formatter)
        self.security_logger.addHandler(security_handler)
        
        # Configure access logger
        self.access_logger = logging.getLogger('access')
        self.access_logger.setLevel(logging.INFO)
        access_handler = logging.FileHandler(self.access_log)
        access_handler.setFormatter(formatter)
        self.access_logger.addHandler(access_handler)
    
    def _get_request_context(self) -> Dict[str, Any]:
        """
        Extract context information from the current request.
        
        Returns:
            Dict with request context (IP, user, endpoint, etc.)
        """
        if not request:
            return {}
        
        # Get IP address (handle proxy headers)
        ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip and ',' in ip:
            ip = ip.split(',')[0].strip()
        
        # Get user info if authenticated
        user = None
        if hasattr(request, 'user') and request.user:
            user = request.user.get('username')
        
        return {
            'ip': ip,
            'user': user,
            'endpoint': request.path,
            'method': request.method,
            'user_agent': request.headers.get('User-Agent', 'unknown')[:200]
        }
    
    def _format_log_entry(self, event_type: str, action: str, result: str,
                         details: Optional[Dict[str, Any]] = None) -> str:
        """
        Format a log entry as structured JSON.
        
        Args:
            event_type: Type of event (AUTH, AUTHZ, QUERY, etc.)
            action: Description of action
            result: Result (success, failure, error)
            details: Additional details
            
        Returns:
            Formatted log entry as JSON string
        """
        # Build log entry
        entry = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'event_type': event_type,
            'action': action,
            'result': result,
        }
        
        # Add request context
        entry.update(self._get_request_context())
        
        # Add additional details
        if details:
            # Sanitize details (remove sensitive info)
            sanitized_details = self._sanitize_details(details)
            entry['details'] = sanitized_details
        
        return json.dumps(entry)
    
    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize log details to remove sensitive information.
        
        Removes or masks:
        - Passwords
        - API keys
        - Tokens
        - Credit card numbers
        - SSN
        
        Args:
            details: Original details dict
            
        Returns:
            Sanitized details dict
        """
        sanitized = {}
        
        # Fields to completely remove
        sensitive_keys = ['password', 'token', 'api_key', 'secret', 'ssn', 'credit_card']
        
        for key, value in details.items():
            key_lower = key.lower()
            
            # Remove sensitive fields
            if any(sensitive in key_lower for sensitive in sensitive_keys):
                sanitized[key] = '[REDACTED]'
            # Truncate long strings
            elif isinstance(value, str) and len(value) > 500:
                sanitized[key] = value[:500] + '...[truncated]'
            # Recursively sanitize nested dicts
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_details(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def log_auth_attempt(self, username: str, success: bool, reason: Optional[str] = None):
        """
        Log an authentication attempt.
        
        Critical for:
        - Detecting brute force attacks
        - Compliance requirements
        - Security incident investigation
        
        Args:
            username: Username attempting to authenticate
            success: Whether authentication succeeded
            reason: Reason for failure (if applicable)
        """
        result = 'success' if success else 'failure'
        details = {'username': username}
        
        if not success and reason:
            details['reason'] = reason
        
        log_entry = self._format_log_entry('AUTH', 'login_attempt', result, details)
        
        if success:
            self.logger.info(log_entry)
        else:
            # Failed auth attempts are security events
            self.security_logger.warning(log_entry)
            self.logger.warning(log_entry)
    
    def log_authz_failure(self, username: str, endpoint: str, required_role: str, user_role: str):
        """
        Log an authorization failure.
        
        Critical for:
        - Detecting privilege escalation attempts
        - Access control violations
        - Compliance requirements
        
        Args:
            username: Username attempting access
            endpoint: Endpoint being accessed
            required_role: Required role for access
            user_role: User's actual role
        """
        details = {
            'username': username,
            'endpoint': endpoint,
            'required_role': required_role,
            'user_role': user_role
        }
        
        log_entry = self._format_log_entry('AUTHZ', 'authorization_failure', 'failure', details)
        
        # Authorization failures are security events
        self.security_logger.warning(log_entry)
        self.logger.warning(log_entry)
    
    def log_query(self, query: str, success: bool, execution_time_ms: float,
                 row_count: int = 0, error: Optional[str] = None):
        """
        Log a query execution.
        
        Important for:
        - Performance monitoring
        - Compliance (data access tracking)
        - Debugging
        - Security (detecting malicious queries)
        
        Args:
            query: SQL query executed (sanitized)
            success: Whether query succeeded
            execution_time_ms: Execution time in milliseconds
            row_count: Number of rows returned
            error: Error message if failed
        """
        result = 'success' if success else 'failure'
        
        # Truncate long queries for logging
        query_preview = query[:200] + '...' if len(query) > 200 else query
        
        details = {
            'query': query_preview,
            'execution_time_ms': execution_time_ms,
            'row_count': row_count
        }
        
        if error:
            details['error'] = error[:500]  # Truncate long errors
        
        log_entry = self._format_log_entry('QUERY', 'execute_query', result, details)
        
        # Log to access log (for compliance)
        self.access_logger.info(log_entry)
        
        # Also log to main log
        if success:
            self.logger.info(log_entry)
        else:
            self.logger.error(log_entry)
    
    def log_access(self, resource: str, action: str, success: bool):
        """
        Log a data access event.
        
        Critical for:
        - GDPR compliance (tracking personal data access)
        - HIPAA compliance (PHI access tracking)
        - Security auditing
        
        Args:
            resource: Resource being accessed (table, file, etc.)
            action: Action performed (read, write, delete)
            success: Whether access succeeded
        """
        result = 'success' if success else 'failure'
        
        details = {
            'resource': resource,
            'action': action
        }
        
        log_entry = self._format_log_entry('ACCESS', f'{action}_{resource}', result, details)
        
        # Log to access log (for compliance)
        self.access_logger.info(log_entry)
        self.logger.info(log_entry)
    
    def log_security_event(self, event: str, severity: str, details: Optional[Dict[str, Any]] = None):
        """
        Log a security event.
        
        Security events include:
        - SQL injection attempts
        - Rate limit violations
        - Invalid tokens
        - Suspicious patterns
        
        Args:
            event: Description of security event
            severity: Severity (low, medium, high, critical)
            details: Additional details
        """
        if details is None:
            details = {}
        
        details['severity'] = severity
        
        log_entry = self._format_log_entry('SECURITY', event, 'detected', details)
        
        # All security events go to security log
        self.security_logger.warning(log_entry)
        
        # High/critical also go to main log
        if severity in ['high', 'critical']:
            self.logger.error(log_entry)
    
    def log_config_change(self, setting: str, old_value: Any, new_value: Any, changed_by: str):
        """
        Log a configuration change.
        
        Important for:
        - Compliance requirements
        - Change tracking
        - Security auditing
        
        Args:
            setting: Setting that was changed
            old_value: Previous value
            new_value: New value
            changed_by: User who made the change
        """
        details = {
            'setting': setting,
            'old_value': str(old_value)[:200],
            'new_value': str(new_value)[:200],
            'changed_by': changed_by
        }
        
        log_entry = self._format_log_entry('CONFIG', 'config_change', 'success', details)
        
        self.logger.warning(log_entry)  # Config changes are important
    
    def log_error(self, error_type: str, error_message: str, details: Optional[Dict[str, Any]] = None):
        """
        Log an error event.
        
        Args:
            error_type: Type of error
            error_message: Error message
            details: Additional details
        """
        if details is None:
            details = {}
        
        details['error_type'] = error_type
        details['error_message'] = error_message[:500]
        
        log_entry = self._format_log_entry('ERROR', error_type, 'error', details)
        
        self.logger.error(log_entry)


# Global audit logger instance
audit_logger = AuditLogger()


def log_access(resource: str, action: str = 'read'):
    """
    Decorator to automatically log data access.
    
    Usage:
        @app.route('/api/data')
        @log_access(resource='customer_data', action='read')
        def get_data():
            return {'data': [...]}
    
    Args:
        resource: Resource being accessed
        action: Action being performed
        
    Returns:
        Decorator function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Execute the function
                result = f(*args, **kwargs)
                
                # Log successful access
                audit_logger.log_access(resource, action, success=True)
                
                return result
                
            except Exception as e:
                # Log failed access
                audit_logger.log_access(resource, action, success=False)
                audit_logger.log_error(type(e).__name__, str(e))
                raise
        
        return decorated_function
    return decorator


def log_query(f):
    """
    Decorator to automatically log query executions.
    
    Usage:
        @log_query
        def execute_sql(query):
            # ... execute query ...
            return result
    
    Returns:
        Decorator function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract query from args if possible
        query = args[0] if args else kwargs.get('sql', 'unknown')
        
        start_time = time.time()
        
        try:
            # Execute the function
            result = f(*args, **kwargs)
            
            execution_time = (time.time() - start_time) * 1000
            
            # Log successful query
            row_count = getattr(result, 'row_count', 0)
            audit_logger.log_query(
                query=str(query)[:500],
                success=True,
                execution_time_ms=execution_time,
                row_count=row_count
            )
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            # Log failed query
            audit_logger.log_query(
                query=str(query)[:500],
                success=False,
                execution_time_ms=execution_time,
                error=str(e)
            )
            raise
    
    return decorated_function


# Initialize audit logging
print(f"✅ Audit logging initialized. Logs: {LOG_DIR}")
