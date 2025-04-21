# JARVIS Integrated System

A powerful AI assistant system that combines the MCP server with advanced autonomous features from Jarvis35.

## Features

- **Knowledge Base**: Store and retrieve information using keyword-based search
- **File Search**: Find files and content throughout your file system
- **Code Generation**: Generate code snippets in multiple languages (Python, JavaScript, HTML)
- **Code Execution**: Securely execute Python and JavaScript code
- **Autonomous Agent**: Run complex tasks with step-by-step execution tracking
- **SSE Streaming**: Real-time connection with Cursor and other clients

## Getting Started

1. Install the requirements:
   ```
   pip install fastapi uvicorn
   ```

2. Start the JARVIS server:
   ```
   python jarvis_server.py
   ```
   
   Or use the startup script:
   ```
   start_jarvis.bat
   ```

3. Access JARVIS in Cursor:
   - The server automatically connects to Cursor via the MCP integration
   - Ask questions and use commands in Cursor to interact with JARVIS

## API Endpoints

### Main Endpoint: POST /

Send JSON requests with a `method` and `params` object:

```json
{
  "method": "search_files",
  "params": {
    "query": "example",
    "path": "."
  }
}
```

Available methods:
- `search_files`: Search for files with matching names or content
- `search_knowledge`: Search the knowledge base
- `add_knowledge`: Add information to the knowledge base
- `generate_code`: Generate code in various languages
- `execute_code`: Execute code in Python or JavaScript
- `start_task`: Start an autonomous agent task
- `get_task_state`: Check the status of a running task

### SSE Streaming: GET /mcp/sse

Connect to the server using Server-Sent Events (SSE) for real-time updates.

## Automatic Startup

To make JARVIS start automatically when your computer boots:

1. Press `Win+R`, type `shell:startup` and press Enter
2. Create a shortcut to the `start_jarvis.bat` file in this folder

## Integration with Cursor

The JARVIS server integrates with Cursor through the MCP protocol, allowing you to:

1. Use natural language to control JARVIS
2. Execute code directly
3. Search for files and information
4. Start autonomous tasks
5. Get real-time status updates 