# JARVIS Multi-Channel Processor (MCP)

A sophisticated AI assistant system that seamlessly integrates with various platforms to provide enhanced AI capabilities, including voice interaction, knowledge management, code generation, and task automation.

![GitHub](https://img.shields.io/github/license/DaflerJ35/jarvis_mcp)

## 🌟 Features

### Core Capabilities
- **Advanced Voice Interaction**: Natural voice communication with configurable TTS providers (Google TTS and pyttsx3)
- **Knowledge Management System**: Store, retrieve, and enhance your assistant's knowledge over time
- **Multi-Client Integration**: Connect with AI platforms like Claude, Cursor, and other assistants
- **Server-Sent Events**: Real-time streaming communication for responsive interactions
- **Autonomous Agents**: Execute complex tasks with step-by-step progress tracking
- **Web Research Tools**: Fetch information from websites, YouTube, and news sources

### Specific Functions
- **Semantic Search**: Find information based on meaning, not just keywords
- **File Management**: Search and organize files across your system
- **Code Generation**: Create code snippets in multiple languages (Python, JavaScript, HTML)
- **GUI Interface**: Clean graphical user interface with voice activation
- **Holographic UI Option**: Advanced visual interface with immersive design
- **System Automation**: Control your computer through natural language commands
- **Cross-Assistant Knowledge Sharing**: Share knowledge between different AI systems

## 🏗️ Architecture

JARVIS MCP is built on a modular architecture consisting of:

1. **Core Server**: FastAPI-based server handling requests and managing features
2. **Knowledge Enhancer**: Vector database for semantic understanding and information retrieval
3. **Voice Module**: Text-to-speech and speech-to-text capabilities
4. **MCP Connector**: Protocol for connecting to external AI systems like Cursor
5. **Client Modules**: Specialized integrations for various platforms
6. **Autonomous Evolution System**: Self-improvement capabilities
7. **Multi-Modal Processor**: Handle various data types (text, images, audio)

## 🚀 Getting Started

### Prerequisites
- Python 3.8+ (3.9+ recommended)
- pip for package installation
- Windows, macOS, or Linux

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DaflerJ35/jarvis_mcp.git
   cd jarvis_mcp
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install voice dependencies (optional but recommended):
   ```bash
   # Windows
   .\install_voice.bat
   
   # Linux/macOS
   pip install pyttsx3 gtts playsound SpeechRecognition
   ```

4. Configure environment (copy and edit the example file):
   ```bash
   cp .env.example .env
   # Edit .env with your preferred settings
   ```

### Starting JARVIS

#### Standard Start
```bash
python enhanced_jarvis_server.py
```

#### With Batch Script (Windows)
```bash
.\run_enhanced_jarvis.bat
```

#### With GUI
```bash
python jarvis_gui.py
```

## 💬 Usage

### Voice Commands
Once the server is running, you can use voice commands like:
- "Hello JARVIS"
- "What time is it?"
- "Search for files containing 'project'"
- "Tell me about your capabilities"

### API Requests
Send JSON requests to the main endpoint:

```json
{
  "method": "process_text",
  "params": {
    "text": "What can you do?"
  }
}
```

### Cursor Integration
1. Ensure your Cursor installation has the MCP configuration pointing to your JARVIS server
2. The `connect_claude_to_jarvis.py` script enables bidirectional communication

## ⚙️ Configuration

### Environment Variables (.env)
- `SERVER_PORT`: Port number (default: 8000)
- `ENABLE_VOICE`: Enable/disable voice capabilities (true/false)
- `VOICE_PROVIDER`: Choose voice provider (gtts/pyttsx3)
- `ENABLE_MCP`: Enable Cursor integration (true/false)
- `KNOWLEDGE_DIR`: Directory for knowledge storage

### API Keys
For enhanced features, add these to your .env file:
- `OPENAI_API_KEY`: For OpenAI API integration
- `SERPAPI_KEY`: For web search capabilities
- `NEWS_API_KEY`: For fetching news articles
- `YOUTUBE_API_KEY`: For YouTube video information

## 📁 Project Structure

```
jarvis_mcp/
├── enhanced_jarvis_server.py  # Main enhanced server
├── jarvis_gui.py              # Graphical user interface
├── jarvis_modules/            # Modular components
│   ├── autonomous_evolution.py # Self-improvement system
│   └── multimodal.py          # Multi-modal processing
├── knowledge_enhancer.py      # Knowledge management system
├── mcp_server_integration.py  # Cursor MCP integration
├── connect_claude_to_jarvis.py # Claude integration
└── jarvis_voice_recognition.py # Voice recognition system
```

## 🔄 Integration Options

### Desktop JARVIS Integration
See `JARVIS_INTEGRATION_GUIDE.md` for connecting your desktop assistant to the enhanced MCP system.

### Claude Integration
```bash
python connect_claude_to_jarvis.py --enhanced
```

### Cursor Integration
The MCP endpoint at `/mcp/sse` automatically connects with Cursor.

## 🛠️ Advanced Usage

### Automatic Startup
To make JARVIS start automatically:
```bash
.\create_jarvis_startup.bat
```

### Custom Voice Configuration
Modify voice settings in .env:
```
VOICE_PROVIDER=gtts  # More natural sounding
VOICE_RATE=125       # Speech rate
VOICE_VOLUME=1.0     # Volume level
```

### Knowledge Management
Add new knowledge programmatically:
```python
from knowledge_enhancer import JARVISKnowledgeEnhancer

enhancer = JARVISKnowledgeEnhancer()
enhancer.add_to_knowledge(
    "JARVIS is a powerful AI assistant system.",
    "manual_entry",
    {"importance": "high"}
)
```

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
- Inspired by the fictional J.A.R.V.I.S. from Iron Man
- Thanks to the open-source AI community for various tools and libraries
- Special thanks to Claude and Cursor for their amazing AI capabilities 