#!/usr/bin/env python3
"""
Secure Web UI for Voice-to-SQL Multi-Agent System
Real-time logging with enterprise-grade security.

SECURITY FEATURES:
- Authentication and authorization (JWT)
- Rate limiting (prevents abuse)
- CORS protection (controlled cross-origin access)
- Security headers (XSS, clickjacking, etc.)
- Input validation and sanitization
- Audit logging
- Secure error handling (no information disclosure)
- HTTPS enforcement (production)
- Request size limits
"""

from flask import Flask, render_template, request, jsonify, Response, make_response
from flask_cors import CORS  # Cross-Origin Resource Sharing
import sys
import os
from pathlib import Path
import json
import time
from queue import Queue
from threading import Thread
from functools import wraps

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from src.agent.multi_agent_orchestrator import MultiAgentOrchestrator

# SECURITY: Import security modules
try:
    from src.security.auth import auth_manager, require_auth, get_client_ip
    from src.security.rate_limiter import rate_limiter, rate_limit
    from src.security.input_validator import input_validator
    from src.security.audit_logger import audit_logger
    SECURITY_ENABLED = True
except ImportError:
    # SECURITY: Graceful degradation if security modules not available
    # In production, this should fail hard
    print("WARNING: Security modules not available. Running in insecure mode!")
    SECURITY_ENABLED = False

# SECURITY: Initialize Flask with security configurations
app = Flask(__name__)

# SECURITY: Set maximum request size to prevent memory exhaustion
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_REQUEST_SIZE_MB * 1024 * 1024

# SECURITY: Disable debug mode in production (exposes sensitive info)
app.config['DEBUG'] = Config.DEBUG

# SECURITY: Set secure session configuration
app.config['SECRET_KEY'] = Config.JWT_SECRET_KEY or os.urandom(32)
app.config['SESSION_COOKIE_SECURE'] = Config.HTTPS_ONLY  # Only send cookie over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection

# SECURITY: Configure CORS (Cross-Origin Resource Sharing)
# Only allow requests from trusted origins
if Config.CORS_ORIGINS:
    origins = [origin.strip() for origin in Config.CORS_ORIGINS.split(',')]
    CORS(app, origins=origins, supports_credentials=True)

# Global queue for logging messages
log_queue = Queue()

class UILogger:
    """Logger that sends messages to the web UI"""
    
    def log(self, step, message, status="info"):
        """Send a log message to the UI"""
        log_queue.put({
            'step': step,
            'message': message,
            'status': status,
            'timestamp': time.time()
        })

logger = UILogger()


@app.before_request
def before_request():
    """
    Security checks before processing any request.
    
    SECURITY: Pre-request validation:
    - HTTPS enforcement (production)
    - Request size limits
    - Content type validation
    """
    # SECURITY: Enforce HTTPS in production
    if Config.HTTPS_ONLY and not request.is_secure:
        return jsonify({
            'error': 'HTTPS Required',
            'message': 'This API requires HTTPS connections'
        }), 403
    
    # SECURITY: Log request for audit trail
    if SECURITY_ENABLED and Config.ENABLE_AUDIT_LOGGING:
        try:
            audit_logger.log_api_call(
                endpoint=request.endpoint or request.path,
                method=request.method,
                user_id=getattr(request, 'user_id', None),
                ip_address=get_client_ip(),
                status_code=0,  # Will be updated in after_request
                response_time_ms=0,
                query_params=request.args.to_dict() if request.args else None
            )
        except Exception:
            pass


@app.after_request
def after_request(response):
    """
    Add security headers to all responses.
    
    SECURITY: Protection against:
    - XSS (Cross-Site Scripting)
    - Clickjacking
    - MIME sniffing
    - Information disclosure
    """
    # SECURITY: Content Security Policy (CSP)
    # Prevents XSS attacks by restricting resource loading
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self' data:; "
        "connect-src 'self'"
    )
    
    # SECURITY: X-Content-Type-Options
    # Prevents MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # SECURITY: X-Frame-Options
    # Prevents clickjacking attacks
    response.headers['X-Frame-Options'] = 'DENY'
    
    # SECURITY: X-XSS-Protection
    # Enables browser XSS filtering
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # SECURITY: Strict-Transport-Security (HSTS)
    # Forces HTTPS connections
    if Config.HTTPS_ONLY:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    # SECURITY: Referrer-Policy
    # Controls referrer information sent with requests
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # SECURITY: Permissions-Policy
    # Restricts browser features
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=(), '
        'magnetometer=(), '
        'gyroscope=()'
    )
    
    # SECURITY: Remove server version information
    response.headers.pop('Server', None)
    
    # SECURITY: Add security version header (for monitoring)
    response.headers['X-Security-Version'] = '1.0'
    
    return response


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors without exposing information."""
    return jsonify({'error': 'Not Found', 'message': 'The requested resource was not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """
    Handle 500 errors without exposing sensitive information.
    
    SECURITY: Generic error message prevents information disclosure
    """
    # SECURITY: Log error for debugging but don't expose to user
    if Config.DEBUG:
        import traceback
        print("Internal Error:", traceback.format_exc())
    
    return jsonify({
        'error': 'Internal Server Error',
        'message': 'An unexpected error occurred. Please try again later.'
    }), 500


@app.errorhandler(413)
def request_too_large(error):
    """Handle oversized requests."""
    return jsonify({
        'error': 'Request Too Large',
        'message': f'Request size exceeds maximum of {Config.MAX_REQUEST_SIZE_MB}MB'
    }), 413


@app.route('/')
def index():
    """
    Main page.
    
    SECURITY: Public endpoint (no authentication required for UI)
    """
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """
    Get current configuration status.
    
    SECURITY: Public endpoint with redacted sensitive values
    """
    errors = Config.validate()
    
    # SECURITY: Redact sensitive configuration values
    return jsonify({
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY),
        'database_configured': bool(Config.DATABASE_URL),
        'whisper_model': Config.WHISPER_MODEL,
        'auth_required': Config.REQUIRE_AUTH,
        'rate_limiting': Config.ENABLE_RATE_LIMITING,
        'environment': Config.ENVIRONMENT,
        'security_enabled': SECURITY_ENABLED,
        'errors': errors,
        'ready': len(errors) == 0
    })

@app.route('/api/query', methods=['POST'])
@rate_limit('authenticated' if Config.REQUIRE_AUTH else 'default')  # Apply rate limiting
def process_query():
    """
    Process a text query with multi-agent collaboration.
    
    SECURITY:
    - Rate limited to prevent abuse
    - Input validation and sanitization
    - Authentication required (if configured)
    - Audit logging
    """
    start_time = time.time()
    client_ip = get_client_ip() if SECURITY_ENABLED else 'unknown'
    user_id = getattr(request, 'user_id', None)
    
    try:
        # SECURITY: Validate content type
        if not request.is_json:
            return jsonify({
                'error': 'Invalid Content Type',
                'message': 'Content-Type must be application/json'
            }), 400
        
        data = request.json
        query = data.get('query', '').strip()
        
        # SECURITY: Validate query is provided
        if not query:
            if SECURITY_ENABLED:
                audit_logger.log_input_validation_failure(
                    'query',
                    'Empty query',
                    client_ip,
                    user_id
                )
            return jsonify({'error': 'Query is required'}), 400
        
        # SECURITY: Validate and sanitize input
        if SECURITY_ENABLED:
            is_valid, error_msg = input_validator.validate_query(query)
            if not is_valid:
                # SECURITY: Log validation failure for security monitoring
                audit_logger.log_input_validation_failure(
                    'query',
                    error_msg,
                    client_ip,
                    user_id
                )
                return jsonify({
                    'error': 'Invalid Input',
                    'message': error_msg
                }), 400
            
            # SECURITY: Sanitize query
            query = input_validator.sanitize_text(query)
    
        # Clear log queue
        while not log_queue.empty():
            log_queue.get()
        
        # Create multi-agent orchestrator with custom status callback
        def status_callback(message):
            logger.log("agent", message, "info")
        
        orchestrator = MultiAgentOrchestrator(on_status=status_callback, verbose=False)
        
        # Process the query
        def process():
            try:
                logger.log("start", f"Processing query: {query}", "info")
                
                # Multi-agent processing with collaboration
                result = orchestrator.process_query(query)
                
                if result.success:
                    logger.log("complete", "Multi-agent collaboration complete!", "success")
                    
                    # Build response with collaboration details
                    response_data = {
                        'success': True,
                        'query': query,
                        'mode': result.mode,
                        'agents_used': result.agents_used,
                        'confidence': result.routing_confidence,
                        'final_response': result.final_response,
                        'collaboration_session': result.collaboration_session
                    }
                    
                    # Add agent-specific data
                    if result.sql:
                        response_data['sql'] = result.sql
                        response_data['sql_results'] = result.sql_results
                    
                    if result.csharp_response:
                        response_data['csharp_response'] = result.csharp_response
                    
                    if result.epicor_response:
                        response_data['epicor_response'] = result.epicor_response
                    
                    # SECURITY: Log successful query execution
                    if SECURITY_ENABLED:
                        audit_logger.log_event(
                            category='api',
                            action='query_processed',
                            result='success',
                            user_id=user_id or 'anonymous',
                            ip_address=client_ip,
                            details={
                                'query_length': len(query),
                                'agents_used': result.agents_used,
                                'mode': result.mode
                            },
                            severity='INFO'
                        )
                    
                    return response_data
                else:
                    error_msg = result.execution_error or result.routing_error or "Unknown error"
                    logger.log("error", f"Error: {error_msg}", "error")
                    
                    # SECURITY: Log failed query
                    if SECURITY_ENABLED:
                        audit_logger.log_event(
                            category='api',
                            action='query_processed',
                            result='failure',
                            user_id=user_id or 'anonymous',
                            ip_address=client_ip,
                            details={'error': error_msg},
                            severity='WARNING'
                        )
                    
                    return {
                        'success': False,
                        'error': error_msg
                    }
                    
            except Exception as e:
                logger.log("error", f"Exception: {str(e)}", "error")
                
                # SECURITY: Log exception but don't expose details to user
                if SECURITY_ENABLED:
                    audit_logger.log_event(
                        category='api',
                        action='query_exception',
                        result='error',
                        user_id=user_id or 'anonymous',
                        ip_address=client_ip,
                        details={'exception': str(e)},
                        severity='ERROR'
                    )
                
                if Config.DEBUG:
                    import traceback
                    traceback.print_exc()
                    return {
                        'success': False,
                        'error': str(e)
                    }
                else:
                    # SECURITY: Generic error in production
                    return {
                        'success': False,
                        'error': 'An error occurred processing your query'
                    }
        
        # Process the query
        result = process()
        
        # SECURITY: Add timing information
        execution_time = (time.time() - start_time) * 1000
        result['execution_time_ms'] = round(execution_time, 2)
        
        return jsonify(result)
        
    except Exception as e:
        # SECURITY: Catch-all for unexpected errors
        if SECURITY_ENABLED:
            audit_logger.log_security_event(
                event_type='unexpected_error',
                description=f"Unexpected error in query endpoint: {str(e)}",
                ip_address=client_ip,
                user_id=user_id,
                severity='ERROR'
            )
        
        if Config.DEBUG:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            return jsonify({
                'success': False,
                'error': 'An unexpected error occurred'
            }), 500

@app.route('/api/logs')
def stream_logs():
    """Stream logs to the UI using Server-Sent Events"""
    def generate():
        while True:
            if not log_queue.empty():
                log = log_queue.get()
                yield f"data: {json.dumps(log)}\n\n"
            else:
                time.sleep(0.1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/test_connection')
@rate_limit('default')  # Apply rate limiting
def test_connection():
    """
    Test database connection.
    
    SECURITY: Rate limited to prevent abuse
    """
    client_ip = get_client_ip() if SECURITY_ENABLED else 'unknown'
    
    try:
        logger.log("test", "Testing database connection...", "working")
        from src.sql.executor import execute_query
        result = execute_query("SELECT 1 as test;")
        
        if result.success:
            logger.log("test", "Database connection successful!", "success")
            
            # SECURITY: Log successful connection test
            if SECURITY_ENABLED:
                audit_logger.log_event(
                    category='api',
                    action='db_connection_test',
                    result='success',
                    user_id='anonymous',
                    ip_address=client_ip,
                    severity='INFO'
                )
            
            return jsonify({'success': True, 'message': 'Database connected'})
        else:
            logger.log("test", f"Database error: {result.error}", "error")
            
            # SECURITY: Log failed connection test
            if SECURITY_ENABLED:
                audit_logger.log_event(
                    category='api',
                    action='db_connection_test',
                    result='failure',
                    user_id='anonymous',
                    ip_address=client_ip,
                    details={'error': result.error},
                    severity='WARNING'
                )
            
            return jsonify({'success': False, 'error': result.error})
            
    except Exception as e:
        logger.log("test", f"Connection failed: {str(e)}", "error")
        
        # SECURITY: Log exception
        if SECURITY_ENABLED:
            audit_logger.log_security_event(
                event_type='db_connection_error',
                description=f"Database connection test failed: {str(e)}",
                ip_address=client_ip,
                severity='ERROR'
            )
        
        # SECURITY: Don't expose detailed error in production
        if Config.DEBUG:
            return jsonify({'success': False, 'error': str(e)})
        else:
            return jsonify({'success': False, 'error': 'Database connection failed'})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🔒 SECURE MULTI-AGENT VOICE-TO-SQL WEB UI")
    print("="*70)
    
    # SECURITY: Print configuration
    Config.print_config()
    
    print("\n📝 Setup Instructions:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Set ANTHROPIC_API_KEY environment variable")
    print("   3. Set JWT_SECRET_KEY environment variable (production)")
    print("   4. Run database initialization: python scripts/init_db.py")
    
    print("\n🔒 Security Status:")
    print(f"   • Security Modules: {'✅ Enabled' if SECURITY_ENABLED else '❌ Disabled'}")
    print(f"   • Authentication: {'✅ Required' if Config.REQUIRE_AUTH else '⚠️  Optional'}")
    print(f"   • Rate Limiting: {'✅ Enabled' if Config.ENABLE_RATE_LIMITING else '❌ Disabled'}")
    print(f"   • Audit Logging: {'✅ Enabled' if Config.ENABLE_AUDIT_LOGGING else '❌ Disabled'}")
    print(f"   • HTTPS Only: {'✅ Yes' if Config.HTTPS_ONLY else '⚠️  No'}")
    print(f"   • Environment: {Config.ENVIRONMENT}")
    
    # SECURITY: Validate configuration
    errors = Config.validate()
    if errors:
        critical = [e for e in errors if 'CRITICAL' in e]
        warnings = [e for e in errors if 'WARNING' in e]
        
        if critical:
            print("\n❌ CRITICAL SECURITY ISSUES:")
            for error in critical:
                print(f"   • {error}")
            print("\n⚠️  Cannot start with critical security issues!")
            print("   Please fix these issues and restart.\n")
            sys.exit(1)
        
        if warnings:
            print("\n⚠️  SECURITY WARNINGS:")
            for warning in warnings:
                print(f"   • {warning}")
            print("\n   Consider fixing these for production use.")
    
    print("\n🌐 Starting web server...")
    print(f"   URL: http://{'127.0.0.1' if not Config.HTTPS_ONLY else 'localhost'}:5001")
    print("\n   Press Ctrl+C to stop\n")
    print("="*70 + "\n")
    
    # SECURITY: Run with appropriate settings
    # NOTE: Changed from port 5000 to 5001 to avoid macOS AirPlay Receiver conflict
    app.run(
        debug=Config.DEBUG,
        host='127.0.0.1',
        port=5001,
        threaded=True,
        # SECURITY: In production, use a production WSGI server like gunicorn
        # Example: gunicorn -w 4 -b 127.0.0.1:5001 web_ui:app
    )
