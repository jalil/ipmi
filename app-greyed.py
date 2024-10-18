
from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta

app = Flask(__name__)

last_click_time = None

@app.route('/', methods=['GET', 'POST'])
def index():
    global last_click_time

    if request.method == 'POST':
        current_time = datetime.now()
        if last_click_time is None or current_time - last_click_time > timedelta(minutes=1):
            last_click_time = current_time
            return jsonify({
                "message": "Power cycle initiated",
                "disabled": True,
                "remainingTime": 60  # 10 minutes in seconds
            })
        else:
            remaining_time = int((last_click_time + timedelta(minutes=1) - current_time).total_seconds())
            return jsonify({
                "message": f"Please wait {remaining_time} seconds",
                "disabled": True,
                "remainingTime": remaining_time
            })

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
