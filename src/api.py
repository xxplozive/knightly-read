"""Simple API server for Instapaper integration."""
from flask import Flask, request, jsonify
from flask_cors import CORS
from .instapaper import InstapaperClient
import logging

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

instapaper = InstapaperClient()


@app.route('/api/instapaper/status', methods=['GET'])
def instapaper_status():
    """Check Instapaper authentication status."""
    authenticated = instapaper.is_authenticated()
    if authenticated:
        success, message = instapaper.verify_credentials()
        return jsonify({
            'authenticated': success,
            'message': message
        })
    return jsonify({
        'authenticated': False,
        'message': 'Not logged in'
    })


@app.route('/api/instapaper/login', methods=['POST'])
def instapaper_login():
    """Authenticate with Instapaper."""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({
            'success': False,
            'message': 'Username and password required'
        }), 400

    success, message = instapaper.authenticate(username, password)
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/instapaper/save', methods=['POST'])
def instapaper_save():
    """Save an article to Instapaper."""
    data = request.json
    url = data.get('url')
    title = data.get('title')

    if not url:
        return jsonify({
            'success': False,
            'message': 'URL required'
        }), 400

    success, message = instapaper.add_bookmark(url, title)
    return jsonify({
        'success': success,
        'message': message
    })


@app.route('/api/instapaper/logout', methods=['POST'])
def instapaper_logout():
    """Clear Instapaper credentials."""
    instapaper.logout()
    return jsonify({
        'success': True,
        'message': 'Logged out'
    })


def run_server(host='127.0.0.1', port=5000):
    """Run the API server."""
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_server()
