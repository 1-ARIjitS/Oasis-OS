# 🌟 OASIS OS - Intelligent Workflow Automation Platform

<div align="center">
  <img src="https://img.shields.io/badge/Version-1.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/Next.js-15.3.5-black.svg" alt="Next.js">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</div>

<div align="center">
  <h3>🚀 Transform Your Workspace with AI-Powered Automation</h3>
  <p>Teach OASIS OS your workflows once, and watch it handle your repetitive tasks forever.</p>
</div>

---

## 📋 Table of Contents

- [✨ Features](#-features)
- [🏗️ Architecture](#️-architecture)
- [🛠️ Prerequisites](#️-prerequisites)
- [🚀 Quick Start](#-quick-start)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
  - [GUI Agents Setup](#gui-agents-setup)
- [📖 Usage Guide](#-usage-guide)
  - [Teach Mode](#teach-mode)
  - [Workflow Execution](#workflow-execution)
  - [GUI Automation](#gui-automation)
- [🔌 API Documentation](#-api-documentation)
- [🎯 Use Cases](#-use-cases)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

### 🧠 **Teach Mode**
Record your workflows once and OASIS OS learns to replicate them perfectly. Supports:
- 🖱️ Mouse tracking and click recording
- ⌨️ Keyboard input capture
- 🎤 Voice commands with speech-to-text (Groq API)
- 📸 Screen capture at regular intervals
- 🔄 Automatic workflow generation from recordings

### ⚡ **Smart Automation**
- Execute complex workflows with simple commands
- Cross-platform support (Windows, macOS, Linux)
- AI-powered task execution with multiple LLM backends
- Visual debugging with screenshots and logs

### 🎨 **Modern UI**
- Beautiful Next.js frontend with dark/light mode
- Real-time workflow visualization
- Interactive workspace management
- Smooth animations and transitions

### 🔧 **Extensible Architecture**
- FastAPI backend with async support
- Modular plugin system
- REST API for easy integration
- Support for multiple AI models (GPT-4, Claude, Groq, Ollama)

---

## 🏗️ Architecture

```
OASIS-Final/
├── 📁 Oasis-OS/
│   ├── 📁 backend/          # FastAPI backend server
│   │   ├── 📁 teach_mode/   # Workflow recording & building
│   │   ├── 📁 routers/      # API endpoints
│   │   └── 📁 services/     # Business logic
│   │
│   ├── 📁 frontend/         # Next.js frontend app
│   │   ├── 📁 src/
│   │   │   ├── 📁 app/      # App routes
│   │   │   └── 📁 components/ # UI components
│   │   └── 📁 public/       # Static assets
│   │
│   └── 📁 gui_agents/       # Desktop automation agents
│       └── 📁 s1/           # Agent implementation
│           ├── 📁 aci/      # Platform-specific interfaces
│           └── 📁 core/     # Core agent logic
```

---

## 🛠️ Prerequisites

### System Requirements
- **Python 3.8+** (3.11 recommended)
- **Node.js 18+** and npm/yarn
- **Git**
- **Operating System**: Windows 10+, macOS 11+, or Linux (Ubuntu 20.04+)

### API Keys (Optional but Recommended)
- **GROQ_API_KEY**: For speech-to-text in teach mode
- **OPENAI_API_KEY**: For GPT models
- **ANTHROPIC_API_KEY**: For Claude models

---

## 🚀 Quick Start

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/yourusername/Oasis-Final.git
cd Oasis-Final
```

### 2️⃣ Backend Setup

```bash
# Navigate to backend directory
cd Oasis-OS/backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo "GROQ_API_KEY=your_groq_api_key_here" > .env

# Run the backend server
python start.py
```

The backend will start on `http://localhost:8000`

### 3️⃣ Frontend Setup

Open a new terminal:

```bash
# Navigate to frontend directory
cd Oasis-OS/frontend

# Install dependencies
npm install
# or
yarn install

# Run development server
npm run dev
# or
yarn dev
```

The frontend will start on `http://localhost:3000`

### 4️⃣ GUI Agents Setup

Open another terminal:

```bash
# Navigate to root directory
cd Oasis-Final

# Install GUI agents dependencies
pip install -r requirements.txt

# Test the installation
python -m gui_agents.s1.cli_app --help
```

---

## 📖 Usage Guide

### 🎓 Teach Mode

Teach Mode allows you to record your workflows and have OASIS OS learn from them.

#### Starting a Recording Session

1. **Via API (curl/Postman):**
```bash
# Start recording
curl -X POST http://localhost:8000/start_recording/my_workflow

# Stop recording and build workflow
curl -X POST http://localhost:8000/stop_recording

# Execute the recorded workflow
curl -X POST http://localhost:8000/run_workflow/my_workflow
```

2. **Via Python Script:**
```python
import requests

# Start recording
response = requests.post("http://localhost:8000/start_recording/file_organization")
print("Recording started!")

# Perform your tasks...
# - Click on folders
# - Type commands
# - Speak instructions (if GROQ_API_KEY is set)

# Stop recording
response = requests.post("http://localhost:8000/stop_recording")
print("Workflow built!")
```

#### What Gets Recorded?
- **Mouse Events**: Clicks, movements, scrolls
- **Keyboard Input**: All keystrokes and shortcuts
- **Voice Commands**: Spoken instructions (requires GROQ API)
- **Screenshots**: Visual context every 0.5 seconds
- **Timing**: Precise timestamps for replay

### 🔄 Workflow Execution

Execute your recorded workflows programmatically:

```python
# Execute a workflow
response = requests.post("http://localhost:8000/run_workflow/file_organization")
```

### 🤖 GUI Automation

Use the GUI agents for advanced automation:

```bash
# Interactive mode with GPT-4
python -m gui_agents.s1.cli_app --model gpt-4o

# Use local models with Ollama
python -m gui_agents.s1.cli_app --model llama3.2 --engine-type ollama

# Teaching mode - record a demonstration
python -m gui_agents.s1.cli_app --teach
```

#### Example Commands:
- "Open Chrome and navigate to GitHub"
- "Create a new folder called 'Projects' on the desktop"
- "Take a screenshot and save it to Downloads"
- "Find all PDF files in Documents and move them to a new folder"

---

## 🔌 API Documentation

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information and available endpoints |
| POST | `/start_recording/{session_name}` | Start a new teach mode recording |
| POST | `/stop_recording` | Stop recording and build workflow |
| POST | `/run_workflow/{session_name}` | Execute a recorded workflow |
| GET | `/api/v1/workflow/{workflow_id}/status` | Get workflow execution status |
| DELETE | `/api/v1/workflow/{workflow_id}` | Cancel a running workflow |
| GET | `/api/v1/workflow/active` | List all active workflows |

### Example API Usage

```javascript
// Frontend integration example
async function startTeaching() {
  const response = await fetch('http://localhost:8000/start_recording/email_automation', {
    method: 'POST'
  });
  const data = await response.json();
  console.log('Recording started:', data);
}

async function executeWorkflow() {
  const response = await fetch('http://localhost:8000/run_workflow/email_automation', {
    method: 'POST'
  });
  const data = await response.json();
  console.log('Workflow executed:', data);
}
```

---

## 🎯 Use Cases

### 📁 File Organization
```python
# Record organizing downloads folder
# OASIS OS learns your file sorting patterns
# Automatically sorts new downloads based on your rules
```

### 📧 Email Automation
```python
# Teach OASIS OS to:
# - Filter and categorize emails
# - Auto-respond to common queries
# - Archive old conversations
```

### 📊 Data Processing
```python
# Record your Excel/CSV workflows
# - Data cleaning and formatting
# - Report generation
# - Chart creation
```

### 🌐 Web Automation
```python
# Automate browser tasks:
# - Form filling
# - Data scraping
# - Social media posting
```

---

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# Speech-to-Text (Optional)
GROQ_API_KEY=your_groq_api_key

# AI Models (Choose one or more)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
AZURE_OPENAI_API_KEY=your_azure_key

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

### Advanced Settings

Edit `backend/teach_mode/teach_mode.py` for:
- VAD threshold adjustment
- Frame capture intervals  
- Audio recording settings

---

## 🐛 Troubleshooting

### Common Issues

1. **"No audio detected" in Teach Mode**
   - Check microphone permissions
   - Verify GROQ_API_KEY is set correctly
   - Adjust VAD_THRESHOLD in teach_mode.py

2. **"Module not found" errors**
   - Ensure virtual environment is activated
   - Run `pip install -r requirements.txt` again
   - Check Python version (3.8+ required)

3. **Frontend connection issues**
   - Verify backend is running on port 8000
   - Check CORS settings in server.py
   - Clear browser cache

4. **GUI agents not working**
   - Install platform-specific dependencies
   - Grant accessibility permissions (macOS)
   - Run as administrator (Windows)

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt
npm install --save-dev

# Run tests
pytest
npm test

# Format code
black .
prettier --write .
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">
  <h3>🌟 Built with ❤️ by the OASIS OS Team</h3>
  <p>Transform your workspace. Automate your world.</p>
</div> 