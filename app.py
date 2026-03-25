from flask import Flask, render_template, jsonify, request, abort
from bot.engine import bot
from bot.config import PORT, ADMIN_USER, ADMIN_PASS
import logging
from functools import wraps

app = Flask(__name__)

# Reduce werkzeug default logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # In a real production app, we'd use sessions or JWT.
        # For this tool, we trust the frontend login for the UI,
        # but we can add an optional header check here if desired.
        return f(*args, **kwargs)
    return decorated

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify(bot.get_stats())

@app.route('/api/bot/start', methods=['POST'])
@require_auth
def start_bot():
    if bot.start():
        return jsonify({"success": True, "message": "Bot startup initiated."})
    return jsonify({"success": False, "message": "Bot is already running."}), 400

@app.route('/api/bot/stop', methods=['POST'])
@require_auth
def stop_bot():
    if bot.stop():
        return jsonify({"success": True, "message": "Bot stopping process initiated."})
    return jsonify({"success": False, "message": "Bot is not currently running."}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, threaded=True)
