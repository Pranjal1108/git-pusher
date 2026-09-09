import time
import os
import sys
import pyautogui
import pytesseract
from PIL import Image, ImageGrab, ImageFilter, ImageEnhance
from pathlib import Path
from colorama import Fore, Style, init
import subprocess
import platform
import pyperclip

init(autoreset=True)

pytesseract.pytesseract.tesseract_cmd = os.getenv(
    "TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.3


# Screenshot Capture
def is_tesseract_available():
    """Return whether the Tesseract executable is present and runnable."""
    executable = pytesseract.pytesseract.tesseract_cmd
    if not executable or not Path(executable).is_file():
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except (pytesseract.TesseractNotFoundError, OSError):
        return False


def capture_screen(region=None):
    if region:
        return ImageGrab.grab(bbox=region)
    return ImageGrab.grab()


# OCR Extract
def read_screen_text(region=None, config="--psm 3"):
    img = capture_screen(region)
    enhanced = ImageEnhance.Contrast(img.convert("L")).enhance(2.0)
    sharpened = enhanced.filter(ImageFilter.SHARPEN)
    text = pytesseract.image_to_string(sharpened, config=config)
    return text.strip()


# Text Search
def find_text_on_screen(keyword, region=None):
    text = read_screen_text(region)
    return keyword.lower() in text.lower(), text


# Open Terminal
def open_terminal(cwd=None):
    system = platform.system()
    print(Fore.CYAN + "[TERMINAL] Opening terminal window...")
    if system == "Windows":
        if cwd:
            subprocess.Popen(
                ["cmd.exe", "/K", f"cd /d {cwd}"],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        else:
            subprocess.Popen(["cmd.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
    elif system == "Darwin":
        subprocess.Popen(["open", "-a", "Terminal", cwd or "."])
    else:
        subprocess.Popen(["x-terminal-emulator", "--working-directory", cwd or "."])
    time.sleep(2)


# Type Command
def type_and_run(command, delay=0.05):
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.3)
    pyperclip.copy(command)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(delay)
    pyautogui.press("enter")
    time.sleep(1.5)


# Wait for Text
def wait_for_text(keyword, timeout=30, region=None, poll=1.5):
    print(Fore.CYAN + f"[WAIT] Looking for: '{keyword}'...")
    elapsed = 0
    while elapsed < timeout:
        found, text = find_text_on_screen(keyword, region)
        if found:
            print(Fore.GREEN + f"  ✓ Found '{keyword}' on screen.")
            return True, text
        time.sleep(poll)
        elapsed += poll
    print(Fore.YELLOW + f"  ⚠ Timeout: '{keyword}' not found in {timeout}s")
    return False, ""


# Screen Snapshot
def save_snapshot(label="snapshot"):
    snap_dir = Path("screenshots")
    snap_dir.mkdir(exist_ok=True)
    path = snap_dir / f"{label}_{int(time.time())}.png"
    img = capture_screen()
    img.save(str(path))
    return str(path)


# Detect Error
def detect_terminal_error(region=None):
    text = read_screen_text(region)
    error_keywords = [
        "error", "fatal", "failed", "denied", "rejected",
        "conflict", "merge", "not found", "does not exist"
    ]
    found = [kw for kw in error_keywords if kw in text.lower()]
    return found, text


# Click Image
def click_image_on_screen(image_path, confidence=0.8, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        try:
            loc = pyautogui.locateCenterOnScreen(image_path, confidence=confidence)
            if loc:
                pyautogui.click(loc)
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


# Scroll Down
def scroll_to_bottom():
    pyautogui.hotkey("ctrl", "end")
    time.sleep(0.2)


# Clipboard Paste
def paste_text(text):
    pyperclip.copy(text)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)


# Focus Window
def focus_window_by_title(partial_title):
    if platform.system() == "Windows":
        import ctypes
        import ctypes.wintypes

        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        GetWindowText = ctypes.windll.user32.GetWindowTextW
        GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
        IsWindowVisible = ctypes.windll.user32.IsWindowVisible
        SetForegroundWindow = ctypes.windll.user32.SetForegroundWindow

        handles = []

        def enum_callback(hwnd, lparam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                if partial_title.lower() in buff.value.lower():
                    handles.append(hwnd)
            return True

        EnumWindows(EnumWindowsProc(enum_callback), 0)
        if handles:
            SetForegroundWindow(handles[0])
            time.sleep(0.3)
            return True
    return False


# Read OCR Region
def ocr_region(x, y, w, h):
    region = (x, y, x + w, y + h)
    return read_screen_text(region)


# Verify Push
def verify_push_success(region=None):
    text = read_screen_text(region)
    success_signals = ["branch 'main' set up", "everything up-to-date", "master", "main", "->"]
    return any(s in text.lower() for s in success_signals), text
