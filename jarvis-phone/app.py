import os
import hmac
import secrets
import requests
from flask import Flask, request, session, redirect, render_template_string, jsonify

app = Flask(__name__)

app.secret_key = os.environ["FLASK_SECRET_KEY"]
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="Lax",
    MAX_CONTENT_LENGTH=32 * 1024
)

PASSWORD = os.environ["JARVIS_PASSWORD"]
GEMINI_KEY = os.environ["GEMINI_API_KEY"]
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

PAGE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jarvis</title>
<style>
body{margin:0;background:#10131b;color:white;font-family:Arial;padding:20px}
main{max-width:650px;margin:40px auto}
h1{color:#69baff}
input,button,textarea{box-sizing:border-box;width:100%;padding:14px;
margin:8px 0;border-radius:10px;border:1px solid #444;background:#202633;color:white}
button{background:#1769aa;border:0;font-weight:bold}
#chat{white-space:pre-wrap;line-height:1.5;margin:20px 0}
.msg{padding:12px;margin:10px 0;background:#202633;border-radius:10px}
</style>
</head>
<body><main>
<h1>JARVIS</h1>
<p>Your personal AI assistant</p>
{% if not logged_in %}
<form method="post" action="/login">
<input type="hidden" name="csrf" value="{{ csrf }}">
<input type="password" name="password" placeholder="Jarvis password" required>
<button>Unlock Jarvis</button>
</form>
{% else %}
<div id="chat"></div>
<textarea id="prompt" placeholder="Ask Jarvis anything..." rows="3"></textarea>
<button onclick="sendMessage()">Send</button>
<button onclick="location.href='/logout'">Lock Jarvis</button>
<script>
const csrf = "{{ csrf }}";
async function sendMessage(){
 const box=document.getElementById("prompt");
 const prompt=box.value.trim();
 if(!prompt)return;
 box.value="";
 const chat=document.getElementById("chat");
 chat.innerHTML += '<div class="msg"><b>Sir:</b> '+escapeHtml(prompt)+'</div>';
 const wait=document.createElement("div");
 wait.className="msg"; wait.textContent="Jarvis is thinking...";
 chat.appendChild(wait);
 try{
  const r=await fetch("/chat",{method:"POST",
   headers:{"Content-Type":"application/json","X-CSRF-Token":csrf},
   body:JSON.stringify({prompt})});
  const data=await r.json();
  wait.textContent=data.reply || data.error || "Something went wrong.";
 }catch(e){wait.textContent="Connection error. Please try again.";}
}
function escapeHtml(s){
 return s.replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
</script>
{% endif %}
</main></body></html>
"""

def check_csrf():
    return hmac.compare_digest(
        session.get("csrf", ""),
        request.headers.get("X-CSRF-Token", request.form.get("csrf", ""))
    )

@app.route("/")
def home():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return render_template_string(
        PAGE, logged_in=session.get("logged_in", False),
        csrf=session["csrf"]
    )

@app.route("/login", methods=["POST"])
def login():
    if not check_csrf():
        return "Invalid request", 403
    password = request.form.get("password", "")
    if hmac.compare_digest(password, PASSWORD):
        session.clear()
        session["logged_in"] = True
        session["csrf"] = secrets.token_urlsafe(24)
        return redirect("/")
    return "Incorrect password. Go back and try again.", 401

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/chat", methods=["POST"])
def chat():
    if not session.get("logged_in"):
        return jsonify(error="Please unlock Jarvis first."), 401
    if not check_csrf():
        return jsonify(error="Invalid request."), 403

    prompt = request.json.get("prompt", "").strip()
    if not prompt or len(prompt) > 4000:
        return jsonify(error="Please enter a message under 4000 characters."), 400

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": GEMINI_KEY},
            json={"contents": [{"parts": [{"text":
                "You are Jarvis, a professional and intelligent personal AI. "
                "Address the user as Sir. Ask for approval before external actions. "
                "You cannot perform external actions in this version.\\n\\n"
                + prompt
            }]}]},
            timeout=45
        )
        response.raise_for_status()
        data = response.json()
        reply = data["candidates"][0]["content"]["parts"][0]["text"]
        return jsonify(reply=reply)
    except Exception:
        return jsonify(error="Gemini could not respond. Check your server settings."), 502

@app.route("/health")
def health():
    return "Jarvis is running", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
