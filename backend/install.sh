#!/bin/bash

# Oasis OS Backend Installation Script

echo "🚀 Installing Oasis OS Backend..."
echo "=================================="

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create logs directory
echo "📁 Creating logs directory..."
mkdir -p logs

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "⚙️  Creating environment configuration..."
    cat > .env << EOF
# Environment Configuration for Oasis OS Backend
HOST=0.0.0.0
PORT=8000
DEBUG=True
FRONTEND_URL=http://localhost:3000
LOG_LEVEL=INFO
LOG_DIR=logs
DEFAULT_MODEL=gpt-4o

# Add your API keys here if needed
# OPENAI_API_KEY=your_openai_api_key_here
# ANTHROPIC_API_KEY=your_anthropic_api_key_here
# GROQ_API_KEY=your_groq_api_key_here
EOF
fi

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎯 To start the backend server:"
echo "   cd backend"
echo "   source venv/bin/activate  # (if not already activated)"
echo "   python run.py"
echo ""
echo "🌐 The API will be available at: http://localhost:8000"
echo "📊 API documentation will be at: http://localhost:8000/docs"
echo "" 