"""
Rate Limiting Module.
Prevents abuse and ensures fair usage of API resources.

SECURITY FEATURES:
- Sliding window rate limiting for accurate tracking
- Multiple rate limit tiers (per-second, per-minute, per-hour, per-day)
- IP-based and user-based rate limiting
- Automatic cleanup of expired entries
- DDoS protection through aggressive rate limits

COMPLIANCE:
- Prevents service abuse (SOC2 availability requirement)
- Protects against brute force attacks
- Ensures fair resource allocation
- Supports API usage billing and quota management
"""

import time
from collections import defaultdict, deque
from typing import Optional, Tuple
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify


class RateLimiter:
    """
    Implements sliding window rate limiting for API protection.
    
    SECURITY: Prevents:
    - Brute force attacks
    - DDoS attacks
    - API abuse and resource exhaustion
    - Credential stuffing
    - Data scraping
    """
    
    def __init__(self):
        # SECURITY: Track requests per identifier with sliding window
        # Key: identifier (IP or user_id)
        # Value: deque of timestamps
        self.request_history: defaultdict = defaultdict(lambda: {
            'second': deque(),
            'minute': deque(),
            'hour': deque(),
            'day': deque()
        })
        
        # SECURITY: Define rate limits for different tiers
        # Format: (requests, time_window_seconds)
        self.limits = {
            'default': {
                'second': (5, 1),      # 5 requests per second
                'minute': (60, 60),    # 60 requests per minute
                'hour': (1000, 3600),  # 1000 requests per hour
                'day': (10000, 86400)  # 10000 requests per day
            },
            'authenticated': {
                'second': (10, 1),
                'minute': (300, 60),
                'hour': (5000, 3600),
                'day': (50000, 86400)
            },
            'premium': {
                'second': (20, 1),
                'minute': (1000, 60),
                'hour': (20000, 3600),
                'day': (200000, 86400)
            },
            'admin': {
                'second': (50, 1),
                'minute': (5000, 60),
                'hour': (100000, 3600),
                'day': (1000000, 86400)
            }
        }
        
        # SECURITY: Track when last cleanup was performed
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # Cleanup every hour
    
    def _cleanup_old_entries(self, identifier: str):
        """
        Remove expired request timestamps to prevent memory growth.
        
        SECURITY: Prevents memory exhaustion attacks
        
        Args:
            identifier: IP address or user ID
        """
        now = time.time()
        
        # SECURITY: Only cleanup if interval has passed
        if now - self.last_cleanup < self.cleanup_interval:
            return
        
        history = self.request_history[identifier]
        
        # SECURITY: Remove timestamps older than 24 hours
        cutoff = now - 86400
        
        for window in ['second', 'minute', 'hour', 'day']:
            # Remove old timestamps from left of deque
            while history[window] and history[window][0] < cutoff:
                history[window].popleft()
        
        self.last_cleanup = now
    
    def _check_limit(
        self,
        identifier: str,
        window: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limit for a specific window.
        
        SECURITY: Sliding window algorithm for accurate rate limiting
        - More accurate than fixed window
        - Prevents burst attacks at window boundaries
        
        Args:
            identifier: IP address or user ID
            window: Time window ('second', 'minute', 'hour', 'day')
            max_requests: Maximum requests allowed in window
            window_seconds: Window size in seconds
            
        Returns:
            Tuple of (is_allowed, requests_made, retry_after_seconds)
        """
        now = time.time()
        history = self.request_history[identifier][window]
        
        # SECURITY: Remove timestamps outside the sliding window
        cutoff = now - window_seconds
        while history and history[0] < cutoff:
            history.popleft()
        
        # SECURITY: Count requests in current window
        requests_made = len(history)
        
        # SECURITY: Check if limit exceeded
        if requests_made >= max_requests:
            # Calculate when oldest request will expire
            if history:
                oldest_request = history[0]
                retry_after = int(oldest_request + window_seconds - now) + 1
            else:
                retry_after = window_seconds
            
            return False, requests_made, retry_after
        
        return True, requests_made, 0
    
    def is_allowed(
        self,
        identifier: str,
        tier: str = 'default'
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Check if request is allowed under rate limits.
        
        SECURITY: Checks all time windows (second, minute, hour, day)
        Request is only allowed if ALL windows are under limit
        
        Args:
            identifier: IP address or user ID
            tier: Rate limit tier ('default', 'authenticated', 'premium', 'admin')
            
        Returns:
            Tuple of (is_allowed, reason, retry_after_seconds)
        """
        # SECURITY: Validate tier
        if tier not in self.limits:
            tier = 'default'
        
        limits = self.limits[tier]
        
        # SECURITY: Check all time windows
        for window in ['second', 'minute', 'hour', 'day']:
            max_requests, window_seconds = limits[window]
            
            is_allowed, requests_made, retry_after = self._check_limit(
                identifier,
                window,
                max_requests,
                window_seconds
            )
            
            if not is_allowed:
                # SECURITY: Return specific rate limit violation
                reason = f"Rate limit exceeded: {requests_made}/{max_requests} requests per {window}"
                return False, reason, retry_after
        
        # SECURITY: Record this request
        now = time.time()
        for window in ['second', 'minute', 'hour', 'day']:
            self.request_history[identifier][window].append(now)
        
        # SECURITY: Periodic cleanup to prevent memory growth
        self._cleanup_old_entries(identifier)
        
        return True, None, None
    
    def get_usage_stats(self, identifier: str, tier: str = 'default') -> dict:
        """
        Get current usage statistics for an identifier.
        
        SECURITY: Used for:
        - User dashboard showing API usage
        - Billing and quota management
        - Detecting abuse patterns
        
        Args:
            identifier: IP address or user ID
            tier: Rate limit tier
            
        Returns:
            Dictionary with usage statistics
        """
        if tier not in self.limits:
            tier = 'default'
        
        limits = self.limits[tier]
        stats = {}
        
        now = time.time()
        history = self.request_history[identifier]
        
        # SECURITY: Calculate usage for each window
        for window in ['second', 'minute', 'hour', 'day']:
            max_requests, window_seconds = limits[window]
            
            # Count requests in window
            cutoff = now - window_seconds
            requests = sum(1 for ts in history[window] if ts > cutoff)
            
            stats[window] = {
                'requests': requests,
                'limit': max_requests,
                'remaining': max(0, max_requests - requests),
                'percentage': (requests / max_requests * 100) if max_requests > 0 else 0
            }
        
        return stats
    
    def reset_limits(self, identifier: str):
        """
        Reset rate limits for an identifier.
        
        SECURITY: Use cases:
        - Administrative override
        - User upgrade to higher tier
        - Testing and development
        - Incident response
        
        Args:
            identifier: IP address or user ID
        """
        if identifier in self.request_history:
            del self.request_history[identifier]


# SECURITY: Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(tier: str = 'default'):
    """
    Decorator to apply rate limiting to Flask routes.
    
    SECURITY: Automatically enforces rate limits on endpoints
    
    Usage:
        @app.route('/api/query')
        @rate_limit('authenticated')
        def query_endpoint():
            return {'result': 'data'}
    
    Args:
        tier: Rate limit tier to apply
        
    Returns:
        Decorated function with rate limiting
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # SECURITY: Identify user by token if authenticated, otherwise by IP
            identifier = None
            
            # Try to get user ID from JWT token
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split(' ')[1]
                    # Import here to avoid circular dependency
                    from .auth import auth_manager
                    payload = auth_manager.verify_token(token, 'access')
                    if payload:
                        identifier = f"user:{payload.get('sub')}"
                except Exception:
                    pass
            
            # SECURITY: Fall back to IP-based rate limiting
            if not identifier:
                # Get client IP considering proxies
                if request.headers.get('X-Forwarded-For'):
                    ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
                elif request.headers.get('X-Real-IP'):
                    ip = request.headers.get('X-Real-IP')
                else:
                    ip = request.remote_addr or 'unknown'
                
                identifier = f"ip:{ip}"
            
            # SECURITY: Check rate limit
            is_allowed, reason, retry_after = rate_limiter.is_allowed(identifier, tier)
            
            if not is_allowed:
                # SECURITY: Return 429 Too Many Requests with Retry-After header
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': reason,
                    'retry_after': retry_after
                })
                response.status_code = 429
                
                # SECURITY: Standard Retry-After header
                if retry_after:
                    response.headers['Retry-After'] = str(retry_after)
                
                # SECURITY: Rate limit headers for client information
                response.headers['X-RateLimit-Limit'] = '100'
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(int(time.time() + retry_after))
                
                return response
            
            # SECURITY: Add rate limit headers to successful response
            stats = rate_limiter.get_usage_stats(identifier, tier)
            
            result = f(*args, **kwargs)
            
            # Add headers if result is a Response object
            if hasattr(result, 'headers'):
                minute_stats = stats.get('minute', {})
                result.headers['X-RateLimit-Limit'] = str(minute_stats.get('limit', 100))
                result.headers['X-RateLimit-Remaining'] = str(minute_stats.get('remaining', 0))
            
            return result
        
        return decorated_function
    return decorator


def get_rate_limit_status(identifier: str, tier: str = 'default') -> dict:
    """
    Get rate limit status for monitoring and dashboards.
    
    Args:
        identifier: IP address or user ID
        tier: Rate limit tier
        
    Returns:
        Rate limit status dictionary
    """
    stats = rate_limiter.get_usage_stats(identifier, tier)
    
    # SECURITY: Add warnings for approaching limits
    warnings = []
    for window, data in stats.items():
        if data['percentage'] > 90:
            warnings.append(f"Approaching {window} limit: {data['percentage']:.1f}%")
    
    return {
        'usage': stats,
        'warnings': warnings,
        'tier': tier
    }
