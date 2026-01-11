#!/usr/bin/env python3
"""
Simple Web UI for Voice-to-SQL Agent
Shows real-time logging of agent steps and progress
"""

from flask import Flask, render_template, request, jsonify, Response
import sys
import os
from pathlib import Path
import json
import time
from queue import Queue
from threading import Thread

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from src.agent.multi_agent_orchestrator import MultiAgentOrchestrator

app = Flask(__name__)

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

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/config')
def get_config():
    """Get current configuration status"""
    errors = Config.validate()
    
    return jsonify({
        'anthropic_configured': bool(Config.ANTHROPIC_API_KEY),
        'database_url': Config.DATABASE_URL,
        'whisper_model': Config.WHISPER_MODEL,
        'errors': errors,
        'ready': len(errors) == 0
    })

@app.route('/api/query', methods=['POST'])
def process_query():
    """Process a text query with multi-agent collaboration"""
    data = request.json
    query = data.get('query', '').strip()
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
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
                
                return response_data
            else:
                error_msg = result.execution_error or result.routing_error or "Unknown error"
                logger.log("error", f"Error: {error_msg}", "error")
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            logger.log("error", f"Exception: {str(e)}", "error")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }
    
    # Process the query
    result = process()
    return jsonify(result)

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
def test_connection():
    """Test database connection"""
    try:
        logger.log("test", "Testing database connection...", "working")
        from src.sql.executor import execute_query
        result = execute_query("SELECT 1 as test;")
        
        if result.success:
            logger.log("test", "Database connection successful!", "success")
            return jsonify({'success': True, 'message': 'Database connected'})
        else:
            logger.log("test", f"Database error: {result.error}", "error")
            return jsonify({'success': False, 'error': result.error})
    except Exception as e:
        logger.log("test", f"Connection failed: {str(e)}", "error")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 VOICE-TO-SQL WEB UI")
    print("="*60)
    print("\n📝 Setup Instructions:")
    print("   1. Make sure PostgreSQL is running")
    print("   2. Set ANTHROPIC_API_KEY environment variable")
    print("   3. Run database initialization: python scripts/init_db.py")
    print("\n🌐 Starting web server...")
    print("   Open: http://localhost:5000")
    print("\n   Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    app.run(debug=True, host='127.0.0.1', port=5001, threaded=True)
