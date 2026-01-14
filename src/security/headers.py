"""
Security Headers Module

Implements secure HTTP headers to protect against common web vulnerabilities.

Security Headers:
- Content-Security-Policy (CSP): Prevents XSS attacks
- X-Content-Type-Options: Prevents MIME sniffing
- X-Frame-Options: Prevents clickjacking
- X-XSS-Protection: Enables browser XSS protection
- Strict-Transport-Security (HSTS): Forces HTTPS
- Referrer-Policy: Controls referrer information
- Permissions-Policy: Controls browser features

Compliance:
- OWASP Top 10: Addresses multiple vulnerabilities
- PCI DSS: Requires secure headers
- NIST: Recommends security headers
"""

from flask import Flask
from typing import Dict, Optional


class SecurityHeaders:
    """
    Manages security headers for Flask applications.
    
    Implements OWASP recommended security headers to protect against:
    - Cross-Site Scripting (XSS)
    - Clickjacking
    - MIME sniffing attacks
    - Man-in-the-middle attacks
    - Information leakage
    """
    
    # Default secure headers configuration
    DEFAULT_HEADERS = {
        # Content Security Policy - Prevents XSS and injection attacks
        # This policy:
        # - Allows scripts only from same origin
        # - Allows styles only from same origin and inline styles (for UI frameworks)
        # - Allows images from same origin and data URIs
        # - Blocks all other content types by default
        'Content-Security-Policy': (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # unsafe-inline needed for some JS frameworks
            "style-src 'self' 'unsafe-inline'; "   # unsafe-inline needed for some CSS frameworks
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "  # Prevents embedding in iframes (clickjacking)
            "base-uri 'self'; "
            "form-action 'self'"
        ),
        
        # X-Content-Type-Options - Prevents MIME sniffing
        # Browsers will not try to guess the MIME type, preventing attacks
        # where malicious files are disguised as safe types
        'X-Content-Type-Options': 'nosniff',
        
        # X-Frame-Options - Prevents clickjacking attacks
        # DENY: Page cannot be displayed in a frame (most secure)
        # SAMEORIGIN: Page can only be displayed in a frame on the same origin
        'X-Frame-Options': 'DENY',
        
        # X-XSS-Protection - Enables browser's XSS filter
        # 1; mode=block: If XSS is detected, block the page
        # Note: Modern browsers prefer CSP, but this adds defense in depth
        'X-XSS-Protection': '1; mode=block',
        
        # Strict-Transport-Security (HSTS) - Forces HTTPS
        # max-age=31536000: Remember HTTPS preference for 1 year
        # includeSubDomains: Apply to all subdomains
        # preload: Allow inclusion in browser HSTS preload lists
        # WARNING: Only enable in production with valid HTTPS certificate
        # 'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        
        # Referrer-Policy - Controls referrer information
        # strict-origin-when-cross-origin: 
        # - Send full URL for same-origin requests
        # - Send only origin for cross-origin HTTPS requests
        # - Send nothing for HTTPS to HTTP
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        
        # Permissions-Policy (formerly Feature-Policy)
        # Restricts which browser features can be used
        # This prevents the page from using:
        # - Camera, microphone (privacy)
        # - Geolocation (privacy)
        # - Payment APIs (security)
        # - USB, MIDI devices (security)
        'Permissions-Policy': (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), "
            "gyroscope=(), accelerometer=()"
        ),
        
        # Cache-Control - Prevents caching of sensitive data
        # no-store: Don't cache anything
        # no-cache: Revalidate before using cached content
        # must-revalidate: Must revalidate stale content
        # private: Only cache in browser, not in shared caches
        'Cache-Control': 'no-store, no-cache, must-revalidate, private',
        
        # Pragma - HTTP/1.0 cache control (for older clients)
        'Pragma': 'no-cache',
        
        # Expires - Set to past date to prevent caching
        'Expires': '0',
    }
    
    def __init__(self, custom_headers: Optional[Dict[str, str]] = None):
        """
        Initialize security headers.
        
        Args:
            custom_headers: Optional dict of custom headers to override defaults
        """
        self.headers = self.DEFAULT_HEADERS.copy()
        
        # Apply custom headers
        if custom_headers:
            self.headers.update(custom_headers)
    
    def add_header(self, name: str, value: str):
        """
        Add or update a security header.
        
        Args:
            name: Header name
            value: Header value
        """
        self.headers[name] = value
    
    def remove_header(self, name: str):
        """
        Remove a security header.
        
        Args:
            name: Header name to remove
        """
        if name in self.headers:
            del self.headers[name]
    
    def get_headers(self) -> Dict[str, str]:
        """
        Get all configured security headers.
        
        Returns:
            Dict of headers
        """
        return self.headers.copy()
    
    def enable_hsts(self, max_age: int = 31536000, include_subdomains: bool = True, 
                   preload: bool = False):
        """
        Enable HTTP Strict Transport Security (HSTS).
        
        WARNING: Only enable in production with valid HTTPS certificate.
        Enabling HSTS without proper HTTPS can lock users out of your site.
        
        Args:
            max_age: How long (in seconds) browsers should remember to use HTTPS
            include_subdomains: Apply to all subdomains
            preload: Allow inclusion in browser HSTS preload lists
        """
        hsts_value = f'max-age={max_age}'
        
        if include_subdomains:
            hsts_value += '; includeSubDomains'
        
        if preload:
            hsts_value += '; preload'
        
        self.headers['Strict-Transport-Security'] = hsts_value
    
    def configure_cors(self, allowed_origins: list = None, 
                      allowed_methods: list = None,
                      allowed_headers: list = None,
                      allow_credentials: bool = False,
                      max_age: int = 3600):
        """
        Configure CORS headers.
        
        CORS (Cross-Origin Resource Sharing) controls which origins can access the API.
        
        Security Note:
        - Never use '*' for allowed_origins in production with credentials
        - Be specific about allowed origins
        - Limit allowed methods and headers
        
        Args:
            allowed_origins: List of allowed origins (default: same origin only)
            allowed_methods: List of allowed HTTP methods
            allowed_headers: List of allowed headers
            allow_credentials: Whether to allow credentials (cookies, auth)
            max_age: How long browsers can cache preflight requests
        """
        if allowed_origins is None:
            # Default: same origin only (most secure)
            allowed_origins = []
        
        if allowed_methods is None:
            # Default: safe methods only
            allowed_methods = ['GET', 'POST', 'OPTIONS']
        
        if allowed_headers is None:
            # Default: common safe headers
            allowed_headers = ['Content-Type', 'Authorization']
        
        # Set CORS headers
        if allowed_origins:
            # Join multiple origins with comma (or use '*' if all allowed)
            origins_value = ', '.join(allowed_origins) if allowed_origins != ['*'] else '*'
            self.headers['Access-Control-Allow-Origin'] = origins_value
        
        self.headers['Access-Control-Allow-Methods'] = ', '.join(allowed_methods)
        self.headers['Access-Control-Allow-Headers'] = ', '.join(allowed_headers)
        self.headers['Access-Control-Max-Age'] = str(max_age)
        
        if allow_credentials:
            self.headers['Access-Control-Allow-Credentials'] = 'true'
    
    def apply_to_response(self, response):
        """
        Apply security headers to a Flask response object.
        
        Args:
            response: Flask response object
            
        Returns:
            Response with headers added
        """
        for name, value in self.headers.items():
            response.headers[name] = value
        
        return response


def configure_security_headers(app: Flask, 
                              custom_headers: Optional[Dict[str, str]] = None,
                              enable_hsts: bool = False,
                              cors_config: Optional[Dict] = None):
    """
    Configure security headers for a Flask application.
    
    This function sets up an after_request handler that adds security headers
    to all responses automatically.
    
    Usage:
        app = Flask(__name__)
        configure_security_headers(app)
    
    Args:
        app: Flask application instance
        custom_headers: Optional custom headers to override defaults
        enable_hsts: Whether to enable HSTS (only for production with HTTPS)
        cors_config: Optional CORS configuration dict
    """
    # Create security headers instance
    sec_headers = SecurityHeaders(custom_headers)
    
    # Enable HSTS if requested (only for production)
    if enable_hsts:
        sec_headers.enable_hsts()
    
    # Configure CORS if requested
    if cors_config:
        sec_headers.configure_cors(**cors_config)
    
    # Add after_request handler to apply headers to all responses
    @app.after_request
    def add_security_headers(response):
        """
        After-request handler to add security headers to all responses.
        
        This runs after every request and adds security headers before
        sending the response to the client.
        
        Args:
            response: Flask response object
            
        Returns:
            Response with security headers added
        """
        return sec_headers.apply_to_response(response)
    
    print("✅ Security headers configured")
    
    return sec_headers


def get_recommended_csp_for_development() -> str:
    """
    Get a relaxed CSP policy for development.
    
    This policy is less strict to allow development tools like:
    - Live reload
    - Browser dev tools
    - Local debugging
    
    WARNING: Never use this in production!
    
    Returns:
        CSP policy string
    """
    return (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # unsafe-eval for dev tools
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https: http:; "
        "font-src 'self' data:; "
        "connect-src 'self' ws: wss:; "  # WebSocket for live reload
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )


def get_recommended_csp_for_production() -> str:
    """
    Get a strict CSP policy for production.
    
    This policy is very strict and may need customization based on
    your specific needs (e.g., if using CDNs, analytics, etc.)
    
    Returns:
        CSP policy string
    """
    return (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "upgrade-insecure-requests"  # Upgrade HTTP to HTTPS
    )


# Example usage
if __name__ == "__main__":
    from flask import Flask, jsonify
    
    print("Testing Security Headers Module")
    print("=" * 60)
    
    # Create test app
    app = Flask(__name__)
    
    @app.route('/test')
    def test():
        return jsonify({'message': 'Test endpoint'})
    
    # Configure security headers
    configure_security_headers(
        app,
        enable_hsts=False,  # Disable HSTS for testing
        cors_config={
            'allowed_origins': ['http://localhost:3000'],
            'allowed_methods': ['GET', 'POST'],
            'allow_credentials': True
        }
    )
    
    # Test request
    with app.test_client() as client:
        response = client.get('/test')
        
        print("\nResponse Headers:")
        for header, value in response.headers:
            if header.startswith(('Content-Security', 'X-', 'Access-Control', 
                                'Strict-Transport', 'Referrer', 'Permissions')):
                print(f"  {header}: {value}")
    
    print("\n" + "=" * 60)
    print("✅ Security headers test complete!")
