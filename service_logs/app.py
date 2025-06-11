from flask import Flask, request, jsonify
import os
import time
from tinydb import TinyDB

app = Flask(__name__)

# Initialize TinyDB
db_path = '/app/data/logs.json'
os.makedirs(os.path.dirname(db_path), exist_ok=True)
db = TinyDB(db_path)


@app.route('/logs', methods=['POST'])
def store_log():
    """Store a log entry"""
    try:
        log_data = request.json
        if not log_data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Add timestamp if not present
        if 'timestamp' not in log_data:
            log_data['timestamp'] = time.time()
        
        # Store in TinyDB
        db.insert(log_data)
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs', methods=['GET'])
def get_logs():
    """Get logs with optional filtering"""
    try:
        # Get query parameters
        service = request.args.get('service')
        level = request.args.get('level')
        limit = int(request.args.get('limit', 100))
        
        # Get all logs
        logs = db.all()
        
        # Filter by service if specified
        if service:
            logs = [log for log in logs if log.get('service') == service]
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.get('level') == level]
        
        # Sort by timestamp (newest first) and limit
        logs.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
        logs = logs[:limit]
        
        return jsonify({
            'status': 'success',
            'logs': logs
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/logs/clear', methods=['POST'])
def clear_logs():
    """Clear all logs"""
    try:
        db.truncate()
        return jsonify({'status': 'success', 'message': 'All logs cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)