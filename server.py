import os
from flask import Flask, request, jsonify, session
from groq import Groq
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
user_chats = {}

@app.route("/")
def home():
    if "uid" not in session:
        session["uid"] = secrets.token_hex(8)
    return open("index.html", encoding="utf-8").read()

@app.route("/chat", methods=["POST"])
def chat():
    uid = session.get("uid")
    data = request.json
    msg = data.get("message", "")
    history = user_chats.get(uid, [])
    history.append({"role": "user", "content": msg})
    history = history[-10:]
    try:
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=history)
        reply = res.choices[0].message.content
    except Exception as e:
        reply = f"Error: {e}"
    history.append({"role": "assistant", "content": reply})
    user_chats[uid] = history
    return jsonify({"reply": reply})

@app.route("/history")
def history():
    return jsonify(user_chats.get(session.get("uid"), []))

@app.route("/clear", methods=["POST"])
def clear():
    uid = session.get("uid")
    if uid in user_chats:
        del user_chats[uid]
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5001)))
