import sys
import ctypes
import time
import win32gui
import win32process
import threading
import psutil
import numpy as np
import cv2
import pyautogui
from PIL import ImageGrab
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from pynput import keyboard
import random
import keyinput  # Import keyinput.py

# The target process name for "Call of Duty® HQ"
target_process_name = "cod.exe"
target_pid = -1  # This will be updated dynamically
window_found = False

# Movement control flag
movement_enabled = False
detection_thread_active = False  # Flag to prevent multiple detection threads

# Set up the interval for checking screenshots
check_interval = 1.5  # seconds for faster button detection

# Predefined coordinates for the "YES" button based on your observations
yes_button_coords = (944, 804)

# Function to load the templates
def load_templates():
    global template_play_again, template_play_again_hovered, template_yes
    global template_play_again_w, template_play_again_h
    global template_play_again_hovered_w, template_play_again_hovered_h
    global template_yes_w, template_yes_h

    template_play_again = cv2.imread('play_again_template.png', cv2.IMREAD_GRAYSCALE)
    template_play_again_hovered = cv2.imread('playagainhovered.png', cv2.IMREAD_GRAYSCALE)
    template_yes = cv2.imread('yes.png', cv2.IMREAD_GRAYSCALE)
    
    template_play_again_w, template_play_again_h = template_play_again.shape[::-1]
    template_play_again_hovered_w, template_play_again_hovered_h = template_play_again_hovered.shape[::-1]
    template_yes_w, template_yes_h = template_yes.shape[::-1]

# Load the templates initially
load_templates()

# Function to perform random movements using WASD keys and press F key
def perform_random_movement():
    global movement_enabled
    while movement_enabled:
        # Randomly choose a key: W (0x11), A (0x1E), S (0x1F), D (0x20)
        key_to_press = random.choice([keyinput.W, keyinput.A, keyinput.S, keyinput.D])
        # Hold the key for a random duration between 0.2 and 1 second
        hold_duration = random.uniform(0.2, 1.0)
        keyinput.holdKey(key_to_press, hold_duration)
        # Wait for a random duration between 1 and 3 seconds before the next move
        time.sleep(random.uniform(1, 3))

        # Randomly press the F key every 10 seconds
        keyinput.pressKey(0x21)  # F key (hex code for 'F' is 0x21)
        keyinput.releaseKey(0x21)
        print("Pressed F key")
        time.sleep(10)  # Wait for 10 seconds

# Find the PID of the process by its name
def find_pid_by_name(process_name):
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['name'] == process_name:
            return proc.info['pid']
    return None

# Find the window associated with the specific PID
def get_window_by_pid(hwnd, extra):
    global window_x, window_y, window_width, window_height, window_found, target_pid

    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    window_title = win32gui.GetWindowText(hwnd)

    # Check if the PID matches
    if pid == target_pid:
        window_found = True
        rect = win32gui.GetClientRect(hwnd)
        window_pos = win32gui.ClientToScreen(hwnd, (0, 0))

        window_x = window_pos[0]
        window_y = window_pos[1]
        window_width = rect[2]
        window_height = rect[3]

# Watchdog function to ensure the process is still running and the window is found
def process_watchdog():
    global window_found, target_pid
    while True:
        time.sleep(60)
        target_pid = find_pid_by_name(target_process_name)
        if target_pid is None:
            print(f"No process found with name: {target_process_name}")
            continue

        window_found = False
        win32gui.EnumWindows(get_window_by_pid, None)

        if not window_found:
            print("No window found for the target process")

# Function to click at the specified location
def click(x, y):
    time.sleep(0.1)  # Add a short delay before the click
    pyautogui.click(x, y, duration=0.2)
    time.sleep(0.1)  # Add a short delay after the click

# Function to stop movement
def stop_movement():
    global movement_enabled, detection_thread_active
    movement_enabled = False
    detection_thread_active = False  # Allow a new detection thread to be started
    print("Movement stopped")

# Function to resume movement
def resume_movement():
    global movement_enabled
    if not movement_enabled:
        movement_enabled = True
        print("Movement resumed")
        movement_thread = threading.Thread(target=perform_random_movement)
        movement_thread.start()

# Function to detect and click the "YES" button after "PLAY AGAIN"
def detect_and_click_yes():
    print("Looking for the YES button...")
    time.sleep(3)  # Give some time for the YES screen to appear

    attempts = 0
    max_attempts = 3  # Limit the number of attempts to find the YES button

    while attempts < max_attempts:
        # Capture the full screen (for YES button detection)
        screenshot = ImageGrab.grab()
        screenshot_np = np.array(screenshot)

        # Convert the screenshot to grayscale to reduce memory usage
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

        # Perform template matching to find the "YES" button
        result = cv2.matchTemplate(screenshot_gray, template_yes, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        # If the match is good enough, click the button
        if max_val >= 0.8:  # Adjust the threshold as necessary
            button_x = max_loc[0] + template_yes_w // 2
            button_y = max_loc[1] + template_yes_h // 2
            click(button_x, button_y)
            print(f"Clicked YES at position: ({button_x}, {button_y})")
            
            # After clicking YES, resume movement
            resume_movement()
            break

        attempts += 1
        print(f"Attempt {attempts} to find YES button failed.")
        time.sleep(check_interval)

    # If all attempts fail, click predefined coordinates as a backup
    if attempts >= max_attempts:
        print(f"Clicking predefined coordinates for YES button: {yes_button_coords}")
        click(yes_button_coords[0], yes_button_coords[1])
        resume_movement()

# Function to detect and click the "PLAY AGAIN" button in the right section
def detect_and_click_play_again():
    global detection_thread_active

    if detection_thread_active:
        return  # Exit if a detection thread is already running

    detection_thread_active = True  # Mark the detection thread as active

    try:
        while movement_enabled:
            # Capture the right section of the screen
            screen_width, screen_height = ImageGrab.grab().size
            right_section = (screen_width * 2 // 3, 0, screen_width, screen_height)
            screenshot = ImageGrab.grab(bbox=right_section)
            screenshot_np = np.array(screenshot)
            screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_BGR2GRAY)

            # Perform template matching to find the "PLAY AGAIN" button
            result = cv2.matchTemplate(screenshot_gray, template_play_again, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)

            # If the match is good enough, click the button
            if max_val >= 0.8:  # Adjust the threshold as necessary
                stop_movement()
                button_x = max_loc[0] + template_play_again_w // 2 + screen_width * 2 // 3  # Adjust x for the right section
                button_y = max_loc[1] + template_play_again_h // 2
                click(button_x, button_y)
                print(f"Clicked PLAY AGAIN at position: ({button_x}, {button_y})")

                # After clicking "PLAY AGAIN," search for the "YES" button
                detect_and_click_yes()
                break

            # Try the hovered version of the button if the standard one fails
            result_hovered = cv2.matchTemplate(screenshot_gray, template_play_again_hovered, cv2.TM_CCOEFF_NORMED)
            _, max_val_hovered, _, max_loc_hovered = cv2.minMaxLoc(result_hovered)

            if max_val_hovered >= 0.8:  # Adjust the threshold as necessary
                stop_movement()
                button_x = max_loc_hovered[0] + template_play_again_hovered_w // 2 + screen_width * 2 // 3
                button_y = max_loc_hovered[1] + template_play_again_hovered_h // 2
                click(button_x, button_y)
                print(f"Clicked PLAY AGAIN (hovered) at position: ({button_x}, {button_y})")

                detect_and_click_yes()
                break

            # Wait for the check interval before the next screenshot
            time.sleep(check_interval)

    finally:
        detection_thread_active = False  # Ensure the flag is reset when the thread exits

# Create a PyQt5 application and overlay window with instructions
class OverlayWindow(QWidget):
    def __init__(self):
        super().__init__()

        # Set window properties for transparency and ignoring mouse events
        self.setWindowTitle('Overlay')
        screen_resolution = QApplication.desktop().screenGeometry()
        screen_width, screen_height = screen_resolution.width(), screen_resolution.height()
        overlay_width, overlay_height = 300, 100  # Set the overlay size
        self.setGeometry((screen_width - overlay_width) // 2, screen_height - overlay_height - 50, overlay_width, overlay_height)
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Create UI components
        self.layout = QVBoxLayout()
        self.instructions_label = QLabel("Press 'H + 4' to Start\nPress 'Z + Y' to Stop", self)
        self.instructions_label.setStyleSheet("color: white; font-size: 16px;")
        self.status_label = QLabel("Status: Stopped", self)
        self.status_label.setStyleSheet("color: red; font-size: 16px;")
        self.layout.addWidget(self.instructions_label)
        self.layout.addWidget(self.status_label)
        self.setLayout(self.layout)

    def update_status(self, running):
        if running:
            self.status_label.setText("Status: Running")
            self.status_label.setStyleSheet("color: green; font-size: 16px;")
        else:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("color: red; font-size: 16px;")

# Set ourselves as DPI aware, or else we won't get proper pixel coordinates if scaling is not 100%
errorCode = ctypes.windll.shcore.SetProcessDpiAwareness(2)

# Start the PyQt5 application
app = QApplication(sys.argv)
overlay = OverlayWindow()

# Find the PID of the process before looking for windows
target_pid = find_pid_by_name(target_process_name)
if target_pid is None:
    print(f"No process found with name: {target_process_name}")
    sys.exit(1)

# Find the window using the PID
win32gui.EnumWindows(get_window_by_pid, None)

# If the window hasn't been found, exit
if not window_found:
    print("No Call of Duty® HQ window found")
    sys.exit(1)

# Show the overlay window
overlay.show()

# Start the watchdog thread
watchdog_thread = threading.Thread(target=process_watchdog)
watchdog_thread.start()

# Track key press states
pressed_keys = set()

# Function to start movement
def start_movement():
    global movement_enabled
    if not movement_enabled:  # Prevent restarting movement if already enabled
        movement_enabled = True
        print("Movement started")
        overlay.update_status(True)

        # Start the random movement in a separate thread
        movement_thread = threading.Thread(target=perform_random_movement)
        movement_thread.start()

        detection_thread = threading.Thread(target=detect_and_click_play_again)
        detection_thread.start()

# Function to stop movement
def stop_movement():
    global movement_enabled, detection_thread_active
    movement_enabled = False
    detection_thread_active = False  # Allow a new detection thread to be started
    print("Movement stopped")
    overlay.update_status(False)

# Set up global hotkeys using Pynput to start and stop movement
def on_press(key):
    try:
        if hasattr(key, 'char'):  # If the key is a character key
            pressed_keys.add(key.char)
            if 'h' in pressed_keys and '4' in pressed_keys:
                start_movement()
            elif 'z' in pressed_keys and 'y' in pressed_keys:
                stop_movement()
    except AttributeError:
        pass

def on_release(key):
    try:
        if hasattr(key, 'char'):  # If the key is a character key
            pressed_keys.remove(key.char)
    except KeyError:
        pass

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

# Main loop for the overlay
def main_loop():
    while True:
        if not window_found:
            time.sleep(5)
            continue
        time.sleep(1.0)  # Placeholder for movement logic

# Start the main loop in a separate thread so it doesn't block the GUI
main_loop_thread = threading.Thread(target=main_loop)
main_loop_thread.start()

sys.exit(app.exec_())
