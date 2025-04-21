import os
import sys
import subprocess
import webbrowser
import json
import platform
import ctypes
import time
from datetime import datetime
import pyautogui
import psutil
import pywintypes
import win32api
import win32con
import win32gui
import win32process

class JARVISSystemControl:
    """
    System control module that enables JARVIS to interact with the computer system
    like the movie version - controlling applications, files, and settings
    """
    def __init__(self):
        self.system = platform.system()
        self.apps_paths = self._load_app_paths()
        
    def _load_app_paths(self):
        """Load known application paths from configuration or create default"""
        default_paths = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "firefox": r"C:\Program Files\Mozilla Firefox\firefox.exe",
            "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            "notepad": r"C:\Windows\System32\notepad.exe",
            "explorer": r"C:\Windows\explorer.exe",
            "word": r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            "excel": r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            "spotify": r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
            "code": r"C:\Users\%USERNAME%\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "cursor": r"C:\Users\%USERNAME%\AppData\Local\Programs\Cursor\Cursor.exe"
        }
        
        # Try to load from file, or use default
        config_path = os.path.join(os.path.dirname(__file__), "jarvis_apps.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        # Resolve username in paths
        for key, path in default_paths.items():
            default_paths[key] = path.replace("%USERNAME%", os.getenv("USERNAME"))
        
        # Save default paths
        try:
            with open(config_path, 'w') as f:
                json.dump(default_paths, f, indent=2)
        except:
            pass
            
        return default_paths
    
    def open_application(self, app_name):
        """Open an application by name"""
        app_name = app_name.lower()
        
        try:
            # Check if it's in our known apps
            if app_name in self.apps_paths:
                path = self.apps_paths[app_name]
                if os.path.exists(path):
                    subprocess.Popen([path])
                    return f"Opening {app_name}"
                
            # Try as a system command
            subprocess.Popen([app_name], shell=True)
            return f"Attempting to open {app_name}"
            
        except Exception as e:
            return f"Failed to open {app_name}: {str(e)}"
    
    def open_website(self, url):
        """Open a website in the default browser"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        try:
            webbrowser.open(url)
            return f"Opening {url}"
        except Exception as e:
            return f"Failed to open {url}: {str(e)}"
    
    def search_web(self, query):
        """Search the web for a query"""
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        try:
            webbrowser.open(search_url)
            return f"Searching for {query}"
        except Exception as e:
            return f"Failed to search for {query}: {str(e)}"
    
    def show_system_info(self):
        """Get system information like CPU, memory, disk usage"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            battery_info = ""
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = f"Battery: {battery.percent}% ({'Charging' if battery.power_plugged else 'Discharging'})"
            
            return f"""System Information:
CPU Usage: {cpu_percent}%
Memory: {memory.percent}% used ({memory.used / (1024**3):.2f} GB / {memory.total / (1024**3):.2f} GB)
Disk: {disk.percent}% used ({disk.used / (1024**3):.2f} GB / {disk.total / (1024**3):.2f} GB)
{battery_info}
OS: {platform.system()} {platform.version()}
Machine: {platform.machine()}
"""
        except Exception as e:
            return f"Failed to get system information: {str(e)}"
    
    def set_volume(self, level):
        """Set system volume (0-100)"""
        if self.system != 'Windows':
            return "Volume control is only supported on Windows"
            
        try:
            level = max(0, min(100, level))  # Ensure level is between 0-100
            
            # Windows-specific volume control
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
            
            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            
            # Convert to scalar value (0.0 to 1.0)
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
            
            return f"Volume set to {level}%"
        except Exception as e:
            # Fallback method using keyboard simulation
            try:
                # Set system volume using keyboard shortcuts
                # First mute to reset
                pyautogui.press('volumemute')
                time.sleep(0.5)
                
                # Then set to desired level
                vol_steps = round(level / 2)  # Each press is ~2%
                for _ in range(vol_steps):
                    pyautogui.press('volumeup')
                    time.sleep(0.1)
                
                return f"Volume set to approximately {level}%"
            except:
                return f"Failed to set volume: {str(e)}"
    
    def take_screenshot(self, filename=None):
        """Take a screenshot and save it"""
        try:
            if not filename:
                filename = f"jarvis_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            
            save_path = os.path.join(os.path.expanduser("~"), "Pictures", filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            screenshot = pyautogui.screenshot()
            screenshot.save(save_path)
            
            return f"Screenshot saved to {save_path}"
        except Exception as e:
            return f"Failed to take screenshot: {str(e)}"
    
    def list_running_apps(self):
        """List currently running applications"""
        try:
            result = []
            
            if self.system == 'Windows':
                def window_enum_handler(hwnd, results):
                    if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            process = psutil.Process(pid)
                            title = win32gui.GetWindowText(hwnd)
                            if title and process.name() not in [p.name() for _, p in results]:
                                results.append((title, process))
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                
                window_list = []
                win32gui.EnumWindows(window_enum_handler, window_list)
                
                for title, process in window_list:
                    result.append(f"{process.name()} - {title}")
            else:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        # Filter out background processes
                        if proc.info['name'] not in ['System', 'svchost.exe', 'services.exe']:
                            result.append(proc.info['name'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            
            # Remove duplicates while preserving order
            unique_results = []
            for item in result:
                if item not in unique_results:
                    unique_results.append(item)
            
            return "Running Applications:\n" + "\n".join(unique_results[:15])  # Limit to first 15 for readability
        except Exception as e:
            return f"Failed to list running applications: {str(e)}"
    
    def execute_command(self, command):
        """Execute a system command (with safety limits)"""
        # List of potentially dangerous commands
        dangerous_commands = ['rm', 'del', 'format', 'shutdown', 'reboot', 'mkfs', 'fdisk']
        
        # Check if command contains dangerous operations
        if any(cmd in command.lower() for cmd in dangerous_commands):
            return "I cannot execute potentially dangerous system commands"
        
        try:
            # Execute with timeout for safety
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                return f"Command executed:\n{result.stdout}"
            else:
                return f"Command failed with error code {result.returncode}:\n{result.stderr}"
        except subprocess.TimeoutExpired:
            return "Command timed out after 10 seconds"
        except Exception as e:
            return f"Failed to execute command: {str(e)}"
    
    def create_reminder(self, message, minutes=0):
        """Create a reminder that will show a notification"""
        try:
            if minutes <= 0:
                return "Please specify a valid time in minutes"
                
            # Convert to seconds
            seconds = minutes * 60
            
            # Create a background thread for the reminder
            import threading
            
            def show_reminder():
                time.sleep(seconds)
                self.show_notification("JARVIS Reminder", message)
            
            reminder_thread = threading.Thread(target=show_reminder)
            reminder_thread.daemon = True
            reminder_thread.start()
            
            return f"Reminder set for {minutes} minutes from now"
        except Exception as e:
            return f"Failed to set reminder: {str(e)}"
    
    def show_notification(self, title, message):
        """Show a system notification"""
        try:
            if self.system == 'Windows':
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=10)
            else:
                # For other systems, we could use other notification methods
                print(f"Notification: {title} - {message}")
                
            return "Notification sent"
        except Exception as e:
            return f"Failed to show notification: {str(e)}"
    
    def process_system_command(self, command_text):
        """Process natural language command and map to system functions"""
        command_text = command_text.lower()
        
        # Application control
        if "open" in command_text:
            for app in self.apps_paths.keys():
                if app in command_text:
                    return self.open_application(app)
            
            # Check for website opening commands
            if "website" in command_text or ".com" in command_text or ".org" in command_text or ".net" in command_text:
                # Extract URL
                words = command_text.split()
                for word in words:
                    if "." in word:
                        return self.open_website(word)
        
        # Web search
        if "search" in command_text or "google" in command_text or "look up" in command_text:
            # Extract search query
            search_terms = command_text.replace("search", "").replace("google", "").replace("look up", "").strip()
            if search_terms:
                return self.search_web(search_terms)
        
        # System information
        if "system" in command_text and ("info" in command_text or "status" in command_text or "statistics" in command_text):
            return self.show_system_info()
        
        # Volume control
        if "volume" in command_text:
            if "set" in command_text or "change" in command_text:
                for word in command_text.split():
                    if word.isdigit():
                        return self.set_volume(int(word))
                        
            if "up" in command_text or "increase" in command_text:
                return self.set_volume(75)
                
            if "down" in command_text or "decrease" in command_text:
                return self.set_volume(25)
                
            if "mute" in command_text:
                return self.set_volume(0)
        
        # Screenshot
        if "screenshot" in command_text or "capture screen" in command_text:
            return self.take_screenshot()
        
        # List running applications
        if "list" in command_text and ("apps" in command_text or "applications" in command_text or "programs" in command_text):
            return self.list_running_apps()
        
        # Reminder
        if "remind" in command_text or "reminder" in command_text:
            # Extract time (in minutes)
            minutes = 5  # Default to 5 minutes
            for word in command_text.split():
                if word.isdigit():
                    minutes = int(word)
                    break
                    
            # Extract message
            message = command_text
            for time_word in ["minutes", "minute", "mins", "min"]:
                if time_word in message:
                    message = message.split(time_word, 1)[1].strip()
                    break
                    
            return self.create_reminder(message, minutes)
        
        # Command execution (restricted)
        if "execute" in command_text or "run command" in command_text:
            cmd = command_text.replace("execute", "").replace("run command", "").strip()
            return self.execute_command(cmd)
        
        return "I'm not sure how to process that system command"

# Simple test function
def test_system_control():
    controller = JARVISSystemControl()
    
    # Test basic functions
    print("System Info:")
    print(controller.show_system_info())
    
    print("\nRunning Apps:")
    print(controller.list_running_apps())
    
    # Test natural language commands
    test_commands = [
        "open chrome",
        "search for latest AI news",
        "show system status",
        "take a screenshot",
        "set volume to 50",
        "remind me in 5 minutes to check email"
    ]
    
    print("\nTesting natural language commands:")
    for cmd in test_commands:
        print(f"\nCommand: {cmd}")
        print(f"Response: {controller.process_system_command(cmd)}")

if __name__ == "__main__":
    test_system_control() 