import requests
import json
import os
import sys
import time
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import colorama
from colorama import Fore, Style

# Initialize colorama for colored output
colorama.init()

# Load environment variables
load_dotenv()

# Server settings
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")

def send_request(method: str, params: Dict[str, Any] = {}) -> Optional[Dict[str, Any]]:
    """Send a request to the JARVIS server"""
    try:
        response = requests.post(
            f"{SERVER_URL}/",
            json={"method": method, "params": params},
            timeout=60  # Longer timeout for research operations
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"{Fore.RED}Error: Server returned status {response.status_code}{Style.RESET_ALL}")
            print(response.text)
            return None
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        return None

def process_text(text: str) -> Optional[Dict[str, Any]]:
    """Process a text command"""
    return send_request("process_text", {"text": text})

def generate_voice(text: str) -> Optional[Dict[str, Any]]:
    """Generate voice output"""
    return send_request("generate_voice", {"text": text})

def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_command_list():
    """Print list of available commands"""
    print(f"\n{Fore.CYAN}=== Available Commands ==={Style.RESET_ALL}")
    print(f"{Fore.YELLOW}!help{Style.RESET_ALL} - Show this help message")
    print(f"{Fore.YELLOW}!exit{Style.RESET_ALL} - Exit the client")
    print(f"{Fore.YELLOW}!clear{Style.RESET_ALL} - Clear the screen")
    print(f"{Fore.YELLOW}!status{Style.RESET_ALL} - Check server status")
    print(f"{Fore.YELLOW}!research <query>{Style.RESET_ALL} - Research a topic")
    print(f"{Fore.YELLOW}!setup <project_type> [<requirement1> <requirement2> ...]{Style.RESET_ALL} - Setup a development environment")
    print(f"{Fore.YELLOW}!analyze{Style.RESET_ALL} - Analyze JARVIS capabilities")
    print(f"{Fore.YELLOW}!voice <text>{Style.RESET_ALL} - Generate voice output")
    print(f"{Fore.YELLOW}!agent <query>{Style.RESET_ALL} - Use JARVIS MCP agent for complex tasks\n")

def check_server_status() -> bool:
    """Check if the JARVIS server is running"""
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            data = response.json()
            uptime = data.get("uptime", "Unknown")
            version = data.get("version", "Unknown")
            voice_enabled = data.get("voice_enabled", False)
            voice_provider = data.get("voice_provider", "None")
            features = ", ".join(data.get("features", []))
            
            print(f"\n{Fore.GREEN}=== JARVIS Server Status ==={Style.RESET_ALL}")
            print(f"{Fore.CYAN}Version:{Style.RESET_ALL} {version}")
            print(f"{Fore.CYAN}Uptime:{Style.RESET_ALL} {uptime}")
            print(f"{Fore.CYAN}Voice:{Style.RESET_ALL} {'Enabled - ' + voice_provider if voice_enabled else 'Disabled'}")
            print(f"{Fore.CYAN}Features:{Style.RESET_ALL} {features}\n")
            
            return True
        else:
            print(f"{Fore.RED}Server is not responding correctly. Status code: {response.status_code}{Style.RESET_ALL}")
            return False
    except Exception as e:
        print(f"{Fore.RED}Error connecting to server: {str(e)}{Style.RESET_ALL}")
        return False

def process_special_command(command: str) -> bool:
    """Process special commands that start with !"""
    if command == "!help":
        print_command_list()
        return True
    
    elif command == "!exit":
        print(f"{Fore.YELLOW}Exiting JARVIS client. Goodbye!{Style.RESET_ALL}")
        sys.exit(0)
    
    elif command == "!clear":
        clear_screen()
        print(f"{Fore.GREEN}=== JARVIS Text Client ==={Style.RESET_ALL}")
        print(f"Type your messages to JARVIS below. Type '!help' for commands or '!exit' to quit.")
        return True
    
    elif command == "!status":
        check_server_status()
        return True
    
    elif command.startswith("!research "):
        query = command[10:]
        if not query:
            print(f"{Fore.RED}Error: Research query is required{Style.RESET_ALL}")
            return True
            
        print(f"{Fore.YELLOW}Researching: {query}...{Style.RESET_ALL}")
        try:
            # Use MCPAction endpoint to access the new research capability
            response = requests.post(
                f"{SERVER_URL}/mcp/action",
                json={
                    "action_type": "web_research",
                    "parameters": {"query": query, "depth": 2, "max_results": 5},
                    "connection_id": "text_client"
                },
                timeout=120  # Research can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    
                    # Display sources
                    sources = result.get("sources", [])
                    print(f"\n{Fore.GREEN}Found {len(sources)} sources:{Style.RESET_ALL}")
                    
                    for i, source in enumerate(sources):
                        print(f"  {i+1}. {Fore.CYAN}{source.get('title', 'No title')}{Style.RESET_ALL}")
                        print(f"     {Fore.BLUE}{source.get('link', 'No link')}{Style.RESET_ALL}")
                        print(f"     {source.get('snippet', '')[:100]}...\n")
                    
                    # Display summary
                    summary = result.get("summary", "No summary available")
                    print(f"{Fore.GREEN}Summary:{Style.RESET_ALL}")
                    print(f"{summary}\n")
                    
                    # Generate voice for summary
                    generate_voice(f"Research results for {query}: {summary}")
                    
                else:
                    print(f"{Fore.RED}Error: {data.get('error', 'Unknown error')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error: Server returned status {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error researching topic: {str(e)}{Style.RESET_ALL}")
        
        return True
    
    elif command.startswith("!setup "):
        parts = command[7:].split()
        if not parts:
            print(f"{Fore.RED}Error: Project type is required{Style.RESET_ALL}")
            return True
            
        project_type = parts[0]
        requirements = parts[1:] if len(parts) > 1 else []
        
        print(f"{Fore.YELLOW}Setting up {project_type} environment with requirements: {', '.join(requirements) if requirements else 'none'}{Style.RESET_ALL}")
        
        try:
            # Use MCPAction endpoint to access the new environment setup capability
            response = requests.post(
                f"{SERVER_URL}/mcp/action",
                json={
                    "action_type": "setup_environment",
                    "parameters": {
                        "project_type": project_type,
                        "requirements": requirements,
                        "path": os.path.join(os.getcwd(), "projects", project_type)
                    },
                    "connection_id": "text_client"
                },
                timeout=180  # Environment setup can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    
                    # Display steps completed
                    steps_completed = result.get("steps_completed", [])
                    print(f"\n{Fore.GREEN}Steps completed:{Style.RESET_ALL}")
                    for step in steps_completed:
                        print(f"  ✓ {step}")
                    
                    # Display steps failed
                    steps_failed = result.get("steps_failed", [])
                    if steps_failed:
                        print(f"\n{Fore.RED}Steps failed:{Style.RESET_ALL}")
                        for step in steps_failed:
                            print(f"  ✗ {step}")
                    
                    # Project path
                    project_path = os.path.join(os.getcwd(), "projects", project_type)
                    print(f"\n{Fore.GREEN}Project setup at:{Style.RESET_ALL} {project_path}\n")
                    
                    # Generate voice for summary
                    generate_voice(f"Project {project_type} setup complete with {len(steps_completed)} steps completed and {len(steps_failed)} failures")
                    
                else:
                    print(f"{Fore.RED}Error: {data.get('error', 'Unknown error')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error: Server returned status {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error setting up environment: {str(e)}{Style.RESET_ALL}")
        
        return True
    
    elif command == "!analyze":
        print(f"{Fore.YELLOW}Analyzing JARVIS capabilities...{Style.RESET_ALL}")
        
        try:
            # Use MCPAction endpoint to access the new analysis capability
            response = requests.post(
                f"{SERVER_URL}/mcp/action",
                json={
                    "action_type": "analyze_capabilities",
                    "parameters": {},
                    "connection_id": "text_client"
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    result = data.get("result", {})
                    
                    # Display current capabilities
                    capabilities = result.get("current_capabilities", [])
                    print(f"\n{Fore.GREEN}Current capabilities ({len(capabilities)}):{Style.RESET_ALL}")
                    
                    # Group by file
                    capabilities_by_file = {}
                    for cap in capabilities:
                        file = cap.get("file", "unknown")
                        if file not in capabilities_by_file:
                            capabilities_by_file[file] = []
                        capabilities_by_file[file].append(cap)
                    
                    for file, caps in capabilities_by_file.items():
                        print(f"  {Fore.CYAN}{os.path.basename(file)}:{Style.RESET_ALL}")
                        for cap in caps:
                            print(f"    - {cap.get('type', 'unknown')}: {cap.get('name', 'unnamed')}")
                    
                    # Display suggested improvements
                    improvements = result.get("suggested_improvements", [])
                    print(f"\n{Fore.GREEN}Suggested improvements ({len(improvements)}):{Style.RESET_ALL}")
                    for imp in improvements:
                        print(f"  {Fore.YELLOW}{imp.get('name', 'unnamed')} ({imp.get('type', 'unknown')}){Style.RESET_ALL}")
                        print(f"    {imp.get('description', 'No description')}")
                    
                    print()
                    
                    # Generate voice for summary
                    generate_voice(f"Analysis complete. Found {len(capabilities)} capabilities and {len(improvements)} potential improvements")
                    
                else:
                    print(f"{Fore.RED}Error: {data.get('error', 'Unknown error')}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Error: Server returned status {response.status_code}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error analyzing capabilities: {str(e)}{Style.RESET_ALL}")
        
        return True
    
    elif command.startswith("!voice "):
        text = command[7:]
        if not text:
            print(f"{Fore.RED}Error: Text is required{Style.RESET_ALL}")
            return True
            
        print(f"{Fore.YELLOW}Generating voice: \"{text}\"{Style.RESET_ALL}")
        result = generate_voice(text)
        
        if result and result.get("success"):
            print(f"{Fore.GREEN}Voice generated successfully{Style.RESET_ALL}")
        
        return True
    
    elif command.startswith("!agent "):
        query = command[7:]
        if not query:
            print(f"{Fore.RED}Error: Query is required{Style.RESET_ALL}")
            return True
            
        print(f"{Fore.YELLOW}Running JARVIS agent with query: \"{query}\"{Style.RESET_ALL}")
        print(f"{Fore.CYAN}This might take some time as the agent works on your request...{Style.RESET_ALL}")
        
        # Check for required environment variables
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            print(f"{Fore.RED}Error: OPENAI_API_KEY environment variable is required for agent operations{Style.RESET_ALL}")
            return True
        
        try:
            # Launch the run_jarvis_agent.py script as a separate process
            import subprocess
            
            # Create a process to run the agent
            process = subprocess.Popen(
                [sys.executable, "run_jarvis_agent.py", query],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Display output in real-time
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())
            
            # Check for errors
            return_code = process.poll()
            if return_code != 0:
                error = process.stderr.read()
                print(f"{Fore.RED}Error running agent: {error}{Style.RESET_ALL}")
            
        except Exception as e:
            print(f"{Fore.RED}Error running agent: {str(e)}{Style.RESET_ALL}")
        
        return True
    
    return False

def main():
    """Main function to run the JARVIS text client"""
    clear_screen()
    print(f"{Fore.GREEN}=== JARVIS Text Client ==={Style.RESET_ALL}")
    print(f"Type your messages to JARVIS below. Type '!help' for commands or '!exit' to quit.")
    
    # Check if server is running
    server_ok = check_server_status()
    if server_ok:
        print(f"{Fore.GREEN}✓ Connected to JARVIS server{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ Could not connect to JARVIS server{Style.RESET_ALL}")
        print(f"Make sure the server is running on {SERVER_URL}")
        return
    
    # Register connection with the MCP server
    try:
        response = requests.get(f"{SERVER_URL}/mcp/connect?client_type=text_client")
        if response.status_code == 200:
            data = response.json()
            connection_id = data.get("connection_id")
            print(f"{Fore.GREEN}✓ Registered with MCP server (ID: {connection_id}){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}! MCP registration failed (status: {response.status_code}){Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.YELLOW}! MCP registration failed: {str(e)}{Style.RESET_ALL}")
    
    # Main input loop
    while True:
        try:
            user_input = input(f"{Fore.CYAN}You:{Style.RESET_ALL} ")
            
            # Handle special commands
            if user_input.startswith("!"):
                if process_special_command(user_input):
                    continue
            
            # Process regular input
            result = process_text(user_input)
            
            if result and "response" in result:
                print(f"{Fore.GREEN}JARVIS:{Style.RESET_ALL} {result['response']}")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Exiting JARVIS client. Goodbye!{Style.RESET_ALL}")
            break
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")

if __name__ == "__main__":
    main() 