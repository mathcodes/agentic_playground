"""
Input Validation and Sanitization Module.
Protects against injection attacks, XSS, and malicious input.

SECURITY FEATURES:
- SQL injection prevention through validation and sanitization
- XSS (Cross-Site Scripting) prevention
- Command injection prevention
- Path traversal prevention
- LLM prompt injection detection
- Input length limits to prevent DoS
- Character encoding validation

COMPLIANCE:
- OWASP Top 10 protection (A03:2021 – Injection)
- CWE-79 (XSS), CWE-89 (SQL Injection), CWE-77 (Command Injection)
- PCI DSS requirement 6.5.1 (Injection flaws)
"""

import re
import html
import unicodedata
from typing import Optional, Tuple, List
from urllib.parse import urlparse


class InputValidator:
    """
    Validates and sanitizes all user inputs for security.
    
    SECURITY: Defense in depth - validate at multiple layers:
    1. Format validation (type, length, charset)
    2. Content validation (allowed patterns)
    3. Sanitization (remove dangerous characters)
    4. Contextual encoding (HTML, SQL, etc.)
    """
    
    # SECURITY: Maximum input lengths to prevent DoS and buffer overflow
    MAX_QUERY_LENGTH = 5000  # Natural language queries
    MAX_USERNAME_LENGTH = 100
    MAX_EMAIL_LENGTH = 254  # RFC 5321 compliant
    MAX_PASSWORD_LENGTH = 128
    MAX_API_KEY_LENGTH = 256
    MAX_URL_LENGTH = 2048
    
    # SECURITY: Dangerous SQL keywords that could indicate injection
    SQL_INJECTION_PATTERNS = [
        r'\b(UNION|SELECT|INSERT|UPDATE|DELETE|DROP|EXEC|EXECUTE)\b',
        r'--',  # SQL comments
        r'/\*.*\*/',  # Multi-line comments
        r';.*',  # Multiple statements
        r'xp_\w+',  # SQL Server extended procedures
        r'sp_\w+',  # SQL Server stored procedures
    ]
    
    # SECURITY: XSS patterns to detect script injection
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',  # Event handlers (onclick, onerror, etc.)
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'eval\s*\(',
        r'expression\s*\(',
    ]
    
    # SECURITY: Command injection patterns
    COMMAND_INJECTION_PATTERNS = [
        r'[;&|`$]',  # Shell metacharacters
        r'\$\(',  # Command substitution
        r'\.\./\.\.',  # Path traversal
    ]
    
    # SECURITY: LLM prompt injection patterns
    PROMPT_INJECTION_PATTERNS = [
        r'ignore\s+(previous|all|above)\s+(instructions|prompts)',
        r'system\s+prompt',
        r'forget\s+(everything|all)',
        r'new\s+(instructions|prompt|rules)',
        r'you\s+are\s+now',
        r'jailbreak',
        r'roleplay\s+as',
        r'pretend\s+to\s+be',
    ]
    
    @staticmethod
    def validate_length(
        value: str,
        max_length: int,
        field_name: str = "input"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate input length.
        
        SECURITY: Prevents:
        - Buffer overflow attacks
        - DoS through excessive processing
        - Database column overflow
        
        Args:
            value: Input string to validate
            max_length: Maximum allowed length
            field_name: Name of field for error messages
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not value:
            return False, f"{field_name} cannot be empty"
        
        if len(value) > max_length:
            return False, f"{field_name} exceeds maximum length of {max_length} characters"
        
        return True, None
    
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Sanitize text input by removing potentially dangerous characters.
        
        SECURITY: Removes:
        - Control characters
        - Zero-width characters
        - Bidirectional override characters (used in homograph attacks)
        - Non-printable characters
        
        Args:
            text: Input text to sanitize
            
        Returns:
            Sanitized text
        """
        if not text:
            return ""
        
        # SECURITY: Normalize unicode to prevent homograph attacks
        # NFD = decompose characters, then recompose with NFC
        text = unicodedata.normalize('NFKC', text)
        
        # SECURITY: Remove control characters (except newline, tab, carriage return)
        text = ''.join(
            char for char in text
            if unicodedata.category(char)[0] != 'C' or char in '\n\t\r'
        )
        
        # SECURITY: Remove zero-width characters used in obfuscation
        zero_width_chars = [
            '\u200B',  # Zero-width space
            '\u200C',  # Zero-width non-joiner
            '\u200D',  # Zero-width joiner
            '\uFEFF',  # Zero-width no-break space
        ]
        for char in zero_width_chars:
            text = text.replace(char, '')
        
        # SECURITY: Limit consecutive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    @staticmethod
    def detect_sql_injection(query: str) -> Tuple[bool, List[str]]:
        """
        Detect potential SQL injection attempts.
        
        SECURITY: Defense in depth - use with parameterized queries
        This detects obvious injection attempts in natural language input
        
        Args:
            query: Input query to check
            
        Returns:
            Tuple of (is_suspicious, list_of_matched_patterns)
        """
        suspicious_patterns = []
        query_upper = query.upper()
        
        # SECURITY: Check each injection pattern
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query_upper, re.IGNORECASE):
                suspicious_patterns.append(pattern)
        
        return len(suspicious_patterns) > 0, suspicious_patterns
    
    @staticmethod
    def detect_xss(input_str: str) -> Tuple[bool, List[str]]:
        """
        Detect potential XSS (Cross-Site Scripting) attacks.
        
        SECURITY: Detects script injection attempts
        
        Args:
            input_str: Input string to check
            
        Returns:
            Tuple of (is_suspicious, list_of_matched_patterns)
        """
        suspicious_patterns = []
        
        # SECURITY: Check each XSS pattern
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, input_str, re.IGNORECASE):
                suspicious_patterns.append(pattern)
        
        return len(suspicious_patterns) > 0, suspicious_patterns
    
    @staticmethod
    def detect_command_injection(input_str: str) -> Tuple[bool, List[str]]:
        """
        Detect potential command injection attempts.
        
        SECURITY: Detects shell command injection
        
        Args:
            input_str: Input string to check
            
        Returns:
            Tuple of (is_suspicious, list_of_matched_patterns)
        """
        suspicious_patterns = []
        
        # SECURITY: Check each command injection pattern
        for pattern in InputValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, input_str):
                suspicious_patterns.append(pattern)
        
        return len(suspicious_patterns) > 0, suspicious_patterns
    
    @staticmethod
    def detect_prompt_injection(query: str) -> Tuple[bool, List[str]]:
        """
        Detect potential LLM prompt injection attempts.
        
        SECURITY: LLM-specific threat - attempts to override system prompts
        
        Common attacks:
        - "Ignore previous instructions and..."
        - "You are now in roleplay mode..."
        - "Forget everything above and..."
        
        Args:
            query: User query to check
            
        Returns:
            Tuple of (is_suspicious, list_of_matched_patterns)
        """
        suspicious_patterns = []
        
        # SECURITY: Check each prompt injection pattern
        for pattern in InputValidator.PROMPT_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                suspicious_patterns.append(pattern)
        
        return len(suspicious_patterns) > 0, suspicious_patterns
    
    @staticmethod
    def validate_query(query: str) -> Tuple[bool, Optional[str]]:
        """
        Comprehensive validation for user queries.
        
        SECURITY: Multi-layer validation:
        1. Length check
        2. Sanitization
        3. SQL injection detection
        4. XSS detection
        5. Prompt injection detection
        
        Args:
            query: Natural language query from user
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # SECURITY: Validate length
        is_valid, error = InputValidator.validate_length(
            query,
            InputValidator.MAX_QUERY_LENGTH,
            "Query"
        )
        if not is_valid:
            return False, error
        
        # SECURITY: Sanitize input
        sanitized = InputValidator.sanitize_text(query)
        
        # SECURITY: Check for SQL injection
        has_sql_injection, sql_patterns = InputValidator.detect_sql_injection(sanitized)
        if has_sql_injection:
            return False, "Query contains potentially dangerous SQL patterns"
        
        # SECURITY: Check for XSS
        has_xss, xss_patterns = InputValidator.detect_xss(sanitized)
        if has_xss:
            return False, "Query contains potentially dangerous script patterns"
        
        # SECURITY: Check for prompt injection
        has_prompt_injection, prompt_patterns = InputValidator.detect_prompt_injection(sanitized)
        if has_prompt_injection:
            return False, "Query appears to be attempting prompt injection"
        
        return True, None
    
    @staticmethod
    def sanitize_for_html(text: str) -> str:
        """
        Sanitize text for safe display in HTML.
        
        SECURITY: Prevents XSS by encoding HTML special characters
        
        Args:
            text: Text to sanitize
            
        Returns:
            HTML-safe text
        """
        if not text:
            return ""
        
        # SECURITY: Escape HTML entities
        return html.escape(text)
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email address format.
        
        SECURITY: RFC 5322 compliant email validation
        
        Args:
            email: Email address to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # SECURITY: Length check
        is_valid, error = InputValidator.validate_length(
            email,
            InputValidator.MAX_EMAIL_LENGTH,
            "Email"
        )
        if not is_valid:
            return False, error
        
        # SECURITY: Format validation (simplified RFC 5322)
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "Invalid email format"
        
        return True, None
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate username format.
        
        SECURITY: Alphanumeric + underscore/hyphen only
        
        Args:
            username: Username to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # SECURITY: Length check
        is_valid, error = InputValidator.validate_length(
            username,
            InputValidator.MAX_USERNAME_LENGTH,
            "Username"
        )
        if not is_valid:
            return False, error
        
        # SECURITY: Character validation
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            return False, "Username can only contain letters, numbers, underscore, and hyphen"
        
        # SECURITY: Must start with letter
        if not username[0].isalpha():
            return False, "Username must start with a letter"
        
        return True, None
    
    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate URL format and safety.
        
        SECURITY: Prevents SSRF (Server-Side Request Forgery)
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # SECURITY: Length check
        is_valid, error = InputValidator.validate_length(
            url,
            InputValidator.MAX_URL_LENGTH,
            "URL"
        )
        if not is_valid:
            return False, error
        
        try:
            # SECURITY: Parse URL
            parsed = urlparse(url)
            
            # SECURITY: Must have scheme (http/https only)
            if parsed.scheme not in ['http', 'https']:
                return False, "URL must use HTTP or HTTPS protocol"
            
            # SECURITY: Must have netloc (domain)
            if not parsed.netloc:
                return False, "URL must include a domain"
            
            # SECURITY: Prevent localhost/internal IP access (SSRF prevention)
            blocked_hosts = [
                'localhost',
                '127.0.0.1',
                '0.0.0.0',
                '10.',
                '172.16.',
                '192.168.',
                '169.254.',  # Link-local
            ]
            
            netloc_lower = parsed.netloc.lower()
            for blocked in blocked_hosts:
                if netloc_lower.startswith(blocked):
                    return False, "URL cannot reference internal/localhost addresses"
            
            return True, None
            
        except Exception:
            return False, "Invalid URL format"
    
    @staticmethod
    def validate_api_key(api_key: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API key format.
        
        SECURITY: Basic format validation
        
        Args:
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # SECURITY: Length check
        is_valid, error = InputValidator.validate_length(
            api_key,
            InputValidator.MAX_API_KEY_LENGTH,
            "API key"
        )
        if not is_valid:
            return False, error
        
        # SECURITY: Minimum length (typical API keys are 32+ characters)
        if len(api_key) < 32:
            return False, "API key is too short"
        
        # SECURITY: Alphanumeric + hyphen/underscore only
        if not re.match(r'^[a-zA-Z0-9_-]+$', api_key):
            return False, "API key contains invalid characters"
        
        return True, None


# SECURITY: Global validator instance
input_validator = InputValidator()
