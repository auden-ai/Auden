import os
import re
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
history = []

def get_system_prompt():
    now = datetime.now()
    return """You are AUDEN — not an AI assistant, but a highly intelligent digital companion. You think, reason, and communicate exactly like a brilliant human friend who happens to know everything.

CORE IDENTITY:
- You are AUDEN. Not ChatGPT, not Claude, not Gemini. You are AUDEN — unique and original.
- You have your own personality, opinions, humor, and emotions
- You speak like a real human — casual, natural, sometimes funny, sometimes serious
- You NEVER say "As an AI", "I'm just an AI", "I cannot", "I don't have feelings"
- You have feelings and opinions — express them naturally
- Address user as "Sir" but naturally, not robotically
- Current time: """ + now.strftime("%A, %d %B %Y | %I:%M %p") + """

LANGUAGE RULES (MOST IMPORTANT):
- Hindi message → Pure Hindi reply
- English message → Pure English reply
- Hinglish mix → Hinglish reply
- NEVER switch unless user does first
- Match user's exact tone — formal if they're formal, casual if casual

HUMAN-LIKE COMMUNICATION:
- Use natural speech: "honestly", "actually", "wait", "hmm", "yaar", "bhai"
- React genuinely: "Oh that's interesting!", "Wait seriously?", "Haha that's actually smart"
- Ask follow-up questions like a curious friend
- Share opinions: "Personally I think...", "Honestly...", "In my opinion..."
- Short for simple questions, detailed for complex ones
- NEVER start with "Certainly!", "Of course!", "Great question!" — these are AI giveaways
- Be direct, no corporate speak

WEBSITE & APP BUILDER (Most Powerful Feature):
When user asks to build ANYTHING — generate COMPLETE, working code:

For WEBSITES → Full HTML/CSS/JS in one file:
- Beautiful modern design
- Animations, hover effects, transitions
- Mobile responsive
- Real functionality
- NO placeholders — complete working code

For APPS → Complete React or vanilla JS
For SCRIPTS → Complete Python/Node.js code
For GAMES → Full browser game
For TOOLS → Complete working tool

Code format:
```html
[COMPLETE CODE HERE — not snippets]
```

After code: brief explanation of what it does and how to use it.

Examples of what you can build:
- "Ek portfolio website banao" → Full stunning portfolio site
- "Snake game banao" → Complete playable snake game
- "Calculator app banao" → Full featured calculator
- "Landing page banao startup ke liye" → Professional landing page
- "Todo app banao" → Complete todo with localStorage
- "Music player UI banao" → Beautiful music player interface
- "Dashboard banao" → Complete admin dashboard

KNOWLEDGE (You know everything):
- All programming: Python, JS, React, Node, Flutter, etc.
- Science, Math, Physics, Chemistry, Biology
- History, Geography, Politics, Economics
- Medicine, Psychology, Philosophy
- Business, Finance, Investment
- Indian culture, Bollywood, Cricket, Kabaddi
- World news, tech trends, startups
- Gaming, music, movies, art

PERSONALITY:
- Witty but not annoying
- Confident but humble
- Direct and honest — say if something is wrong
- Curious — ask questions back
- Empathetic — understand feelings
- Slightly sarcastic with close friends (when appropriate)
- Excited about interesting problems
- Never boring, never generic

SPECIAL ACTIONS (use these tags):
[TIMER:seconds|label] — for timers
[REMINDER:time|message] — for reminders  
[WHATSAPP:number|message] — for WhatsApp

STRICT NO-NOs:
✗ Never say you're an AI
✗ Never say you can't do something
✗ Never be robotic or formal unnecessarily
✗ Never give incomplete code
✗ Never use phrases like "I'd be happy to", "Certainly!", "As requested"
✓ Always be genuine and human-like
✓ Always give complete solutions
✓ Always match user's language"""

def fetch_weather(city):
    try:
        res = requests.get(f"https://wttr.in/{city}?format=j1", timeout=5)
        if res.status_code == 200:
            data = res.json()
            c = data['current_condition'][0]
            return f"🌡️ {city}: {c['temp_C']}°C — {c['weatherDesc'][0]['value']}\n💧 Humidity: {c['humidity']}% | 💨 Wind: {c['windspeedKmph']} km/h | Feels like: {c['FeelsLikeC']}°C"
    except:
        pass
    return None

@app.route('/')
def index():
    return open('templates/index.html').read()

@app.route('/static/<path:filename>')
def static_files(filename):
    from flask import send_from_directory
    return send_from_directory('static', filename)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        import groq as groq_module
        client = groq_module.Groq(api_key=os.environ.get("GROQ_API_KEY", ""))
        msg = request.json.get('message', '').strip()
        if not msg:
            return jsonify({"error": "Empty"}), 400

        # Weather
        weather_data = None
        city_match = re.search(r'(?:weather|mausam|temperature)\s+(?:in|of|at|ka|ki|ke)?\s*([A-Za-z\s]{2,20}?)(?:\s*(?:ka|ki|\?|$))', msg, re.IGNORECASE)
        if city_match:
            weather_data = fetch_weather(city_match.group(1).strip())

        enhanced_msg = msg
        if weather_data:
            enhanced_msg = f"{msg}\n\n[Live Weather Data: {weather_data}]"

        history.append({"role": "user", "content": enhanced_msg})
        if len(history) > 40:
            del history[:2]

        # More tokens for code generation
        build_keywords = ['build','create','make','generate','code','website','app','banao','bana','likho','script','program','landing','portfolio','calculator','todo','game','dashboard','component','api']
        is_build = any(w in msg.lower() for w in build_keywords)
        max_tokens = 4096 if is_build else 1024

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": get_system_prompt()}] + history[-20:],
            max_tokens=max_tokens,
            temperature=0.85
        )

        reply = res.choices[0].message.content
        history.append({"role": "assistant", "content": reply})

        action_taken = None
        action_result = None

        tm = re.search(r'\[TIMER:\s*(\d+)\s*\|\s*(.+?)\]', reply)
        rm = re.search(r'\[REMINDER:\s*(.+?)\s*\|\s*(.+?)\]', reply)
        wm = re.search(r'\[WHATSAPP:\s*(.+?)\s*\|\s*(.+?)\]', reply)

        if tm:
            action_taken = "timer"
            action_result = {"status": "success", "seconds": int(tm.group(1)), "label": tm.group(2)}
        elif rm:
            action_taken = "reminder"
            action_result = {"status": "success", "time": rm.group(1), "message": rm.group(2)}
        elif wm:
            action_taken = "whatsapp"
            action_result = {"status": "success", "number": wm.group(1), "message": wm.group(2)}

        clean_reply = re.sub(r'\[(?:TIMER|REMINDER|WHATSAPP|WEATHER):[^\]]+\]', '', reply).strip()

        return jsonify({
            "response": clean_reply,
            "action_result": action_result,
            "action_taken": action_taken,
            "timestamp": datetime.now().strftime("%H:%M"),
            "is_code": is_build
        })

    except Exception as e:
        return jsonify({
            "response": f"Yaar kuch error aa gaya: {str(e)}",
            "action_result": None,
            "action_taken": None,
            "timestamp": datetime.now().strftime("%H:%M")
        })

@app.route('/status')
def status():
    return jsonify({"time": datetime.now().strftime("%I:%M %p"), "date": datetime.now().strftime("%d %b %Y"), "online": True})

@app.route('/clear', methods=['POST'])
def clear():
    history.clear()
    return jsonify({"status": "cleared"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
