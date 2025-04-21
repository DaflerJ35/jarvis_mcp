import sys
import os
import json
import time
import random
import requests
from datetime import datetime
import threading
import subprocess
import queue
import speech_recognition as sr

# Modern UI imports
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QLineEdit, QTextEdit, QTabWidget,
                             QSplitter, QFrame, QGraphicsDropShadowEffect, QListWidget,
                             QListWidgetItem, QProgressBar, QSystemTrayIcon, QMenu, QAction,
                             QComboBox, QRadioButton, QButtonGroup, QToolTip)
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon, QPixmap, QLinearGradient, QGradient, QPainter, QBrush, QPen, QRadialGradient
from PyQt5.QtCore import Qt, QSize, QTimer, QThread, pyqtSignal, QUrl, QPropertyAnimation, QRect, QPoint
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtWebEngineWidgets import QWebEngineView

# Import voice recognition
from jarvis_voice_recognition import JARVISVoiceRecognition

# Global Configuration Settings
DEFAULT_AUTO_START_VOICE = True  # Auto start voice recognition
DEFAULT_VOICE_MODE = 1  # 0 = Wake Word, 1 = Seamless Chat
FORCE_SEAMLESS_MODE = True  # Always use seamless mode for voice

# Constants
JARVIS_SERVER_URL = "http://localhost:8000"
DARK_BLUE = "#1A1A2E"
MEDIUM_BLUE = "#16213E"
LIGHT_BLUE = "#0F3460"
ACCENT_BLUE = "#3282B8"
ACCENT_ORANGE = "#E94560"
FONT_PRIMARY = "Roboto"
FONT_SECONDARY = "Consolas"
FONT_SIZE_NORMAL = 10
FONT_SIZE_LARGE = 14

class NetworkWorker(threading.Thread):
    def __init__(self, callback, error_callback, method, **kwargs):
        super().__init__()
        self.callback = callback
        self.error_callback = error_callback
        self.method = method
        self.kwargs = kwargs
        self.daemon = True  # Thread will exit when main program exits
        
    def run(self):
        try:
            if self.method == "get":
                response = requests.get(**self.kwargs)
            elif self.method == "post":
                response = requests.post(**self.kwargs)
            else:
                raise ValueError(f"Unsupported method: {self.method}")
                
            if response.status_code == 200:
                data = response.json()
                if self.callback:
                    self.callback(data)
            else:
                if self.error_callback:
                    self.error_callback(f"Server returned status {response.status_code}")
        except Exception as e:
            if self.error_callback:
                self.error_callback(str(e))

class JarvisGUI(QMainWindow):
    def __init__(self, server_port=8000, alternate_port=8080, mcp_port=5000):
        """Initialize JARVIS GUI"""
        super().__init__()
        
        # Set window title and size
        self.setWindowTitle("JARVIS - Just A Rather Very Intelligent System")
        self.resize(1200, 800)
        
        # Server settings
        self.server_port = server_port
        self.alternate_port = alternate_port
        self.mcp_port = mcp_port
        self.server_url = f"http://localhost:{server_port}"
        
        # Initialize UI components
        self.setup_ui()
        
        # Add startup sequence animations
        self.setup_startup_sequence()
        
        # Setup timers for periodic updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_animations)
        self.update_timer.start(1000)  # Update every second
        
        # Server status check timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.check_server_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
        # Setup voice recognition related variables
        self.voice_active = False
        self.voice_recognition = None
        self.voice_setup_complete = False
        self.voice_command_thread = None
        self.voice_timer = QTimer(self)
        self.voice_timer.timeout.connect(self.process_voice_commands)
        
        # Define voice modes
        self.voice_modes = ["Push-to-Talk", "Wake Word", "Seamless Chat"]
        self.current_voice_mode = DEFAULT_VOICE_MODE
        
        # Check server status on startup
        self.check_server_status()
        
        # Auto-start voice if configured
        if DEFAULT_AUTO_START_VOICE:
            QTimer.singleShot(2000, self.auto_start_voice)  # Start after 2 seconds to ensure server connection is established
        
    def setup_ui(self):
        # Main widget
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main layout
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MEDIUM_BLUE};
                border-radius: 10px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        
        # JARVIS logo & title
        logo_label = QLabel()
        logo_label.setPixmap(self.create_dummy_logo())
        logo_label.setMaximumSize(70, 70)
        logo_label.setScaledContents(True)
        
        title_label = QLabel("J.A.R.V.I.S.")
        title_label.setFont(QFont(FONT_PRIMARY, 24, QFont.Bold))
        title_label.setStyleSheet(f"color: {ACCENT_BLUE};")
        
        # System status
        self.status_label = QLabel("System Status: Connecting...")
        self.status_label.setFont(QFont(FONT_PRIMARY, 12))
        
        # Voice status indicator
        self.voice_status = QLabel("Voice: Inactive")
        self.voice_status.setStyleSheet("color: #555555;")
        
        # Voice control area
        voice_area = QWidget()
        voice_layout = QVBoxLayout(voice_area)
        
        # Create voice mode selection area
        voice_mode_frame = QFrame()
        voice_mode_layout = QHBoxLayout(voice_mode_frame)
        voice_mode_layout.setContentsMargins(10, 5, 10, 5)
        
        voice_mode_label = QLabel("Voice Mode:")
        voice_mode_layout.addWidget(voice_mode_label)
        
        self.voice_mode_group = QButtonGroup(self)
        
        # Add radio buttons for each voice mode
        for i, mode in enumerate(self.voice_modes):
            radio = QRadioButton(mode)
            voice_mode_layout.addWidget(radio)
            self.voice_mode_group.addButton(radio, i)
            if mode == self.current_voice_mode:
                radio.setChecked(True)
                
        self.voice_mode_group.buttonClicked.connect(self.change_voice_mode)
        
        # Add voice mode selection to main layout
        main_layout.addWidget(voice_mode_frame)
        
        # Voice activation button
        self.voice_button = QPushButton("🎤 Activate Voice")
        self.voice_button.setToolTip("Click to activate voice recognition")
        self.voice_button.clicked.connect(self.toggle_voice_recognition)
        voice_layout.addWidget(self.voice_button)
        
        # Voice status indicator
        self.voice_status = QLabel("Voice: Inactive")
        self.voice_status.setStyleSheet("color: #555555;")
        voice_layout.addWidget(self.voice_status)
        
        # Add to header
        header_layout.addWidget(logo_label)
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.voice_status)
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.voice_button)
        
        # Main content area
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left sidebar
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # System metrics
        metrics_frame = QFrame()
        metrics_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MEDIUM_BLUE};
                border-radius: 10px;
            }}
        """)
        metrics_layout = QVBoxLayout(metrics_frame)
        
        metrics_title = QLabel("System Metrics")
        metrics_title.setFont(QFont(FONT_PRIMARY, FONT_SIZE_LARGE, QFont.Bold))
        
        self.cpu_bar = QProgressBar()
        self.cpu_bar.setFormat("CPU: %p%")
        self.cpu_bar.setValue(random.randint(5, 20))
        
        self.memory_bar = QProgressBar()
        self.memory_bar.setFormat("Memory: %p%")
        self.memory_bar.setValue(random.randint(20, 40))
        
        self.tasks_bar = QProgressBar()
        self.tasks_bar.setFormat("Active Tasks: %v")
        self.tasks_bar.setRange(0, 10)
        self.tasks_bar.setValue(0)
        
        metrics_layout.addWidget(metrics_title)
        metrics_layout.addWidget(self.cpu_bar)
        metrics_layout.addWidget(self.memory_bar)
        metrics_layout.addWidget(self.tasks_bar)
        
        # Status log
        status_frame = QFrame()
        status_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {MEDIUM_BLUE};
                border-radius: 10px;
            }}
        """)
        status_layout = QVBoxLayout(status_frame)
        
        status_title = QLabel("System Log")
        status_title.setFont(QFont(FONT_PRIMARY, FONT_SIZE_LARGE, QFont.Bold))
        
        self.status_list = QListWidget()
        self.status_list.setFont(QFont(FONT_SECONDARY, FONT_SIZE_NORMAL))
        
        status_layout.addWidget(status_title)
        status_layout.addWidget(self.status_list)
        
        # Add to left sidebar
        left_layout.addWidget(metrics_frame)
        left_layout.addWidget(status_frame)
        
        # Main tab area
        self.tabs = QTabWidget()
        
        # Dashboard tab
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        
        # Create a web view for dashboard (HUD-like display)
        dashboard_web = QWebEngineView()
        dashboard_web.setHtml(self.get_dashboard_html())
        
        dashboard_layout.addWidget(dashboard_web)
        
        # Console tab
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont(FONT_SECONDARY, FONT_SIZE_NORMAL))
        self.console_output.setLineWrapMode(QTextEdit.NoWrap)
        
        self.console_input = QLineEdit()
        self.console_input.setFont(QFont(FONT_SECONDARY, FONT_SIZE_NORMAL))
        self.console_input.setPlaceholderText("Enter command...")
        self.console_input.returnPressed.connect(self.process_command)
        
        console_layout.addWidget(self.console_output)
        console_layout.addWidget(self.console_input)
        
        # Knowledge tab
        knowledge_widget = QWidget()
        knowledge_layout = QVBoxLayout(knowledge_widget)
        
        self.knowledge_search = QLineEdit()
        self.knowledge_search.setPlaceholderText("Search knowledge base...")
        self.knowledge_search.returnPressed.connect(self.search_knowledge)
        
        self.knowledge_results = QTextEdit()
        self.knowledge_results.setReadOnly(True)
        
        knowledge_layout.addWidget(self.knowledge_search)
        knowledge_layout.addWidget(self.knowledge_results)
        
        # Code tab
        code_widget = QWidget()
        code_layout = QVBoxLayout(code_widget)
        
        code_input_layout = QHBoxLayout()
        
        self.code_spec = QLineEdit()
        self.code_spec.setPlaceholderText("Describe the code you need...")
        
        self.code_language = QLineEdit()
        self.code_language.setPlaceholderText("Language (python, javascript, etc.)")
        self.code_language.setText("python")
        self.code_language.setMaximumWidth(150)
        
        self.generate_button = QPushButton("Generate")
        self.generate_button.clicked.connect(self.generate_code)
        
        code_input_layout.addWidget(self.code_spec)
        code_input_layout.addWidget(self.code_language)
        code_input_layout.addWidget(self.generate_button)
        
        self.code_output = QTextEdit()
        self.code_output.setFont(QFont(FONT_SECONDARY, FONT_SIZE_NORMAL))
        
        self.execute_button = QPushButton("Execute")
        self.execute_button.clicked.connect(self.execute_code)
        
        code_layout.addLayout(code_input_layout)
        code_layout.addWidget(self.code_output)
        code_layout.addWidget(self.execute_button)
        
        # Add tabs
        self.tabs.addTab(dashboard_widget, "Dashboard")
        self.tabs.addTab(console_widget, "Console")
        self.tabs.addTab(knowledge_widget, "Knowledge")
        self.tabs.addTab(code_widget, "Code")
        
        # Add widgets to splitter
        content_splitter.addWidget(left_widget)
        content_splitter.addWidget(self.tabs)
        content_splitter.setSizes([300, 900])  # Initial sizes
        
        # Add to main layout
        main_layout.addWidget(header_frame)
        main_layout.addWidget(content_splitter, 1)  # 1 = stretch factor
        
        # Create shadow effect for the header
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 5)
        header_frame.setGraphicsEffect(shadow)
        
        # Create shadow effects for frames
        for frame in [metrics_frame, status_frame]:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(10)
            shadow.setColor(QColor(0, 0, 0, 180))
            shadow.setOffset(0, 2)
            frame.setGraphicsEffect(shadow)

    def create_dummy_logo(self):
        """Create a simple blue circle as a placeholder logo"""
        pixmap = QPixmap(100, 100)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Create a gradient for the logo
        gradient = QRadialGradient(50, 50, 50)
        gradient.setColorAt(0, QColor(ACCENT_BLUE))
        gradient.setColorAt(1, QColor(DARK_BLUE))
        
        # Draw the main circle
        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(10, 10, 80, 80)
        
        # Draw a "J" in the middle
        painter.setPen(QPen(Qt.white, 2))
        painter.setFont(QFont(FONT_PRIMARY, 40, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "J")
        
        painter.end()
        return pixmap
        
    def init_voice_recognition(self):
        """Initialize voice recognition system"""
        try:
            from jarvis_voice_recognition import JARVISVoiceRecognition
            self.voice_system = JARVISVoiceRecognition(wake_word="jarvis")
            self.voice_setup_complete = True
            self.add_status_message("Voice recognition initialized")
            
            # Start a thread to check for voice commands
            self.voice_command_thread = threading.Thread(target=self.process_voice_commands, daemon=True)
            self.voice_command_thread.start()
            
            # Auto-start voice based on selected mode
            self.change_voice_mode(self.voice_mode_group.button(self.current_voice_mode))
            
        except Exception as e:
            self.add_status_message(f"Error initializing voice recognition: {str(e)}")
            self.voice_status.setText("Voice: ERROR")
            self.voice_status.setStyleSheet("color: red;")
    
    def change_voice_mode(self, button):
        """Change the voice recognition mode"""
        # Get selected mode
        selected_id = self.voice_mode_group.id(button)
        self.current_voice_mode = self.voice_modes[selected_id]
        
        self.add_status_message(f"Voice mode changed to {self.current_voice_mode}")
        
        # If voice is active, restart it with new mode
        if self.voice_active:
            self.stop_voice_recognition()
            self.start_voice_recognition()
        
        # Update button text based on mode even if not active
        if self.current_voice_mode == "Push-to-Talk":
            self.voice_button.setText("🎤 Activate Push-to-Talk")
        elif self.current_voice_mode == "Wake Word":
            self.voice_button.setText("🎤 Activate Wake Word")
        else:  # Seamless Chat
            self.voice_button.setText("🎤 Activate Seamless Chat")
    
    def toggle_voice_recognition(self):
        """Toggle voice recognition on/off"""
        if not hasattr(self, 'voice_recognition') or self.voice_recognition is None:
            self.setup_voice_recognition()
            
        if self.voice_recognition.is_running():
            # Stop voice recognition
            self.voice_recognition.stop_listening()
            self.update_voice_status(False)
            self.add_status_message("Voice recognition stopped")
        else:
            # Start voice recognition in the current mode
            seamless = self.current_voice_mode == 1
            self.voice_recognition.start_listening(continuous=True, seamless=seamless)
            self.update_voice_status(True)
            self.add_status_message(f"Voice recognition started in {'Seamless Chat' if seamless else 'Wake Word'} mode")
    
    def auto_start_voice(self):
        """Automatically start voice recognition in Seamless Chat mode."""
        try:
            if not hasattr(self, 'voice_recognition') or self.voice_recognition is None:
                self.setup_voice_recognition()
            
            # If voice recognition is already running, no need to start it again
            if hasattr(self, 'voice_recognition') and self.voice_recognition.is_running():
                self.add_status_message("Voice recognition already running")
                return
                
            # Always use Seamless Chat mode for auto-start
            self.current_voice_mode = 1  # Seamless Chat mode
            
            # Make sure voice button is visible
            if hasattr(self, 'voice_button') and self.voice_button.isHidden():
                self.voice_button.show()
            
            # Start voice recognition in Seamless Chat mode
            self.toggle_voice_recognition()
            
            self.add_status_message("Voice recognition auto-started in Seamless Chat mode")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error auto-starting voice recognition: {str(e)}")
            print(f"Error auto-starting voice recognition: {str(e)}")
    
    def update_voice_status(self, is_active, mode=""):
        self.voice_active = is_active
        self.voice_status.setText(f"Voice: {mode} Mode")
        self.voice_status.setStyleSheet("color: #50c878;" if is_active else "color: #555555;")
    
    def start_voice_recognition(self):
        """Start voice recognition based on current mode"""
        if not hasattr(self, 'voice_recognition') or self.voice_recognition is None:
            if not self.setup_voice_recognition():
                self.add_status_message("Failed to initialize voice recognition", "error")
                return
            
        try:
            # Override mode to Seamless Chat if forced
            if FORCE_SEAMLESS_MODE:
                self.current_voice_mode = "Seamless Chat"
            
            # Set mode based on selection
            if self.current_voice_mode == "Push-to-Talk":
                # Push-to-Talk mode (single command)
                self.voice_recognition.start_listening(continuous=False, seamless=False)
                self.voice_button.setText("🎤 Listening...")
                self.voice_button.setStyleSheet("background-color: #ff5050;")
                self.add_status_message("Push-to-Talk mode activated - click to speak")
            
            elif self.current_voice_mode == "Wake Word":
                # Wake word mode (continuous with wake word)
                self.voice_recognition.start_listening(continuous=True, seamless=False)
                self.voice_button.setText("🎤 Wake Word Active")
                self.voice_button.setStyleSheet("background-color: #50c878;")
                self.add_status_message(f"Wake Word mode activated - say '{self.voice_recognition.wake_word}' to begin")
            
            else:  # Seamless Chat
                # Seamless mode (continuous without wake word)
                self.voice_recognition.start_listening(continuous=True, seamless=True)
                self.voice_button.setText("🎤 Seamless Chat Active")
                self.voice_button.setStyleSheet("background-color: #50c878;")
                self.add_status_message("Seamless mode activated - speak naturally without a wake word")
            
            self.voice_active = True
            self.voice_status.setText(f"Voice: {self.current_voice_mode} Mode")
            self.voice_status.setStyleSheet("color: #50c878;")
            
            # Start command processing timer if not already running
            if not self.voice_timer.isActive():
                self.voice_timer.start(100)  # Check for commands every 100ms
                
        except Exception as e:
            self.add_status_message(f"Error starting voice recognition: {str(e)}")
            self.voice_button.setText("🎤 Voice Error")
            self.voice_button.setStyleSheet("background-color: #ff5050;")
            print(f"Voice error: {str(e)}")
    
    def stop_voice_recognition(self):
        """Stop voice recognition"""
        if self.voice_recognition:
            self.voice_recognition.stop_listening()
            
        self.voice_active = False
        self.seamless_mode = False
        self.voice_button.setText("🎤 Activate Voice")
        self.voice_button.setStyleSheet("")
        self.add_status_message("Voice recognition stopped")
    
    def process_voice_commands(self):
        """Process voice commands from the queue"""
        if not hasattr(self, 'voice_recognition') or not self.voice_recognition or not self.voice_active:
            return
        
        try:
            # Check for commands
            command = self.voice_recognition.get_next_command(block=False)
            
            if command:
                self.add_status_message(f"Voice command received: {command}")
                self.process_input(command, is_voice=True)
                
                # In Push-to-Talk mode, stop after one command
                if self.current_voice_mode == "Push-to-Talk":
                    self.voice_active = False
                    self.voice_button.setText("🎤 Activate Voice")
                    self.voice_button.setStyleSheet("")
                    self.stop_voice_recognition()
                
        except Exception as e:
            self.add_status_message(f"Error processing voice commands: {str(e)}")
        
        # Thread ending
        self.status_bar.showMessage("Voice recognition stopped", 3000)
        
    def process_input(self, text, is_voice=False):
        """Process input from text field or voice"""
        if not text.strip():
            return
            
        # If not from voice input, add to chat display
        if not is_voice:
            self.add_message(f"You: {text}", is_user=True)
        
        # Reset input field if not voice
        if not is_voice:
            self.input_field.clear()
        
        # Process and send to server
        self.send_to_server(text)
        
    def send_to_server(self, text):
        """Send request to JARVIS server and process response"""
        # ... existing code ...
    
    def keyPressEvent(self, event):
        """Handle key press events"""
        # ... existing code ...

    def play_startup_sound(self):
        """Play a startup sound effect"""
        # This would use QMediaPlayer to play an actual sound
        # For now, we'll just log it
        self.add_status_message("Startup sequence complete")
    
    def update_animations(self):
        """Update animated elements"""
        # Update progress bars with slightly random values to simulate activity
        current_cpu = self.cpu_bar.value()
        current_mem = self.memory_bar.value()
        
        new_cpu = max(5, min(95, current_cpu + random.randint(-2, 2)))
        new_mem = max(20, min(90, current_mem + random.randint(-1, 1)))
        
        self.cpu_bar.setValue(new_cpu)
        self.memory_bar.setValue(new_mem)
    
    def process_command(self, voice_command=None):
        """Process a command entered in the console or from voice"""
        # Get command from either voice or text input
        if voice_command:
            command = voice_command.strip()
        else:
            command = self.console_input.text().strip()
            self.console_input.clear()
        
        if not command:
            return
            
        # Echo the command if from text input (voice commands already echoed)
        if not voice_command:
            self.console_output.append(f"<span style='color:#E94560;'>>&gt; {command}</span>")
        
        # Process command
        if command.lower() == "help":
            self.console_output.append("""
<span style='color:#3282B8;'>Available commands:</span>
- help: Show this help message
- status: Show server status
- search &lt;query&gt;: Search knowledge base
- task &lt;description&gt;: Start a new task
- clear: Clear console
            """)
        elif command.lower() == "status":
            self.check_server_status(show_output=True)
        elif command.lower() == "clear":
            self.console_output.clear()
        elif command.lower().startswith("search "):
            query = command[7:]
            self.search_knowledge(query, show_in_console=True)
        elif command.lower().startswith("task "):
            description = command[5:]
            self.start_task(description, show_in_console=True)
        else:
            # For any other command, try to send it to the server
            self.send_command_to_server(command)
            
        # Speak the response if this was a voice command
        if voice_command:
            self.speak_response(f"Processing command: {command}")

    def speak_response(self, text):
        """Send text to server for voice synthesis"""
        try:
            worker = NetworkWorker(
                callback=None,
                error_callback=lambda err: self.add_status_message(f"Voice error: {err}"),
                method="post",
                url=f"{JARVIS_SERVER_URL}/",
                json={"method": "generate_voice", "params": {"text": text}}
            )
            worker.start()
        except Exception as e:
            self.add_status_message(f"Error in voice synthesis: {str(e)}")

    def send_command_to_server(self, command):
        """Send a general command to the server"""
        try:
            response = requests.post(
                f"{JARVIS_SERVER_URL}/",
                json={"method": "automate_task", "params": {"command": command}}
            )
            if response.status_code == 200:
                data = response.json()
                self.console_output.append(f"<span style='color:#3282B8;'>{data.get('output', 'Command executed')}</span>")
            else:
                self.console_output.append(f"<span style='color:#E94560;'>Error: Server returned status {response.status_code}</span>")
        except Exception as e:
            self.console_output.append(f"<span style='color:#E94560;'>Error: {str(e)}</span>")
    
    def check_server_status(self, show_output=False):
        """Check if the JARVIS server is running"""
        def success_callback(data):
            self.status_label.setText(f"System Status: Online ({data.get('version', 'Unknown')})")
            self.status_label.setStyleSheet("color: #4ADE80;")  # Green color
            
            # Update tasks if available in the response
            if "active_tasks" in data:
                self.tasks_bar.setValue(data["active_tasks"])
            
            if show_output:
                features = ", ".join(data.get("features", []))
                self.console_output.append(f"""
<span style='color:#3282B8;'>JARVIS Server Status:</span>
- Name: {data.get('name', 'Unknown')}
- Version: {data.get('version', 'Unknown')}
- Status: {data.get('status', 'Unknown')}
- Features: {features}
                """)
        
        def error_callback(error_msg):
            self.status_label.setText("System Status: Error")
            self.status_label.setStyleSheet(f"color: {ACCENT_ORANGE};")
            
            if show_output:
                self.console_output.append(f"<span style='color:#E94560;'>Error: {error_msg}</span>")
        
        worker = NetworkWorker(
            callback=success_callback,
            error_callback=error_callback,
            method="get",
            url=f"{JARVIS_SERVER_URL}/"
        )
        worker.start()
    
    def add_status_message(self, message):
        """Add a message to the status log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        item = QListWidgetItem(f"{timestamp} - {message}")
        self.status_list.insertItem(0, item)  # Add at the top
    
    def search_knowledge(self, query=None, show_in_console=False):
        """Search the knowledge base"""
        if query is None:
            query = self.knowledge_search.text().strip()
            
        if not query:
            return
            
        def success_callback(data):
            results = data.get("results", [])
            
            # Format results
            formatted_results = ""
            for i, result in enumerate(results, 1):
                text = result.get("text", "")
                source = result.get("source", "unknown")
                formatted_results += f"{i}. {text}\n   Source: {source}\n\n"
            
            # Display results
            if show_in_console:
                self.console_output.append(f"<span style='color:#3282B8;'>Search results for '{query}':</span>")
                if formatted_results:
                    self.console_output.append(formatted_results)
                else:
                    self.console_output.append("No results found.")
            else:
                self.knowledge_results.setText(formatted_results or "No results found.")
        
        def error_callback(error_msg):
            if show_in_console:
                self.console_output.append(f"<span style='color:#E94560;'>Error: {error_msg}</span>")
            else:
                self.knowledge_results.setText(f"Error: {error_msg}")
        
        worker = NetworkWorker(
            callback=success_callback,
            error_callback=error_callback,
            method="post",
            url=f"{JARVIS_SERVER_URL}/",
            json={"method": "search_knowledge", "params": {"query": query}}
        )
        worker.start()
    
    def generate_code(self):
        """Generate code based on specification"""
        spec = self.code_spec.text().strip()
        language = self.code_language.text().strip()
        
        if not spec:
            self.code_output.setText("Please enter a specification.")
            return
            
        # Disable button while processing
        self.generate_button.setEnabled(False)
        self.generate_button.setText("Generating...")
        
        def success_callback(data):
            code = data.get("code", "")
            
            # Display code
            self.code_output.setText(code)
            self.add_status_message(f"Generated {language} code")
            
            # Re-enable button
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Generate")
        
        def error_callback(error_msg):
            self.code_output.setText(f"Error: {error_msg}")
            self.generate_button.setEnabled(True)
            self.generate_button.setText("Generate")
        
        worker = NetworkWorker(
            callback=success_callback,
            error_callback=error_callback,
            method="post",
            url=f"{JARVIS_SERVER_URL}/",
            json={"method": "generate_code", "params": {"spec": spec, "language": language}}
        )
        worker.start()
    
    def execute_code(self):
        """Execute the code in the code output"""
        code = self.code_output.toPlainText().strip()
        language = self.code_language.text().strip()
        
        if not code:
            return
            
        try:
            response = requests.post(
                f"{JARVIS_SERVER_URL}/",
                json={"method": "execute_code", "params": {"code": code, "language": language}}
            )
            
            if response.status_code == 200:
                data = response.json()
                output = data.get("output", "")
                error = data.get("error", "")
                
                # Display results
                result_text = f"Execution result:\n\n"
                if output:
                    result_text += f"Output:\n{output}\n\n"
                if error:
                    result_text += f"Error:\n{error}\n"
                
                self.code_output.append("\n\n" + result_text)
                self.add_status_message(f"Executed {language} code")
            else:
                self.code_output.append(f"\n\nError: Server returned status {response.status_code}")
        except Exception as e:
            self.code_output.append(f"\n\nError: {str(e)}")
    
    def start_task(self, description, show_in_console=False):
        """Start a new autonomous task"""
        try:
            response = requests.post(
                f"{JARVIS_SERVER_URL}/",
                json={"method": "start_task", "params": {"description": description}}
            )
            
            if response.status_code == 200:
                data = response.json()
                task_id = data.get("task_id", "")
                
                self.add_status_message(f"Started task: {description}")
                
                # Update task count
                current_tasks = self.tasks_bar.value()
                self.tasks_bar.setValue(current_tasks + 1)
                
                # Show message
                message = f"Task started with ID: {task_id}"
                if show_in_console:
                    self.console_output.append(f"<span style='color:#3282B8;'>{message}</span>")
            else:
                error_msg = f"Error: Server returned status {response.status_code}"
                if show_in_console:
                    self.console_output.append(f"<span style='color:#E94560;'>{error_msg}</span>")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            if show_in_console:
                self.console_output.append(f"<span style='color:#E94560;'>{error_msg}</span>")
    
    def get_dashboard_html(self):
        """Create HTML for the dashboard view"""
        # This is a simple HTML/CSS/JS dashboard that resembles a HUD
        return """
<!DOCTYPE html>
<html>
<head>
    <style>
        body {
            background-color: #1A1A2E;
            color: white;
            font-family: 'Segoe UI', Arial, sans-serif;
            margin: 0;
            padding: 20px;
            overflow: hidden;
        }
        .container {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-gap: 20px;
        }
        .card {
            background-color: #16213E;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            position: relative;
            overflow: hidden;
        }
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(to right, #3282B8, #4ADE80);
        }
        h2 {
            margin-top: 0;
            color: #3282B8;
            font-weight: normal;
        }
        .metric {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .metric-name {
            width: 120px;
        }
        .metric-bar {
            flex-grow: 1;
            height: 8px;
            background-color: #0F3460;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        .metric-value {
            height: 100%;
            background-color: #3282B8;
            border-radius: 4px;
            transition: width 0.5s ease;
        }
        .circle-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 300px;
        }
        .circle {
            width: 250px;
            height: 250px;
            border-radius: 50%;
            border: 4px solid #3282B8;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: pulse 4s infinite;
        }
        .inner-circle {
            width: 200px;
            height: 200px;
            border-radius: 50%;
            border: 2px solid #3282B8;
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .center-circle {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            background: radial-gradient(circle, #3282B8 0%, #16213E 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 36px;
            color: white;
        }
        .bubble {
            position: absolute;
            border-radius: 50%;
            background-color: rgba(50, 130, 184, 0.3);
            animation: float 10s infinite linear;
        }
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(50, 130, 184, 0.4); }
            70% { box-shadow: 0 0 0 15px rgba(50, 130, 184, 0); }
            100% { box-shadow: 0 0 0 0 rgba(50, 130, 184, 0); }
        }
        @keyframes float {
            0% { transform: translateY(0) translateX(0); }
            25% { transform: translateY(-10px) translateX(10px); }
            50% { transform: translateY(0) translateX(20px); }
            75% { transform: translateY(10px) translateX(10px); }
            100% { transform: translateY(0) translateX(0); }
        }
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-gap: 15px;
        }
        .stat-box {
            background-color: #0F3460;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #3282B8;
        }
        .stat-label {
            font-size: 14px;
            color: #AAAAAA;
        }
        .rotating-border {
            position: absolute;
            width: 270px;
            height: 270px;
            border-radius: 50%;
            border: 2px dashed rgba(50, 130, 184, 0.5);
            animation: rotate 20s linear infinite;
        }
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <h2>System Status</h2>
            <div class="metric">
                <div class="metric-name">CPU Usage</div>
                <div class="metric-bar">
                    <div class="metric-value" id="cpu-bar" style="width: 25%;"></div>
                </div>
                <div id="cpu-value" style="margin-left: 10px;">25%</div>
            </div>
            <div class="metric">
                <div class="metric-name">Memory</div>
                <div class="metric-bar">
                    <div class="metric-value" id="memory-bar" style="width: 40%;"></div>
                </div>
                <div id="memory-value" style="margin-left: 10px;">40%</div>
            </div>
            <div class="metric">
                <div class="metric-name">Network</div>
                <div class="metric-bar">
                    <div class="metric-value" id="network-bar" style="width: 15%;"></div>
                </div>
                <div id="network-value" style="margin-left: 10px;">15%</div>
            </div>
            <div class="metric">
                <div class="metric-name">Server Load</div>
                <div class="metric-bar">
                    <div class="metric-value" id="server-bar" style="width: 30%;"></div>
                </div>
                <div id="server-value" style="margin-left: 10px;">30%</div>
            </div>
            
            <div class="stat-grid" style="margin-top: 20px;">
                <div class="stat-box">
                    <div class="stat-value" id="uptime">12:45:22</div>
                    <div class="stat-label">Uptime</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="tasks">2</div>
                    <div class="stat-label">Active Tasks</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="requests">248</div>
                    <div class="stat-label">Total Requests</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value" id="kb-count">32</div>
                    <div class="stat-label">Knowledge Items</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>AI Core</h2>
            <div class="circle-container">
                <div class="rotating-border"></div>
                <div class="circle">
                    <div class="bubble" style="width: 20px; height: 20px; top: 50px; left: 60px;"></div>
                    <div class="bubble" style="width: 15px; height: 15px; bottom: 70px; right: 60px;"></div>
                    <div class="bubble" style="width: 25px; height: 25px; bottom: 40px; left: 50px;"></div>
                    <div class="inner-circle">
                        <div class="center-circle" id="jarvis-logo">J</div>
                    </div>
                </div>
            </div>
            <div id="jarvis-status" style="text-align: center; margin-top: 20px; color: #3282B8;">
                All systems operational
            </div>
        </div>
    </div>
    
    <script>
        // Simulate changing metrics
        function updateMetrics() {
            // CPU usage
            let cpuUsage = Math.floor(Math.random() * 30) + 10;
            document.getElementById('cpu-bar').style.width = cpuUsage + '%';
            document.getElementById('cpu-value').innerText = cpuUsage + '%';
            
            // Memory usage
            let memoryUsage = Math.floor(Math.random() * 20) + 30;
            document.getElementById('memory-bar').style.width = memoryUsage + '%';
            document.getElementById('memory-value').innerText = memoryUsage + '%';
            
            // Network usage
            let networkUsage = Math.floor(Math.random() * 20) + 10;
            document.getElementById('network-bar').style.width = networkUsage + '%';
            document.getElementById('network-value').innerText = networkUsage + '%';
            
            // Server load
            let serverLoad = Math.floor(Math.random() * 20) + 20;
            document.getElementById('server-bar').style.width = serverLoad + '%';
            document.getElementById('server-value').innerText = serverLoad + '%';
            
            // Stats updates
            let tasks = Math.floor(Math.random() * 3) + 1;
            document.getElementById('tasks').innerText = tasks;
            
            let requests = parseInt(document.getElementById('requests').innerText) + Math.floor(Math.random() * 3);
            document.getElementById('requests').innerText = requests;
            
            // Update uptime
            updateUptime();
        }
        
        // Update uptime clock
        function updateUptime() {
            let uptime = document.getElementById('uptime').innerText;
            let [hours, minutes, seconds] = uptime.split(':').map(Number);
            
            seconds++;
            if (seconds >= 60) {
                seconds = 0;
                minutes++;
                if (minutes >= 60) {
                    minutes = 0;
                    hours++;
                }
            }
            
            document.getElementById('uptime').innerText = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
        
        // Update metrics every 3 seconds
        setInterval(updateMetrics, 3000);
        
        // Initial call
        updateMetrics();
    </script>
</body>
</html>
        """

    def setup_voice_recognition(self):
        """Setup voice recognition system"""
        try:
            from jarvis_voice_recognition import JARVISVoiceRecognition
            self.voice_recognition = JARVISVoiceRecognition()
            self.voice_timer.start(100)  # Check for voice commands every 100ms
            self.add_status_message("Voice recognition system initialized")
            return True
        except Exception as e:
            self.add_status_message(f"Error setting up voice recognition: {str(e)}")
            return False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = JarvisGUI()
    window.show()
    sys.exit(app.exec_()) 