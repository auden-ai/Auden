"""
AUDEN Phone Control Module
Controls Android phone via Termux:API
"""

import subprocess
import json
import os


def run_termux(command: list, timeout: int = 15) -> dict:
    """Execute a Termux:API command and return result."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "success": True,
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "output": "", "error": "Command timed out"}
    except FileNotFoundError:
        return {"success": False, "output": "", "error": f"Command not found: {command[0]}. Is Termux:API installed?"}
    except Exception as e:
        return {"success": False, "output": "", "error": str(e)}


# ══════════════════════════════════════
#  📞 CALLS
# ══════════════════════════════════════

def make_call(number: str) -> dict:
    """Make a phone call."""
    result = run_termux(['termux-telephony-call', number])
    if result["success"]:
        return {"status": "success", "message": f"Calling {number}..."}
    return {"status": "error", "message": result["error"]}


def get_call_log() -> dict:
    """Get recent call log."""
    result = run_termux(['termux-call-log', '-l', '10'])
    if result["success"] and result["output"]:
        try:
            calls = json.loads(result["output"])
            return {"status": "success", "data": calls}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  💬 SMS
# ══════════════════════════════════════

def send_sms(number: str, message: str) -> dict:
    """Send an SMS."""
    result = run_termux(['termux-sms-send', '-n', number, message])
    if result["success"]:
        return {"status": "success", "message": f"SMS sent to {number}"}
    return {"status": "error", "message": result["error"]}


def read_sms(limit: int = 10) -> dict:
    """Read recent SMS messages."""
    result = run_termux(['termux-sms-list', '-l', str(limit)])
    if result["success"] and result["output"]:
        try:
            messages = json.loads(result["output"])
            return {"status": "success", "data": messages}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  📷 CAMERA
# ══════════════════════════════════════

def take_photo(filename: str = "auden_photo.jpg", camera_id: int = 0) -> dict:
    """Take a photo."""
    filepath = f"/sdcard/AUDEN/{filename}"
    # Create directory if not exists
    os.makedirs("/sdcard/AUDEN", exist_ok=True)
    result = run_termux(['termux-camera-photo', '-c', str(camera_id), filepath], timeout=20)
    if result["success"]:
        return {"status": "success", "message": f"Photo saved: {filepath}", "path": filepath}
    return {"status": "error", "message": result["error"]}


def list_cameras() -> dict:
    """List available cameras."""
    result = run_termux(['termux-camera-info'])
    if result["success"] and result["output"]:
        return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  🔔 NOTIFICATIONS
# ══════════════════════════════════════

def send_notification(title: str, content: str, vibrate: bool = True) -> dict:
    """Send a notification."""
    cmd = ['termux-notification', '--title', title, '--content', content, '--id', '42']
    if vibrate:
        cmd.extend(['--vibrate', '100,200,100'])
    result = run_termux(cmd)
    if result["success"]:
        return {"status": "success", "message": "Notification sent"}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  📱 APPS & URLS
# ══════════════════════════════════════

def open_url(url: str) -> dict:
    """Open a URL in browser."""
    result = run_termux(['termux-open-url', url])
    if result["success"]:
        return {"status": "success", "message": f"Opening: {url}"}
    return {"status": "error", "message": result["error"]}


def open_app(package_name: str) -> dict:
    """Open an Android app by package name."""
    result = run_termux(['am', 'start', '-n', package_name])
    if result["success"]:
        return {"status": "success", "message": f"Opening app: {package_name}"}
    # Try alternative method
    result2 = run_termux(['monkey', '-p', package_name, '-c', 'android.intent.category.LAUNCHER', '1'])
    if result2["success"]:
        return {"status": "success", "message": f"Opening app: {package_name}"}
    return {"status": "error", "message": "Could not open app"}


# ══════════════════════════════════════
#  📁 FILES
# ══════════════════════════════════════

def list_files(path: str = "/sdcard") -> dict:
    """List files in a directory."""
    result = run_termux(['ls', '-la', path])
    if result["success"]:
        return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def read_file(path: str) -> dict:
    """Read a text file."""
    result = run_termux(['cat', path])
    if result["success"]:
        return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def delete_file(path: str) -> dict:
    """Delete a file."""
    result = run_termux(['rm', path])
    if result["success"]:
        return {"status": "success", "message": f"Deleted: {path}"}
    return {"status": "error", "message": result["error"]}


def create_folder(path: str) -> dict:
    """Create a folder."""
    result = run_termux(['mkdir', '-p', path])
    if result["success"]:
        return {"status": "success", "message": f"Folder created: {path}"}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  🔋 DEVICE STATUS
# ══════════════════════════════════════

def get_battery() -> dict:
    """Get battery status."""
    result = run_termux(['termux-battery-status'])
    if result["success"] and result["output"]:
        try:
            return {"status": "success", "data": json.loads(result["output"])}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def get_wifi_info() -> dict:
    """Get WiFi connection info."""
    result = run_termux(['termux-wifi-connectioninfo'])
    if result["success"] and result["output"]:
        try:
            return {"status": "success", "data": json.loads(result["output"])}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def get_location() -> dict:
    """Get current location (GPS)."""
    result = run_termux(['termux-location', '-p', 'network'], timeout=30)
    if result["success"] and result["output"]:
        try:
            return {"status": "success", "data": json.loads(result["output"])}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


# ══════════════════════════════════════
#  🎚️ CONTROLS
# ══════════════════════════════════════

def set_torch(state: bool) -> dict:
    """Toggle flashlight."""
    cmd = ['termux-torch', 'on' if state else 'off']
    result = run_termux(cmd)
    if result["success"]:
        return {"status": "success", "message": f"Torch {'ON' if state else 'OFF'}"}
    return {"status": "error", "message": result["error"]}


def set_volume(level: int, stream: str = "music") -> dict:
    """Set volume level (0-15)."""
    result = run_termux(['termux-volume', stream, str(level)])
    if result["success"]:
        return {"status": "success", "message": f"Volume set to {level}"}
    return {"status": "error", "message": result["error"]}


def get_clipboard() -> dict:
    """Get clipboard content."""
    result = run_termux(['termux-clipboard-get'])
    if result["success"]:
        return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def set_clipboard(text: str) -> dict:
    """Set clipboard content."""
    result = run_termux(['termux-clipboard-set', text])
    if result["success"]:
        return {"status": "success", "message": "Copied to clipboard"}
    return {"status": "error", "message": result["error"]}


def get_contacts() -> dict:
    """Get contact list."""
    result = run_termux(['termux-contact-list'])
    if result["success"] and result["output"]:
        try:
            return {"status": "success", "data": json.loads(result["output"])}
        except:
            return {"status": "success", "data": result["output"]}
    return {"status": "error", "message": result["error"]}


def speak(text: str, rate: float = 1.0) -> dict:
    """Text to speech using Termux."""
    subprocess.Popen(['termux-tts-speak', '-r', str(rate), text])
    return {"status": "success", "message": "Speaking..."}


def run_custom_command(command: str) -> dict:
    """Run any custom shell command."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "status": "success",
            "output": result.stdout.strip(),
            "error": result.stderr.strip()
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ══════════════════════════════════════
#  🗺️ ACTION DISPATCHER
# ══════════════════════════════════════

def execute_action(action: str, params: dict) -> dict:
    """Main dispatcher for all phone actions."""
    actions = {
        "call":             lambda p: make_call(p.get("number", "")),
        "sms_send":         lambda p: send_sms(p.get("number", ""), p.get("message", "")),
        "sms_read":         lambda p: read_sms(p.get("limit", 10)),
        "call_log":         lambda p: get_call_log(),
        "camera":           lambda p: take_photo(p.get("filename", "photo.jpg"), p.get("camera_id", 0)),
        "notification":     lambda p: send_notification(p.get("title", "AUDEN"), p.get("content", ""), p.get("vibrate", True)),
        "open_url":         lambda p: open_url(p.get("url", "")),
        "open_app":         lambda p: open_app(p.get("package", "")),
        "battery":          lambda p: get_battery(),
        "wifi":             lambda p: get_wifi_info(),
        "location":         lambda p: get_location(),
        "torch_on":         lambda p: set_torch(True),
        "torch_off":        lambda p: set_torch(False),
        "volume":           lambda p: set_volume(p.get("level", 5), p.get("stream", "music")),
        "contacts":         lambda p: get_contacts(),
        "clipboard_get":    lambda p: get_clipboard(),
        "clipboard_set":    lambda p: set_clipboard(p.get("text", "")),
        "list_files":       lambda p: list_files(p.get("path", "/sdcard")),
        "read_file":        lambda p: read_file(p.get("path", "")),
        "delete_file":      lambda p: delete_file(p.get("path", "")),
        "create_folder":    lambda p: create_folder(p.get("path", "")),
        "speak":            lambda p: speak(p.get("text", ""), p.get("rate", 1.0)),
        "run_command":      lambda p: run_custom_command(p.get("command", "")),
    }

    if action in actions:
        return actions[action](params)
    return {"status": "error", "message": f"Unknown action: {action}"}
