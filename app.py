from flask import Flask, render_template_string, request, redirect, url_for
from datetime import datetime, timedelta
import csv
import os

app = Flask(__name__)

# 保存するファイルの名前
LOG_FILE = 'logs.csv'

# --- データの読み書き関数 ---
def load_logs():
    """ファイルから記録を読み込む"""
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def save_logs(logs):
    """ファイルに記録を書き込む"""
    with open(LOG_FILE, 'w', encoding='utf-8', newline='') as f:
        fieldnames = ['date', 'time', 'name']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)

# 薬の種類
MEDICINES = ["朝の薬(1)", "朝の薬(2)", "朝の薬(3)", "頓服"]

@app.route('/')
def index():
    logs = load_logs()  # 保存されたファイルを読み込む
    now = datetime.now()
    today = now.strftime("%Y/%m/%d")
    today_logs = [log for log in logs if log['date'] == today]
    taken_names = [log['name'] for log in today_logs]
    all_clear = all(m in taken_names for m in MEDICINES[:3])
    
    # 頓服の4時間チェック
    tonpuku_wait_msg = ""
    can_take_tonpuku = True
    tonpuku_logs = [l for l in logs if l['name'] == "頓服"]
    if tonpuku_logs:
        last_tonpuku = tonpuku_logs[-1]
        last_time = datetime.strptime(f"{last_tonpuku['date']} {last_tonpuku['time']}", "%Y/%m/%d %H:%M:%S")
        next_available_time = last_time + timedelta(hours=4)
        if now < next_available_time:
            can_take_tonpuku = False
            remaining = next_available_time - now
            h, rem = divmod(remaining.seconds, 3600)
            m, _ = divmod(rem, 60)
            tonpuku_wait_msg = f"(あと{h}h{m}m)"

    return render_template_string(f"""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
        <title>薬マネ</title>
        <link href="https://fonts.googleapis.com/css2?family=Zen+Maru+Gothic:wght@500;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Zen Maru Gothic', sans-serif; text-align: center; background: #fff5f7; margin: 0; padding: 20px; color: #5d5d5d; -webkit-user-select: none; }}
            .container {{ max-width: 400px; margin: auto; }}
            h1 {{ color: #ff8fb1; font-size: 1.8rem; margin: 10px 0; }}
            .status {{ font-size: 1.1rem; color: #ffb7c5; margin-bottom: 20px; font-weight: bold; min-height: 1.5em; }}
            .card {{ background: white; padding: 12px; border-radius: 20px; box-shadow: 0 8px 15px rgba(255, 143, 177, 0.1); margin-bottom: 12px; border: 2px solid #ffe4e9; }}
            .btn {{ 
                width: 100%; font-size: 18px; padding: 18px; background: #87ceeb; color: white; border: none; 
                border-radius: 15px; cursor: pointer; font-family: 'Zen Maru Gothic', sans-serif; font-weight: 700;
                touch-action: manipulation;
            }}
            .btn.done {{ background: #e0e0e0; color: #999; }}
            .btn.tonpuku {{ background: #ff8fb1; }}
            .btn.wait {{ background: #f3d1d9; color: #fff; font-size: 14px; }}
            .log-list {{ text-align: left; background: white; padding: 15px; border-radius: 15px; margin-top: 20px; max-height: 200px; overflow-y: auto; }}
            .all-clear-msg {{ font-size: 20px; color: #ff6b81; animation: heartBeat 1.5s infinite; }}
            @keyframes heartBeat {{ 0% {{ transform: scale(1); }} 14% {{ transform: scale(1.1); }} 28% {{ transform: scale(1); }} }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌸 薬マネ 🌸</h1>
            <div class="status">
                {"<div class='all-clear-msg'>💖 朝の分、ばっちり！ 💖</div>" if all_clear else "きょうも ぼちぼち のもうね"}
            </div>

            {"".join([f'''
            <div class="card">
                <form action="/record" method="post">
                    <input type="hidden" name="med_name" value="{m}">
                    <button type="button" class="btn {"done" if (m in taken_names and m != "頓服") else ("tonpuku" if (m == "頓服" and can_take_tonpuku) else ("wait" if (m == "頓服" and not can_take_tonpuku) else ""))}"
                        onmousedown="start_press('{m}')" onmouseup="end_press()"
                        ontouchstart="start_press('{m}')" ontouchend="end_press()">
                        {m} {"(済)" if (m in taken_names and m != "頓服") else ""} {tonpuku_wait_msg if (m == "頓服" and not can_take_tonpuku) else ""}
                    </button>
                </form>
            </div>
            ''' for m in MEDICINES])}

            <div class="log-list">
                <h3 style="margin:0; color:#ff8fb1; font-size: 1rem;">📝 さいきんのきろく</h3>
                {"".join([f"<li style='list-style:none; font-size:0.8rem; border-bottom:1px dashed #eee; padding:5px 0;'>✅ {log['date']} {log['time']} - {log['name']}</li>" for log in reversed(logs[:50])])}
            </div>
        </div>

        <script>
            let timer;
            let isLongPress = false;
            function start_press(name) {{
                isLongPress = false;
                timer = setTimeout(function() {{
                    isLongPress = true;
                    if(confirm(name + " の記録をけす？")) {{ window.location.href = "/delete/" + encodeURIComponent(name); }}
                }}, 800);
            }}
            function end_press() {{
                clearTimeout(timer);
                if(!isLongPress) {{
                    const btn = event.currentTarget;
                    if(!btn.classList.contains('wait') && !btn.classList.contains('done')) {{ btn.closest('form').submit(); }}
                }}
            }}
            window.oncontextmenu = function(e) {{ e.preventDefault(); return false; }};
        </script>
    </body>
    </html>
    """)

@app.route('/record', methods=['POST'])
def record():
    med_name = request.form.get('med_name')
    logs = load_logs()
    now = datetime.now()
    logs.append({"date": now.strftime("%Y/%m/%d"), "time": now.strftime("%H:%M:%S"), "name": med_name})
    save_logs(logs) # ファイルに保存！
    return redirect(url_for('index'))

@app.route('/delete/<name>')
def delete(name):
    logs = load_logs()
    today = datetime.now().strftime("%Y/%m/%d")
    new_logs = []
    found = False
    for log in reversed(logs):
        if not found and log['name'] == name and log['date'] == today:
            found = True
            continue
        new_logs.append(log)
    save_logs(list(reversed(new_logs))) # ファイルを更新！
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
