"""Flask web server for wait times dashboard."""

import logging
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request

from src.data.database import get_database

logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__, template_folder='templates')

# Database reference (set during initialization)
_db = None


def init_app(database):
    """Initialize the web app with database."""
    global _db
    _db = database


@app.route('/')
def index():
    """Main dashboard page showing current wait times."""
    if not _db:
        return "Database not initialized", 500

    current_waits = _db.get_current_waits()
    parks = _db.get_all_parks()

    # Group waits by park
    waits_by_park = {}
    for wait in current_waits:
        park = wait['park_name']
        if park not in waits_by_park:
            waits_by_park[park] = []
        waits_by_park[park].append(wait)

    return render_template('index.html',
                           waits_by_park=waits_by_park,
                           parks=parks,
                           last_updated=current_waits[0]['timestamp'] if current_waits else None)


@app.route('/trends')
def trends():
    """Historical trends page."""
    if not _db:
        return "Database not initialized", 500

    rides = _db.get_all_rides()
    parks = _db.get_all_parks()
    stats = _db.get_database_stats()

    return render_template('trends.html',
                           rides=rides,
                           parks=parks,
                           stats=stats)


@app.route('/ride/<ride_name>')
def ride_detail(ride_name):
    """Individual ride statistics page."""
    if not _db:
        return "Database not initialized", 500

    hours = request.args.get('hours', 24, type=int)
    history = _db.get_ride_history(ride_name, hours=hours)
    stats = _db.get_ride_stats(ride_name)

    return render_template('ride.html',
                           ride_name=ride_name,
                           history=history,
                           stats=stats,
                           hours=hours)


# API Endpoints

@app.route('/api/waits')
def api_current_waits():
    """API endpoint for current wait times."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    waits = _db.get_current_waits()
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'waits': waits
    })


@app.route('/api/history/<ride_name>')
def api_ride_history(ride_name):
    """API endpoint for ride history."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    hours = request.args.get('hours', 24, type=int)
    history = _db.get_ride_history(ride_name, hours=hours)

    return jsonify({
        'ride_name': ride_name,
        'hours': hours,
        'history': history
    })


@app.route('/api/park/<park_name>')
def api_park_history(park_name):
    """API endpoint for park average wait history."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    hours = request.args.get('hours', 24, type=int)
    history = _db.get_park_history(park_name, hours=hours)

    return jsonify({
        'park_name': park_name,
        'hours': hours,
        'history': history
    })


@app.route('/api/stats/<ride_name>')
def api_ride_stats(ride_name):
    """API endpoint for ride statistics."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    days = request.args.get('days', 7, type=int)
    stats = _db.get_ride_stats(ride_name, days=days)

    return jsonify({
        'ride_name': ride_name,
        'days': days,
        'stats': stats
    })


@app.route('/api/rides')
def api_all_rides():
    """API endpoint for list of all rides."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    rides = _db.get_all_rides()
    return jsonify({'rides': rides})


@app.route('/api/parks')
def api_all_parks():
    """API endpoint for list of all parks."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    parks = _db.get_all_parks()
    return jsonify({'parks': parks})


@app.route('/api/db-stats')
def api_db_stats():
    """API endpoint for database statistics."""
    if not _db:
        return jsonify({'error': 'Database not initialized'}), 500

    stats = _db.get_database_stats()
    return jsonify(stats)


def run_server(host='0.0.0.0', port=8080, database=None):
    """Run the Flask server in a background thread.

    Args:
        host: Host to bind to
        port: Port to listen on
        database: WaitTimesDatabase instance
    """
    if database:
        init_app(database)

    def run():
        # Suppress Flask's default logging in production
        import logging as flask_logging
        flask_log = flask_logging.getLogger('werkzeug')
        flask_log.setLevel(flask_logging.WARNING)

        app.run(host=host, port=port, debug=False, use_reloader=False)

    thread = threading.Thread(target=run, daemon=True, name="WebServer")
    thread.start()
    logger.info(f"Web dashboard started at http://{host}:{port}")
    return thread
