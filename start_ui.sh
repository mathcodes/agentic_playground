#!/bin/bash
# Start the Voice-to-SQL Web UI

cd "$(dirname "$0")"

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║           Voice-to-SQL Agent - Web UI                     ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "📋 Starting web interface..."
echo ""

# Activate virtual environment and run
source venv/bin/activate

# Check if database is set up
echo "Checking configuration..."
python3 -c "from config import Config; errors = Config.validate(); print('✅ Configuration OK' if not errors else '⚠️  ' + errors[0])"
echo ""

echo "🌐 Starting server..."
echo "   Open your browser to: http://localhost:5000"
echo ""
echo "   Press Ctrl+C to stop"
echo ""

python3 web_ui.py
