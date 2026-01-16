"""Simple API server for Instapaper integration and news refresh."""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from .instapaper import InstapaperClient
from .aggregator import NewsAggregator
from .generator import HTMLGenerator
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

instapaper = InstapaperClient()

# Paths for aggregator
BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / 'config' / 'feeds.yaml'
OUTPUT_DIR = BASE_DIR / 'output'
TEMPLATE_DIR = BASE_DIR / 'templates'


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


@app.route('/api/refresh', methods=['POST'])
def refresh_news():
    """Refresh news for a specific region or all regions."""
    data = request.json or {}
    region_id = data.get('region')

    try:
        logger.info(f"Refreshing news for region: {region_id or 'all'}")
        aggregator = NewsAggregator(str(CONFIG_PATH))
        results = aggregator.aggregate()

        # Generate new HTML and JSON
        generator = HTMLGenerator(str(TEMPLATE_DIR), str(OUTPUT_DIR))
        generator.generate(results)

        # Return data for the requested region or all
        if region_id and region_id in results:
            return jsonify({
                'success': True,
                'data': {region_id: results[region_id]}
            })
        else:
            return jsonify({
                'success': True,
                'data': results
            })
    except Exception as e:
        logger.error(f"Refresh failed: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/data', methods=['GET'])
def get_data():
    """Get current news data."""
    try:
        json_path = OUTPUT_DIR / 'data.json'
        with open(json_path, 'r') as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def serve_index():
    """Serve the main HTML page."""
    return send_from_directory(str(OUTPUT_DIR), 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from output directory."""
    return send_from_directory(str(OUTPUT_DIR), filename)


def run_server(host='127.0.0.1', port=5000):
    """Run the API server."""
    app.run(host=host, port=port, debug=False)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    run_server()
