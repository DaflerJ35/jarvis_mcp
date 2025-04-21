from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import json
import os
import sys
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from sse_starlette.sse import EventSourceResponse
import asyncio
import platform

# Import MCP Server Integration
from mcp_server_integration import integrate_mcp_with_jarvis

# Voice dependencies - import conditionally
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    import tempfile
    import playsound
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

# Create FastAPI app
app = FastAPI(title="JARVIS Enhanced Server")
app_startup_time = datetime.now()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables from .env file if it exists
if os.path.exists(".env"):
    env_vars = {}
    with open(".env", "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                env_vars[key] = value
else:
    env_vars = {}

# Configuration
SERVER_PORT = int(env_vars.get("SERVER_PORT", 8000))
ENABLE_VOICE = env_vars.get("ENABLE_VOICE", "true").lower() == "true"
VOICE_PROVIDER = env_vars.get("VOICE_PROVIDER", "pyttsx3")
VOICE_RATE = int(env_vars.get("VOICE_RATE", 125))  # Slower rate for more natural speech
VOICE_VOLUME = float(env_vars.get("VOICE_VOLUME", 1.0))
ENABLE_MCP = env_vars.get("ENABLE_MCP", "true").lower() == "true"
MCP_SSE_PATH = env_vars.get("MCP_SSE_PATH", "/mcp/sse")
STREAM_PATH = env_vars.get("STREAM_PATH", "/stream")
VOICE_ID = env_vars.get("VOICE_ID", None)  # Will use default voice if None

# Initialize voice engine if enabled
voice_engine = None
if ENABLE_VOICE:
    if VOICE_PROVIDER == "pyttsx3" and PYTTSX3_AVAILABLE:
        voice_engine = pyttsx3.init()
        voice_engine.setProperty('rate', VOICE_RATE)
        voice_engine.setProperty('volume', VOICE_VOLUME)
        
        # Get available voices and set a more natural voice if available
        voices = voice_engine.getProperty('voices')
        print(f"Available voices: {len(voices)}")
        
        # List all available voices
        for i, voice in enumerate(voices):
            print(f"Voice {i}: {voice.name} ({voice.id})")
        
        # Try to set a more natural voice
        if VOICE_ID:
            print(f"Setting custom voice ID: {VOICE_ID}")
            voice_engine.setProperty('voice', VOICE_ID)
        else:
            # Try to find a female voice which often sounds more natural
            female_voices = [v for v in voices if 'female' in v.name.lower() or 'zira' in v.name.lower()]
            if female_voices:
                voice_engine.setProperty('voice', female_voices[0].id)
                print(f"Set voice to {female_voices[0].name}")
            # Otherwise set the first non-default voice if available
            elif len(voices) > 1:
                voice_engine.setProperty('voice', voices[1].id)
                print(f"Set voice to {voices[1].name}")
        
        print(f"Voice enabled: Using pyttsx3 engine")
    elif VOICE_PROVIDER == "gtts" and GTTS_AVAILABLE:
        print(f"Voice enabled: Using Google Text-to-Speech (more natural sounding)")
    else:
        print(f"Warning: Selected voice provider '{VOICE_PROVIDER}' is not available")

# Request models
class RequestModel(BaseModel):
    method: str
    params: Dict[str, Any] = {}
    
class MCPRequestModel(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Dict[str, Any] = {}
    id: Optional[str] = None

# MCP Event Queue - for streaming responses to Cursor
mcp_event_queue = asyncio.Queue()

# Helper methods
def generate_voice(text: str) -> Dict[str, Any]:
    """Generate voice output for the given text"""
    if not ENABLE_VOICE:
        return {"error": "Voice is disabled"}
    
    try:
        if VOICE_PROVIDER == "pyttsx3" and voice_engine:
            print(f"Speaking with pyttsx3: {text}")
            # Add a slight pause before speaking for more natural rhythm
            time.sleep(0.2)
            
            # Use a thread to avoid blocking
            def speak_text():
                # Add some natural pauses using punctuation
                processed_text = text
                # Add more natural breathing points for longer sentences
                if len(text) > 60 and ',' not in text and '.' not in text:
                    words = text.split()
                    midpoint = len(words) // 2
                    processed_text = ' '.join(words[:midpoint]) + ', ' + ' '.join(words[midpoint:])
                
                voice_engine.say(processed_text)
                voice_engine.runAndWait()
            
            threading.Thread(target=speak_text).start()
            return {"success": True, "provider": "pyttsx3"}
            
        elif VOICE_PROVIDER == "gtts" and GTTS_AVAILABLE:
            print(f"Speaking with gTTS: {text}")
            try:
                # Fix for spaces in filenames causing playback issues
                tts = gTTS(text=text, lang='en', slow=False)
                
                # Use a simpler temp file path without spaces
                temp_dir = os.path.join(os.getcwd(), "temp")
                os.makedirs(temp_dir, exist_ok=True)
                
                temp_filename = os.path.join(temp_dir, f"jarvis_speech_{int(time.time())}.mp3")
                
                tts.save(temp_filename)
                
                # Play the audio in a separate thread
                def play_audio():
                    try:
                        # Alternative playback method if playsound fails
                        if platform.system() == 'Windows':
                            os.system(f'start /min powershell -c "(New-Object Media.SoundPlayer \'{temp_filename}\').PlaySync()"')
                        else:
                            playsound.playsound(temp_filename, block=False)
                        
                        # Clean up after playing
                        time.sleep(10)
                        try:
                            if os.path.exists(temp_filename):
                                os.remove(temp_filename)
                        except Exception as e:
                            print(f"Failed to delete temp file: {str(e)}")
                    except Exception as e:
                        print(f"Audio playback error: {str(e)}")
                
                threading.Thread(target=play_audio).start()
                return {"success": True, "provider": "gtts", "file": temp_filename}
            except Exception as e:
                print(f"gTTS error: {str(e)}")
                
                # Fallback to pyttsx3 if Google TTS fails
                if PYTTSX3_AVAILABLE and voice_engine:
                    print("Falling back to pyttsx3")
                    def speak_text():
                        voice_engine.say(text)
                        voice_engine.runAndWait()
                    
                    threading.Thread(target=speak_text).start()
                    return {"success": True, "provider": "pyttsx3 (fallback)"}
                return {"error": str(e)}
        else:
            return {"error": f"Voice provider '{VOICE_PROVIDER}' is not available"}
    except Exception as e:
        print(f"Voice error: {str(e)}")
        return {"error": str(e)}

def search_files(query: str) -> List[Dict[str, str]]:
    """Search for files matching the query"""
    results = []
    for root, dirs, files in os.walk("."):
        for file in files:
            if query.lower() in file.lower():
                results.append({
                    "path": os.path.join(root, file),
                    "name": file
                })
    return results

def process_text_command(text: str) -> str:
    """Process a text command and return a response"""
    text = text.lower().strip()
    
    # Simple responses for basic commands
    if "hello" in text or "hi" in text:
        return "Hello! How can I help you today?"
    
    elif "time" in text:
        current_time = datetime.now().strftime("%H:%M:%S")
        return f"The current time is {current_time}"
    
    elif "date" in text:
        current_date = datetime.now().strftime("%B %d, %Y")
        return f"Today is {current_date}"
    
    elif "status" in text or "system" in text:
        uptime = datetime.now() - app_startup_time
        hours, remainder = divmod(uptime.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"JARVIS system is online. Uptime: {hours} hours, {minutes} minutes, {seconds} seconds."
    
    elif "voice" in text and "change" in text:
        if "google" in text or "gtts" in text:
            global VOICE_PROVIDER
            VOICE_PROVIDER = "gtts"
            return "Voice changed to Google Text-to-Speech for more natural sound."
        elif "pyttsx" in text:
            VOICE_PROVIDER = "pyttsx3"
            return "Voice changed to local pyttsx3 engine."
        else:
            return "To change voice, say 'change voice to google' or 'change voice to pyttsx3'"
            
    elif "voice" in text:
        if ENABLE_VOICE:
            provider = VOICE_PROVIDER
            return f"Voice system is enabled and using {provider} provider."
        else:
            return "Voice system is currently disabled."
    
    elif ("what" in text and "do" in text) or ("abilities" in text) or ("capabilities" in text) or ("help" in text):
        return """I am JARVIS, a virtual assistant with several capabilities:

1. Answer basic questions and provide information
2. Tell you the current time and date
3. Report on system status and uptime
4. Change my voice between different providers
5. Connect with Cursor through the MCP interface
6. Search files in the current directory
7. Process and respond to text commands
8. Generate spoken responses using text-to-speech

You can ask me to perform these tasks using natural language. For example:
- "Hello Jarvis"
- "What time is it?"
- "Change voice to Google"
- "Tell me about your system status"

How can I assist you today?"""
    
    else:
        return f"I received your message: '{text}'. Please let me know how I can assist you."

async def process_mcp_request(request: MCPRequestModel) -> Dict[str, Any]:
    """Process MCP request from Cursor"""
    method = request.method
    params = request.params
    
    if method == "search_files":
        query = params.get("query", "")
        results = search_files(query)
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"results": results}
        }
    
    elif method == "generate_voice":
        text = params.get("text", "")
        if not text:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32600, "message": "Text parameter is required"}
            }
        
        result = generate_voice(text)
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": result
        }
    
    elif method == "process_text":
        text = params.get("text", "")
        if not text:
            return {
                "jsonrpc": "2.0",
                "id": request.id,
                "error": {"code": -32600, "message": "Text parameter is required"}
            }
        
        response = process_text_command(text)
        if ENABLE_VOICE:
            generate_voice(response)
        
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "result": {"response": response}
        }
    
    else:
        return {
            "jsonrpc": "2.0",
            "id": request.id,
            "error": {"code": -32601, "message": f"Method not found: {method}"}
        }

# API Routes
@app.get("/")
async def root():
    """Root endpoint that returns basic server information"""
    uptime = datetime.now() - app_startup_time
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    return {
        "name": "JARVIS Enhanced Server",
        "version": "1.0.0",
        "status": "online",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "voice_enabled": ENABLE_VOICE,
        "voice_provider": VOICE_PROVIDER if ENABLE_VOICE else None,
        "features": ["search_files", "generate_voice", "process_text"]
    }

@app.post("/")
async def process_request(request: RequestModel):
    """Main endpoint for processing all types of requests"""
    method = request.method
    params = request.params
    
    try:
        if method == "search_files":
            query = params.get("query", "")
            results = search_files(query)
            return {"results": results}
            
        elif method == "generate_voice":
            text = params.get("text", "")
            if not text:
                raise HTTPException(status_code=400, detail="Text parameter is required")
            
            result = generate_voice(text)
            return result
            
        elif method == "process_text":
            text = params.get("text", "")
            if not text:
                raise HTTPException(status_code=400, detail="Text parameter is required")
            
            response = process_text_command(text)
            
            # Also generate voice for the response
            if ENABLE_VOICE:
                generate_voice(response)
            
            return {"response": response}
            
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jarvis://overview")
async def jarvis_overview():
    """Overview endpoint for JARVIS project details"""
    return {
        "project": "JARVIS Enhanced Server",
        "description": "A versatile server with voice capabilities for building AI assistants",
        "capabilities": [
            "File search",
            "Voice generation",
            "Text command processing"
        ]
    }

# MCP SSE endpoint for Cursor integration
@app.get(MCP_SSE_PATH)
async def mcp_sse(request: Request):
    """Server-Sent Events endpoint for MCP protocol (Cursor integration)"""
    print(f"MCP SSE connection established from {request.client}")
    
    async def event_generator():
        while True:
            # Keep connection alive with a ping every 5 seconds
            await asyncio.sleep(5)
            yield {
                "event": "ping",
                "data": json.dumps({"time": datetime.now().isoformat()})
            }
    
    return EventSourceResponse(event_generator())

# MCP request endpoint 
@app.post(MCP_SSE_PATH)
async def mcp_request(request: MCPRequestModel):
    """Process MCP requests from Cursor"""
    print(f"Received MCP request: {request.method}")
    response = await process_mcp_request(request)
    
    # Also send voice if appropriate
    if request.method == "process_text" and ENABLE_VOICE and "result" in response:
        if "response" in response["result"]:
            generate_voice(response["result"]["response"])
    
    return response

# SSE stream endpoint
@app.get(STREAM_PATH)
async def stream_endpoint(request: Request):
    """Additional streaming endpoint for bidirectional communication"""
    print(f"Stream connection established from {request.client}")
    return Response(content="Streaming endpoint not fully implemented yet", media_type="text/plain")

@app.post("/toggle_voice")
async def toggle_voice():
    """Toggle voice on/off"""
    global ENABLE_VOICE
    ENABLE_VOICE = not ENABLE_VOICE
    
    print(f"Voice {'enabled' if ENABLE_VOICE else 'disabled'}")
    return {"status": "success", "voice_enabled": ENABLE_VOICE}

@app.post("/change_voice")
async def change_voice(request: Request):
    """Change voice provider"""
    global VOICE_PROVIDER
    
    data = await request.json()
    provider = data.get("provider", "gtts")
    
    if provider in ["gtts", "pyttsx3"]:
        VOICE_PROVIDER = provider
        print(f"Voice provider changed to {VOICE_PROVIDER}")
        return {"status": "success", "voice_provider": VOICE_PROVIDER}
    else:
        return {"status": "error", "message": f"Unknown voice provider: {provider}"}

@app.get("/jarvis://voice_status")
async def voice_status():
    """Get voice status"""
    return {
        "enabled": ENABLE_VOICE,
        "provider": VOICE_PROVIDER,
        "rate": VOICE_RATE,
        "volume": VOICE_VOLUME
    }

# Run the server if executed as a script
if __name__ == "__main__":
    print(f"Starting JARVIS Enhanced Server on port {SERVER_PORT}")
    if ENABLE_VOICE:
        print(f"Voice is enabled using {VOICE_PROVIDER} provider")
    
    # Integrate MCP server capabilities
    mcp_integration = integrate_mcp_with_jarvis(app)
    
    if ENABLE_MCP:
        print(f"MCP SSE endpoint enabled at {MCP_SSE_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=SERVER_PORT) 