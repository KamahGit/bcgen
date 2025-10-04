#!/bin/bash
# Start script for AAMVA PDF417 Barcode Generator

echo "======================================================================"
echo "Starting AAMVA PDF417 Barcode Generator Web Application"
echo "======================================================================"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: No virtual environment detected"
    echo "   Consider running: python3 -m venv venv && source venv/bin/activate"
    echo ""
fi

# Check dependencies
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null || {
    echo "❌ Flask not installed. Installing dependencies..."
    pip install -r requirements.txt
}

echo "✅ Dependencies OK"
echo ""

# Start the application
echo "🚀 Starting Flask application..."
echo ""
echo "Access the web interface at:"
echo "   http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"
echo ""

python3 app.py
