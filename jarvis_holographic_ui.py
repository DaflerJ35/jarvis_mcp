import pygame
import pygame.gfxdraw
import sys
import math
import random
import time
import threading
from typing import Dict, List, Tuple, Optional, Union, Any
import numpy as np
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("jarvis_ui.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JARVIS-UI")

# Colors
COLOR_BLUE = (41, 128, 185)
COLOR_LIGHT_BLUE = (52, 152, 219)
COLOR_BRIGHT_BLUE = (0, 255, 255)
COLOR_DARK_BLUE = (44, 62, 80)
COLOR_WHITE = (236, 240, 241)
COLOR_ORANGE = (230, 126, 34)
COLOR_BACKGROUND = (25, 25, 35)
COLOR_TEXT = COLOR_WHITE
COLOR_GRID = (52, 73, 94, 50)  # Semi-transparent grid lines

class JARVISHolographicUI:
    """
    PyGame-based holographic UI for JARVIS inspired by Iron Man interfaces
    """
    def __init__(self, width: int = 1024, height: int = 768, fullscreen: bool = False):
        self.width = width
        self.height = height
        self.fullscreen = fullscreen
        self.running = False
        self.screen = None
        self.clock = None
        self.font_small = None
        self.font_medium = None
        self.font_large = None
        
        # UI elements
        self.circles = []
        self.animations = []
        self.text_queue = []
        self.status_text = ""
        self.status_mode = "idle"  # "idle", "listening", "processing", "speaking"
        self.visualization_data = None
        self.audio_bars = [0] * 20  # For audio visualization
        
        # Initialize pygame in a separate thread to avoid blocking
        self.init_thread = threading.Thread(target=self._init_pygame)
        self.init_thread.daemon = True
        self.init_thread.start()
        
        # Message display settings
        self.current_message = ""
        self.current_message_time = 0
        self.message_duration = 5  # seconds
        
        # Voice visualization
        self.waveform_points = []
        self.waveform_height = 50
        self.waveform_color = COLOR_BRIGHT_BLUE
        
        # Process monitoring
        self.cpu_history = [0] * 60  # Last 60 seconds
        self.memory_history = [0] * 60
        
        # Command history
        self.command_history = []
        self.max_command_history = 5
        
        logger.info("JARVIS Holographic UI initialized")
    
    def _init_pygame(self):
        """
        Initialize pygame - runs in a separate thread
        """
        try:
            pygame.init()
            pygame.display.set_caption("J.A.R.V.I.S.")
            
            if self.fullscreen:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                self.width, self.height = self.screen.get_size()
            else:
                self.screen = pygame.display.set_mode((self.width, self.height))
            
            self.clock = pygame.time.Clock()
            
            # Load fonts
            pygame.font.init()
            try:
                # Try to load a nice tech-looking font
                font_path = os.path.join("assets", "fonts", "Roboto-Light.ttf")
                if os.path.exists(font_path):
                    self.font_small = pygame.font.Font(font_path, 14)
                    self.font_medium = pygame.font.Font(font_path, 20)
                    self.font_large = pygame.font.Font(font_path, 36)
                else:
                    # Fallback to system font
                    self.font_small = pygame.font.SysFont("Arial", 14)
                    self.font_medium = pygame.font.SysFont("Arial", 20)
                    self.font_large = pygame.font.SysFont("Arial", 36)
            except Exception as e:
                logger.error(f"Error loading fonts: {e}")
                # Fallback to system font
                self.font_small = pygame.font.SysFont("Arial", 14)
                self.font_medium = pygame.font.SysFont("Arial", 20)
                self.font_large = pygame.font.SysFont("Arial", 36)
            
            # Create initial UI elements
            self._create_ui_elements()
            
            logger.info("PyGame initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing PyGame: {e}")
    
    def _create_ui_elements(self):
        """
        Create initial UI elements
        """
        # Create main circles
        center_x, center_y = self.width // 2, self.height // 2
        self.circles = [
            {"radius": 150, "speed": 0.5, "angle": 0, "color": COLOR_BLUE, "line_width": 2},
            {"radius": 180, "speed": -0.3, "angle": 0, "color": COLOR_LIGHT_BLUE, "line_width": 1},
            {"radius": 210, "speed": 0.2, "angle": 0, "color": COLOR_LIGHT_BLUE, "line_width": 1},
            {"radius": 240, "speed": -0.1, "angle": 0, "color": COLOR_BLUE, "line_width": 1}
        ]
        
        # Add random dots for animations around the circles
        for i in range(20):
            angle = random.uniform(0, 2 * math.pi)
            radius = random.uniform(120, 260)
            speed = random.uniform(0.02, 0.1) * (1 if random.random() > 0.5 else -1)
            size = random.randint(2, 5)
            self.animations.append({
                "x": center_x + radius * math.cos(angle),
                "y": center_y + radius * math.sin(angle),
                "angle": angle,
                "radius": radius,
                "speed": speed,
                "size": size,
                "color": COLOR_BRIGHT_BLUE if random.random() > 0.8 else COLOR_LIGHT_BLUE
            })
    
    def start(self):
        """
        Start the UI loop
        """
        self.running = True
        # Wait for pygame to initialize
        while self.init_thread.is_alive():
            time.sleep(0.1)
        
        if self.screen is None:
            logger.error("PyGame failed to initialize properly")
            return
        
        try:
            self._main_loop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            pygame.quit()
    
    def stop(self):
        """
        Stop the UI loop
        """
        self.running = False
    
    def set_status(self, text: str, mode: str = "idle"):
        """
        Set the status text and mode
        
        Args:
            text: Status text to display
            mode: Status mode ("idle", "listening", "processing", "speaking")
        """
        self.status_text = text
        self.status_mode = mode
    
    def show_message(self, message: str, duration: float = 5.0):
        """
        Show a message on the screen for a specific duration
        
        Args:
            message: Message to display
            duration: Duration in seconds
        """
        self.current_message = message
        self.current_message_time = time.time()
        self.message_duration = duration
    
    def add_to_command_history(self, command: str):
        """
        Add a command to the history
        
        Args:
            command: Command text
        """
        self.command_history.insert(0, {
            "text": command, 
            "time": time.time()
        })
        
        # Limit the history length
        if len(self.command_history) > self.max_command_history:
            self.command_history = self.command_history[:self.max_command_history]
    
    def update_audio_visualization(self, audio_data: List[float]):
        """
        Update audio visualization data
        
        Args:
            audio_data: List of audio amplitude values (normalized between 0 and 1)
        """
        if audio_data:
            # Ensure we have the right number of bars
            if len(audio_data) >= len(self.audio_bars):
                # Take a sample of the values
                step = len(audio_data) // len(self.audio_bars)
                self.audio_bars = [audio_data[i*step] for i in range(len(self.audio_bars))]
            else:
                # Stretch the audio data
                self.audio_bars = audio_data + [0] * (len(self.audio_bars) - len(audio_data))
    
    def update_waveform(self, waveform_data: List[float]):
        """
        Update voice waveform visualization
        
        Args:
            waveform_data: List of waveform amplitude values (normalized between -1 and 1)
        """
        self.waveform_points = waveform_data
    
    def update_system_stats(self, cpu_percent: float, memory_percent: float):
        """
        Update system stats (CPU, memory)
        
        Args:
            cpu_percent: CPU usage percentage (0-100)
            memory_percent: Memory usage percentage (0-100)
        """
        self.cpu_history.pop(0)
        self.cpu_history.append(cpu_percent)
        self.memory_history.pop(0)
        self.memory_history.append(memory_percent)
    
    def _main_loop(self):
        """
        Main UI loop
        """
        center_x, center_y = self.width // 2, self.height // 2
        
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
            
            # Clear the screen
            self.screen.fill(COLOR_BACKGROUND)
            
            # Draw grid
            self._draw_grid()
            
            # Draw circles
            for circle in self.circles:
                circle["angle"] += circle["speed"] * 0.01
                pygame.gfxdraw.aacircle(
                    self.screen, 
                    center_x, center_y, 
                    circle["radius"], 
                    circle["color"]
                )
                
                # Draw ticks on the circle
                num_ticks = 36
                for i in range(num_ticks):
                    angle = 2 * math.pi * i / num_ticks + circle["angle"]
                    inner_x = center_x + (circle["radius"] - 5) * math.cos(angle)
                    inner_y = center_y + (circle["radius"] - 5) * math.sin(angle)
                    outer_x = center_x + (circle["radius"] + 5) * math.cos(angle)
                    outer_y = center_y + (circle["radius"] + 5) * math.sin(angle)
                    
                    # Use different colors for some ticks
                    color = COLOR_ORANGE if i % 4 == 0 else circle["color"]
                    pygame.draw.aaline(self.screen, color, 
                                      (inner_x, inner_y), 
                                      (outer_x, outer_y))
            
            # Draw animated dots
            for dot in self.animations:
                dot["angle"] += dot["speed"]
                dot["x"] = center_x + dot["radius"] * math.cos(dot["angle"])
                dot["y"] = center_y + dot["radius"] * math.sin(dot["angle"])
                
                pygame.gfxdraw.filled_circle(
                    self.screen, 
                    int(dot["x"]), int(dot["y"]), 
                    dot["size"], 
                    dot["color"]
                )
            
            # Draw status
            self._draw_status()
            
            # Draw message if needed
            current_time = time.time()
            if self.current_message and (current_time - self.current_message_time < self.message_duration):
                alpha = min(255, int(255 * (1 - (current_time - self.current_message_time) / self.message_duration)))
                self._draw_message(self.current_message, alpha)
            
            # Draw command history
            self._draw_command_history()
            
            # Draw system stats
            self._draw_system_stats()
            
            # Draw audio visualization
            self._draw_audio_visualization()
            
            # Draw voice waveform if available
            if self.waveform_points:
                self._draw_waveform()
            
            # Update the screen
            pygame.display.flip()
            
            # Cap the frame rate
            self.clock.tick(60)
    
    def _draw_grid(self):
        """
        Draw a grid background
        """
        # Draw horizontal grid lines
        for y in range(0, self.height, 20):
            pygame.draw.line(self.screen, COLOR_GRID, (0, y), (self.width, y), 1)
        
        # Draw vertical grid lines
        for x in range(0, self.width, 20):
            pygame.draw.line(self.screen, COLOR_GRID, (x, 0), (x, self.height), 1)
    
    def _draw_status(self):
        """
        Draw the status text and mode indicator
        """
        if not self.status_text:
            self.status_text = "JARVIS Online"
        
        # Draw the status text
        status_surface = self.font_medium.render(self.status_text, True, COLOR_TEXT)
        status_rect = status_surface.get_rect(center=(self.width // 2, self.height - 30))
        self.screen.blit(status_surface, status_rect)
        
        # Draw mode indicator
        mode_colors = {
            "idle": COLOR_BLUE,
            "listening": COLOR_ORANGE,
            "processing": COLOR_LIGHT_BLUE,
            "speaking": COLOR_BRIGHT_BLUE
        }
        
        mode_color = mode_colors.get(self.status_mode, COLOR_BLUE)
        pygame.gfxdraw.filled_circle(
            self.screen, 
            status_rect.left - 15, status_rect.centery, 
            5, 
            mode_color
        )
    
    def _draw_message(self, message: str, alpha: int = 255):
        """
        Draw a message with optional alpha transparency
        
        Args:
            message: Message to display
            alpha: Alpha transparency (0-255)
        """
        # Create a text surface
        text_surface = self.font_large.render(message, True, COLOR_BRIGHT_BLUE)
        
        # Apply alpha
        text_surface.set_alpha(alpha)
        
        # Position it
        text_rect = text_surface.get_rect(center=(self.width // 2, 50))
        
        # Draw it
        self.screen.blit(text_surface, text_rect)
    
    def _draw_command_history(self):
        """
        Draw the command history
        """
        if not self.command_history:
            return
        
        y_pos = 100
        current_time = time.time()
        
        for i, cmd in enumerate(self.command_history):
            # Calculate age and fade out older commands
            age = current_time - cmd["time"]
            if age > 60:  # Older than 60 seconds
                continue
                
            alpha = min(255, int(255 * (1 - age / 60)))
            text_surface = self.font_small.render(cmd["text"], True, COLOR_WHITE)
            text_surface.set_alpha(alpha)
            
            text_rect = text_surface.get_rect(left=50, top=y_pos)
            self.screen.blit(text_surface, text_rect)
            
            y_pos += 25
    
    def _draw_system_stats(self):
        """
        Draw CPU and memory usage graphs
        """
        # Draw CPU history
        self._draw_history_graph(
            self.cpu_history, 
            self.width - 150, 50, 
            140, 40, 
            "CPU", 
            COLOR_BLUE
        )
        
        # Draw memory history
        self._draw_history_graph(
            self.memory_history, 
            self.width - 150, 110, 
            140, 40, 
            "MEM", 
            COLOR_LIGHT_BLUE
        )
    
    def _draw_history_graph(self, history: List[float], x: int, y: int, 
                          width: int, height: int, label: str, color: Tuple[int, int, int]):
        """
        Draw a historical line graph
        
        Args:
            history: List of values to plot
            x, y: Position
            width, height: Dimensions
            label: Graph label
            color: Line color
        """
        # Draw background
        pygame.draw.rect(self.screen, COLOR_DARK_BLUE, (x, y, width, height))
        
        # Draw border
        pygame.draw.rect(self.screen, color, (x, y, width, height), 1)
        
        # Draw label
        label_surface = self.font_small.render(label, True, color)
        label_rect = label_surface.get_rect(left=x + 5, top=y + 2)
        self.screen.blit(label_surface, label_rect)
        
        # Draw current value
        if history:
            value_text = f"{history[-1]:.1f}%"
            value_surface = self.font_small.render(value_text, True, COLOR_WHITE)
            value_rect = value_surface.get_rect(right=x + width - 5, top=y + 2)
            self.screen.blit(value_surface, value_rect)
        
        # Draw the graph
        if len(history) < 2:
            return
            
        points = []
        for i, value in enumerate(history):
            px = x + (i * width) / len(history)
            py = y + height - (value * height / 100)
            points.append((px, py))
        
        if len(points) > 1:
            pygame.draw.aalines(self.screen, color, False, points)
    
    def _draw_audio_visualization(self):
        """
        Draw audio visualization bars
        """
        bar_width = 8
        bar_spacing = 4
        bar_height_max = 60
        
        # Position at bottom center
        start_x = self.width // 2 - ((bar_width + bar_spacing) * len(self.audio_bars)) // 2
        bottom_y = self.height - 100
        
        for i, value in enumerate(self.audio_bars):
            # Calculate height (with some minimum to always show something)
            height = max(2, int(value * bar_height_max))
            
            # Calculate position
            x = start_x + i * (bar_width + bar_spacing)
            y = bottom_y - height
            
            # Draw the bar
            pygame.draw.rect(
                self.screen, 
                COLOR_BRIGHT_BLUE, 
                (x, y, bar_width, height)
            )
    
    def _draw_waveform(self):
        """
        Draw voice waveform visualization
        """
        if not self.waveform_points:
            return
            
        # Calculate the center line and scaling
        center_y = 200
        points = []
        
        # Create points for drawing the waveform
        for i, value in enumerate(self.waveform_points):
            x = 50 + i * (self.width - 100) / len(self.waveform_points)
            y = center_y + value * self.waveform_height
            points.append((x, y))
            
        # Draw the waveform
        if len(points) > 1:
            pygame.draw.aalines(self.screen, self.waveform_color, False, points)

# Example usage function to demonstrate the UI
def test_holographic_ui():
    ui = JARVISHolographicUI(width=1024, height=768, fullscreen=False)
    
    # Start UI in a separate thread
    ui_thread = threading.Thread(target=ui.start)
    ui_thread.daemon = True
    ui_thread.start()
    
    try:
        # Simulate some activity
        ui.show_message("JARVIS Online", 3)
        time.sleep(1)
        
        ui.set_status("Listening...", "listening")
        time.sleep(2)
        
        ui.add_to_command_history("What's the weather like today?")
        ui.set_status("Processing request...", "processing")
        time.sleep(2)
        
        ui.set_status("Retrieving weather data...", "processing")
        time.sleep(1.5)
        
        # Simulate voice response
        ui.show_message("Weather: Sunny, 72°F", 3)
        ui.set_status("Responding...", "speaking")
        
        # Generate some fake waveform data
        waveform = [math.sin(x/10) * random.uniform(0.5, 1.0) for x in range(100)]
        ui.update_waveform(waveform)
        time.sleep(3)
        
        # Simulate audio visualization
        for i in range(50):
            audio_data = [random.uniform(0, 1) for _ in range(20)]
            ui.update_audio_visualization(audio_data)
            
            # Update system stats
            cpu = 20 + 10 * math.sin(i / 10)
            memory = 40 + 5 * math.cos(i / 8)
            ui.update_system_stats(cpu, memory)
            
            time.sleep(0.1)
        
        ui.set_status("Idle", "idle")
        time.sleep(2)
        
        ui.add_to_command_history("What time is it?")
        ui.set_status("Processing...", "processing")
        time.sleep(1)
        
        ui.show_message("Current time: 3:45 PM", 3)
        ui.set_status("JARVIS Ready", "idle")
        
        # Keep the UI running for a bit more
        time.sleep(5)
    
    except KeyboardInterrupt:
        pass
    finally:
        # Stop the UI
        ui.stop()
        ui_thread.join(timeout=1)

def create_jarvis_ui() -> JARVISHolographicUI:
    """
    Create and return a JARVIS holographic UI instance
    """
    return JARVISHolographicUI(width=1024, height=768, fullscreen=False)

if __name__ == "__main__":
    test_holographic_ui() 