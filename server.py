from flask import Flask, request, jsonify, render_template_string
import json, os, requests, re
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
FILE = "chat_history.json"
API_KEY = os.getenv("GROQ_API_KEY", "").strip()
MODEL = "llama-3.1-8b-instant"

def load_history():
    if not os.path.exists(FILE):
        return []
    try:
        with open(FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_history(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route("/")
def home():
    return render_template_string("""
<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SK Advanced AI</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#0f1117;color:#fff;font-family:Arial,sans-serif;height:100dvh;display:flex;flex-direction:column}
header{background:linear-gradient(90deg,#6a5cff,#00d4ff);padding:15px;text-align:center;font-size:22px;font-weight:bold}
header button{float:right;background:#ff4444;color:#fff;border:none;padding:7px 12px;border-radius:8px;cursor:pointer}
#chat{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}
.welcome{text-align:center;margin-top:70px}
.welcome h1{font-size:32px;background:linear-gradient(90deg,#ff6bff,#00d4ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.welcome p{color:#aaa;margin-top:10px}
.msg{max-width:85%;padding:12px 16px;border-radius:18px;line-height:1.7;white-space:pre-wrap;font-size:15px}
.user{background:linear-gradient(135deg,#6a5cff,#00d4ff);align-self:flex-end}
.ai{background:#1e1e2e;align-self:flex-start;border:1px solid #333}
.msg img{max-width:200px;border-radius:10px;display:block}
.box{padding:12px;background:#12121c;display:flex;gap:8px}
.box input{flex:1;padding:14px;border-radius:25px;border:1px solid #333;background:#1e1e2e;color:#fff;outline:none;font-size:16px}
.send{width:50px;height:50px;border-radius:50%;background:linear-gradient(135deg,#6a5cff,#00d4ff);border:none;font-size:22px;color:#fff;cursor:pointer}
.plus{width:45px;height:45px;border-radius:50%;background:#222;display:flex;align-items:center;justify-content:center;font-size:22px;cursor:pointer}
.typing{color:#aaa;font-style:italic}
</style>
</head>
<body>
<header>SK Advanced AI <button onclick="clearChat()">Clear</button></header>
<div id="chat"><div class="welcome" id="welcome"><h1>হ্যালো! 👋</h1><p>আমি SK Advanced AI<br>আজ কি সাহায্য করবো?</p></div></div>
<div class="box">
<label class="plus">+<input type="file" id="image" accept="image/*" hidden></label>
<input type="text" id="msg" placeholder="মেসেজ লিখো..." onkeypress="if(event.key==='Enter')send()">
<button class="send" onclick="send()">➤</button>
</div>
<script>
let box=document.getElementById('chat');
let inp=document.getElementById('msg');
let imgInp=document.getElementById('image');
let selImg=null;
function addMsg(role,text,img){
  let w=document.getElementById('welcome'); if(w) w.remove();
  let d=document.createElement('div'); d.className='msg '+(role==='You'?'user':'ai');
  if(img){let im=document.createElement('img'); im.src=img; d.appendChild(im);}
  d.appendChild(document.createTextNode(text)); box.appendChild(d); box.scrollTop=box.scrollHeight;
}
async function refresh(){
  let r=await fetch('/history'); let d=await r.json(); box.innerHTML='';
  if(!d.history.length){box.innerHTML='<div class="welcome" id="welcome"><h1>হ্যালো! 👋</h1><p>আমি SK Advanced AI<br>আজ কি সাহায্য করবো?</p></div>'; return;}
  d.history.forEach(m=>addMsg(m.role,m.text));
}
imgInp.onchange=()=>{let f=imgInp.files[0]; if(!f) return; let rd=new FileReader(); rd.onload=e=>selImg=e.target.result; rd.readAsDataURL(f); alert('ছবি সিলেক্ট হয়েছে!');}
async function send(){
  let t=inp.value.trim(); if(!t && !selImg) return;
  addMsg('You',t||'ছবি পাঠিয়েছি',selImg); let imgData=selImg; inp.value=''; selImg=null; imgInp.value='';
  let ty=document.createElement('div'); ty.className='typing'; ty.textContent='SK লিখছে...'; box.appendChild(ty);
  let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:t,image:imgData})});
  let d=await r.json(); ty.remove(); addMsg('AI',d.reply||d.error||'সমস্যা হয়েছে');
}
async function clearChat(){ if(confirm('সব চ্যাট মুছবে?')){ await fetch('/clear',{method:'POST'}); refresh(); } }
refresh();
</script>
</body>
</html>
""")

@app.route("/history")
def history():
    return jsonify({"history": load_history()})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()
    if not message:
        return jsonify({"error": "মেসেজ পাঠাও"}), 400
    if re.search(r"নির্মাতা|কে তৈরি|কে বানিয়েছে|কে বানিয়েছে", message.lower()):
        reply = "আমার নির্মাতা মোঃ সামিউল ইসলাম। তিনি বাংলাদেশের নাটোরের বাসিন্দা।"
        old = load_history()
        old.extend([{"role": "You", "text": message}, {"role": "AI", "text": reply}])
        save_history(old)
        return jsonify({"reply": reply})
    if not API_KEY:
        return jsonify({"error": "Groq API Key পাওয়া যায়নি"}), 500
    conv = []
    for item in load_history()[-10:]:
        role = {"You": "user", "AI": "assistant"}.get(item.get("role"))
        if role and item.get("text"):
            conv.append({"role": role, "content": item["text"]})
    conv.append({"role": "user", "content": message})
    try:
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json={"model": MODEL, "messages": [{"role": "system", "content": "তোমার নাম SK Advanced AI। নির্মাতা মোঃ সামিউল ইসলাম, নাটোর, বাংলাদেশ। বাংলায় উত্তর দেবে।"}] + conv}, timeout=60)
        if not res.ok:
            return jsonify({"error": "Groq Error"}), 502
        reply = res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    old = load_history()
    old.extend([{"role": "You", "text": message}, {"role": "AI", "text": reply}])
    save_history(old)
    return jsonify({"reply": reply})

@app.route("/clear", methods=["POST"])
def clear():
    save_history([])
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
    # fix
