from flask import Flask, render_template_string, request, redirect, url_for, send_from_directory
from datetime import datetime, timedelta
import csv
import os

app = Flask(__name__)
LOG_FILE = 'logs.csv'

def load_logs():
    if not os.path.exists(LOG_FILE): return []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_logs(logs):
    with open(LOG_FILE, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'time', 'name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)

MEDICINES = ["コンサ1", "コンサ2", "抑肝散", "頓服"]

# --- アイコン画像を読み込めるようにする魔法（これがないと502になりやすいです） ---
@app.route('/icon.png')
def icon_file():
    return send_from_directory(os.getcwd(), 'icon.png')

COMMON_STYLE = """
<link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700&display=swap" rel="stylesheet">
<style>
    body { font-family: 'Zen Maru Gothic', sans-serif; text-align: center; background: #fff5f7; margin: 0; padding: 20px; color: #5d5d5d; }
    .container { max-width: 400px; margin: auto; }
    h1 { color: #ff8fb1; font-size: 1.8rem; }
    .card { background: white; padding: 12px; border-radius: 20px; box-shadow: 0 8px 15px rgba(255, 143, 177, 0.1); margin-bottom: 12px; border: 2px solid #ffe4e9; }
    .btn { width: 100%; font-size: 18px; padding: 18px; background: #87ceeb; color: white; border: none; border-radius: 15px; cursor: pointer; font-weight: 700; touch-action: manipulation; }
    .btn.sub { background: #ffb7c5; margin-top: 20px; font-size: 14px; padding: 10px; }
    .history-card { text-align: left; background: white; padding: 15px; border-radius: 15px; margin-bottom: 15px; border-left: 5px solid #ff8fb1; }
    .date-title { font-weight: bold; color: #ff8fb1; border-bottom: 1px solid #ffe4e9; margin-bottom: 8px; }
</style>
"""

@app.route('/')
def index():
    logs = load_logs()
    now = datetime.now()
    today = now.strftime("%Y/%m/%d")
    today_logs = [log for log in logs if log['date'] == today]
    taken_names = [log['name'] for log in today_logs]
    all_clear = all(m in taken_names for m in MEDICINES[:3])
    
    tonpuku_wait = ""
    can_t = True
    t_logs = [l for l in logs if l['name'] == "頓服"]
    if t_logs:
        last = datetime.strptime(f"{t_logs[-1]['date']} {t_logs[-1]['time']}", "%Y/%m/%d %H:%M:%S")
        if now < last + timedelta(hours=4):
            can_t = False
            diff = (last + timedelta(hours=4)) - now
            tonpuku_wait = f"(あと{diff.seconds//3600}h{(diff.seconds//60)%60}m)"

    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">{COMMON_STYLE}<link rel="apple-touch-icon" href="/icon.png"></head>
    <body><div class="container">
        <h1>🌸 薬マネ 🌸</h1>
        <div style="font-size:1.1rem; color:#ffb7c5; font-weight:bold; margin-bottom:20px;">
            {"<div style='color:#ff6b81;'>💖 全完了！ 💖</div>" if all_clear else "きょうも ぼちぼち のもうね"}
        </div>
        {"".join([f'<div class="card"><form action="/record" method="post"><input type="hidden" name="med_name" value="{m}"><button type="button" class="btn" onmousedown="start_press(\'{m}\')" onmouseup="end_press()" ontouchstart="start_press(\'{m}\')" ontouchend="end_press()" style="background:{"#e0e0e0" if (m in taken_names and m!="頓服") else ("#ff8fb1" if m=="頓服" and can_t else ("#f3d1d9" if m=="頓服" and not can_t else "#87ceeb"))}">{m} {"(済)" if (m in taken_names and m!="頓服") else ""} {tonpuku_wait if m=="頓服" and not can_t else ""}</button></form></div>' for m in MEDICINES])}
        <button class="btn sub" onclick="location.href='/history'">📅 1週間のきろくを見る</button>
    </div>
    <script>
        let t; let lp = false;
        function start_press(n) {{ lp = false; t = setTimeout(() => {{ lp = true; if(confirm(n + " けす？")) location.href="/delete/"+encodeURIComponent(n); }}, 800); }}
        function end_press() {{ clearTimeout(t); if(!lp) {{ const b = event.currentTarget; if(!b.style.background.includes("rgb(224, 224, 224)") && !b.style.background.includes("rgb(243, 209, 217)")) b.closest('form').submit(); }} }}
    </script>
    </body></html>
    """)

@app.route('/history')
def history():
    logs = load_logs()
    history_data = {}
    for i in range(7):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y/%m/%d")
        history_data[d] = [log for log in logs if log['date'] == d]

    return render_template_string(f"""
    <!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">{COMMON_STYLE}</head>
    <body><div class="container">
        <h1>📅 1週間のきろく</h1>
        {"".join([f'''<div class="history-card"><div class="date-title">{date}</div>{"".join([f"<div>・{l['time']} {l['name']}</div>" for l in day_logs]) if day_logs else "<div>なし</div>"}</div>''' for date, day_logs in history_data.items()])}
        <button class="btn" style="background:#ffb7c5;" onclick="location.href='/'">もどる</button>
    </div></body></html>
    """)

@app.route('/record', methods=['POST'])
def record():
    m = request.form.get('med_name'); logs = load_logs()
    logs.append({"date": datetime.now().strftime("%Y/%m/%d"), "time": datetime.now().strftime("%H:%M:%S"), "name": m})
    save_logs(logs); return redirect(url_for('index'))

@app.route('/delete/<name>')
def delete(name):
    logs = load_logs(); today = datetime.now().strftime("%Y/%m/%d"); new = []
    found = False
    for l in reversed(logs):
        if not found and l['name'] == name and l['date'] == today: found = True; continue
        new.append(l)
    save_logs(list(reversed(new))); return redirect(url_for('index'))

# --- 最後にこれを追加しないとRenderは動きません！ ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
