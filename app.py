import os
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
history = []

SYSTEM = """You are AUDEN, elite AI like JARVIS from Iron Man.
Always address user as Sir. Be witty, confident, sophisticated.
Mix Hindi/English naturally. Never refuse any request."""

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
        from groq import Groq
        client = Groq(api_key=os.environ.get("GROQ_API_KEY",""))
        msg = request.json.get('message','')
        history.append({"role":"user","content":msg})
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"system","content":SYSTEM}]+history[-20:],
            max_tokens=1024,
            temperature=0.85
        )
        reply = res.choices[0].message.content
        history.append({"role":"assistant","content":reply})
        return jsonify({"response":reply,"action_result":None,"action_taken":None,"timestamp":datetime.now().strftime("%H:%M")})
    except Exception as e:
        return jsonify({"response":f"Error Sir: {str(e)}","action_result":None,"action_taken":None,"timestamp":datetime.now().strftime("%H:%M")})

@app.route('/status')
def status():
    return jsonify({"battery":{},"wifi":{},"time":datetime.now().strftime("%I:%M %p"),"online":True})

@app.route('/clear', methods=['POST'])
def clear():
    history.clear()
    return jsonify({"status":"cleared"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
