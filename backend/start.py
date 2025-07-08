#!/usr/bin/env python3
"""
One-command startup for Oasis OS Backend
"""

import sys
import subprocess
import os
from pathlib import Path

def main():
    """Install dependencies if needed and start the server"""
    
    backend_dir = Path(__file__).parent
    requirements_file = backend_dir / "requirements.txt"
    
    # Add backend directory to Python path
    sys.path.insert(0, str(backend_dir))
    
    print("🚀 Oasis OS Backend Startup")
    print("=" * 40)
    
    # Check if requirements.txt exists
    if not requirements_file.exists():
        print("❌ requirements.txt not found!")
        sys.exit(1)
    
    # Install dependencies
    print("📦 Installing dependencies...")
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, cwd=backend_dir)
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)
    
    # Create logs directory
    logs_dir = backend_dir / "logs"
    logs_dir.mkdir(exist_ok=True)
    print("📁 Logs directory ready")
    
    # Start the server
    print("🌐 Starting FastAPI server...")
    print("   API will be available at: http://localhost:8000")
    print("   Documentation at: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop the server")
    print("-" * 40)
    
    try:
        # Change to backend directory before starting
        os.chdir(backend_dir)
        
        from server import app
        import uvicorn
        
        uvicorn.run(
            "server:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all dependencies are installed correctly")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 