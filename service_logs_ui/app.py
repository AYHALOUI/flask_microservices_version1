from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime


app = Flask(__name__)

# URL of logs service
LOGS_SERVICE_URL = "http://service_logs:5000"


@app.route('/', methods=['GET'])
def logs_ui():
    """Main logs viewing page"""
    try:
        # Get query parameters
        service = request.args.get('service', '')
        level = request.args.get('level', '')
        limit = request.args.get('limit', '100')
        
        # Build request to logs service
        params = {}
        if service:
            params['service'] = service
        if level:
            params['level'] = level
        params['limit'] = limit
        
        # Fetch logs from service_logs
        response = requests.get(f"{LOGS_SERVICE_URL}/logs", params=params)
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            grouped_logs = []
            current_group = []
            
            for log in reversed(logs):  # Process in chronological order
                if 'timestamp' in log:
                    try:
                        adjusted_timestamp = log['timestamp'] + 3600
                        log['formatted_time'] = timestamp_to_time(adjusted_timestamp)
                        
                        # Start new group when we see "incoming_request"
                        if log.get('action') == 'incoming_request':
                            if current_group:  # Save previous group
                                grouped_logs.append(current_group)
                            current_group = [log]
                        else:
                            current_group.append(log)
                    except:
                        log['formatted_time'] = "00:00:00"
            if current_group:
                grouped_logs.append(current_group)
            grouped_logs.reverse()
        else:
            grouped_logs = []
        return render_template('logs.html', grouped_logs=grouped_logs)
    except Exception as e:
        return f"Error fetching logs: {str(e)}"

@app.route('/clear', methods=['POST'])
def clear_logs():
    """Clear all logs via UI"""
    try:
        # Call logs service to clear
        response = requests.post(f"{LOGS_SERVICE_URL}/logs/clear")
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Logs cleared'})
        else:
            return jsonify({'error': 'Failed to clear logs'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.template_filter('timestamp_to_time')
def timestamp_to_time(timestamp):
    """Convert timestamp to readable time"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
    except:
        return "00:00:00"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)