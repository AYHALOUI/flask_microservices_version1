from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
from collections import defaultdict

app = Flask(__name__)

# URL of logs service
LOGS_SERVICE_URL = "http://service_logs:5000"

@app.template_filter('timestamp_to_time')
def timestamp_to_time(timestamp):
    """Convert timestamp to readable time"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
    except:
        return "00:00:00"

@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert timestamp to readable datetime"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown time"


@app.route('/', methods=['GET'])
def request_list():
    """Main page: Shows list of incoming requests"""
    try:
        # Use the new enhanced endpoint if available
        try:
            response = requests.get(f"{LOGS_SERVICE_URL}/requests")
            if response.status_code == 200:
                data = response.json()
                request_summaries = data.get('requests', [])
                
                # Add formatted time and status
                for req in request_summaries:
                    req['formatted_time'] = timestamp_to_datetime(req.get('timestamp', 0))
                    req['status'] = 'Error' if req.get('has_errors') else 'Success'
                
                return render_template('request_list.html', requests=request_summaries)
        except:
            pass  # Fall back to old method
        
        # Fallback: Fetch all logs and group manually (old method)
        response = requests.get(f"{LOGS_SERVICE_URL}/logs", params={'limit': 1000})
        
        if response.status_code == 200:
            data = response.json()
            logs = data.get('logs', [])
            
            # Group logs by request_id and find incoming requests
            request_groups = defaultdict(list)
            incoming_requests = {}
            
            for log in logs:
                request_id = log.get('request_id')
                if request_id:
                    request_groups[request_id].append(log)
                    
                    # Track incoming requests
                    if log.get('action') in ['incoming_request', 'incoming_request_with_payload']:
                        incoming_requests[request_id] = log
            
            # Create summary data for each request
            request_summaries = []
            for request_id, initial_log in incoming_requests.items():
                group_logs = request_groups[request_id]
                
                # Count steps and check for errors
                step_count = len(group_logs)
                has_errors = any('error' in log.get('level', '').lower() or 
                               'ERROR' in log.get('to_service', '') for log in group_logs)
                
                # Extract endpoint info
                endpoint = initial_log.get('endpoint', 'Unknown')
                method = initial_log.get('method', 'GET')
                
                request_summaries.append({
                    'request_id': request_id,
                    'timestamp': initial_log.get('timestamp'),
                    'formatted_time': timestamp_to_datetime(initial_log.get('timestamp', 0)),
                    'endpoint': endpoint,
                    'method': method,
                    'step_count': step_count,
                    'has_errors': has_errors,
                    'status': 'Error' if has_errors else 'Success'
                })
            
            # Sort by timestamp (newest first)
            request_summaries.sort(key=lambda x: x.get('timestamp', 0), reverse=True)
            
        else:
            request_summaries = []
            
        return render_template('request_list.html', requests=request_summaries)
        
    except Exception as e:
        return f"Error fetching requests: {str(e)}"

@app.route('/request/<request_id>')
def request_detail(request_id):
    """Detail page: Shows detailed flow for a specific request with enhanced details"""
    try:
        # Get all logs for this request
        response = requests.get(f"{LOGS_SERVICE_URL}/logs", params={'limit': 1000})
        
        if response.status_code == 200:
            data = response.json()
            all_logs = data.get('logs', [])
            
            # Filter logs for this specific request
            request_logs = [log for log in all_logs if log.get('request_id') == request_id]
            
            if not request_logs:
                return f"No logs found for request ID: {request_id}"
            
            # Separate flow logs from payload logs
            flow_logs = []
            request_payload = None
            response_data = None
            request_info = {}
            
            for log in request_logs:
                if log.get('action') == 'request_payload':
                    # Extract request info and payload
                    request_info = {
                        'request_id': request_id,
                        'method': log.get('method', 'POST'),
                        'endpoint': log.get('endpoint', '/unknown'),
                        'timestamp': log.get('timestamp'),
                        'formatted_datetime': timestamp_to_datetime(log.get('timestamp', 0))
                    }
                    request_payload = log.get('payload', {})
                    
                elif log.get('action') == 'response_data':
                    # Extract response data
                    response_data = {
                        'status_code': log.get('status_code', 200),
                        'response_time_ms': log.get('response_time_ms', 0),
                        'data': log.get('response', {})
                    }
                    
                else:
                    # Regular flow log - enhance with details
                    enhanced_log = enhance_log_with_details(log)
                    flow_logs.append(enhanced_log)
            
            # Sort flow logs by timestamp
            flow_logs.sort(key=lambda x: x.get('timestamp', 0))
            
            # Add formatted time to flow logs
            for log in flow_logs:
                if 'timestamp' in log:
                    log['formatted_time'] = timestamp_to_time(log['timestamp'])
                else:
                    log['formatted_time'] = "00:00:00"
                
                # IMPORTANT: Ensure details exists, even if empty
                if 'details' not in log:
                    log['details'] = []
            
            # Set defaults if no payload/response data found
            if not request_info:
                initial_log = flow_logs[0] if flow_logs else {}
                request_info = {
                    'request_id': request_id,
                    'method': 'POST',
                    'endpoint': '/unknown',
                    'timestamp': initial_log.get('timestamp'),
                    'formatted_datetime': timestamp_to_datetime(initial_log.get('timestamp', 0))
                }
            
            if request_payload is None:
                request_payload = {'note': 'No request payload captured'}
            
            if response_data is None:
                response_data = {
                    'status_code': 200,
                    'response_time_ms': 0,
                    'data': {'note': 'No response data captured'}
                }
            
            # Add payload and response to request_info
            request_info['payload'] = request_payload
            request_info['response'] = response_data
            
        else:
            flow_logs = []
            request_info = {
                'request_id': request_id,
                'formatted_datetime': 'Unknown',
                'method': 'Unknown',
                'endpoint': 'Unknown',
                'payload': {'error': 'Could not load request data'},
                'response': {'error': 'Could not load response data'}
            }
            
        return render_template('request_detail.html', 
                             logs=flow_logs, 
                             request_info=request_info)
        
    except Exception as e:
        return f"Error fetching request details: {str(e)}"

@app.route('/request/<request_id>/step/<int:step_index>')
def step_detail(request_id, step_index):
    """Detailed page for a specific step/sublog"""
    try:
        # Get all logs for this request
        response = requests.get(f"{LOGS_SERVICE_URL}/logs", params={'limit': 1000})
        
        if response.status_code == 200:
            data = response.json()
            all_logs = data.get('logs', [])
            
            # Filter logs for this specific request
            request_logs = [log for log in all_logs if log.get('request_id') == request_id]
            
            if not request_logs:
                return f"No logs found for request ID: {request_id}"
            
            # Sort by timestamp to match the order shown in flow
            request_logs.sort(key=lambda x: x.get('timestamp', 0))
            
            # Get the specific step
            if step_index <= 0 or step_index > len(request_logs):
                return f"Invalid step index: {step_index}"
            
            step_log = request_logs[step_index - 1]  # Convert to 0-based index
            
            # Enhance the step with details
            enhanced_step = enhance_log_with_details(step_log)
            
            # Add formatted time
            enhanced_step['formatted_time'] = timestamp_to_time(enhanced_step.get('timestamp', 0))
            enhanced_step['formatted_datetime'] = timestamp_to_datetime(enhanced_step.get('timestamp', 0))
            
            # Prepare step info for the template
            step_info = {
                'request_id': request_id,
                'step_index': step_index,
                'total_steps': len(request_logs),
                'action': enhanced_step.get('action', 'Unknown'),
                'from_service': enhanced_step.get('from_service', 'Unknown'),
                'to_service': enhanced_step.get('to_service', 'Unknown'),
                'timestamp': enhanced_step.get('timestamp'),
                'formatted_datetime': enhanced_step['formatted_datetime'],
                'formatted_time': enhanced_step['formatted_time'],
                'level': enhanced_step.get('level', 'info'),
                'message': enhanced_step.get('message', ''),
                'details': enhanced_step.get('details', [])
            }
            
            # Extract request data (if this step has it)
            request_data = {
                'method': enhanced_step.get('method'),
                'endpoint': enhanced_step.get('endpoint'),
                'headers': enhanced_step.get('headers', {}),
                'payload': enhanced_step.get('payload'),
                'params': enhanced_step.get('params')
            }
            
            # Extract response data (if this step has it)
            response_data = {
                'status_code': enhanced_step.get('status_code'),
                'response': enhanced_step.get('response'),
                'response_time_ms': enhanced_step.get('response_time_ms'),
                'headers': enhanced_step.get('response_headers', {})
            }
            
            # Extract context/error data
            context_data = {
                'context': enhanced_step.get('context'),
                'error': enhanced_step.get('error'),
                'stack_trace': enhanced_step.get('stack_trace'),
                'additional_data': enhanced_step.get('data')
            }
            
            # Get navigation info (previous/next steps)
            navigation = {
                'has_previous': step_index > 1,
                'has_next': step_index < len(request_logs),
                'previous_step': step_index - 1 if step_index > 1 else None,
                'next_step': step_index + 1 if step_index < len(request_logs) else None
            }
            
            return render_template('step_detail.html',
                                 step_info=step_info,
                                 request_data=request_data,
                                 response_data=response_data,
                                 context_data=context_data,
                                 navigation=navigation)
        
        else:
            return f"Error fetching logs: {response.status_code}"
            
    except Exception as e:
        return f"Error fetching step details: {str(e)}"

def enhance_log_with_details(log):
    """Add simple details to log entries for better debugging"""
    try:
        action = log.get('action', '').lower()
        
        # Add simple details based on action type
        details = []
        
        if 'incoming_request' in action:
            if log.get('payload'):
                payload_str = str(log.get('payload', {}))
                payload_preview = payload_str[:100] + "..." if len(payload_str) > 100 else payload_str
                details.append(f"📤 Payload: {payload_preview}")
            
            method = log.get('method', 'POST')
            endpoint = log.get('endpoint', '/unknown')
            details.append(f"🌐 {method} {endpoint}")
        
        elif 'routing' in action:
            to_service = log.get('to_service', '').replace('service_', '')
            details.append(f"🔀 Routing to {to_service}")
        
        elif 'fetch' in action and 'oggo' in action:
            details.append("📥 Fetching data from Oggo API")
        
        elif 'transform' in action:
            details.append("🔄 Applying field mappings and transformations")
        
        elif 'send' in action and 'hubspot' in action:
            details.append("📤 Sending transformed data to HubSpot")
        
        elif 'api_call' in action:
            to_service = log.get('to_service', '').replace('external_', '').replace('service_', '')
            details.append(f"🔗 Making API call to {to_service}")
        
        elif 'response' in action:
            from_service = log.get('from_service', '').replace('external_', '').replace('service_', '')
            details.append(f"✅ Response received from {from_service}")
        
        elif 'final_response' in action:
            status_code = log.get('status_code', 200)
            response_time = log.get('response_time_ms', 0)
            details.append(f"🏁 Status: {status_code} • Time: {response_time}ms")
        
        elif 'error' in action or 'ERROR' in log.get('to_service', ''):
            error_context = log.get('context', log.get('message', 'Unknown error'))
            error_preview = str(error_context)[:80] + "..." if len(str(error_context)) > 80 else str(error_context)
            details.append(f"❌ Error: {error_preview}")
        
        # Always ensure details is a list (never None or undefined)
        log['details'] = details if details else []
        return log
        
    except Exception as e:
        # If anything goes wrong, return the log with empty details
        log['details'] = []
        return log

@app.route('/clear', methods=['POST'])
def clear_logs():
    """Clear all logs via UI"""
    try:
        response = requests.post(f"{LOGS_SERVICE_URL}/logs/clear")
        if response.status_code == 200:
            return jsonify({'status': 'success', 'message': 'Logs cleared'})
        else:
            return jsonify({'error': 'Failed to clear logs'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)