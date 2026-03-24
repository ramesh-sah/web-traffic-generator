from flask import Flask, render_template, jsonify, request
from bot.engine import bot
from bot.config import PORT
import logging

app = Flask(__name__)

# Reduce werkzeug default logging so it doesn't clutter our beautiful app log
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify(bot.get_stats())

@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    success = bot.start()
    if success:
        return jsonify({"success": True, "message": "Bot startup initiated."})
    else:
        return jsonify({"success": False, "message": "Bot is already running."}), 400

@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    success = bot.stop()
    if success:
        return jsonify({"success": True, "message": "Bot stopping process initiated."})
    else:
        return jsonify({"success": False, "message": "Bot is not currently running."}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
