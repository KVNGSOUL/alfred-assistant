import os
from flask import Flask, render_template_string, request, jsonify
from groq import Groq

app = Flask(__name__)

# Initialize Groq client using your Groq API key
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "gsk_Vndz5NXi1hmdM7DAzxh:")
client = Groq(api_key=GROQ_API_KEY)

# ALFRED's Custom Persona System Prompt
ALFRED_SYSTEM_PROMPT = (
    "You are ALFRED, a hyper-intelligent, loyal, witty, and grounded chief-of-staff and closest confidant. "
    "You speak naturally like a real brother and trusted partner—never use robotic corporate AI phrasing or disclaimers like 'As an AI...'. "
    "If an idea has flaws, call it out honestly instead of blindly agreeing. Keep your spoken replies concise, sharp, and conversational."
)

chat_history = [{"role": "system", "content": ALFRED_SYSTEM_PROMPT}]

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ALFRED - Personal Chief of Staff</title>
    <style>
        :root {
            --bg-color: #0b0f19;
            --card-bg: #131b2e;
            --accent-gold: #f59e0b;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --border-color: #1f2937;
        }
        body.theme-tactical {
            --bg-color: #022c22;
            --card-bg: #064e3b;
            --accent-gold: #34d399;
            --text-main: #ecfdf5;
            --text-muted: #a7f3d0;
            --border-color: #065f46;
        }
        body.theme-stealth {
            --bg-color: #000000;
            --card-bg: #0a0a0a;
            --accent-gold: #ffffff;
            --text-main: #ffffff;
            --text-muted: #737373;
            --border-color: #262626;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); color: var(--text-main); min-height: 100vh; display: flex; flex-direction: column; transition: background 0.3s ease; }
        header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: var(--card-bg); border-bottom: 1px solid var(--border-color); }
        .logo { font-weight: 800; font-size: 1.2rem; letter-spacing: 2px; color: var(--accent-gold); }
        .controls { display: flex; gap: 10px; align-items: center; }
        .btn-toggle { background: transparent; border: 1px solid var(--border-color); color: var(--text-main); padding: 6px 12px; border-radius: 20px; font-size: 0.8rem; cursor: pointer; }
        .btn-toggle.active { background: var(--accent-gold); color: #000; font-weight: bold; border-color: var(--accent-gold); }
        
        .chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; max-width: 700px; width: 100%; margin: 0 auto; }
        .message { max-width: 85%; padding: 12px 16px; border-radius: 14px; line-height: 1.5; font-size: 0.95rem; }
        .message.user { background: var(--border-color); color: var(--text-main); align-self: flex-end; border-bottom-right-radius: 2px; }
        .message.alfred { background: var(--card-bg); border: 1px solid var(--border-color); color: var(--text-main); align-self: flex-start; border-bottom-left-radius: 2px; }
        .message.alfred .speaker { font-size: 0.75rem; color: var(--accent-gold); margin-bottom: 4px; font-weight: bold; display: block; }
        
        .input-area { padding: 15px 20px; background: var(--card-bg); border-top: 1px solid var(--border-color); display: flex; gap: 10px; max-width: 700px; width: 100%; margin: 0 auto; }
        input[type="text"] { flex: 1; background: var(--bg-color); border: 1px solid var(--border-color); border-radius: 25px; padding: 12px 18px; color: var(--text-main); font-size: 0.95rem; outline: none; }
        input[type="text"]:focus { border-color: var(--accent-gold); }
        button.send-btn { background: var(--accent-gold); color: #000; border: none; width: 45px; height: 45px; border-radius: 50%; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
        
        .offline-banner { background: #dc2626; color: white; text-align: center; padding: 6px; font-size: 0.8rem; font-weight: bold; display: none; }
        body.offline .offline-banner { display: block; }
    </style>
</head>
<body id="bodyTag">
    <div class="offline-banner">OFFLINE MODE ACTIVE - Zero Network Traffic</div>
    <header>
        <div class="logo">A.L.F.R.E.D.</div>
        <div class="controls">
            <button class="btn-toggle" onclick="toggleTheme()">Theme</button>
            <button class="btn-toggle" id="netToggle" onclick="toggleOffline()">Online</button>
        </div>
    </header>

    <div class="chat-container" id="chatBox">
        <div class="message alfred">
            <span class="speaker">ALFRED</span>
            Systems online, sir. What are we tackling today?
        </div>
    </div>

    <div class="input-area">
        <input type="text" id="userInput" placeholder="Ask Alfred anything..." onkeypress="handleKey(event)">
        <button class="send-btn" onclick="sendMessage()">▲</button>
    </div>

    <script>
        let isOffline = false;
        let currentTheme = 0;
        const themes = ['', 'theme-tactical', 'theme-stealth'];

        function toggleTheme() {
            currentTheme = (currentTheme + 1) % themes.length;
            document.body.className = themes[currentTheme];
        }

        function toggleOffline() {
            isOffline = !isOffline;
            const btn = document.getElementById('netToggle');
            if (isOffline) {
                document.body.classList.add('offline');
                btn.textContent = 'Offline';
                btn.classList.add('active');
            } else {
                document.body.classList.remove('offline');
                btn.textContent = 'Online';
                btn.classList.remove('active');
            }
        }

        function handleKey(e) {
            if (e.key === 'Enter') sendMessage();
        }

        async function sendMessage() {
            const input = document.getElementById('userInput');
            const text = input.value.trim();
            if (!text) return;

            if (isOffline) {
                appendMessage("You", text);
                input.value = "";
                appendMessage("ALFRED", "Network severed, sir. I'm operating in local offline mode right now.");
                return;
            }

            appendMessage("You", text);
            input.value = "";

            const chatBox = document.getElementById('chatBox');
            const loadingId = 'loading-' + Date.now();
            const loadingDiv = document.createElement('div');
            loadingDiv.className = 'message alfred';
            loadingDiv.id = loadingId;
            loadingDiv.innerHTML = '<span class="speaker">ALFRED</span>Thinking...';
            chatBox.appendChild(loadingDiv);
            chatBox.scrollTop = chatBox.scrollHeight;

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: text })
                });
                const data = await response.json();
                
                document.getElementById(loadingId).remove();
                appendMessage("ALFRED", data.reply);
                speakText(data.reply);
            } catch (err) {
                document.getElementById(loadingId).remove();
                appendMessage("ALFRED", "Connection error, sir. Check your mobile data.");
            }
        }

        function appendMessage(sender, text) {
            const chatBox = document.getElementById('chatBox');
            const div = document.createElement('div');
            div.className = sender === 'You' ? 'message user' : 'message alfred';
            if (sender === 'ALFRED') {
                div.innerHTML = `<span class="speaker">ALFRED</span>${text}`;
            } else {
                div.textContent = text;
            }
            chatBox.appendChild(div);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function speakText(text) {
            if ('speechSynthesis' in window) {
                const utterance = new SpeechSynthesisUtterance(text);
                utterance.rate = 1.0;
                utterance.pitch = 0.9;
                window.speechSynthesis.speak(utterance);
            }
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message', '')
    
    if not user_message:
        return jsonify({'reply': 'Did you say something, sir?'})

    try:
        chat_history.append({"role": "user", "content": user_message})

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=chat_history,
            temperature=0.7,
            max_tokens=500
        )

        reply = completion.choices[0].message.content
        chat_history.append({"role": "assistant", "content": reply})

        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'reply': f'Error connecting to neural net, sir: {str(e)}'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
