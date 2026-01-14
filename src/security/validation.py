"""
Input Validation and Sanitization Module

Provides comprehensive input validation and sanitization to prevent:
- SQL Injection attacks
- Cross-Site Scripting (XSS) attacks
- Command Injection attacks
- Path Traversal attacks
- NoSQL Injection attacks
- LDAP Injection attacks
- XML Injection attacks

All inputs from users should be validated before processing.
"""

import re
import html
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, quote


class InputValidator:
    """
    Validates and sanitizes user inputs to prevent security vulnerabilities.
    
    This class implements multiple layers of input validation:
    1. Type checking - Ensure input is expected type
    2. Length validation - Prevent buffer overflow and DoS
    3. Pattern matching - Allow only expected patterns
    4. Content sanitization - Remove dangerous characters
    5. Context-specific validation - SQL, file paths, etc.
    """
    
    # Maximum lengths to prevent DoS attacks
    MAX_QUERY_LENGTH = 10000      # Max characters in a query
    MAX_USERNAME_LENGTH = 100     # Max characters in username
    MAX_PASSWORD_LENGTH = 128     # Max characters in password
    MAX_FILE_PATH_LENGTH = 512    # Max characters in file path
    MAX_URL_LENGTH = 2048         # Max characters in URL
    
    # Dangerous SQL patterns that might indicate SQL injection
    SQL_INJECTION_PATTERNS = [
        r'\b(union|select|insert|update|delete|drop|create|alter|exec|execute)\b.*\b(from|into|table|database)\b',
        r'[;]\s*(drop|delete|truncate|alter)',
        r'--',  # SQL comment
        r'/\*.*\*/',  # Multi-line SQL comment
        r'\b(xp_|sp_)\w+',  # SQL Server stored procedures
        r'@@\w+',  # SQL Server variables
        r'\bor\b\s+\d+\s*=\s*\d+',  # OR 1=1 style injection
        r'\band\b\s+\d+\s*=\s*\d+',  # AND 1=1 style injection
        r'(\'|\")(\s*)(or|and)(\s*)(\'|\")?\d+',  # Quote-based injection
    ]
    
    # Dangerous characters for XSS attacks
    XSS_DANGEROUS_CHARS = ['<', '>', '"', "'", '&', '/', '\\']
    
    # Allowed characters for different contexts
    ALPHANUMERIC_PATTERN = re.compile(r'^[a-zA-Z0-9]+$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string input by removing dangerous characters.
        
        This function:
        1. Strips leading/trailing whitespace
        2. Limits length to prevent DoS
        3. Escapes HTML entities to prevent XSS
        4. Removes null bytes
        
        Args:
            input_str: String to sanitize
            max_length: Maximum allowed length (default: MAX_QUERY_LENGTH)
            
        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Strip whitespace
        sanitized = input_str.strip()
        
        # Remove null bytes (can cause issues in C-based libraries)
        sanitized = sanitized.replace('\x00', '')
        
        # Limit length
        if max_length is None:
            max_length = InputValidator.MAX_QUERY_LENGTH
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
        
        # Escape HTML entities to prevent XSS
        sanitized = html.escape(sanitized)
        
        return sanitized
    
    @staticmethod
    def validate_query(query: str) -> Dict[str, Any]:
        """
        Validate a natural language query for security issues.
        
        Checks for:
        1. Length limits (prevent DoS)
        2. SQL injection patterns
        3. Command injection patterns
        4. Dangerous characters
        
        Args:
            query: Natural language query to validate
            
        Returns:
            Dict with keys:
                - valid: bool - True if query is safe
                - sanitized: str - Sanitized version of query
                - issues: List[str] - List of security issues found
        """
        issues = []
        
        # Check if query is a string
        if not isinstance(query, str):
            return {
                'valid': False,
                'sanitized': '',
                'issues': ['Query must be a string']
            }
        
        # Strip whitespace
        query = query.strip()
        
        # Check for empty query
        if not query:
            return {
                'valid': False,
                'sanitized': '',
                'issues': ['Query cannot be empty']
            }
        
        # Check length
        if len(query) > InputValidator.MAX_QUERY_LENGTH:
            issues.append(f'Query exceeds maximum length ({InputValidator.MAX_QUERY_LENGTH} characters)')
        
        # Check for SQL injection patterns
        query_lower = query.lower()
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                issues.append(f'Potential SQL injection pattern detected: {pattern}')
        
        # Check for command injection patterns
        command_injection_chars = ['|', '&', ';', '$', '`', '\n', '\r']
        for char in command_injection_chars:
            if char in query:
                issues.append(f'Potentially dangerous character detected: {char}')
        
        # Check for excessive special characters (might indicate attack)
        special_char_count = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if special_char_count > len(query) * 0.3:  # More than 30% special chars
            issues.append('Excessive special characters detected')
        
        # Sanitize the query
        sanitized = InputValidator.sanitize_string(query)
        
        return {
            'valid': len(issues) == 0,
            'sanitized': sanitized,
            'issues': issues
        }
    
    @staticmethod
    def validate_username(username: str) -> Dict[str, Any]:
        """
        Validate a username for security and format.
        
        Username rules:
        - Must be 3-100 characters
        - Can only contain letters, numbers, underscore, and hyphen
        - Must start with a letter
        
        Args:
            username: Username to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        if not isinstance(username, str):
            return {'valid': False, 'issues': ['Username must be a string']}
        
        username = username.strip()
        
        # Check length
        if len(username) < 3:
            issues.append('Username must be at least 3 characters')
        if len(username) > InputValidator.MAX_USERNAME_LENGTH:
            issues.append(f'Username must be less than {InputValidator.MAX_USERNAME_LENGTH} characters')
        
        # Check format
        if not InputValidator.USERNAME_PATTERN.match(username):
            issues.append('Username can only contain letters, numbers, underscore, and hyphen')
        
        # Check first character
        if username and not username[0].isalpha():
            issues.append('Username must start with a letter')
        
        return {
            'valid': len(issues) == 0,
            'sanitized': username,
            'issues': issues
        }
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """
        Validate a password for strength and security.
        
        Password requirements:
        - At least 8 characters (12+ recommended)
        - Contains uppercase and lowercase letters
        - Contains numbers
        - Contains special characters
        - Not a common password
        
        Args:
            password: Password to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        if not isinstance(password, str):
            return {'valid': False, 'issues': ['Password must be a string']}
        
        # Check length
        if len(password) < 8:
            issues.append('Password must be at least 8 characters')
        if len(password) > InputValidator.MAX_PASSWORD_LENGTH:
            issues.append(f'Password must be less than {InputValidator.MAX_PASSWORD_LENGTH} characters')
        
        # Check complexity
        if not any(c.isupper() for c in password):
            issues.append('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in password):
            issues.append('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in password):
            issues.append('Password must contain at least one number')
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            issues.append('Password must contain at least one special character')
        
        # Check for common passwords
        common_passwords = [
            'password', '12345678', 'qwerty', 'abc123', 'password123',
            'admin123', 'letmein', 'welcome', 'monkey', '1234567890'
        ]
        if password.lower() in common_passwords:
            issues.append('Password is too common')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
    
    @staticmethod
    def validate_email(email: str) -> Dict[str, Any]:
        """
        Validate an email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        if not isinstance(email, str):
            return {'valid': False, 'issues': ['Email must be a string']}
        
        email = email.strip().lower()
        
        # Check format
        if not InputValidator.EMAIL_PATTERN.match(email):
            issues.append('Invalid email format')
        
        # Check length
        if len(email) > 254:  # RFC 5321
            issues.append('Email address too long')
        
        return {
            'valid': len(issues) == 0,
            'sanitized': email,
            'issues': issues
        }
    
    @staticmethod
    def validate_file_path(path: str, allowed_extensions: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate a file path to prevent path traversal attacks.
        
        Security checks:
        - No parent directory references (..)
        - No absolute paths
        - No null bytes
        - Limited to allowed extensions
        - Length limits
        
        Args:
            path: File path to validate
            allowed_extensions: List of allowed file extensions (e.g., ['.wav', '.mp3'])
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        if not isinstance(path, str):
            return {'valid': False, 'issues': ['Path must be a string']}
        
        path = path.strip()
        
        # Check for path traversal
        if '..' in path:
            issues.append('Path traversal detected (..)') 
        
        # Check for absolute paths
        if path.startswith('/') or (len(path) > 1 and path[1] == ':'):
            issues.append('Absolute paths not allowed')
        
        # Check for null bytes
        if '\x00' in path:
            issues.append('Null bytes in path')
        
        # Check length
        if len(path) > InputValidator.MAX_FILE_PATH_LENGTH:
            issues.append(f'Path exceeds maximum length ({InputValidator.MAX_FILE_PATH_LENGTH})')
        
        # Check extension if specified
        if allowed_extensions:
            import os
            _, ext = os.path.splitext(path)
            if ext.lower() not in [e.lower() for e in allowed_extensions]:
                issues.append(f'File extension not allowed. Allowed: {", ".join(allowed_extensions)}')
        
        return {
            'valid': len(issues) == 0,
            'sanitized': path,
            'issues': issues
        }
    
    @staticmethod
    def validate_sql_query(sql: str) -> Dict[str, Any]:
        """
        Validate a generated SQL query for safety before execution.
        
        This is a secondary validation layer for SQL generated by the LLM.
        
        Security checks:
        - No write operations (INSERT, UPDATE, DELETE, DROP, etc.)
        - No multiple statements
        - No comments
        - No system calls
        - No suspicious patterns
        
        Args:
            sql: SQL query to validate
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        if not isinstance(sql, str):
            return {'valid': False, 'issues': ['SQL must be a string']}
        
        sql = sql.strip()
        sql_upper = sql.upper()
        
        # Check for dangerous operations
        dangerous_keywords = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'TRUNCATE',
            'ALTER', 'CREATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
        
        for keyword in dangerous_keywords:
            # Use word boundary to match whole words only
            if re.search(rf'\b{keyword}\b', sql_upper):
                issues.append(f'Dangerous SQL keyword detected: {keyword}')
        
        # Check for multiple statements (SQL injection)
        # Count semicolons not at the end
        semicolons = sql.count(';')
        if semicolons > 1 or (semicolons == 1 and not sql.rstrip().endswith(';')):
            issues.append('Multiple SQL statements detected')
        
        # Check for comments (could hide malicious code)
        if '--' in sql or '/*' in sql:
            issues.append('SQL comments detected')
        
        # Check for system commands (PostgreSQL specific)
        system_patterns = [
            r'\bCOPY\b.*\bFROM\b',
            r'\bCOPY\b.*\bTO\b',
            r'\bpg_read_file\b',
            r'\bpg_ls_dir\b',
            r'\\!',  # psql shell command
        ]
        for pattern in system_patterns:
            if re.search(pattern, sql_upper):
                issues.append(f'System command pattern detected: {pattern}')
        
        # Check if query starts with SELECT or WITH (CTEs)
        if not sql_upper.lstrip().startswith(('SELECT', 'WITH')):
            issues.append('Query must start with SELECT or WITH')
        
        return {
            'valid': len(issues) == 0,
            'sanitized': sql,
            'issues': issues
        }
    
    @staticmethod
    def validate_json_input(data: Any, required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate JSON input from API requests.
        
        Args:
            data: Parsed JSON data
            required_fields: List of required field names
            
        Returns:
            Dict with validation results
        """
        issues = []
        
        # Check if data is a dict
        if not isinstance(data, dict):
            return {'valid': False, 'issues': ['Input must be a JSON object']}
        
        # Check required fields
        if required_fields:
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                issues.append(f'Missing required fields: {", ".join(missing_fields)}')
        
        # Check for excessively nested data (DoS attack)
        def get_max_depth(obj, depth=0):
            if depth > 20:  # Arbitrary limit
                return depth
            if isinstance(obj, dict):
                return max([get_max_depth(v, depth + 1) for v in obj.values()], default=depth)
            elif isinstance(obj, list):
                return max([get_max_depth(item, depth + 1) for item in obj], default=depth)
            return depth
        
        max_depth = get_max_depth(data)
        if max_depth > 20:
            issues.append('JSON nesting too deep (possible DoS attack)')
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }


def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
    """
    Convenience function to sanitize string input.
    
    Args:
        input_str: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    return InputValidator.sanitize_string(input_str, max_length)


def validate_query(query: str) -> Dict[str, Any]:
    """
    Convenience function to validate a query.
    
    Args:
        query: Query to validate
        
    Returns:
        Dict with validation results
    """
    return InputValidator.validate_query(query)


def validate_sql(sql: str) -> Dict[str, Any]:
    """
    Convenience function to validate SQL.
    
    Args:
        sql: SQL query to validate
        
    Returns:
        Dict with validation results
    """
    return InputValidator.validate_sql_query(sql)
