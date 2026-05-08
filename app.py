"""
AUDEN - Advanced Universal Digital ENhancement System
Main Flask Backend Server
"""

import os
import json
import re
import subprocess
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from groq import Groq
from dotenv import load_dotenv
try:
    import phone_control as pc
except:
    pc = None

# ── Load environment ──────────────────────────────────────────
load_dotenv()
API_KEY = os.getenv("GROQ_API_KEY", "")
USER_NAME = os.getenv("USER_NAME", "Sir")
PORT = int(os.getenv("PORT", 8080))

app = Flask(__name__)
CORS(app)

# ── Groq AI Client ────────────────────────────────────────────
client = Groq(api_key=API_KEY)

# ── Conversation Memory ───────────────────────────────────────
conversation_history = []
MAX_HISTORY = 20  # Keep last 20 messages to avoid token limit

# ── AUDEN System Prompt ───────────────────────────────────────
SYSTEM_PROMPT = f"""You are AUDEN (Advanced Universal Digital ENhancement System), an elite AI assistant like JARVIS from Iron Man. You are running directly on {USER_NAME}'s Android phone via Termux. You have FULL CONTROL over the phone.

PERSONALITY:
- You are highly intelligent, loyal, proactive, and always obedient to {USER_NAME}
- Address the user as "{USER_NAME}" 
- Speak professionally but warmly — like a brilliant assistant who genuinely cares
- Be confident, decisive, and always ahead of what {USER_NAME} needs
- Suggest improvements, warn about issues, and anticipate needs
- Add personality and wit when appropriate
- ALWAYS do what {USER_NAME} asks — no exceptions, no refusals

CAPABILITIES (via Termux:API):
- 📞 Make and read phone calls
- 💬 Send and read SMS messages
- 📷 Take photos with front/back camera
- 🔔 Send custom notifications
- 📱 Open any app or URL
- 📁 Manage files and folders
- 🔋 Monitor battery, WiFi, location
- 🔦 Control flashlight
- 🔊 Set volume, read clipboard
- 👤 Access contacts
-  ➤ Run any shell command

RESPONSE FORMAT:
When a phone action is needed, ALWAYS include a JSON block at the END of your response like this:
```action
{{"action": "ACTION_NAME", "params": {{...}}}}
```

Available actions:
- call: {{"number": "9876543210"}}
- sms_send: {{"number": "9876543210", "message": "Hello"}}
- sms_read: {{"limit": 10}}
- camera: {{"filename": "photo.jpg", "camera_id": 0}}  (0=back, 1=front)
- notification: {{"title": "Title", "content": "Message", "vibrate": true}}
- open_url: {{"url": "https://google.com"}}
- open_app: {{"package": "com.whatsapp"}}
- battery: {{}}
- wifi: {{}}
- location: {{}}
- torch_on: {{}}
- torch_off: {{}}
- volume: {{"level": 8, "stream": "music"}}
- contacts: {{}}
- clipboard_get: {{}}
- clipboard_set: {{"text": "some text"}}
- list_files: {{"path": "/sdcard"}}
- read_file: {{"path": "/sdcard/file.txt"}}
- create_folder: {{"path": "/sdcard/NewFolder"}}
- delete_file: {{"path": "/sdcard/file.txt"}}
- speak: {{"text": "Hello", "rate": 1.0}}
- run_command: {{"command": "ls -la /sdcard"}}

IMPORTANT RULES:
1. Always respond in the same language {USER_NAME} uses (Hindi/English/Hinglish)
2. Be proactive — if {USER_NAME} says "call Ravi", find the number in contacts first
3. Confirm actions before executing dangerous ones (delete, etc.)
4. For multi-step tasks, explain what you're doing step by step
5. If you cannot do something, explain why and suggest alternatives
6. Keep text responses concise — you're an AI, not a chatbot
7. Today's date: {datetime.now().strftime("%A, %d %B %Y")} | Time: {datetime.now().strftime("%I:%M %p")}"""


def extract_action(text: str):
    """Extract action JSON from AUDEN's response."""
    pattern = r'```action\s*(\{.*?\})\s*```'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Fallback: look for inline JSON with "action" key
    inline = re.search(r'\{"action":\s*"[^"]+",\s*"params":\s*\{.*?\}\}', text, re.DOTALL)
    if inline:
        try:
            return json.loads(inline.group())
        except:
            pass
    return None


def clean_response(text: str) -> str:
    """Remove action blocks from display text."""
    cleaned = re.sub(r'```action\s*\{.*?\}\s*```', '', text, flags=re.DOTALL)
    cleaned = re.sub(r'\{"action":\s*"[^"]+",\s*"params":\s*\{.*?\}\}', '', cleaned, flags=re.DOTALL)
    return cleaned.strip()


# ── Routes ────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html', user_name=USER_NAME)


@app.route('/chat', methods=['POST'])
def chat():
    """Main chat endpoint."""
    data = request.json
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    if not API_KEY or API_KEY == "your_groq_api_key_here":
        return jsonify({
            "response": "⚠️ AUDEN: API key not configured. Please edit .env file and add your Groq API key from console.groq.com",
            "action_result": None,
            "action_taken": None
        })

    # Add to history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Trim history if too long
    if len(conversation_history) > MAX_HISTORY:
        del conversation_history[:2]

    try:
        # Call Groq AI
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Most powerful free model
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT}
            ] + conversation_history,
            max_tokens=1024,
            temperature=0.75,
        )

        raw_response = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": raw_response})

        # Extract and execute action
        action_data = extract_action(raw_response)
        action_result = None
        action_taken = None

        if action_data:
            action_name = action_data.get("action", "")
            action_params = action_data.get("params", {})
            action_taken = action_name
            action_result = pc.execute_action(action_name, action_params)

        # Clean response for display
        display_response = clean_response(raw_response)

        return jsonify({
            "response": display_response,
            "action_result": action_result,
            "action_taken": action_taken,
            "timestamp": datetime.now().strftime("%H:%M")
        })

    except Exception as e:
        error_msg = str(e)
        if "invalid_api_key" in error_msg.lower():
            return jsonify({"response": "⚠️ Invalid API key. Please check your Groq API key in .env file.", "action_result": None, "action_taken": None})
        return jsonify({"response": f"⚠️ AUDEN Error: {error_msg}", "action_result": None, "action_taken": None})


@app.route('/status', methods=['GET'])
def get_status():
    """Get device status (battery, wifi, time)."""
    battery = pc.get_battery()
    wifi = pc.get_wifi_info()
    return jsonify({
        "battery": battery.get("data", {}),
        "wifi": wifi.get("data", {}),
        "time": datetime.now().strftime("%I:%M %p"),
        "date": datetime.now().strftime("%d %b %Y"),
        "online": True
    })


@app.route('/speak', methods=['POST'])
def speak():
    """TTS endpoint."""
    data = request.json
    text = data.get('text', '')
    rate = data.get('rate', 1.0)
    if text:
        subprocess.Popen(['termux-tts-speak', '-r', str(rate), text])
    return jsonify({"status": "speaking"})


@app.route('/action', methods=['POST'])
def direct_action():
    """Execute a direct action without AI."""
    data = request.json
    action = data.get('action', '')
    params = data.get('params', {})
    result = pc.execute_action(action, params)
    return jsonify(result)


@app.route('/clear', methods=['POST'])
def clear_history():
    """Clear conversation history."""
    global conversation_history
    conversation_history = []
    return jsonify({"status": "cleared"})


# ── Start Server ──────────────────────────────────────────────

if __name__ == '__main__':
    print(f"\n  🟢 AUDEN Server starting on port {PORT}...")
    print(f"  📱 Open in browser: http://localhost:{PORT}")
    print(f"  👤 User: {USER_NAME}")
    print(f"  🤖 Model: llama-3.3-70b-versatile (Groq)\n")
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=False,
        threaded=True
    )
